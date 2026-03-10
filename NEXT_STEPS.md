# GraphRAG-OMOP — Next Steps

Estado actual: Pipeline funcional end-to-end (Phase 1: LLM extraction → Phase 2: FAISS + Graph mapping → Dashboard).
Este documento recoge las mejoras identificadas, decisiones tomadas, y cambios implementados.

---

## Estado actual del pipeline

### Lo que funciona bien
- **Conditions** (hypertension, diabetes, chest pain, dyspnea, edema, heart failure): scores >0.92, resolución estándar correcta via SNOMED
- **Drugs** (enalapril, metformin, liraglutide): scores 1.0, graph traversal SNOMED→RxNorm correcto
- **Graph traversal**: Cuando FAISS encuentra un concepto SNOMED no-estándar, el grafo resuelve correctamente via "Maps to" / "Non-standard to Standard map (OMOP)"
- **FAISS**: Búsqueda semántica en milisegundos sobre 3.8M conceptos
- **Dashboard**: Visualización completa con tabla expandible, export CSV, logs detallados en terminal

---

## Cambios implementados

### P1 — Soporte multiidioma (español → inglés) ✅
**Archivo**: `backend/src/phase1/prompts.py` (Regla 9)

**Problema**: SapBERT está entrenado en UMLS (inglés). Textos en español producen scores bajos y matches incorrectos.

**Solución**: Regla en el prompt de Phase 1 para que GPT-4 extraiga siempre en inglés clínico, independientemente del idioma de entrada. Sin coste extra (traducción dentro de la misma llamada LLM).

---

### P2 — Abreviaturas clínicas mal resueltas ✅
**Archivo**: `backend/src/phase1/prompts.py` (Regla 10)

**Problema**: "eGFR" → "Epidermal growth factor measurement" (score 0.728). SapBERT no entiende abreviaturas, mapea por similitud de texto literal.

**Solución**: Regla en el prompt para que GPT-4 expanda abreviaturas a su forma completa (eGFR → "estimated glomerular filtration rate", HbA1c → "hemoglobin A1c", etc.).

---

### P5 — Conceptos de Clasificación (`C`) sin mapeo estándar ✅
**Archivo**: `backend/src/phase2/graph.py` (`find_standard_mapping`)

**Problema**: Conceptos como "Blood pressure" (LOINC 1003132), "Heart rate" (LOINC 45876226), "furosemide Injectable Product" (RxNorm 36225444) tienen `standard_concept = "C"` (Classification). Son nodos de jerarquía que no tienen aristas "Maps to" — solo "Subsumes", "Is a", "Has ingredient". `find_standard_mapping()` no los manejaba y devolvía `None` → REVIEW innecesario con scores perfectos.

**Investigación realizada**:
- Verificado en datos reales: estos conceptos `C` solo tienen aristas jerárquicas
- Existen 85K conceptos `C` en el grafo (vs 2.5M `S` y 1.25M sin estándar)
- Sí existen LOINC `S` para blood pressure (320) y heart rate (94), pero son ultra-específicos
- Distribución: `S` = 2,516,863 | `NaN` = 1,253,210 | `C` = 85,377

**Solución demo**: Aceptar conceptos `C` como válidos — son conceptos OMOP reales y reconocibles clínicamente.

**Solución futura** (no implementada): Para producción, navegar "Subsumes" hacia abajo para LOINC `C` → LOINC `S`, o "Has ingredient" para RxNorm `C` → RxNorm `S`.

---

### P6 — Campo `original_text` en todo el pipeline ✅
**Archivos**: 6 archivos modificados (ver tabla abajo)

**Problema**: Phase 1 normaliza y traduce conceptos (español → inglés, abreviaturas → forma completa), pero el texto original del documento clínico se perdía. El dashboard solo mostraba el concepto normalizado, sin contexto de dónde venía.

**Solución**: Nuevo campo `original_text` que captura la mención exacta del texto clínico (e.g., "DM tipo 2", "eGFR", "PA sistólica"). Fluye desde Phase 1 hasta el frontend:

| Archivo | Cambio |
|---|---|
| `backend/src/phase1/schema.py` | Campo `original_text: str` en `MedicalConcept` |
| `backend/src/phase1/prompts.py` | Regla 11: incluir `original_text` con texto exacto del documento |
| `backend/schemas.py` | Campo `original_text: Optional[str]` en `ConceptSchema` y `MappingSchema` |
| `backend/routers/phase2.py` | Pass-through de `original_text` + logging cuando difiere del input |
| `frontend/lib/types.ts` | Campo `original_text` en `ExtractedConcept` y `ConceptMapping` |
| `frontend/components/ConceptRow.tsx` | Muestra transformación `"original" → "normalizado"` en vista expandida |

---

## Decisiones tomadas (no implementar)

### P3 — Matches semánticos débiles
**Decisión**: Dejar como está.

"bilateral basal crackles" → "Bilateral pneumonia" (score 0.625) es un match incorrecto, pero el umbral de 0.7 ya lo captura como REVIEW. El sistema hace bien su trabajo: "no estoy seguro, revísalo". Subir el umbral podría generar falsos REVIEW en conceptos que sí matchean bien. Para demo, tener algunos REVIEW demuestra que el sistema sabe cuándo no está seguro.

### P4 — Conceptos duplicados de Phase 1
**Decisión**: No es un bug.

"blood pressure" aparece 2 veces (sistólica 150 mmHg y diastólica 95 mmHg) porque en OMOP CDM son dos mediciones distintas con concept_ids diferentes. Lo mismo con "metformin" 2 veces (850 mg actual y 1000 mg nueva dosis). Es comportamiento correcto.

---

## Resumen de cambios por archivo

| Archivo | Cambio | Motivo |
|---|---|---|
| `backend/src/phase1/prompts.py` | Regla 9: extraer en inglés | SapBERT solo entiende inglés |
| `backend/src/phase1/prompts.py` | Regla 10: expandir abreviaturas | "eGFR" → match incorrecto |
| `backend/src/phase1/prompts.py` | Regla 11: incluir `original_text` | Mostrar transformación texto original → normalizado |
| `backend/src/phase1/schema.py` | Campo `original_text` en `MedicalConcept` | Capturar mención original del documento |
| `backend/schemas.py` | `original_text` en `ConceptSchema` y `MappingSchema` | Transportar campo por la API |
| `backend/routers/phase2.py` | Pass-through + logging de `original_text` | Pasar campo de Phase 1 a respuesta |
| `backend/src/phase2/graph.py` | Aceptar `standard_concept == "C"` | LOINC/RxNorm Classification sin "Maps to" |
| `frontend/lib/types.ts` | `original_text` en interfaces TS | Tipado para el frontend |
| `frontend/components/ConceptRow.tsx` | Mostrar `"original" → "normalizado"` | UX: ver transformación en vista expandida |

---

## Mejoras futuras (post-demo)

| Mejora | Descripción | Complejidad |
|---|---|---|
| Navegación jerárquica `C` → `S` | Para LOINC: bajar por "Subsumes" al `S` más relevante. Para RxNorm: seguir "Has ingredient" | Alta |
| Fallback sin filtro de dominio | Si score con filtro es bajo, reintentar búsqueda sin filtro | Media |
| Validación por palabras clave | Si match_name no comparte palabras con input, marcar REVIEW | Media |
| Deduplicación visual | Agrupar en frontend por standard_id cuando hay múltiples valores | Baja |

---

## Problemática: Normalización pre-SapBERT

### El problema

SapBERT (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`) tiene dos limitaciones clave:
- **No entiende español** (ni otros idiomas): entrenado exclusivamente en UMLS (inglés). Términos como "hipertensión arterial" o "glucosa en sangre" producen matches incorrectos o scores bajos.
- **No resuelve todas las abreviaturas**: algunas como "DM" (diabetes mellitus) funcionan bien (score 0.90) porque son ubicuas en UMLS, pero otras como "eGFR" fallan (matchea "Epidermal growth factor" con 0.728).

Esto implica que los conceptos **deben llegar normalizados a inglés clínico formal** antes de la búsqueda semántica en FAISS.

### Solución actual (1 modelo, 1 paso)

GPT-4 hace extracción + normalización en una sola llamada:
- Regla 9: traduce a inglés clínico
- Regla 10: expande abreviaturas
- Regla 11: preserva `original_text` para trazabilidad

**Ventajas**: eficiente (1 llamada LLM), sin coste extra, funciona bien.
**Riesgo**: el LLM podría alterar el significado al normalizar (bajo riesgo con GPT-4, pero posible).

### Alternativa futura (2 modelos o 2 pasos)

Separar extracción de normalización:
```
Texto clínico → [Modelo 1: extrae tal cual] → conceptos crudos
                                                  ↓
                                  [Modelo 2 o lookup: normaliza] → conceptos para SapBERT
```

**Opciones para el paso de normalización**:
- Otra llamada LLM (más coste y latencia)
- Diccionario/lookup de abreviaturas (rápido, pero limitado a casos conocidos)
- Modelo ligero de normalización médica (BERT fine-tuned)

**Cuándo tiene sentido**: si se cambia SapBERT por un modelo multilingüe que entienda abreviaturas, la normalización se podría desactivar sin tocar Phase 1. El campo `original_text` ya prepara esta separación.

### Decisión actual

Mantener extracción + normalización juntas en Phase 1 (GPT-4). Es la solución más eficiente para el pipeline actual con SapBERT.

---

## Notas técnicas

- **SapBERT** (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`): Embeddings entrenados en UMLS. 768 dimensiones. Fuerte en inglés, débil en otros idiomas y abreviaturas.
- **FAISS IVF**: Índice con 256 clusters, nprobe=10. Búsqueda ~99% precisa vs brute-force. Thread-safe para lectura.
- **Graph**: NetworkX MultiDiGraph. ~3.8M nodos, relaciones OMOP. Traversal via "Maps to" / "Non-standard to Standard map (OMOP)".
- **standard_concept values**: `S` = Standard (2,516,863) | `C` = Classification (85,377) | `NaN` = Non-standard (1,253,210)
- **Relationship types en el grafo**: Standard/Non-standard map, Has dose form, Subsumes/Is a, Tradename of, Has ingredient, Concept replaced by, Contains, Has form, Has basic dose form
- **Umbral REVIEW**: score < 0.7
