"""
GraphRAG-OMOP Backend API - Main Application
FastAPI application for clinical concept extraction and OMOP standardization.
"""
import sys
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from routers import health, phase1, phase2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="GraphRAG-OMOP API",
    description="Clinical concept extraction and OMOP standardization API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(health.router, tags=["System"])
app.include_router(phase1.router, tags=["Processing"])
app.include_router(phase2.router, tags=["Processing"])

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize grafo on server startup."""
    logger.info("🚀 GraphRAG-OMOP API starting...")
    logger.info(f"📊 Backend: http://{settings.backend_host}:{settings.backend_port}")
    logger.info(f"🌐 Frontend CORS: {settings.frontend_url}")
    logger.info(f"📚 API Docs: http://localhost:{settings.backend_port}/docs")
    logger.info("")
    logger.info("⏳ Starting grafo initialization in background...")
    logger.info("   (This may take 15-30 seconds)")
    logger.info("")

    # Start grafo loading in background
    asyncio.create_task(initialize_grafo())


async def initialize_grafo():
    """
    Background task to pre-load retriever/grafo.
    Uses the singleton from src.phase2.main.
    """
    try:
        from src.phase2.main import get_retriever

        logger.info("Loading embeddings and graph...")
        retriever = get_retriever(load_graph=True)

        if retriever is not None:
            logger.info("✅ Grafo initialization complete!")
            logger.info("   System ready for Phase 2 requests.")
        else:
            logger.warning("⚠️ Retriever returned None")

    except Exception as e:
        logger.error(f"❌ Grafo initialization failed: {e}")
        logger.error("   Phase 2 requests will fail until grafo is loaded.")
        logger.error("   Check data files and dependencies.")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GraphRAG-OMOP API",
        "version": "1.0.0",
        "status": "running",
        "docs": f"http://localhost:{settings.backend_port}/docs",
        "endpoints": {
            "health": "GET /health",
            "status": "GET /status",
            "phase1": "POST /phase1",
            "phase2": "POST /phase2"
        }
    }


# ============================================================================
# Run Server (Development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info"
    )
