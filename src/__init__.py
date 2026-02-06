"""
GraphRAG-OMOP Source Code

Phase 1: Clinical Concept Extraction (src/phase1/)
- extractor.py: LLM-based concept extraction with domain classification
- prompts.py: OMOP extraction prompts

Phase 2: Semantic Search & Standardization (src/phase2/)
- preprocess.py: OMOP data processing
- graph.py: NetworkX graph management
- embeddings.py: SapBERT embedding generation
- retrieve.py: Semantic search engine
"""

__version__ = "0.3.0"
