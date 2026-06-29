# PROTECT-CHILD — El problema, y el subproblema que resuelvo (WP5)

> Documento de contexto para una persona técnica que no conoce el proyecto.
> Explica (1) el problema general del proyecto, (2) la pieza concreta que yo
> aporto en **WP5** —el motor que convierte texto clínico libre en códigos OMOP
> estándar— y (3) los retos abiertos y la hoja de ruta de mejora. La
> implementación vive en este repositorio (`GraphRAG-OMOP`), en el *backend*.

---

## 1. El problema general del proyecto

**PROTECT-CHILD** es un proyecto europeo cuyo objetivo clínico es mejorar los
resultados de los **trasplantes pediátricos de riñón e hígado**. Para lograrlo,
quiere entrenar modelos de IA que ayuden a predecir complicaciones y a apoyar la
decisión clínica.

El obstáculo no es el algoritmo de IA. Es **los datos**.

Los datos clínicos que necesitan esos modelos están repartidos en **muchos
hospitales** de distintos países, y tienen tres propiedades que los hacen
inutilizables tal cual:

1. **No se pueden mover.** Por privacidad y por el marco regulatorio europeo
   (EHDS, European Health Data Space), los datos de pacientes no salen del
   hospital de origen. La plataforma es **federada**: el modelo viaja a los
   datos, no al revés.
2. **Son heterogéneos.** Cada hospital usa sus propios sistemas, idiomas,
   abreviaturas y formatos. "Diabetes mellitus tipo 2", "DM2", "T2DM" y
   "diabetes del adulto" son lo mismo para un médico, pero cuatro cosas
   distintas para una máquina.
3. **Están en texto libre.** Gran parte de la información clínica relevante está
   escrita en notas e historias clínicas en lenguaje natural, no en campos
   estructurados con códigos.

> **El problema central, en una frase:** no puedes entrenar un modelo federado
> sobre datos que cada hospital escribe de forma distinta. Antes de que la IA
> pueda aprender, todos los hospitales tienen que estar hablando **el mismo
> idioma de datos**.

Ese "idioma común" es **OMOP CDM** (Common Data Model), un estándar que asigna a
cada concepto médico un código único y universal (`concept_id`). Si el Hospital A
y el Hospital B convierten ambos sus datos a OMOP, un modelo puede entrenarse
sobre los dos sin que ninguno comparta el dato original.

De aquí sale la necesidad concreta que cubro en **WP5**:

> **Un mecanismo que convierta el caos de texto clínico heterogéneo y multilingüe
> en OMOP estándar, de forma automática, con confianza medida y — crítico —
> sin que el dato del paciente salga del hospital.**

---

## 2. Subproblema en WP5 — Armonización automática de texto clínico a OMOP

### 2.1. Qué resuelve

WP5 es el núcleo de datos del proyecto: limpiar, armonizar y estandarizar los
datos clínicos al modelo común OMOP/EHDS. Mi contribución concreta es el motor
que hace la parte más difícil de eso: **convertir una nota clínica en texto
libre — en cualquier idioma — en una lista de códigos OMOP estándar, con una
puntuación de confianza para cada uno.**

```
Entrada:  "Paciente con DM tipo 2, en tratamiento con metformina 850mg"
Salida:   type 2 diabetes mellitus → SNOMED 201826 (Standard), score 0.95, OK
          metformin                → RxNorm 1503297 (Standard), score 0.98, OK · 850 mg
```

El reto de fondo: el mapeo manual de texto clínico a OMOP (lo que en OHDSI se
llama *concept mapping*) es un trabajo experto, lento y que no escala a millones
de registros ni a múltiples hospitales. Este motor lo automatiza, y deja para
revisión humana solo los casos dudosos.

### 2.2. Cómo funciona — pipeline de dos fases

```
Texto clínico libre
      │
      ▼
[Fase 1: Extracción + normalización con LLM médico LOCAL (MedGemma vía Ollama)]
      │   · extrae conceptos médicos del texto
      │   · los clasifica en 6 dominios OMOP (Condition, Drug, Procedure,
      │     Measurement, Observation, Device)
      │   · traduce a inglés clínico (español → inglés)
      │   · expande abreviaturas (eGFR → estimated glomerular filtration rate)
      │   · separa valor y unidad (850 + mg)
      │   · resuelve temporalidad ("hace 3 meses" → fecha ISO con granularidad)
      │   · conserva original_text para trazabilidad
      │   · salida estructurada validada con Pydantic (sin parseo manual de JSON)
      ▼
Conceptos normalizados (estructurados, en inglés clínico)
      │
      ▼
[Fase 2: Búsqueda semántica (RAG) + resolución por grafo OMOP]
      │   · SapBERT genera un embedding (768-dim) del concepto
      │   · búsqueda por similitud coseno contra ~3M conceptos OMOP de Athena
      │   · se toma el más parecido (top-K)
      │   · ¿es estándar (S)? → listo. ¿no? → el grafo OMOP resuelve hasta el S
      │   · si la similitud es baja → se marca REVIEW
      ▼
Concepto mapeado a su concept_id OMOP estándar + score + estado (OK / REVIEW)
```

### 2.3. Fase 1 en detalle — un LLM **médico y local** como extractor y normalizador

La Fase 1 no es solo "extraer entidades". Hace varias cosas en **una sola llamada
al LLM**, lo que la hace eficiente (sin coste ni latencia extra por traducir o
normalizar aparte):

- **Extracción + clasificación de dominio**, sensible al contexto: "insulin" es
  `Drug` si se prescribe pero `Measurement` si es un valor de laboratorio;
  "glucose" es `Measurement` con un valor pero `Condition` en "glucose
  intolerance". El prompt incluye una tabla de desambiguación.
- **Normalización a inglés clínico** ("hipertensión arterial" → "hypertension").
- **Expansión de abreviaturas** ("HbA1c" → "hemoglobin A1c").
- **Granularidad específica:** "BP 150/90" se parte en **dos** conceptos,
  "systolic blood pressure" (150 mmHg) y "diastolic blood pressure" (90 mmHg).
- **Valor y unidad separados** ("metformina 850mg" → `metformin`, `850`, `mg`).
- **Temporalidad con granularidad variable:** "en 2019" → `2019`; "marzo 2024" →
  `2024-03`; "hace 3 meses" → se calcula desde la fecha de referencia.
- **Trazabilidad (`original_text`):** se guarda la mención exacta del documento
  ("DM tipo 2", "eGFR", "PA sistólica") antes de traducir, para que cada código
  sea auditable hasta su origen.

Salida tipada con Pydantic (`MedicalConcept`, `ExtractionResult`): el LLM está
obligado a devolver una estructura válida, no texto libre que haya que parsear.

#### Por qué un modelo **local** (MedGemma + Ollama) y no una API en la nube

Este es un punto **no negociable** dada la premisa del proyecto. Si la extracción
la hiciera una API en la nube (p. ej. GPT-4 de OpenAI), estaríamos **enviando la
historia clínica del paciente a un tercero fuera del hospital** — exactamente lo
que el modelo federado y el EHDS prohíben. Por eso la Fase 1 se ejecuta con un
**LLM open-weights corriendo en local**, orquestado con **Ollama**: el texto del
paciente nunca abandona la infraestructura del hospital.

El modelo elegido es **MedGemma** (Google), un LLM open-weights **especializado en
medicina**. Es la opción adecuada porque combina tres cosas: es abierto (se puede
desplegar on-premise), está afinado en dominio clínico, y rinde a la altura de
modelos mucho más grandes y caros. Benchmarks publicados (MedGemma Technical
Report, 2025):

| Capacidad | Resultado | Comparación |
|---|---|---|
| Razonamiento médico (MedQA, 27B-text) | **87.7%** | A ~3 puntos de DeepSeek R1, a ~1/10 del coste de inferencia |
| Razonamiento médico (MedQA, 4B) | **64.4%** | Top entre modelos abiertos <8B parámetros |
| MedQA (MedGemma 1.5, 4B) | **69%** | +5% sobre la versión anterior |
| Q&A sobre historiales electrónicos (EHRQA, 1.5 4B) | **90%** | +22% sobre la versión anterior (68%) |
| Recuperación de info en EHR (con fine-tuning) | **−50% errores** | A la par de métodos SOTA especializados |

La extracción de órdenes/datos clínicos estructurados —justo nuestro caso de uso—
es una de las tareas donde MedGemma destaca, y mejora con *in-context prompting*
de 1 ejemplo. Que exista una versión **4B** importa: cabe en hardware modesto
(incluido un portátil/estación del hospital) sin GPU de centro de datos, lo que
hace realista el despliegue federado.

> **Nota de estado:** la lógica de extracción ya está escrita para ser
> *provider-agnostic*. La migración del proveedor actual a **MedGemma local vía
> Ollama** es el siguiente paso de implementación (ver §3.3).

### 2.4. Fase 2 en detalle — cómo se construyó y cómo resuelve

Esta fase es la que da el nombre "GraphRAG": combina **señal semántica**
(embeddings) con **estructura del conocimiento** (el grafo de relaciones OMOP).
Se construyó así:

**Construcción (offline, una vez).**
1. Se descargó la **base de datos completa de OHDSI Athena** (los vocabularios
   OMOP: SNOMED, RxNorm, RxNorm Extension, LOINC) a una estación local.
2. Con el modelo **SapBERT** se convirtieron **todos los ~3M conceptos** de Athena
   en embeddings (vectores de 768 dimensiones) → ~15 GB de vectores.
3. Se construyó el **grafo OMOP**: cada concepto es un nodo, cada relación
   (`Maps to`, `Subsumes`, `Has ingredient`, …) es una arista. Grafo enorme
   (~3.8M nodos, ~17M aristas), cacheado en disco para no reconstruirlo.

> **Por qué SapBERT:** está entrenado sobre UMLS específicamente para *biomedical
> entity linking* — es decir, su trabajo nativo es reconocer que dos formas de
> escribir un mismo concepto médico (sinónimos, variantes) caen cerca en el
> espacio vectorial. Es exactamente el problema que tenemos: mapear una mención
> clínica a su concepto canónico. (Su límite: solo inglés clínico — de ahí la
> normalización previa en la Fase 1.)

**Inferencia (online, por cada concepto de la Fase 1).**
1. Se calcula el embedding del concepto con SapBERT.
2. **Similarity search por coseno** contra los ~3M embeddings → se toma el más
   parecido (top-K).
3. **¿El match es estándar (`S`)?** → genial, ya tenemos el `concept_id` OMOP.
4. **¿No es estándar?** → se usa el **grafo** para navegar desde ese concepto
   hasta el concepto estándar equivalente:
   - `NULL` (no estándar): se siguen las aristas de mapeo (`Maps to`,
     `Non-standard to Standard map (OMOP)`, `Concept replaced by`) hasta un `S`.
   - `C` (clasificación, demasiado genérico): se baja la jerarquía por BFS
     (`Subsumes`, `Has ingredient`) buscando un único `S`; si hay varios
     candidatos al mismo nivel → ambiguo → REVIEW en vez de adivinar.
5. **Control de calidad:** si la similitud del match es **baja**, se marca
   `REVIEW`. El sistema **no inventa**: cuando no está seguro, lo dice.

> **⚠️ A reconciliar — umbral de REVIEW.** El diseño habla de marcar REVIEW por
> **debajo del 80% (0.80)** de similitud, pero el código actual
> ([`retrieve.py`](backend/src/phase2/retrieve.py)) usa **0.70**. Hay que fijar
> uno: 0.80 es más conservador (más casos a revisión humana, menos falsos OK);
> 0.70 deja pasar más automáticamente. Conviene calibrarlo con datos reales.

Salida plana y auditable por concepto: `input`, lo que encontró el RAG
(`match_*`), a lo que resolvió el grafo (`standard_*`), `score`, `status`, `note`,
más `value`/`unit`/`date` arrastrados de la Fase 1.

### 2.5. Por qué no es trivial — los problemas reales que hubo que resolver

| Problema | Síntoma | Solución |
|---|---|---|
| **SapBERT solo entiende inglés** | Texto en español → matches incorrectos | La Fase 1 traduce a inglés clínico *antes* de buscar, en la misma llamada |
| **Abreviaturas rompen la búsqueda literal** | "eGFR" → "Epidermal growth factor" (0.728, mal) | El LLM expande abreviaturas antes de buscar |
| **No todo concepto OMOP es estándar** | Conceptos `C` y `NULL` no usables directamente | Navegación del grafo hasta el `S` correcto |
| **Conceptos de clasificación ambiguos** | Un `C` puede subsumir varios `S` | BFS hacia abajo; si hay >1 candidato → REVIEW |
| **Pérdida de trazabilidad al normalizar** | El dato normalizado no decía de dónde venía | Campo `original_text` por todo el pipeline |
| **Falsa confianza** | Un match malo con score alto parecería bueno | Umbral de similitud + estado REVIEW explícito |
| **Privacidad del dato** | Una API en la nube sacaría la historia del hospital | LLM **local** (MedGemma + Ollama): el dato no sale |

### 2.6. Decisión de diseño — normalización *antes* de SapBERT

SapBERT no entiende español ni resuelve todas las abreviaturas, así que los
conceptos **deben llegar ya normalizados a inglés clínico** a la búsqueda. La
decisión fue **juntar extracción + normalización en un único paso (el LLM)** en
vez de separarlas. El campo `original_text` deja la puerta abierta a separarlas en
el futuro (p. ej. si se cambia SapBERT por un modelo multilingüe, se podría
desactivar la normalización sin tocar la extracción).

---

## 3. Retos abiertos y hoja de ruta

Esta sección es deliberadamente crítica: dónde el sistema actual cojea y cómo
mejorarlo.

### 3.1. ¿Esto es "GraphRAG de verdad"? — siendo honestos

**Respuesta corta: es *RAG sobre un grafo de conocimiento*, pero no es GraphRAG en
el sentido canónico** (el de Microsoft GraphRAG). Conviene tenerlo claro para no
vender algo que no es.

- **Lo que sí es:** un pipeline de **entity linking / normalización**. Hay una
  recuperación semántica ("R" de RAG: embeber + buscar el concepto más cercano en
  una base vectorial) y hay un **grafo de conocimiento** (OMOP) que se usa para
  resolver el concepto estándar. Es legítimamente "RAG + grafo".
- **En qué se diferencia del GraphRAG canónico:**
  1. En GraphRAG, el **grafo se construye a partir de tu corpus** (un LLM extrae
     entidades y relaciones de tus documentos). Aquí el grafo es **pre-existente**
     (el vocabulario OMOP de Athena), no se construye del texto clínico.
  2. GraphRAG usa el grafo (comunidades, resúmenes jerárquicos) para **alimentar
     una generación** del LLM que responde una pregunta. Aquí **no hay generación
     final**: el LLM va *antes* (Fase 1), y el grafo se usa para una **resolución
     determinista** (no-estándar → estándar), no para aumentar un prompt.
  3. La recuperación es **vector-only**; el grafo no participa en *elegir* el
     candidato, solo en *normalizarlo* después.
- **Nombre más preciso:** "*semantic concept normalization con resolución por
  grafo de conocimiento*" o "*OMOP concept linking RAG-style*".

**Cómo acercarlo de verdad a GraphRAG (mejora real):** usar el grafo *durante* la
recuperación, no solo después. Por ejemplo: recuperar top-K candidatos por
vector, y **re-rankearlos usando el vecindario en el grafo** (un candidato cuyos
vecinos OMOP encajan con el dominio/contexto del resto de la nota gana puntos).
Eso convertiría el grafo en parte de la *retrieval*, que es la esencia de
GraphRAG.

### 3.2. Historias clínicas largas — el reto de escala del texto

**El problema.** Una historia clínica real puede ser muy larga (decenas de páginas,
años de evolución, múltiples ingresos). Pasarla entera en una sola llamada al LLM
no funciona bien: supera la ventana de contexto del modelo local, se pierde
información en el medio, es lenta y la calidad de extracción cae.

**Estrategia propuesta — *map-reduce* sobre la historia:**

```
Historia larga
   │
   ▼
[1. Segmentar] por encuentros / secciones / fechas (no cortar a ciegas;
   usar solapamiento -sliding window- para no partir un concepto a la mitad)
   │
   ▼
[2. MAP] extraer conceptos de cada chunk en paralelo (cada uno devuelve
   su lista ExtractionResult.concepts)
   │
   ▼
[3. REDUCE] reconciliar el conjunto global:
   · deduplicar por (text, domain, date, value)
   · resolver temporalidad con una fecha de referencia común
   · fusionar/mantener el mismo concepto con varios valores en el tiempo
     (p. ej. creatinina en 3 fechas → 3 measurements, no 1)
   │
   ▼
[4. Fase 2] correr la búsqueda+grafo sobre el conjunto ya consolidado
```

El esquema actual ya **encaja de forma natural** con esto: `ExtractionResult`
devuelve una **lista** de conceptos, así que el paso *map* concatena listas y el
*reduce* las consolida. Retos finos a resolver: deduplicación entre chunks (el
mismo diagnóstico mencionado en varias notas), conflictos de valor/unidad, y
mantener la coherencia temporal cuando un dato se repite en el tiempo.

**Mejoras complementarias:**
- **Pre-filtrado**: pasar al LLM solo las secciones clínicamente densas
  (diagnósticos, tratamientos, labs), saltando texto administrativo.
- **Procesamiento por lotes / streaming** para historias muy grandes, acumulando
  conceptos sin tener todo en memoria.
- **Caché de conceptos ya vistos** en Fase 2 para no re-embeber repetidos.

### 3.3. Apuesta por modelos 100% locales (MedGemma + Ollama)

Más allá de la Fase 1, la dirección estratégica es que **todo el cómputo con datos
de paciente sea local y open-weights**, orquestado con **Ollama**. Esto:

- Cumple la premisa **federada/EHDS** por diseño (el dato no sale del hospital).
- Elimina dependencia de APIs externas, costes por token y límites de tasa.
- Permite afinar (fine-tuning) MedGemma con datos locales sin exfiltrarlos —y los
  benchmarks muestran que el fine-tuning de MedGemma reduce ~50% los errores de
  recuperación en EHR.

**Paso concreto pendiente:** sustituir el proveedor de LLM actual de la Fase 1 por
MedGemma servido con Ollama, manteniendo la salida Pydantic intacta (la interfaz
no cambia, solo el backend del modelo).

### 3.4. Otras mejoras identificadas

| Mejora | Qué aporta | Complejidad |
|---|---|---|
| Re-ranking por grafo en la recuperación (§3.1) | Acerca el sistema a GraphRAG real; mejora la precisión del candidato | Alta |
| Fallback sin filtro de dominio | Si el score con filtro de dominio es bajo, reintentar sin filtro | Media |
| Validación por palabras clave | Si el `match_name` no comparte términos con el input, marcar REVIEW | Media |
| Navegación jerárquica fina `C → S` | Para LOINC/RxNorm, bajar al `S` más relevante en vez de aceptar el `C` | Alta |
| Calibración del umbral de REVIEW | Fijar 0.70 vs 0.80 con datos reales (ver §2.4) | Baja |

---

## 4. Resumen de una línea

- **Problema general:** la IA de PROTECT-CHILD no puede entrenarse hasta que
  todos los hospitales hablen el mismo idioma de datos (OMOP/EHDS), sin mover los
  datos de su sitio.
- **Lo que aporto en WP5:** un motor que traduce texto clínico libre y
  multilingüe a códigos OMOP estándar —con un LLM médico **local** (MedGemma vía
  Ollama) que respeta la premisa federada, búsqueda semántica con SapBERT y
  resolución por grafo OMOP— automatizando el *concept mapping* manual que hoy no
  escala, con confianza medida y trazabilidad.
- **Retos abiertos:** acercar la recuperación a un GraphRAG real, escalar a
  historias clínicas largas (map-reduce) y completar la migración a modelos 100%
  locales.

---

### Fuentes (benchmarks MedGemma)

- [MedGemma Technical Report (arXiv 2507.05201)](https://arxiv.org/pdf/2507.05201)
- [MedGemma: Our most capable open models for health AI development — Google Research](https://research.google/blog/medgemma-our-most-capable-open-models-for-health-ai-development/)
- [MedGemma 1.5 model card — Google for Developers](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card)
- [google/medgemma-27b-it — Hugging Face](https://huggingface.co/google/medgemma-27b-it)
