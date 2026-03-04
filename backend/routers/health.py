"""
Health & Status Endpoints
System monitoring and readiness checks.
"""
import sys
from pathlib import Path
from fastapi import APIRouter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import HealthResponse, StatusResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Always returns OK if API is running.
    """
    return {"status": "ok"}


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    System status endpoint.
    Checks if grafo/retriever is loaded and ready.
    """
    # Import here to avoid circular dependencies
    from src.phase2.main import _retriever

    is_loaded = _retriever is not None

    return {
        "grafo_loaded": is_loaded,
        "grafo_loading": False,  # Simplified: no separate loading state
        "ready": is_loaded,
        "error": None
    }
