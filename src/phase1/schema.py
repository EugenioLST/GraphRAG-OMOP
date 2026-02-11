"""
schema.py - Pydantic schemas for OMOP concept extraction

Defines the data structures for extracted medical concepts.
"""

from typing import Literal, List, Optional, Union
from pydantic import BaseModel, Field


# Valid OMOP domains for extraction
DomainType = Literal["Condition", "Drug", "Procedure", "Measurement", "Observation", "Device"]


class MedicalConcept(BaseModel):
    """A single medical concept extracted from clinical text."""
    text: str = Field(description="The medical term (e.g., 'systolic blood pressure', 'metformin')")
    domain: DomainType = Field(description="OMOP domain classification")
    value: Optional[Union[float, str]] = Field(default=None, description="Numeric value if applicable (e.g., 150 for BP, 1000 for drug dose)")
    unit: Optional[str] = Field(default=None, description="Unit if applicable (e.g., 'mmHg', 'mg')")


class ExtractionResult(BaseModel):
    """Result of extracting medical concepts from clinical text."""
    concepts: List[MedicalConcept] = Field(default_factory=list)
