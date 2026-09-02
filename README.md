# GraphRAG-OMOP

Sistema de **Concept Linking** para vocabulario OMOP que convierte texto clínico en conceptos médicos estandarizados.

```
Texto Clínico → [Phase 1: Extracción LLM] → Conceptos → [Phase 2: Búsqueda Semántica] → OMOP Estándar
```

## 📚 Entender el proyecto (empieza aquí)

Si abres este repo por primera vez, lee estos tres documentos en orden:

| Documento | Qué explica |
|---|---|
| [EXPLICACION_PROBLEMA.md](EXPLICACION_PROBLEMA.md) | **El problema.** Qué resuelve PROTECT-CHILD (WP5) y cómo funciona el motor texto clínico → OMOP. |
| [PLAN_MEJORAS.md](PLAN_MEJORAS.md) | **Estado, plan y changelog (todo en uno).** Arriba lo que falta (nosotros vs Inetum, construido vs por construir); abajo el histórico de lo hecho. |
| [FASE1_DISENO_EXTRACCION_INETUM.md](FASE1_DISENO_EXTRACCION_INETUM.md) | **Diseño de extracción.** Cómo debe hacerse la Fase 1 (nota de diseño para Inetum). |
| [HANDOVER.md](HANDOVER.md) | **Traspaso.** Contactos, dónde están los datos y las cuentas, decisiones de código que no están en otro sitio. |

El resto de este README es la guía técnica de instalación y uso.

---

## Qué hace este sistema

1. **Phase 1 (Extracción)**: Usa `gpt-4o-mini` (OpenAI) para extraer conceptos médicos de texto clínico y clasificarlos por dominio OMOP (Condition, Drug, Procedure, Measurement, Observation, Device)

2. **Phase 2 (Búsqueda Semántica)**: Usa embeddings médicos (SapBERT) para encontrar los conceptos OMOP estándar más similares semánticamente

3. **Pipeline Completo**: Combina ambas fases para ir de texto libre a códigos OMOP estándar

---

## Requisitos

- Python 3.11+
- API Key de OpenAI (para Phase 1)
- ~4 GB RAM (con embeddings completos: ~16 GB)

## Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/GraphRAG-OMOP.git
cd GraphRAG-OMOP

# 2. Crear entorno virtual (dentro de backend/, que es donde está requirements.txt)
cd backend
python -m venv venv

# 3. Activar entorno
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar API Key de OpenAI
# El fichero .env va en backend/ (no en la raíz): config.py y extractor.py lo leen de ahí
cp .env.example .env         # y rellenar OPENAI_API_KEY
```

## Datos OMOP

> **Los datos NO están incluidos en el repositorio** (~28 GB). Deben obtenerse o generarse por separado.

El sistema necesita 3 capas de datos en `backend/data/`:

| Carpeta | Tamaño | Contenido | Cómo obtener |
|---|---|---|---|
| `data/source/` | ~3 GB | CSVs originales de OMOP | Descargar de [OHDSI Athena](https://athena.ohdsi.org/) |
| `data/processed/` | ~2 GB | nodes.csv, edges.csv, omop_graph.pkl | Generar con `python -m src.phase2.preprocess` |
| `data/embeddings/` | ~23 GB | embeddings.npy, faiss_index.bin, concept_id_to_index.pkl | Generar con `python -m src.phase2.embeddings` |

### Opción A: Compartir datos ya generados (recomendado)

Si alguien del equipo ya tiene los datos generados, copiar la carpeta `backend/data/` completa (OneDrive, disco externo, etc.). Es la forma más rápida.

### Opción B: Generar desde cero

1. Descargar vocabularios de [OHDSI Athena](https://athena.ohdsi.org/) y colocar los CSVs en `backend/data/source/`
   - Vocabularios necesarios: SNOMED, RxNorm, RxNorm Extension, LOINC
   - Archivos mínimos: `CONCEPT.csv`, `CONCEPT_RELATIONSHIP.csv`, `RELATIONSHIP.csv`
2. Ejecutar los pasos de generación (ver sección "Generar Datos")

---

## Uso

Hay dos formas de usar el sistema:

### Opción 1: Dashboard web (recomendado para demos)

Levanta el backend (API) y el frontend (dashboard visual) por separado:

```bash
# Terminal 1: Backend (FastAPI)
cd backend
python main.py                # Arranca en http://localhost:8000

# Terminal 2: Frontend (Next.js)
cd frontend
npm install                   # Solo la primera vez
npm run dev                   # Arranca en http://localhost:3000
```

Abre `http://localhost:3000` en el navegador. El dashboard permite:
- Introducir texto clínico y ver los conceptos extraídos
- Visualizar el patient journey (timeline temporal)
- Ver la tabla de mapeo a OMOP con scores
- Exportar resultados a CSV

### Opción 2: CLI de terminal (rápido para testing)

Sin frontend, directamente desde la terminal:

```bash
cd backend

# Modo interactivo (menú con opciones)
python cli.py

# Pipeline completo con texto
python cli.py --text "Paciente con diabetes tipo 2, toma metformina 850mg"

# Solo Phase 1 (extracción LLM)
python cli.py --phase1 "Paciente con diabetes tratado con metformina"

# Solo Phase 2 (búsqueda semántica)
python cli.py --phase2 "metformina"
```

### Ambas opciones usan el mismo pipeline interno

```
Texto clínico
     │
     ▼
Phase 1 (GPT-4): extrae conceptos, traduce a inglés, expande abreviaturas, detecta temporalidad
     │
     ▼
Phase 2 (SapBERT + FAISS): búsqueda semántica → grafo OMOP → concepto estándar
     │
     ▼
Resultado: cada concepto mapeado a su código OMOP estándar
```

---

## Dominios OMOP soportados

| Dominio | Descripción | Ejemplos |
|---------|-------------|----------|
| Condition | Diagnósticos, enfermedades, síntomas | diabetes, hipertensión, dolor |
| Drug | Medicamentos | metformina, aspirina, enalapril |
| Procedure | Procedimientos médicos | cateterismo, biopsia, cirugía |
| Measurement | Mediciones, valores de laboratorio | glucosa, creatinina, presión arterial |
| Observation | Observaciones clínicas | fumador, embarazo, dolor nivel 7 |
| Device | Dispositivos médicos | marcapasos, stent, bomba insulina |

**Opciones de búsqueda:**
- `--top-k N`: Número de resultados (default: 5)
- `--expand`: Mostrar conceptos relacionados via grafo
- `--domain DOMAIN`: Filtrar por dominio (Drug, Condition, etc.)
- `--vocabulary VOCAB`: Filtrar por vocabulario (SNOMED, RxNorm, LOINC)
- `--standard-only`: Solo conceptos estándar OMOP

---

## Estructura del Proyecto

```
GraphRAG-OMOP/
│
├── backend/
│   ├── main.py                  # Servidor FastAPI (para el frontend)
│   ├── cli.py                   # CLI de terminal (sin frontend)
│   ├── config.py                # Configuración y variables de entorno
│   ├── schemas.py               # Schemas de la API (request/response)
│   ├── routers/                 # Endpoints API (health, phase1, phase2)
│   ├── src/
│   │   ├── phase1/              # Extracción de conceptos (GPT-4)
│   │   │   ├── extractor.py     # Lógica de extracción con LangChain
│   │   │   ├── prompts.py       # System prompt para el LLM
│   │   │   └── schema.py        # Schemas Pydantic de salida
│   │   │
│   │   └── phase2/              # Búsqueda semántica (SapBERT + FAISS)
│   │       ├── retrieve.py      # Motor de búsqueda semántica
│   │       ├── embeddings.py    # Generación de embeddings
│   │       ├── graph.py         # Grafo NetworkX OMOP
│   │       └── preprocess.py    # Preprocesamiento de CSVs OMOP
│   │
│   ├── data/                    # ⚠️ NO incluido en el repo (~28 GB)
│   │   ├── source/              # CSVs de Athena (descargar)
│   │   ├── processed/           # Grafo filtrado (generar)
│   │   └── embeddings/          # Vectores + índice FAISS (generar)
│   │
│   ├── .env                     # API Keys (no commitear, ver .env.example)
│   ├── requirements.txt         # Dependencias Python
│   └── PDF Extraction.ipynb     # Borrador de Inetum (PDF → Ollama), referencia, no se ejecuta
│
├── frontend/
│   ├── app/                     # Next.js pages
│   ├── components/              # Componentes React (dashboard, timeline, tabla)
│   ├── lib/                     # API client, types, utilidades
│   └── package.json             # Dependencias Node.js
│
├── HANDOVER.md                  # Traspaso: estado real, arranque, contactos, pendientes
├── EXPLICACION_PROBLEMA.md      # Contexto del proyecto
├── PLAN_MEJORAS.md              # Estado, plan y changelog
└── FASE1_DISENO_EXTRACCION_INETUM.md
```

---

## Generar Datos (Primera vez)

El sistema necesita datos que NO están en el repositorio. Hay que generarlos siguiendo estos 3 pasos en orden:

### Paso 1: Descargar vocabularios OMOP de Athena

1. Ir a [OHDSI Athena](https://athena.ohdsi.org/) y crear una cuenta (gratis)
2. Seleccionar los vocabularios: **SNOMED**, **RxNorm**, **RxNorm Extension**, **LOINC**
3. Descargar el ZIP y extraer los CSVs en `backend/data/source/`

> **Versión de Athena usada para los datos actuales:** `[RELLENAR]` (se lee en
> `VOCABULARY.csv`, fila `None`, columna `vocabulary_version`). Sin este dato, un
> `concept_id` de un golden dataset puede no coincidir con una descarga futura.

Archivos mínimos necesarios:
- `CONCEPT.csv` (~540 MB) — Todos los conceptos médicos
- `CONCEPT_RELATIONSHIP.csv` (~1.6 GB) — Relaciones entre conceptos
- `RELATIONSHIP.csv` (~53 KB) — Tipos de relación

### Paso 2: Preprocesar (generar grafo)

Filtra los CSVs y construye el grafo de relaciones OMOP. Qué filtra `preprocess.py`:

- Conceptos: solo los 4 vocabularios de arriba. Conserva estándar (`S`), clasificación (`C`)
  y no-estándar (nulo). Descarta nombres nulos. Distribución observada: `S` 2.516.863,
  sin estándar 1.253.210, `C` 85.377.
- Relaciones: whitelist `RELEVANT_RELATIONSHIPS` (24 tipos: `Is a`/`Subsumes`,
  `Non-standard to Standard map (OMOP)`, `Concept replaced by`, y las de ingrediente, forma y
  marca de RxNorm/SNOMED). Ambos extremos deben estar en el conjunto filtrado.

```bash
cd backend
python -m src.phase2.preprocess
```

Genera en `data/processed/`:
- `nodes.csv` (~348 MB) — 3.8M conceptos filtrados
- `edges.csv` (~710 MB) — 17M relaciones filtradas
- `omop_graph.pkl` (~834 MB) — Grafo NetworkX cacheado

Tiempo: ~10-15 minutos

### Paso 3: Generar embeddings + índice FAISS

Pasa cada concepto por el modelo SapBERT para generar vectores semánticos y construye el índice de búsqueda:

```bash
# Dataset completo, 3.8M conceptos (~4-8 horas CPU, ~1 hora GPU)
python -m src.phase2.embeddings

# O subset de 100k para pruebas rápidas (~10 min). Son las PRIMERAS 100k filas de nodes.csv, no una muestra
python -m src.phase2.embeddings --max-concepts 100000

# Índice FAISS (IVF, 256 clusters) y cache del grafo. Si no se generan aquí, se generan
# solos en el primer arranque del backend, pero tardan y lo bloquean
python -m src.phase2.embeddings --build-faiss
python -c "from src.phase2.graph import load_graph; load_graph()"
```

**Todas las rutas del backend son relativas a `backend/`.** Ejecuta siempre desde ahí.

Genera en `data/embeddings/`:
- `embeddings.npy` (~12 GB) — Vectores de 768 dimensiones por concepto
- `faiss_index.bin` (~12 GB) — Índice FAISS para búsqueda rápida
- `concept_id_to_index.pkl` (~37 MB) — Mapeo concept_id → posición

### Resumen del pipeline de datos

```
Athena (descarga)          preprocess.py              embeddings.py
    │                          │                           │
    ▼                          ▼                           ▼
data/source/  ──────►  data/processed/  ──────►  data/embeddings/
  ~3 GB                    ~2 GB                     ~23 GB
  CSVs crudos              Grafo filtrado            Vectores + índice
  (solo para generar)      (se usa en runtime)       (se usa en runtime)
```

---

## Ejemplos de Uso (CLI)

```bash
cd backend

# Historia clínica completa
python cli.py --text "Paciente varón de 58 años con antecedentes de infarto agudo de miocardio. Actualmente en tratamiento con aspirina 100mg, atorvastatina 40mg y bisoprolol 5mg."

# Solo extracción (Phase 1)
python cli.py --phase1 "El paciente presenta disnea de esfuerzo y edemas en miembros inferiores."

# Solo búsqueda semántica (Phase 2)
python cli.py --phase2 "myocardial infarction"
```

---

## Notas Técnicas

### Modelo de Embeddings: SapBERT

- **Modelo**: `cambridgeltl/SapBERT-from-PubMedBERT-fulltext`
- **Entrenado en**: UMLS (vocabularios médicos)
- **Dimensión**: 768
- **Fortaleza**: Excelente en terminología médica estándar (inglés)
- **Limitación**: Términos en español pueden tener scores más bajos

### Scores de Similitud

| Score | Interpretación |
|-------|----------------|
| 0.95+ | Match casi exacto |
| 0.80-0.95 | Match muy bueno |
| 0.60-0.80 | Match razonable (puede necesitar revisión) |
| <0.60 | Match débil (considerar alternativas) |

### GPU vs CPU

- **Con GPU (CUDA)**: ~10x más rápido para generar embeddings
- **Sin GPU**: Funciona correctamente, solo más lento en generación inicial

---

## Performance

| Etapa | Tiempo | Notas |
|-------|--------|-------|
| Backend startup | ~30s | Carga embeddings + grafo en memoria |
| Frontend startup | <5s | Compilación Next.js |
| Phase 1 (Extracción) | 5-10s | Llamada a API GPT-4 |
| Phase 2 (Mapeo) | 10-15s | SapBERT + FAISS + grafo |
| **Total por query** | **15-25s** | |

## Troubleshooting

| Síntoma | Causa probable | Dónde mirar / qué hacer |
|---|---|---|
| `ValueError: OPENAI_API_KEY not found` al importar | Falta `backend/.env` o está en la raíz | `cp backend/.env.example backend/.env`. Lo leen `src/phase1/extractor.py:26` y `config.py:30` |
| `/phase2` devuelve 503 siempre | El grafo no cargó. `/status` **no distingue "cargando" de "falló"** (`grafo_loading` siempre `False`, `error` siempre `None`, `routers/health.py:39-41`) | Busca `❌ Grafo initialization failed` en el log del backend |
| `FileNotFoundError: data/processed/...` o "Embeddings not found" | Ejecutado fuera de `backend/`, o datos no generados | Rutas relativas en `graph.py:25-27`, `retrieve.py:50-51`, `preprocess.py:23-30`. Generar datos: sección anterior |
| Arranque de minutos y RAM al máximo | Primera vez: construye `faiss_index.bin` u `omop_graph.pkl` | Generarlos a mano (Paso 3). Después, 15-30 s |
| Nombres de concepto que no cuadran con el score | `retrieve.py:97` lee `nodes.csv` con `nrows = len(embeddings)`: asume que los embeddings son exactamente las primeras N filas en orden | Regenerar embeddings desde el mismo `nodes.csv` |
| "eGFR" mapea a "Epidermal growth factor" | SapBERT no entiende abreviaturas | Phase 1 debe expandirlas antes: `src/phase1/prompts.py`, regla 10 |
| Scores bajos en español | SapBERT es inglés. Phase 1 traduce, pero pierde 10-20% en algunos términos | Esperado |
| Frontend: "Backend is not available" | Backend en otro puerto/host, o CORS | `frontend/lib/api.ts:16` lee `NEXT_PUBLIC_API_URL`; CORS en `main.py:43` usa `FRONTEND_URL` |
| Puerto 8000 ocupado (Windows) | Otro proceso | `netstat -ano \| findstr :8000` y `taskkill /PID <PID> /F` |
| `load_graph(ruta)` ignora la ruta | Bug latente: `retrieve.py:115` pasa la ruta en la posición de `use_cache`. Siempre usa `data/processed/omop_graph.pkl` | `graph.py:368`. Inofensivo mientras no se muevan los datos |
| Windows: caracteres raros en consola | Falta `sys.stdout.reconfigure(encoding='utf-8')` | Ya está en cada entrypoint; copiar la línea en ficheros nuevos |

---

## Testing

No hay tests automáticos. Los que había (`backend/tests/`, `backend/_scripts/`) quedaron
rotos al reorganizar el código en `src/phase2/` y se eliminaron en el traspaso (sept. 2026).
Validación manual: sección "Testing" de [backend/README.md](backend/README.md).

---

## Referencias

- [OMOP Common Data Model](https://ohdsi.github.io/CommonDataModel/)
- [OHDSI Athena Vocabulary](https://athena.ohdsi.org/)
- [SapBERT Paper](https://arxiv.org/abs/2010.11784)
- [NetworkX Documentation](https://networkx.org/)

---

## Licencia

MIT, © Universidad Politécnica de Madrid (LST). Ver [LICENSE](LICENSE).

## Contribuciones

Pull requests son bienvenidos. Para cambios mayores, abre un issue primero.