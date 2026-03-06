# GraphRAG-OMOP — Next Steps

Estado actual: Pipeline funcional end-to-end (Phase 1: LLM extraction → Phase 2: FAISS + Graph mapping → Dashboard).
Este documento recoge las mejoras pendientes priorizadas tras las primeras pruebas.

---

## Estado actual del pipeline

### Lo que funciona bien
- **Conditions** (hypertension, diabetes, chest pain, dyspnea, edema, heart failure): scores >0.92, resolución estándar correcta via SNOMED
- **Drugs** (enalapril, metformin, liraglutide): scores 1.0, graph traversal SNOMED→RxNorm correcto
- **Graph traversal**: Cuando FAISS encuentra un concepto SNOMED no-estándar, el grafo resuelve correctamente via "Maps to" / "Non-standard to Standard map (OMOP)"
- **FAISS**: Búsqueda semántica en milisegundos sobre 3.8M conceptos
- **Dashboard**: Visualización completa con tabla expandible, export CSV, logs detallados en terminal

---

## Mejoras priorizadas

### P1 — Soporte multiidioma (español → inglés)
**Prioridad: CRÍTICA** | Esfuerzo: bajo

**Problema**: SapBERT está entrenado en UMLS (inglés). Textos en español producen scores bajos y matches incorrectos. El prompt de Phase 1 no especifica idioma de salida.

**Solución**: Añadir al prompt de Phase 1 (`backend/src/phase1/prompts.py`) una regla para que GPT-4 extraiga siempre los conceptos en inglés clínico, independientemente del idioma del texto de entrada. No añade coste (la traducción ocurre dentro de la misma llamada LLM).

**Cambio**: Añadir en la sección Rules del prompt:
```
- ALWAYS output concept names in English clinical terminology, regardless of the input language
- Example: "hipertensión arterial" → extract as "hypertension"
```

**Archivos**: `backend/src/phase1/prompts.py`

---

### P2 — Measurements LOINC sin mapeo estándar
**Prioridad: ALTA** | Esfuerzo: medio

**Problema**: Conceptos como "blood pressure" (LOINC 1003132), "heart rate" (LOINC 45876226) obtienen score 1.0 del RAG pero `find_standard_mapping()` no encuentra concepto estándar → caen en REVIEW innecesariamente.

**Causa raíz**: `find_standard_mapping()` en `backend/src/phase2/graph.py` busca relaciones "Maps to", "Non-standard to Standard map (OMOP)" y "Concept replaced by". Los conceptos LOINC encontrados no tienen estas aristas en el grafo, o los targets no tienen `standard_concept == 'S'`.

**Investigación necesaria**:
1. Verificar qué aristas tienen los nodos LOINC en el grafo (qué relationship types)
2. En OMOP CDM, LOINC **es** el vocabulario estándar para Measurements — quizá hay que reconocer esto directamente
3. Verificar si el edges.csv tiene las relaciones de mapeo LOINC o si se perdieron en el preprocesamiento

**Posibles soluciones**:
- (a) Ampliar los relationship types que busca `find_standard_mapping()`
- (b) Si un concepto LOINC del dominio Measurement ya tiene `standard_concept == 'S'`, aceptarlo directamente
- (c) Revisar el script de preprocesamiento para asegurar que incluye las relaciones "Maps to" de LOINC

**Archivos**: `backend/src/phase2/graph.py`, posiblemente `data/processed/edges.csv`

---

### P3 — Abreviaturas clínicas mal resueltas
**Prioridad: ALTA** | Esfuerzo: bajo

**Problema**: "eGFR" se mapea a "Epidermal growth factor measurement" (score 0.728) en vez de "estimated Glomerular Filtration Rate". Error clínico grave. El score 0.728 pasa el umbral de 0.7, así que no salta REVIEW.

**Causa raíz**: SapBERT genera embeddings del texto literal. "eGFR" como string se parece más a "EGF" (epidermal growth factor) que a "estimated glomerular filtration rate".

**Solución**: Añadir al prompt de Phase 1 una regla para expandir abreviaturas a su forma clínica completa. GPT-4 sabe que eGFR = "estimated glomerular filtration rate". Sin coste extra.

**Cambio**: Añadir en la sección Rules del prompt:
```
- ALWAYS expand clinical abbreviations to their full form
- Example: "eGFR" → extract as "estimated glomerular filtration rate"
- Example: "HbA1c" → extract as "hemoglobin A1c"
- Example: "BP" → extract as "blood pressure"
```

**Archivos**: `backend/src/phase1/prompts.py`

---

### P4 — Matches semánticos débiles (hallazgos físicos)
**Prioridad: MEDIA** | Esfuerzo: medio

**Problema**: "bilateral basal crackles" → "Bilateral pneumonia" (score 0.625). El match es incorrecto (crackles = hallazgo de auscultación, no diagnóstico). El score bajo lo marca como REVIEW (correcto), pero el match sugerido puede confundir al revisor.

**Causa raíz**: El vocabulario OMOP puede no tener un concepto exacto para "crackles". SapBERT se agarra a "bilateral" como señal semántica compartida.

**Posibles mejoras**:
- (a) Subir el umbral de REVIEW de 0.7 a 0.75
- (b) Implementar fallback: si el score con filtro de dominio es bajo, reintentar sin filtro de dominio
- (c) Añadir un segundo nivel de validación: si el match_name no comparte palabras clave con el input, marcar como REVIEW incluso con score alto

**Archivos**: `backend/src/phase2/retrieve.py` (umbral en `search_and_standardize`)

---

### P5 — Furosemide Injectable sin estándar
**Prioridad: MEDIA** | Esfuerzo: depende de P2

**Problema**: "intravenous furosemide" → "furosemide Injectable Product" (RxNorm 36225444, score 0.916) pero `STANDARD: None`.

**Causa raíz**: Mismo patrón que P2 — el concepto RxNorm encontrado no tiene relación "Maps to" hacia un concepto estándar en el grafo. Probablemente se resuelve junto con P2.

**Nota**: El concepto RxNorm "furosemide Injectable Product" puede ser un concepto de clasificación (no prescripción). El estándar sería un Clinical Drug como "furosemide 10 MG/ML Injectable Solution".

---

### P6 — Conceptos duplicados de Phase 1
**Prioridad: BAJA** | Esfuerzo: bajo

**Problema**: Phase 1 extrae "blood pressure" 2 veces (sistólica y diastólica), "metformin" 2 veces (dosis actual y nueva). Genera mapeos duplicados en Phase 2.

**Nota**: No es realmente un bug — GPT-4 extrae correctamente cada mención con su valor/unidad. Los duplicados tienen valores diferentes (150 mmHg vs 95 mmHg, 850 mg vs 1000 mg).

**Posible mejora** (opcional):
- Deduplicar en frontend agrupando por concept + standard_id
- O añadir lógica de merge post-Phase 2 que agrupe mapeos idénticos

**Archivos**: Frontend o `backend/routers/phase2.py`

---

## Orden de implementación sugerido

| # | Fix | Esfuerzo | Impacto | Resuelve |
|---|-----|----------|---------|----------|
| 1 | Prompt: inglés + expandir abreviaturas | ~5 min | Alto | P1 + P3 |
| 2 | Investigar LOINC en grafo + ajustar mapeo | ~30 min | Alto | P2 + P5 |
| 3 | Ajustar umbral / fallback sin filtro dominio | ~15 min | Medio | P4 |
| 4 | Deduplicación en frontend (opcional) | ~15 min | Bajo | P6 |

---

## Notas técnicas

- **SapBERT** (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`): Modelo de embeddings entrenado en UMLS. Fuerte en inglés, débil en otros idiomas y abreviaturas.
- **FAISS IVF**: Índice con 256 clusters, nprobe=10. Búsqueda ~99% precisa vs brute-force.
- **Graph**: NetworkX MultiDiGraph con ~3.8M nodos y relaciones OMOP. Traversal via "Maps to" para encontrar estándar.
- **Umbral actual**: score < 0.7 → REVIEW
