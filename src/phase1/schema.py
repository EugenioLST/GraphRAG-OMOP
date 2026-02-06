"""
schema.py - Pydantic schemas for OMOP concept extraction

Defines the data structures for extracted medical concepts.
"""

from typing import Literal, List
from pydantic import BaseModel, Field


# Valid OMOP domains for extraction
DomainType = Literal["Condition", "Drug", "Procedure", "Measurement", "Observation", "Device"]


class MedicalConcept(BaseModel):
    """A single medical concept extracted from clinical text."""
    text: str = Field(description="The medical term as it appears or normalized")
    domain: DomainType = Field(description="OMOP domain classification")


class ExtractionResult(BaseModel):
    """Result of extracting medical concepts from clinical text."""
    concepts: List[MedicalConcept] = Field(default_factory=list)
