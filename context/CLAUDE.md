# CLAUDE.md — GraphRAG-OMOP Project Context

This file provides persistent project-specific context for Claude.
It is loaded automatically in every session.

# 1. Project Overview or PRD

## **Purpose of the project**

PoC de Concept Linking OMOP que convierte un término médico en lenguaje humano → concept_id OMOP estándar → relaciones relevantes, usando embeddings + grafo mínimo.

## **Core functionality**

Dado **un término médico** (ej: "metformina", "diabetes mellitus", "creatinina"), el sistema:

1. Encuentra el **concepto estándar OMOP** más relevante (SNOMED, RxNorm, LOINC)
2. Devuelve: concept_id, concept_name, vocabulary_id, domain_id
3. Recupera **relaciones relevantes** (1 hop) del grafo OMOP
4. Presenta una **respuesta estructurada** basada exclusivamente en datos del grafo

**Limitaciones del PoC:** Solo términos simples (1-3 palabras). No procesa frases completas ni hace prediagnóstico.

## **Target users / domain**

- **Dominio:** Salud / Clinical Informatics
- **Usuarios:** Investigadores médicos, profesionales de la salud, desarrolladores de sistemas clínicos
- **Uso:** Normalización de términos médicos a vocabulario estándar OMOP

## **Tech stack**

- **Python 3.12** con pandas, networkx, sentence-transformers, numpy
- **NetworkX** para grafo en memoria (no Neo4j)
- **Embeddings:** por definir
- **LLM:** Opcional para formateo de respuestas (ver sección 5 para detalles)

---

## **📘 PRD Completo — PoC de Concept Linking OMOP**

**Versión:** 1.0
**Autor:** Adolfo

### **🧩 1. Archivos de entrada disponibles**

CSVs disponibles en `/data/`:

- **CONCEPT.csv** (obligatorio)
- **CONCEPT_RELATIONSHIP.csv** (obligatorio)
- **RELATIONSHIP.csv** (obligatorio)

⚠ Para el PoC **solo son obligatorios estos 3**. (El resto de CSVs se ignoran)

### **🎯 2. Flujo funcional del PoC**

#### **Paso 1 — Input del usuario**

El usuario introduce un término médico simple (ejemplos: "metformina", "diabetes", "creatinina")

#### **Paso 2 — Búsqueda semántica (embeddings)**

1. Generar embedding del término de entrada
2. Compararlo contra embeddings del campo `concept_name` en CONCEPT.csv
3. Obtener el **top 5 conceptos más similares** (top-K configurable)

#### **Paso 3 — Selección del mejor concepto**

Devolver:

- concept_id
- concept_name
- vocabulary_id (SNOMED, RxNorm…)
- domain_id (Condition, Drug…)

#### **Paso 4 — Expansión 1-hop en el grafo**

Usando **CONCEPT_RELATIONSHIP.csv**:

- Buscar relaciones donde concept_id aparezca como src o dest
- Traducir relationship_id usando RELATIONSHIP.csv
- Recuperar 3–10 relaciones relevantes

Ejemplo:

```
Metformin (RxNorm)
 - has_ingredient → metformin hydrochloride
 - is_a → Biguanide
 - maps_to → Metformin 500 mg oral tablet
```

#### **Paso 5 — Construcción del contexto**

Generar un bloque textual estructurado:

```
Concepto encontrado:
  concept_id: XXXX
  nombre: YYYYY
  vocabulary: SNOMED/RxNorm/LOINC
  dominio: Condition/Drug/Measurement

Relaciones principales:
  - X --relationship_name--> Y
  - X --relationship_name--> Z
```

#### **Paso 6 — Formateo de respuesta (opcional)**

Opcionalmente, usar un LLM para presentar la información de forma clara. El LLM solo formatea, nunca inventa datos.

### **⚠ 4. Requerimientos no funcionales**

- **Simplicidad:** Código directo, sin dependencias complejas, sin UI
- **Arquitectura:** NetworkX (no Neo4j), embeddings sin coste monetario para el desarrollador
- **Scope:** Solo términos simples (ver sección 1 y 6 para limitaciones)

### **🧪 5. Validación**

**Términos de prueba obligatorios:** "metformina", "diabetes", "creatinina", "ibuprofeno", "hipertensión"

**Criterios de éxito para cada término:**

- concept_id, concept_name y vocabulary correctos
- Mínimo 2-5 relaciones relevantes recuperadas

### **🙋‍♂️ 7. Decisiones manuales (NO decidir automáticamente)**

1. **top_K** (5 recomendado)
2. Si incluir CONCEPT_ANCESTOR para jerarquías
3. Si usar LLM para formatear la respuesta final
4. Qué vocabularios considerar prioritarios (SNOMED, RxNorm, LOINC)

---

# 2. Core files to ALWAYS Consider

* `context/ARCHITECTURE.md` - **Arquitectura detallada del sistema**: estructura, flujo de datos, decisiones arquitecturales
* `context/CLAUDE.md` - Este archivo, contexto general del proyecto grafo NetworkX
* `requirements.txt` - Dependencias del proyecto
* `data/` - Directorio con CSVs originales OMOP (⚠ NUNCA modificar estos archivos)

# 3. Extra context and concepts

## **📄 Conceptos OMOP y GraphRAG específicos del proyecto**

### **3.1 Qué es OMOP y por qué se usa**

OMOP es un modelo de datos estandarizado usado mundialmente para representar información clínica.

Incluye un **vocabulario unificado** con conceptos de:

- Enfermedades (SNOMED)
- Medicamentos (RxNorm)
- Laboratorios (LOINC)
- Procedimientos
- Observaciones clínicas
- Ingredientes farmacológicos
- Otros vocabularios médicos

**Cada concepto clínico en OMOP tiene un ID único llamado `concept_id`.**

Este ID permite referirse de forma estandarizada a condiciones, medicamentos, tests, mediciones, etc.

Ejemplo:

```
201826 → Diabetes mellitus (SNOMED)
1503297 → Metformin (RxNorm)
```

### **3.2 Qué significa "Concept Linking"**

**Concept Linking** es normalizar términos médicos en lenguaje natural a conceptos estándar OMOP con sus relaciones del grafo. Esto permite que el texto clínico tenga sentido computacional y sea interoperable entre sistemas.

### **3.3 Qué son los CSV de OMOP y qué contiene cada uno**

#### **CONCEPT.csv (NODOS)**

Contiene **todos los conceptos médicos**. Cada fila es un nodo del grafo.

Columnas clave:

- `concept_id`: identificador único del concepto
- `concept_name`: nombre del concepto
- `vocabulary_id`: vocabulario de donde viene (SNOMED, RxNorm, LOINC)
- `domain_id`: tipo de concepto (Condition, Drug, Measurement…)
- `concept_class_id`: subcategoría

Esto es la **base del universo clínico**.

#### **CONCEPT_RELATIONSHIP.csv (ARISTAS)**

Contiene relaciones entre conceptos. Cada fila es una arista del grafo:

- `concept_id_1`
- `relationship_id`
- `concept_id_2`

Ejemplos:

- metformin → has_ingredient → metformin hydrochloride
- creatinine → measures → blood creatinine
- diabetes → is_a → endocrine disorder

Esto construye la **semántica** del grafo.

#### **RELATIONSHIP.csv (Diccionario de relaciones)**

Define qué significa cada `relationship_id`.

Ejemplo:

- 44818867 = "Is a"
- 46233673 = "Has ingredient"
- 45754819 = "Maps to"

El modelo necesita esto para convertir IDs en relaciones legibles.

#### **CONCEPT_ANCESTOR.csv (Jerarquía opcional)**

Define jerarquías padre-hijo:

- ancestor_concept_id
- descendant_concept_id

Ejemplo:

- "diabetes" ← es un tipo de ← "disease"
- "metformin 500mg tablet" ← es un tipo de ← "metformin product"

Opcional en el PoC, pero útil para entender agrupaciones.

#### **CONCEPT_SYNONYM.csv (opcional para embeddings)**

Lista sinónimos del concept_name.

Ejemplo:

- "DM" → "Diabetes Mellitus", concept_id=201826

Sirve para mejorar búsquedas. No necesario para el PoC inicial.

### **3.4 Qué es GraphRAG y por qué lo usamos**

GraphRAG es un enfoque de Recuperación Aumentada (RAG) que usa:

1. **Embeddings** para buscar los nodos más relevantes por semántica
2. **El grafo** para expandir relaciones relevantes y construir contexto
3. **Un LLM** para responder basado en ese contexto

**Motivos para usar GraphRAG con OMOP:**

- Evita alucinaciones
- Garantiza respuestas fieles al vocabulario médico
- Permite relacionar conceptos clínicos de forma estructurada
- Facilita la normalización de conceptos

### **3.5 Reglas de desarrollo**

- **Naming style**: snake_case para Python (archivos, variables, funciones)
- **Error handling**: Validar existencia de CSVs antes de procesarlos
- **Integridad de datos**: Ver sección 6 para advertencias sobre datos clínicos
- **Arquitectura obligatoria**: NetworkX (nunca Neo4j). Ver sección 6 para detalles

---

# 4. Project-Specific Warnings

### **⚠ Integridad de datos clínicos (CRÍTICO)**

- **NUNCA modificar** los CSV en `/data/` - son la fuente única de verdad
- **NO inventar** concept_ids, concept_names o relaciones médicas
- **NO extrapolar** información más allá de lo que OMOP proporciona
- **LLM solo formatea**, nunca agrega contenido médico

### **⚠ Scope y limitaciones del PoC**

- **NO es un sistema de diagnóstico**
- **Solo términos simples** (1-3 palabras). No frases completas ni extracción de múltiples conceptos
- **No implementar** funcionalidades más allá del PRD sin aprobación explícita
