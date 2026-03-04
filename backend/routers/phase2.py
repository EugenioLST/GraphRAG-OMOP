"""
Phase 2: OMOP Search & Standardization
Search OMOP vocabulary and map concepts to standards.
"""
import sys
import logging
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

        # Process each concept
        mappings = []
        stats = {'total': 0, 'mapped_ok': 0, 'needs_review': 0}

        for concept in request.concepts:
            stats['total'] += 1

            # Search and standardize using existing method
            result = retriever.search_and_standardize(
                query=concept.text,
                domain=concept.domain
            )

            # Add value and unit (pass-through from Phase 1)
            result['value'] = concept.value
            result['unit'] = concept.unit

            mappings.append(result)

            # Update stats
            if result['status'] == 'REVIEW':
                stats['needs_review'] += 1
            else:
                stats['mapped_ok'] += 1

        logger.info(f"✅ Phase 2 success: {stats['mapped_ok']}/{stats['total']} mapped")

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
