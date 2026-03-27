"""
Phase 2: OMOP Search & Standardization
Search OMOP vocabulary and map concepts to standards.
"""
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import Phase2Request, Phase2Response
from src.phase2.main import get_retriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/phase2", response_model=Phase2Response)
async def search_and_map(request: Phase2Request):
    """
    Phase 2: Search OMOP and map concepts to standards.

    For each concept from Phase 1:
    1. Performs semantic search in OMOP vocabulary
    2. Follows graph relationships to find standard concept
    3. Returns mapping with confidence score

    Requires grafo to be loaded (check /status first).

    Args:
        request: List of concepts from Phase 1

    Returns:
        OMOP mappings with statistics

    Raises:
        HTTPException 503: If grafo not loaded yet
        HTTPException 500: If search/mapping fails
    """
    try:
        logger.info(f"🔍 Phase 2 request: {len(request.concepts)} concepts")

        # Get retriever (singleton from src.phase2.main)
        retriever = get_retriever(load_graph=True)

        # Check if retriever is actually loaded
        if retriever is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="System not ready. Grafo still loading. Check /status endpoint."
            )

        # Process all concepts in parallel
        # FAISS index is thread-safe for searches (read-only), no Semaphore needed
        async def process_concept(concept):
            """Process a single concept in a thread."""
            result = await asyncio.to_thread(
                retriever.search_and_standardize,
                query=concept.text,
                domain=concept.domain
            )

            # Add value, unit, original_text, and temporal fields (pass-through from Phase 1)
            result['value'] = concept.value
            result['unit'] = concept.unit
            result['original_text'] = concept.original_text
            result['date'] = concept.date
            result['date_original'] = concept.date_original

            return result

        # Execute all searches in parallel (FAISS handles concurrency natively)
        mappings = await asyncio.gather(*[
            process_concept(concept) for concept in request.concepts
        ])

        # Calculate stats
        stats = {
            'total': len(mappings),
            'mapped_ok': sum(1 for m in mappings if m['status'] != 'REVIEW'),
            'needs_review': sum(1 for m in mappings if m['status'] == 'REVIEW')
        }

        # Detailed per-concept logging for debugging the mapping pipeline
        logger.info("")
        logger.info("=" * 100)
        logger.info("PHASE 2 — DETAILED MAPPING RESULTS")
        logger.info("=" * 100)

        for i, m in enumerate(mappings, 1):
            status_icon = "✅" if m['status'] == 'OK' else "⚠️"
            logger.info(f"")
            logger.info(f"--- Concept {i}/{len(mappings)} {status_icon} [{m['status']}] ---")
            logger.info(f"  INPUT:      \"{m['input']}\" (domain: {m['domain']})")
            if m.get('original_text') and m['original_text'] != m['input']:
                logger.info(f"  ORIGINAL:   \"{m['original_text']}\"")
            if m.get('value') or m.get('unit'):
                logger.info(f"  VALUE:      {m.get('value', '')} {m.get('unit', '')}")
            if m.get('date'):
                logger.info(f"  DATE:       {m['date']} (from: \"{m.get('date_original', '')}\")")

            # RAG match (what FAISS found as closest embedding)
            if m.get('match_name'):
                logger.info(f"  RAG MATCH:  \"{m['match_name']}\" (ID: {m['match_id']}, vocab: {m['match_vocab']})")
                logger.info(f"  SCORE:      {m['score']:.4f} ({m['score']*100:.1f}%)")
            else:
                logger.info(f"  RAG MATCH:  None — no embedding match found")

            # Standard concept (what the graph resolved to)
            if m.get('standard_name'):
                same = m.get('match_id') == m.get('standard_id')
                via = "direct (match IS standard)" if same else "graph traversal (match -> standard)"
                logger.info(f"  STANDARD:   \"{m['standard_name']}\" (ID: {m['standard_id']}, vocab: {m['standard_vocab']})")
                logger.info(f"  RESOLVED:   via {via}")
            else:
                logger.info(f"  STANDARD:   None — no standard mapping found")

            # Note (why it needs review)
            if m.get('note'):
                logger.info(f"  NOTE:       {m['note']}")

        logger.info("")
        logger.info("-" * 100)
        logger.info(f"SUMMARY: {stats['total']} concepts | {stats['mapped_ok']} OK | {stats['needs_review']} REVIEW")
        logger.info("=" * 100)
        logger.info("")

        return {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'mappings': mappings
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"❌ Phase 2 error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OMOP search and mapping failed: {str(e)}"
        )
