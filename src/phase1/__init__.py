"""
Phase 1: Clinical Concept Extraction

Extracts medical concepts from clinical text and assigns OMOP domains.
Uses LLM (GPT-4 via LangChain) to identify and classify medical entities.

Output: List of (concept, domain) pairs for Phase 2 standardization.
"""

from .extractor import extract_medical_entities, visual_json, save_entities
from .schema import MedicalConcept, ExtractionResult, DomainType

__all__ = ['extract_medical_entities', 'visual_json', 'save_entities',
           'MedicalConcept', 'ExtractionResult', 'DomainType']
