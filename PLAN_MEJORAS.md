# Estado, plan y changelog — GraphRAG-OMOP

> Documento único con **todo el estado del proyecto**: primero lo que falta por
> hacer (orden lógico), y al final el **histórico** de lo ya hecho. Para el
> problema general, ver [EXPLICACION_PROBLEMA.md](EXPLICACION_PROBLEMA.md); para el
> diseño de extracción, [FASE1_DISENO_EXTRACCION_INETUM.md](FASE1_DISENO_EXTRACCION_INETUM.md).

**Leyenda:** `[NOSOTROS]` lo hacemos nosotros · `[INETUM]` competencia de Inetum ·
`[COMPARTIDO]` conjunto · ✅ construido · 🟡 demo/POC (prueba, no producción) · ⬜ por hacer.

---

## Estado de un vistazo — qué hay construido vs qué falta

| Componente | Dueño | Estado |
|---|---|---|
| **Pipeline completo end-to-end (demo)** — Fase 1 + Fase 2 funcionando | NOSOTROS | 🟡 Construido como **demo/POC** para probar el pipeline entero |
| Fase 1 extracción (LLM) — versión demo | NOSOTROS | 🟡 Con `gpt-4o-mini` (nube), salida Pydantic |
| Fase 2 mapeo OMOP — SapBERT + FAISS + grafo | NOSOTROS | 🟡 Funciona; con filtro `standard_only` y carga en RAM |
| Ingesta de PDF + extracción local + benchmark de modelos | INETUM | 🟡 POC (notebook); prompt/salida a rediseñar |
| Fase 1 de **producción** (extracción bien hecha) | INETUM | ⬜ Por construir (ver diseño) |
| Golden dataset validado por médico | COMPARTIDO | ⬜ Por construir |
| Mejoras Fase 2 (v1→v3), despliegue, calibración | NOSOTROS | ⬜ Por hacer |

> **Reparto en una frase:** *nosotros tenemos una **demo del pipeline completo** que
> sirve para probar la idea de punta a punta; Inetum debe construir la **Fase 1 de
> producción** (extracción); nosotros mejoramos y ponemos en producción la **Fase 2**.*

---

# PARTE 1 — POR HACER

## Orden de trabajo: Fase A (sin médico) → Fase B (con médico)

La corrección clínica final necesita un médico, pero **casi toda la infra y la
mecánica de búsqueda se pueden validar sin médico**, usando **la propia estructura
de OMOP como verdad** (¿un sinónimo devuelve su concepto? ¿un no-estándar resuelve
a su estándar conocido por "Maps to"?). Dos tipos de validación:

| Validación | ¿Médico? | Qué mide |
|---|---|---|
| **Técnica / estructural** | ❌ No | Performance (latencia, RAM, throughput) + correctitud contra la estructura OMOP |
| **Clínica** | ✅ Sí | "Para ESTE texto de paciente, ¿este es el concepto correcto?" (semántica end-to-end) |

### FASE A — empezar YA, sin validación médica  `[NOSOTROS]`

Orden acordado (1 → 3):

1. **Infra (§3) — primero.** Base vectorial + Neo4j + API stateless (+ mmap).
   Ganancia **cierta** en arranque/RAM/latencia/escala; no toca corrección clínica;
   se necesita igual; y da la plataforma para medir todo lo demás.
2. **Precisión perdida por aproximación.** El índice FAISS está en modo aproximado
   (`nprobe = 10` de 256 clusters, [`retrieve.py`](backend/src/phase2/retrieve.py) —
   ~4% de los datos). Subir `nprobe` / índice exacto recupera vecinos que se
   pierden por aproximación. **Se valida contra búsqueda exacta, sin médico.**
3. **Mecánica de v1 (§2.1) + banco de pruebas.** Sinónimos (`CONCEPT_SYNONYM`),
   quitar `standard_only`, caché. Se valida con **verdad-OMOP** (recall@k: ¿el
   sinónimo devuelve su concepto?, ¿el no-estándar llega a su "Maps to"?). Montar
   aquí el banco de pruebas técnico (recall@k + latencia + RAM) donde luego se
   enchufa el golden clínico.

> Al terminar la Fase A ya hay **mejoras medidas** (performance y precisión
> estructural) **sin depender del médico**.

### FASE B — requiere golden dataset validado por médico  `[COMPARTIDO/NOSOTROS]`

- **Calibrar el umbral** de REVIEW (0.70/0.80, §4) — necesita saber qué *debería*
  ser REVIEW clínicamente.
- **Firma final de v2 (reranking) y v3 (juez LLM)** — se construyen ya, pero el
  "¿es clínicamente mejor?" lo cierra el gold.

---

## §0. Prerrequisitos transversales

### 0.1. Reunión con Inetum  `[COMPARTIDO]` ⬜
Aclarar el diseño de extracción y repartir quién hace qué. Puntos:
- Su pipeline (PDF → MedGemma local → JSON) está bien; se rediseña solo el
  **prompt** y el **esquema de salida**.
- **Extraer ≠ transformar:** extracción literal y determinista, con `source_line`.
- **Traducir a inglés ANTES** con traductor fijo + alineado por línea (proyecto
  multilingüe + benchmark justo de modelos).
- **Dominio OMOP** con precisión máxima; **grounding check** como guardrail.
- Llevar [FASE1_DISENO_EXTRACCION_INETUM.md](FASE1_DISENO_EXTRACCION_INETUM.md).

### 0.2. Golden dataset (validado por médico)  `[COMPARTIDO]` ⬜
Conjunto de tripletes **texto clínico → conceptos extraídos → código OMOP estándar
correcto**, **validado y firmado por un médico**. La verdad del dataset es clínica:
sin la validación de un facultativo no es un "gold" fiable.
- **Por qué es prerrequisito:** sin él, "mejorar la Fase 2" es a ciegas. Con él,
  cada cambio (quitar filtro, sinónimos, rerank, juez, umbral) se mide contra verdad.
- **Sirve a las dos fases:** mide la Fase 1 (precisión de dominio, fidelidad) y
  mide/entrena la Fase 2 (¿el mapeo llega al código gold?).

---

## §1. Fase 1 — extracción

### 1.1. Fase 1 de producción — diseño de etapas  `[INETUM]` ⬜
Tres etapas, cada una con un solo trabajo (detalle en el doc de diseño):
- **Etapa 0 · Traducción a inglés (input-normalization):** traducir **antes** de
  extraer, con **traductor fijo y fuerte** (no los modelos bajo evaluación) y
  **alineado por línea**. Motivo: proyecto multilingüe (ES/IT/EN) + comparación de
  modelos → benchmark justo y mayor precisión (los LLMs van mejor en inglés).
- **Etapa 1 · Extracción (literal, determinista):** `text` + `source_line` +
  `domain` (OMOP) + `value`/`unit` + `date_original`. `original_text` desde la
  línea original alineada (auditable). Solo extrae, no transforma.
- **Etapa 2 · Transformación (posterior):** expandir abreviaturas, fecha ISO, etc.
- **Guardrail estrella:** grounding check — `original_text` literal en su línea.

### 1.2. Ingesta de PDF (paso 0)  `[INETUM]` 🟡→⬜
Ya tienen el POC (PyMuPDF). Falta consolidarlo y usar esquema **anidado**
`encuentro ⊃ conceptos` (metadatos de consulta de Inetum + conceptos OMOP-ready).

### 1.3. Migrar nuestra demo a MedGemma local vía Ollama  `[NOSOTROS]` ⬜
Sustituir en nuestra demo el proveedor OpenAI (`gpt-4o-mini`) por MedGemma en
Ollama. Motivo: privacidad/EHDS — el dato del paciente no puede salir del hospital.
(Inetum ya trabaja local; esto alinea nuestra demo con su enfoque.)

### 1.4. Historias clínicas largas — map-reduce  `[COMPARTIDO]` ⬜
Segmentar con solape → extraer por chunk (en paralelo) → consolidar/deduplicar
(por `text`+`domain`+`date`+`value`) → Fase 2 sobre el conjunto consolidado.

---

## §2. Fase 2 — mapeo a OMOP  `[NOSOTROS]` (medir tras cada versión con el golden dataset)

### 2.1. v1 — base  ⬜
- **Quitar el filtro `standard_only`** (buscar entre todos, resolver a estándar por
  grafo — no perder el puente no-estándar → estándar).
- **Embeber sinónimos** (`CONCEPT_SYNONYM`), no solo el nombre canónico.
- **Caché** por texto normalizado.

### 2.2. v2 — reranking fuerte  ⬜
Reordenar el top-K: **cross-encoder** + coherencia de **dominio** + coherencia de
**grafo** (vecindario OMOP vs resto de la nota) + solape léxico con `original_text`.
(El rerank por grafo es lo que acerca esto a un GraphRAG real.)

### 2.3. v3 — juez LLM gated  ⬜
Juez **MedGemma local**, solo en la banda dudosa. **Elige** el mejor estándar entre
el top-5 (conjunto cerrado → no inventa código), o marca REVIEW. Da confianza + motivo.

---

## §3. Despliegue en producción  `[NOSOTROS]` ⬜
- **Embeddings → base vectorial** always-on (Qdrant / Milvus / pgvector).
- **Grafo → Neo4j** always-on.
- **API stateless** que consulta a ambas → arranca en ~1s, sin cargar nada en RAM.
- (Ortogonal) cuantizar embeddings para encoger el índice.

## §4. Calibración  `[NOSOTROS]` ⬜
- **Umbral de REVIEW:** el código usa **0.70** ([`retrieve.py`](backend/src/phase2/retrieve.py));
  se recordaba **0.80**. Fijar con el golden dataset.

---

## Dependencias (orden sugerido)

```
Reunión Inetum ──► reparto claro
Golden dataset (médico) ──┬──► [INETUM] Fase 1 producción (etapas + PDF)
                          ├──► [NOSOTROS] Fase 1 demo → Ollama
                          └──► [NOSOTROS] Fase 2: v1 ──► v2 ──► v3   (medir en cada salto)
                                                          │
Despliegue producción ◄────────────────────────────────── ┘  (cuando la calidad esté estable)
Calibración de umbral ◄── usa golden dataset
```

---

# PARTE 2 — HECHO (histórico / antiguo NEXT_STEPS)

> Registro de lo **ya construido** y de las decisiones tomadas. Explica *por qué el
> código actual está como está*. ⚠️ Algunas decisiones van a cambiar con el plan de
> arriba (marcadas SUPERSEDED).

## Lo construido (demo/POC del pipeline completo)  `[NOSOTROS]` 🟡

Tenemos una **demo funcional del pipeline entero** (Fase 1 + Fase 2), pensada para
**probar la idea de punta a punta**, no como producción:
- **Fase 1:** extracción con `gpt-4o-mini` (LangChain) → salida Pydantic
  (`MedicalConcept`: `text`, `original_text`, `domain`, `value`, `unit`, `date`).
- **Fase 2:** SapBERT + FAISS sobre ~3M conceptos OMOP + grafo NetworkX para
  resolver a estándar; score + estado OK/REVIEW.
- **Frontend:** dashboard (input, timeline, tabla de mapeo, export).

## Decisiones ya implementadas en el código

### P1 — Soporte multiidioma (ES → EN) ✅
`prompts.py` (Regla 9): el LLM extrae en inglés clínico independientemente del
idioma de entrada. SapBERT solo entiende inglés.
> ⚠️ **SUPERSEDED:** la traducción pasará a ser un paso **previo** (traducir-antes,
> fijo + alineado), separado de la extracción. Ver §1.1.

### P2 — Abreviaturas clínicas ✅
`prompts.py` (Regla 10): el LLM expande abreviaturas ("eGFR" → forma completa),
porque SapBERT no las entiende ("eGFR" mapeaba a "Epidermal growth factor", 0.728).
> ⚠️ **SUPERSEDED:** la expansión pasará a la **Etapa 2 (transformación)**, fuera de
> la extracción literal. Ver §1.1.

### P5 — Conceptos de Clasificación (`C`) ✅
`graph.py` (`find_standard_mapping`): conceptos `C` (p. ej. "Blood pressure" LOINC)
solo tienen aristas jerárquicas, no "Maps to". Distribución real: `S` = 2,516,863 |
sin estándar = 1,253,210 | `C` = 85,377. Solución demo: aceptarlos como válidos.

### P6 — Campo `original_text` en todo el pipeline ✅
Nuevo campo que captura la mención exacta del documento ("DM tipo 2", "eGFR") y
fluye de Phase 1 al frontend. 6 archivos tocados (schema, prompts, schemas, router,
types, ConceptRow). Base de la trazabilidad/auditoría.

## Decisiones tomadas (no implementar)

### P3 — Matches semánticos débiles → dejar como está
"bilateral basal crackles" → "Bilateral pneumonia" (0.625) es incorrecto, pero el
umbral 0.7 ya lo marca REVIEW. Tener algunos REVIEW demuestra que el sistema sabe
cuándo no está seguro.

### P4 — "Duplicados" de Phase 1 → no es bug
"blood pressure" ×2 (sistólica/diastólica) y "metformin" ×2 (850/1000 mg) son
conceptos/medidas distintas en OMOP CDM. Comportamiento correcto.

## Nota histórica: normalización pre-SapBERT (SUPERSEDED)

La decisión original fue **juntar extracción + normalización** en una sola llamada
LLM (eficiente para el pipeline demo con SapBERT). ⚠️ **Cambia con el nuevo plan:**
en el proyecto multilingüe + comparación de modelos, se pasa a **traducir antes** y
a **separar extracción de transformación**. Ver
[FASE1_DISENO_EXTRACCION_INETUM.md](FASE1_DISENO_EXTRACCION_INETUM.md) y §1.1.
