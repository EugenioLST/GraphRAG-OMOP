"""
Phase 1: Clinical Concept Extraction

Extracts medical concepts from clinical text and assigns OMOP domains.
Uses LLM (GPT-4 via LangChain) to identify and classify medical entities.

Output: List of (concept, domain) pairs for Phase 2 standardization.
"""

from .extractor import ConceptExtractor
from .schema import MedicalConcept, ExtractionResult, DomainType

__all__ = ['ConceptExtractor', 'MedicalConcept', 'ExtractionResult', 'DomainType']
