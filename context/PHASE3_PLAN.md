# Phase 3: Clinical Concept Extraction

## Overview

Phase 3 adds LLM-based concept extraction from clinical text. This is the **first step** in the pipeline:

```
Clinical Text → [Phase 1: Extractor] → (concept, domain) → [Phase 2: GraphRAG] → OMOP standard
```

## Implementation Status

**Status:** ✅ Implemented (2026-01-27)

### Files Created

| File | Purpose |
|------|---------|
| `src/phase1/__init__.py` | Package initialization |
| `src/phase1/extractor.py` | ConceptExtractor class with LangChain/GPT-4 |
| `src/phase1/prompts.py` | System prompts and domain definitions |

### Files Reorganized

```
src/
├── phase1/                 # Clinical concept extraction (NEW)
│   ├── __init__.py
│   ├── extractor.py       # LLM-based extraction
│   └── prompts.py         # OMOP prompts
│
├── phase2/                 # Semantic search (MOVED)
│   ├── __init__.py
│   ├── preprocess.py
│   ├── graph.py
│   ├── embeddings.py
│   └── retrieve.py
│
└── __init__.py
```

---

## Usage

### Basic Extraction

```bash
# Single text
python -m src.phase1.extractor "Me diagnosticaron diabetes y me recetaron metformina"

# From file
python -m src.phase1.extractor --file historia_clinica.txt

# Grouped by domain
python -m src.phase1.extractor --file historia.txt --grouped
```

### Programmatic Usage

```python
from src.phase1 import ConceptExtractor

extractor = ConceptExtractor()

# Extract concepts
concepts = extractor.extract("Paciente con hipertensión tratado con enalapril")
# Returns: [{"text": "hipertensión", "domain": "Condition"},
#           {"text": "enalapril", "domain": "Drug"}]

# Group by domain
grouped = extractor.extract_by_domain("...")
# Returns: {"Condition": ["hipertensión"], "Drug": ["enalapril"]}
```

---

## OMOP Domains (6 for PoC)

| Domain | Description | Examples |
|--------|-------------|----------|
| **Condition** | Diagnoses, diseases, symptoms | diabetes, hipertensión, infarto |
| **Drug** | Medications, prescriptions | metformina, aspirina, enalapril |
| **Procedure** | Medical procedures | cateterismo, biopsia, cirugía |
| **Measurement** | Lab tests, vital signs | glucosa, presión arterial, colesterol |
| **Observation** | Clinical observations | dolor, fiebre, estado fumador |
| **Device** | Medical devices | marcapasos, stent, bomba insulina |

---

## Design Decisions

### 1. LLM Choice: GPT-4 via LangChain

**Reason:** Best accuracy for medical text extraction in multiple languages.

**Alternatives for future:**
- Claude API (similar quality)
- Local LLMs via Ollama (free but lower accuracy)
- Fine-tuned models for specific domains

### 2. Domain Assignment: LLM Decides by Context

**Current approach:** LLM assigns one domain per concept based on clinical context.

**Future alternatives (documented in prompts.py):**

```python
# Alternative 1: Multiple domains with confidence
{"text": "insulin", "domains": ["Drug", "Measurement"], "confidence": [0.6, 0.4]}

# Alternative 2: Flag uncertain for review
{"text": "insulin", "domain": "Drug", "uncertain": true, "reason": "could be measurement"}

# Alternative 3: All 50 OMOP domains
# Expand beyond the 6 main domains
```

### 3. Output Format: Pure (concept, domain) Pairs

**No dates, no context, no standardization.**

This keeps Phase 1 focused on extraction. Phase 2 handles standardization.

---

## Configuration

### Environment Variables

```bash
# Required for Phase 1
export OPENAI_API_KEY=sk-...
```

### Dependencies

```
langchain>=0.1.0
langchain-openai>=0.1.0
```

---

## Full Pipeline Example (Future)

```python
from src.phase1 import ConceptExtractor
from src.phase2.retrieve import SemanticRetriever

# Initialize
extractor = ConceptExtractor()
retriever = SemanticRetriever()

# Clinical text
text = """
Me llamo Ignacio, tengo 58 años. En junio de 2024 sufrí un infarto
de miocardio. Me prescribieron aspirina y atorvastatina.
"""

# Phase 1: Extract concepts
concepts = extractor.extract(text)
# [{"text": "infarto de miocardio", "domain": "Condition"},
#  {"text": "aspirina", "domain": "Drug"},
#  {"text": "atorvastatina", "domain": "Drug"}]

# Phase 2: Standardize each concept
for c in concepts:
    results = retriever.search(
        query=c["text"],
        top_k=1,
        filters={"domain": c["domain"]}
    )
    if results:
        print(f"{c['text']} → {results[0]['concept_id']} ({results[0]['concept_name']})")
```

---

## Testing

### Test Case 1: Ignacio's History (Spanish)

```bash
python -m src.phase1.extractor "Me llamo Ignacio, tengo 58 años. En junio de 2024 sufrí un infarto de miocardio por el que fui atendido de urgencia en el hospital. Me realizaron un cateterismo y estuve ingresado varios días en la unidad coronaria. Tras el alta, me prescribieron medicación diaria: ácido acetilsalicílico (aspirina) como antiagregante plaquetario, atorvastatina para el control del colesterol, bisoprolol como betabloqueante, y ramipril. En la revisión de enero de 2025, me diagnosticaron hipertensión arterial."
```

**Expected output:**
```json
{
  "concepts": [
    {"text": "infarto de miocardio", "domain": "Condition"},
    {"text": "cateterismo", "domain": "Procedure"},
    {"text": "aspirina", "domain": "Drug"},
    {"text": "atorvastatina", "domain": "Drug"},
    {"text": "bisoprolol", "domain": "Drug"},
    {"text": "ramipril", "domain": "Drug"},
    {"text": "hipertensión arterial", "domain": "Condition"}
  ]
}
```

### Test Case 2: Lauren's Story (English)

```bash
python -m src.phase1.extractor --file lauren_story.txt
```

**Expected domains:**
- Condition: endometriosis, ruptured cyst, high fever, pain
- Procedure: ultrasound, pelvic exam, surgery, scan
- Observation: painful periods, bloated stomach

---

## Future Enhancements

1. **Batch processing** - Process multiple clinical notes efficiently
2. **Confidence scores** - Add extraction confidence
3. **Entity linking validation** - Verify extracted terms exist in OMOP
4. **Multi-language detection** - Auto-detect and handle Spanish/English
5. **Negation detection** - Identify negated concepts ("no diabetes")
6. **Temporal extraction** - Extract dates and temporal relationships

---

## Document Metadata

- **Version:** 1.0
- **Created:** 2026-01-27
- **Status:** Implemented
- **Author:** Claude (with Adolfo's guidance)
