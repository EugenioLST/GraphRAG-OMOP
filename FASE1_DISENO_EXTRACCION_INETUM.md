# Fase 1 — Diseño de la extracción con LLM (nota para Inetum)

> **Objetivo de esta nota:** vuestro pipeline (PDF → texto → LLM local en Ollama →
> JSON) es la base correcta y os lo reconocemos. Lo que hay que rediseñar es el
> **último paso**: el *prompt* de extracción y el *esquema de salida*. Esta nota
> propone cómo hacerlo para que la extracción sea **precisa, determinista y
> auditable**, y para que su salida encaje con la estandarización a OMOP (Fase 2).
>
> La extracción es vuestra competencia; esto es una propuesta de diseño para
> hacerla juntos lo mejor posible.

---

## 0. Lo que ya está bien y se mantiene

- **PDF → texto** con PyMuPDF. ✅ Correcto, es el paso 0.
- **Todo local en Ollama (MedGemma 4B).** ✅ Imprescindible por privacidad/EHDS.
  El dato del paciente no sale del hospital.
- **Comparar varios modelos y medir energía (CodeCarbon).** ✅ Muy bien; lo
  reutilizamos como parte de la validación (ver §6).
- **Correr N veces por modelo.** ✅ Buena idea; la convertimos en guardrail de
  consenso (ver §5).

---

## 1. El principio rector: EXTRAER ≠ TRANSFORMAR

El problema del prompt actual es que hace un **resumen del documento** (motivo,
datos de consulta…). Un resumen genera prosa: no se puede mapear a un código, no
es determinista y no es auditable. Necesitamos otra tarea: **extracción de
entidades**.

Y sobre todo, separar en dos etapas que **nunca se mezclan**:

```
[ETAPA 1 · EXTRACCIÓN]   ← determinista, literal, fiel al texto
   Sacar lo que pone el documento, TAL CUAL, con su origen. Nada más.
        │
        ▼
[ETAPA 2 · TRANSFORMACIÓN]   ← aquí sí se cambian cosas
   Traducir a inglés clínico, expandir abreviaturas, normalizar fechas a ISO...
```

> **Regla de oro:** en la Etapa 1 **nadie inventa ni cambia nada**. "eGFR" se
> extrae como "eGFR", no como "estimated glomerular filtration rate". La
> expansión, la traducción y el mapeo son **posteriores**. Así la extracción es
> reproducible y se puede auditar contra el documento original.

### Nota sobre la traducción — traducir a inglés ANTES de extraer

SapBERT (Fase 2) necesita inglés clínico, así que la traducción hay que hacerla en
algún momento. En un proyecto **multilingüe** (español, italiano, inglés…) y donde
además **comparamos varios modelos de extracción**, la decisión correcta es
**traducir a inglés primero**, por dos razones:

1. **Elimina el idioma como variable de confusión en el benchmark.** Si cada modelo
   extrajera en su idioma fuente, no sabríamos si una diferencia de rendimiento es
   *el modelo* o *el idioma*. Traduciendo antes, todos los modelos ven **el mismo
   inglés** → la comparación es justa.
2. **La extracción es mejor y más uniforme en inglés.** Los LLMs están mejor
   entrenados en inglés que en italiano o español; extraer en inglés sube la
   precisión y la iguala entre idiomas.

**Cómo hacerlo bien (dos condiciones):**

- **Traductor FIJO y fuerte, no los modelos bajo evaluación.** La traducción la
  hace un modelo de traducción dedicado (p. ej. `translategemma`), una sola vez.
  Así es una **constante controlada**: todos los extractores compiten sobre el
  mismo texto. El idioma deja de ser variable.
- **Alineación por línea** (`línea N original ↔ línea N traducida`). Se extrae del
  inglés, pero el `original_text` se recupera de la **línea original** → el
  grounding check y la auditoría siguen funcionando contra el documento real.

**Coste que se acepta:** un suelo de error de traducción fijo. Como es el mismo para
todos los modelos, no ensucia la comparación; y como se guarda el original
alineado, ese error se puede **medir por separado**.

Lo que **no** hay que hacer: traducir sin alineación (se pierde la trazabilidad
contra el original). Y ojo: la traducción es **input-normalization**, un paso fijo
previo; la extracción sigue siendo **solo extracción** (literal, sin transformar) —
el `original_text` que guarda es el de la línea original, no el traducido.

---

## 2. Qué hay que extraer (Etapa 1)

Concepto a concepto (una entrada por hecho clínico), con estos campos:

| Campo | Qué es | Ejemplo |
|---|---|---|
| `original_text` | La mención **literal** del documento (sin tocar) | `"FK 2mg"`, `"eGFR"`, `"DM tipo 2"` |
| `source_line` | Nº de línea (o span) de donde sale — **para auditar** | `42` |
| `domain` | Dominio OMOP (ver §3) — **máxima precisión** | `"Drug"` |
| `value` | Valor numérico tal cual aparece (o `null`) | `2` |
| `unit` | Unidad tal cual aparece (o `null`) | `"mg"` |
| `date_original` | Expresión temporal **literal** asociada (o `null`) | `"desde marzo 2024"` |

Y a nivel de documento: `document_date` (la fecha del informe) — se usa como
referencia, pero **no se inventa** ninguna fecha por concepto (si no hay
temporalidad en el texto → `null`).

> Fíjate que **no hay campo en inglés todavía**. El nombre clínico normalizado
> (para OMOP) se genera en la Etapa 2. La Etapa 1 solo captura el original.

---

## 3. El campo clave: dominio OMOP (precisión máxima aquí)

Cada concepto debe clasificarse en uno de los 6 dominios OMOP. **Es el campo más
importante**, porque en la Fase 2 el dominio es el *filtro* de la búsqueda: si el
dominio es incorrecto, se busca un fármaco entre diagnósticos → resultado basura.

| Dominio | Qué incluye |
|---|---|
| `Condition` | Diagnósticos, enfermedades, síntomas |
| `Drug` | Medicamentos, prescripciones |
| `Procedure` | Procedimientos, cirugías, intervenciones |
| `Measurement` | Analíticas, constantes, valores de laboratorio |
| `Observation` | Observaciones, estilo de vida, antecedentes |
| `Device` | Dispositivos, implantes |

**Desambiguación por contexto** (hay que dejarlo claro en el prompt, con
ejemplos): el mismo término cambia de dominio según el contexto.

- "insulina" prescrita → `Drug`; "insulina 15 mU/L" (analítica) → `Measurement`.
- "glucosa 120 mg/dL" → `Measurement`; "intolerancia a la glucosa" → `Condition`.
- "marcapasos" mencionado → `Device`; "implante de marcapasos" → `Procedure`.

---

## 4. Reglas de extracción (para el prompt)

1. Extrae **solo** conceptos médicos; ignora nombres, edad, direcciones.
2. **Literal**: copia la mención tal como aparece en `original_text`. No traduzcas,
   no expandas abreviaturas, no corrijas.
3. **Un concepto por entidad.** No agrupes.
4. **Granularidad específica** cuando el texto lo permita: "TA 150/90" son **dos**
   medidas → "TA sistólica" (150) y "TA diastólica" (90), no una sola "tensión".
5. **Valor y unidad separados**, tal como aparecen.
6. **Temporalidad sin inventar**: si hay expresión temporal asociada, cópiala en
   `date_original`; si no la hay, `null`. No deduzcas fechas.
7. **No inventes.** Si no está en el texto, no existe.
8. Devuelve **JSON válido** según el esquema (§ siguiente). Nada de prosa.

---

## 5. Salida estricta + guardrails (auditabilidad)

**Esquema validado (no dict libre).** Definid la salida con un esquema (Pydantic /
JSON Schema) y validadla. Si el modelo se desvía del esquema → reintento
automático. Esto mata el problema de que cada ejecución devuelva formas distintas.

**Guardrails, de más barato a más caro:**

1. **Validación de esquema** (Pydantic). Determinista.
2. **⭐ Grounding check (el más importante y barato):** comprobar que cada
   `original_text` **aparece literalmente** en la línea citada del documento. Es
   una comprobación de string, determinista, y **caza alucinaciones al instante**.
   Si el modelo se inventó algo, no estará en el texto → se rechaza o se marca.
3. **Consenso de N modelos** (lo que ya hacéis con las 3 corridas): correr varios
   modelos/ejecuciones y quedarse con los conceptos en los que hay acuerdo. Los
   que solo aparecen en una corrida → a revisión.
4. **(Opcional) Verificador LLM:** un segundo modelo que revisa "¿este concepto y
   su dominio son correctos respecto al texto?".

> La combinación **esquema + grounding check + consenso** da una extracción muy
> fiable y **100% auditable**: cada concepto tiene su línea de origen y se puede
> comprobar contra el documento.

---

## 6. Qué NO hacer en la Etapa 1 (dejar para después)

Estas cosas son **transformaciones** (Etapa 2), no extracción. Sacarlas de la
extracción la hace más determinista:

- ❌ Traducir a inglés.
- ❌ Expandir abreviaturas ("eGFR" → forma completa).
- ❌ Mapear a OMOP.
- ❌ Resumir o interpretar.

Todo eso se hace **después**, sobre los conceptos ya extraídos, sin tocar el
original. Así, si algún día se cambia el modelo de normalización o el de mapeo, la
extracción no se toca.

---

## 7. Antes / después (el cambio de un vistazo)

**Prompt actual (resumen — a sustituir):**
```
Sácame como diccionario: fecha de la consulta, motivo (breve resumen),
datos de la consulta, valores fuera de rango.
```
→ genera prosa, no mapeable, no determinista, dict libre.

**Prompt propuesto (extracción de entidades):**
```
Eres un extractor de conceptos clínicos. Del texto, extrae CADA concepto médico
como una entrada, LITERAL (sin traducir ni expandir), con:
  - original_text: la mención exacta del texto
  - source_line: la línea de donde sale
  - domain: uno de [Condition, Drug, Procedure, Measurement, Observation, Device]
  - value / unit: si aparecen, separados; si no, null
  - date_original: la expresión temporal literal si la hay; si no, null
Reglas: no inventes; no traduzcas; separa TA en sistólica y diastólica;
un concepto por entidad. Devuelve SOLO JSON válido con este esquema.
```

**Ejemplo de salida (system output correcto):**
```json
{
  "document_date": "2024-03-15",
  "concepts": [
    {"original_text": "FK 2mg", "source_line": 12, "domain": "Drug",
     "value": 2, "unit": "mg", "date_original": null},
    {"original_text": "eGFR 55 ml/min", "source_line": 18, "domain": "Measurement",
     "value": 55, "unit": "ml/min", "date_original": null},
    {"original_text": "TA 150/90", "source_line": 20, "domain": "Measurement",
     "value": 150, "unit": "mmHg", "date_original": null},
    {"original_text": "TA 150/90", "source_line": 20, "domain": "Measurement",
     "value": 90, "unit": "mmHg", "date_original": null}
  ]
}
```
(TA aparece dos veces: sistólica y diastólica → dos measurements.)

---

## 8. Qué probar en la Fase 1 (métricas)

- **Precisión de dominio** (lo más importante): % de conceptos con el dominio OMOP
  correcto. Objetivo: alto.
- **Fidelidad / grounding**: % de `original_text` que aparecen literalmente en el
  documento (idealmente 100%).
- **Reproducibilidad**: variación entre las N corridas del mismo modelo (menos
  variación = mejor).
- **Cobertura**: conceptos extraídos vs conceptos reales (sobre un set anotado a
  mano).
- **Coste/energía** (CodeCarbon): por modelo, para elegir el mejor equilibrio
  calidad/consumo.

---

## Resumen para Inetum

> El pipeline (PDF → MedGemma local → JSON) es correcto. Lo que
> hay que rediseñar es el prompt y la salida del modelo de extracción:
> **extracción de entidades concepto a concepto, literal y con su línea de origen,
> con dominio OMOP (precisión máxima), salida validada por esquema, y guardrails
> (grounding check + consenso).** La traducción, la expansión de abreviaturas y el
> mapeo van **después**, en una etapa aparte. Objetivo: una extracción tan
> determinista y auditable que sirva de **golden dataset** para lo que viene.
