# TASKS.md — Feature Implementation Log

---

## Feature: Temporal Detection + Patient Journey Timeline

**Date:** 2026-03-19
**Status:** COMPLETED

### What was implemented

Phase 1 (GPT-4 extraction) now detects temporal information for each medical concept, and the frontend displays a visual patient journey timeline.

### Backend changes (7 files)

| File | Change |
|---|---|
| `backend/src/phase1/schema.py` | Added `date`, `date_original` to `MedicalConcept`; `reference_date` to `ExtractionResult` |
| `backend/src/phase1/prompts.py` | Added rules 12-14: temporal extraction, reference date, temporal association. Added `{reference_date}` placeholder and examples table |
| `backend/src/phase1/extractor.py` | `extract_medical_entities()` accepts `reference_date`, defaults to today, passes to chain |
| `backend/src/phase1/main.py` | `run_extraction()` passes `reference_date` through |
| `backend/schemas.py` | `reference_date` in Phase1Request/Response; `date`, `date_original` in ConceptSchema and MappingSchema |
| `backend/routers/phase1.py` | Passes `request.reference_date` to `run_extraction()` |
| `backend/routers/phase2.py` | Pass-through of `date` and `date_original` from Phase 1 concepts to mapping results |

### Frontend changes (7 files, 1 new)

| File | Change |
|---|---|
| `frontend/lib/types.ts` | `date`, `date_original` on ExtractedConcept/ConceptMapping; `reference_date` on Phase1Request/Response; `DOMAIN_DOT_COLORS` constant |
| `frontend/lib/api.ts` | `extractConcepts()` accepts optional `referenceDate` parameter |
| `frontend/components/InputSection.tsx` | Added date picker for optional document reference date |
| **`frontend/components/TimelineView.tsx`** | **NEW** — Horizontal patient journey timeline (CSS/Tailwind, no chart library) |
| `frontend/app/page.tsx` | Wired `referenceDate` state, passes to InputSection and extractConcepts, renders TimelineView |
| `frontend/lib/csv-export.ts` | Added "Date" and "Date Original" columns |
| `frontend/components/ConceptRow.tsx` | Shows temporal info in expanded row details |
| `frontend/components/ResultsTable.tsx` | Fixed type narrowing for nullable sort fields |

### How it works

1. User enters clinical text (optionally sets a document reference date)
2. Phase 1 (GPT-4) extracts concepts WITH temporal info: `date` (ISO, variable granularity), `date_original` (verbatim expression), `reference_date` (auto-detected or user-provided)
3. Phase 2 passes temporal fields through unchanged
4. TimelineView renders horizontal timeline with domain-colored pills, tooltips, and undated events section
5. CSV export includes Date and Date Original columns

### Design decisions

- Variable granularity: YYYY / YYYY-MM / YYYY-MM-DD — never invents precision
- Null when unknown: no temporal info → both fields null
- Explicit association only: only link date to concept if explicitly stated in text
- No new dependencies: pure CSS/Tailwind + existing shadcn tooltips
- All fields Optional: fully backward compatible

### Validation

- [x] Frontend builds successfully (`next build`)
- [x] Backend schemas validate (Pydantic)
- [ ] End-to-end test (requires running backend with FAISS index)

---

### TASK CLAVE PARA EL FUTURO (no borrar, cualquier texto que generes, arriba de esto)

La clave para evaular este proyecto es evaluar los embeddings. Son los que generan los vectores, luego la búsqueda es matemática.

Por eso, necesitamos unos embeddings buenos. Tocará crear un dataset de evaluación con conceptos y estándares para que cada modelo de embedding sea evaluado.

Los LLMs aquí solo son para darle formato a la respuesta

Embeddings a probar o usar: 



# 🏆 **1. SapBERT (el mejor para terminología médica y ontologías)**

 **Especializado en UMLS / SNOMED / vocabularios clínicos** .

Es el embedding más adecuado para concept linking médico.

👉 **HuggingFace:**

[https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext)

(Autor: Cambridge Language Technology Lab)

**Por qué es el mejor para tu caso:**

* Entrenado específicamente en entidades biomédicas estándar
* Excelente en normalización de conceptos
* Entiende sinónimos clínicos
* Superior a modelos generales en tareas UMLS, SNOMED, RxNorm

---

# ⭐ **2. BioBERT / PubMedBERT — embeddings biomédicos generales**

Modelos entrenados en PubMed.

No son tan buenos como SapBERT en ontologías, pero mucho mejores que embeddings generalistas.

👉 **BioBERT Base v1.1 (HuggingFace):**

[https://huggingface.co/dmis-lab/biobert-base-cased-v1.1](https://huggingface.co/dmis-lab/biobert-base-cased-v1.1)

👉 **PubMedBERT (full-text):**

[https://huggingface.co/microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext]()

**Por qué usarlos:**

* Capturan vocabulario biomédico mejor que modelos generalistas
* Funcionan bien cuando los conceptos no están exactamente en SNOMED
* Robustez ante términos clínicos y síntomas

---

# ✔️ **3. All-MiniLM-L6-v2 (baseline generalista sorprendentemente robusto)**

Modelo pequeño, rápido y muy eficiente, ideal como baseline o fallback.

👉 **HuggingFace:**

[https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

**Cuándo usarlo:**

* Para comparar rendimiento con modelos biomédicos
* Para PoC rápidos
* Cuando quieres velocidad y carga ligera

**Advertencia:**

* Funciona bien con términos comunes
* Pero falla en casos clínicos especializados
* No entiende jerarquías médicas ni sinónimos complejos como SapBERT
