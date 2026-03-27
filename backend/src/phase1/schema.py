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
    text: str = Field(description="The medical term in English clinical terminology (e.g., 'systolic blood pressure', 'metformin')")
    original_text: str = Field(description="The exact text as it appears in the clinical document before translation or expansion (e.g., 'PA sistólica', 'eGFR')")
    domain: DomainType = Field(description="OMOP domain classification")
    value: Optional[Union[float, str]] = Field(default=None, description="Numeric value if applicable (e.g., 150 for BP, 1000 for drug dose)")
    unit: Optional[str] = Field(default=None, description="Unit if applicable (e.g., 'mmHg', 'mg')")
    date: Optional[str] = Field(default=None, description="ISO date with variable granularity: 'YYYY', 'YYYY-MM', or 'YYYY-MM-DD'. null if no temporal info.")
    date_original: Optional[str] = Field(default=None, description="Original temporal expression from text (e.g., 'hace 3 meses', 'en 2019', 'last March')")


class ExtractionResult(BaseModel):
    """Result of extracting medical concepts from clinical text."""
    reference_date: Optional[str] = Field(default=None, description="Document reference date detected from text in YYYY-MM-DD format")
    concepts: List[MedicalConcept] = Field(default_factory=list)
