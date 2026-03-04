"""
Phase 1: Clinical Concept Extraction
Extracts medical concepts from clinical text using GPT-4.
"""
import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import Phase1Request, Phase1Response
from src.phase1.main import run_extraction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/phase1", response_model=Phase1Response)
async def extract_concepts(request: Phase1Request):
    """
    Phase 1: Extract medical concepts from clinical text.

    Uses GPT-4 to identify and classify medical concepts by OMOP domain.
    Does not require grafo to be loaded.

    Args:
        request: Clinical text to analyze

    Returns:
        Extracted concepts with domain classifications

    Raises:
        HTTPException 500: If extraction fails
    """
    try:
        logger.info(f"📝 Phase 1 request: {len(request.text)} chars")

        # Call existing function from src.phase1.main
        result = run_extraction(request.text, save_output=False)

        logger.info(f"✅ Phase 1 success: {len(result['concepts'])} concepts")
        return result

    except Exception as e:
        logger.error(f"❌ Phase 1 error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concept extraction failed: {str(e)}"
        )
