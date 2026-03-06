"""
Pydantic Schemas for API Request/Response Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================================================
# System Endpoints
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="ok", description="API health status")


class StatusResponse(BaseModel):
    """System status response."""
    grafo_loaded: bool = Field(description="Whether grafo is loaded")
    grafo_loading: bool = Field(description="Whether grafo is loading")
    ready: bool = Field(description="Whether system is ready")
    error: Optional[str] = Field(default=None, description="Error message if any")


# ============================================================================
# Phase 1: Concept Extraction
# ============================================================================

class Phase1Request(BaseModel):
    """Phase 1 extraction request."""
    text: str = Field(description="Clinical text to analyze", min_length=1)


class ConceptSchema(BaseModel):
    """Extracted medical concept."""
    text: str = Field(description="Concept text")
    domain: str = Field(description="OMOP domain (Condition, Drug, etc)")
    value: Optional[float] = Field(default=None, description="Measurement value")
    unit: Optional[str] = Field(default=None, description="Measurement unit")


class Phase1Response(BaseModel):
    """Phase 1 extraction response."""
    concepts: List[ConceptSchema] = Field(description="Extracted concepts")


# ============================================================================
# Phase 2: OMOP Search & Mapping
# ============================================================================

class Phase2Request(BaseModel):
    """Phase 2 search request."""
    concepts: List[ConceptSchema] = Field(
        description="Concepts from Phase 1",
        min_length=1
    )


class MappingSchema(BaseModel):
    """OMOP concept mapping."""
    input: str = Field(description="Input concept text")
    domain: str = Field(description="OMOP domain")
    match_name: Optional[str] = Field(default=None, description="Best match concept name")
    match_id: Optional[int] = Field(default=None, description="Match concept ID")
    match_vocab: Optional[str] = Field(default=None, description="Match vocabulary")
    score: Optional[float] = Field(default=None, description="Similarity score (0-1)")
    standard_name: Optional[str] = Field(default=None, description="Standard OMOP concept name")
    standard_id: Optional[int] = Field(default=None, description="Standard concept ID")
    standard_vocab: Optional[str] = Field(default=None, description="Standard vocabulary")
    status: str = Field(description="Mapping status (OK/REVIEW)")
    note: Optional[str] = Field(default=None, description="Review note")
    value: Optional[float] = Field(default=None, description="Measurement value")
    unit: Optional[str] = Field(default=None, description="Measurement unit")


class StatsSchema(BaseModel):
    """Processing statistics."""
    total: int = Field(description="Total concepts")
    mapped_ok: int = Field(description="Successfully mapped")
    needs_review: int = Field(description="Needs review")


class Phase2Response(BaseModel):
    """Phase 2 search response."""
    timestamp: str = Field(description="Processing timestamp (ISO)")
    stats: StatsSchema = Field(description="Processing stats")
    mappings: List[MappingSchema] = Field(description="Concept mappings")
