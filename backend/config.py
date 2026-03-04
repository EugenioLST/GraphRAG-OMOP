"""
Backend Configuration
Manages environment variables and application settings.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API
    openai_api_key: str

    # Backend Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Frontend URL for CORS
    frontend_url: str = "http://localhost:3000"

    # Project paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    embeddings_dir: Path = data_dir / "embeddings"
    output_dir: Path = data_dir / "output"

    class Config:
        env_file = Path(__file__).parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


# Validate required paths exist
def validate_environment():
    """Validate that required directories and files exist."""
    errors = []

    # Check embeddings exist
    embeddings_file = settings.embeddings_dir / "embeddings.npy"
    if not embeddings_file.exists():
        errors.append(f"Embeddings file not found: {embeddings_file}")

    # Check data directory
    if not settings.data_dir.exists():
        errors.append(f"Data directory not found: {settings.data_dir}")

    if errors:
        error_msg = "\n".join(errors)
        raise EnvironmentError(
            f"Environment validation failed:\n{error_msg}\n\n"
            "Please ensure you have:\n"
            "1. Generated embeddings: python -m src.phase2.embeddings --max-concepts 100000\n"
            "2. Data files in place (nodes.csv, edges.csv, omop_graph.pkl)"
        )

    return True
