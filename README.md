# GraphRAG-OMOP

Sistema de **Concept Linking** para vocabulario OMOP que convierte texto clínico en conceptos médicos estandarizados.

```
Texto Clínico → [Phase 1: Extracción LLM] → Conceptos → [Phase 2: Búsqueda Semántica] → OMOP Estándar
```

**Autor:** Adolfo Viguera Varea

---

## Qué hace este sistema

1. **Phase 1 (Extracción)**: Usa GPT-4 para extraer conceptos médicos de texto clínico y clasificarlos por dominio OMOP (Condition, Drug, Procedure, Measurement, Observation, Device)

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

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno (Windows)
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar API Key de OpenAI
# Crear archivo .env en la raíz del proyecto:
echo OPENAI_API_KEY=sk-tu-api-key-aqui > .env
```

## Datos OMOP

El sistema necesita los CSVs de vocabulario OMOP en `data/source/`:
- `CONCEPT.csv`
- `CONCEPT_RELATIONSHIP.csv`
- `RELATIONSHIP.csv`

Estos archivos se pueden obtener de [OHDSI Athena](https://athena.ohdsi.org/).

Si ya tienes los datos preprocesados (`data/processed/nodes.csv`, `data/processed/edges.csv`, `data/embeddings/embeddings.npy`), puedes omitir la generación.

---

## Uso Rápido

### Modo Interactivo (Recomendado para empezar)

```bash
python main.py
```

Esto abre un menú interactivo donde puedes:
1. Ejecutar el pipeline completo
2. Probar solo Phase 1 (extracción)
3. Probar solo Phase 2 (búsqueda)

### Pipeline Completo con Texto

```bash
python main.py --text "Paciente de 65 años con diabetes mellitus tipo 2 e hipertensión. Se prescribe metformina 850mg y enalapril 10mg."
```

**Output esperado:**
```
PHASE 1: Clinical Concept Extraction
=====================================
Extracted 4 concepts:
  - diabetes mellitus tipo 2 [Condition]
  - hipertensión [Condition]
  - metformina [Drug]
  - enalapril [Drug]

PHASE 2: Semantic Search for OMOP Standards
===========================================
[Condition] diabetes mellitus tipo 2
  1. [0.772] Maturity onset diabetes of the young, type 2
     ID: 4130164 | SNOMED

[Drug] metformina
  1. [0.973] metformin ★
     ID: 1503297 | RxNorm

[Drug] enalapril
  1. [1.000] enalapril ★
     ID: 1341927 | RxNorm

PIPELINE COMPLETE
```

---

## Comandos por Fase

### Phase 1: Extracción de Conceptos (LLM)

```bash
# Via main.py
python main.py --phase1 "Paciente con diabetes tratado con metformina"

# Via módulo standalone
python -m src.phase1.main "Paciente con diabetes tratado con metformina"

# Modo interactivo Phase 1
python -m src.phase1.main
```

**Dominios OMOP soportados:**

| Dominio | Descripción | Ejemplos |
|---------|-------------|----------|
| Condition | Diagnósticos, enfermedades, síntomas | diabetes, hipertensión, dolor |
| Drug | Medicamentos | metformina, aspirina, enalapril |
| Procedure | Procedimientos médicos | cateterismo, biopsia, cirugía |
| Measurement | Mediciones, valores de laboratorio | glucosa, creatinina, presión arterial |
| Observation | Observaciones clínicas | fumador, embarazo, dolor nivel 7 |
| Device | Dispositivos médicos | marcapasos, stent, bomba insulina |

### Phase 2: Búsqueda Semántica OMOP

```bash
# Via main.py
python main.py --phase2 "metformina"

# Via módulo standalone
python -m src.phase2.main "metformina"

# Con opciones
python -m src.phase2.main "diabetes" --top-k 10 --expand

# Modo interactivo Phase 2
python -m src.phase2.main
```

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
├── main.py                      # CLI principal (pipeline completo)
│
├── src/
│   ├── phase1/                  # Extracción de conceptos (LLM)
│   │   ├── main.py              # CLI standalone Phase 1
│   │   ├── extractor.py         # Lógica de extracción con GPT-4
│   │   ├── prompts.py           # Prompts para el LLM
│   │   └── schema.py            # Schemas Pydantic
│   │
│   └── phase2/                  # Búsqueda semántica (Embeddings)
│       ├── main.py              # CLI standalone Phase 2
│       ├── retrieve.py          # Motor de búsqueda semántica
│       ├── embeddings.py        # Generación de embeddings SapBERT
│       ├── graph.py             # Grafo NetworkX OMOP
│       └── preprocess.py        # Preprocesamiento de CSVs OMOP
│
├── data/
│   ├── source/                  # CSVs originales de OMOP (Athena)
│   │   ├── CONCEPT.csv          # Conceptos OMOP (~565 MB)
│   │   ├── CONCEPT_RELATIONSHIP.csv  # Relaciones (~1.7 GB)
│   │   └── RELATIONSHIP.csv     # Tipos de relación
│   │
│   ├── processed/               # Archivos procesados
│   │   ├── nodes.csv            # Conceptos filtrados (3.8M)
│   │   ├── edges.csv            # Relaciones filtradas (17M)
│   │   └── omop_graph.pkl       # Grafo cacheado (~2 GB)
│   │
│   ├── embeddings/              # Embeddings SapBERT
│   │   ├── embeddings.npy       # Vectores de embeddings
│   │   └── concept_id_to_index.pkl  # Mapeo de índices
│   │
│   └── output/                  # Salida del pipeline
│
├── scripts/
│   ├── validation/              # Scripts de validación
│   ├── debug/                   # Herramientas de debugging
│   └── demo/                    # Materiales de demostración
│
├── context/                     # Documentación del proyecto
│   ├── ARCHITECTURE.md          # Arquitectura detallada
│   └── CLAUDE.md                # Contexto para desarrollo
│
├── tests/                       # Tests unitarios
├── requirements.txt             # Dependencias Python
└── .env                         # API Keys (no commitear)
```

---

## Generar Datos (Primera vez)

Si no tienes los archivos generados, ejecuta:

```bash
# 1. Preprocesar CSVs OMOP (genera data/processed/nodes.csv, edges.csv)
python -m src.phase2.preprocess

# 2. Generar embeddings (guarda en data/embeddings/)
# Opción A: Subset para pruebas rápidas (~10 min)
python -m src.phase2.embeddings --max-concepts 100000

# Opción B: Dataset completo (~4-8 horas CPU, ~1 hora GPU)
python -m src.phase2.embeddings
```

---

## Ejemplos de Uso

### Ejemplo 1: Historia Clínica en Español

```bash
python main.py --text "Paciente varón de 58 años con antecedentes de infarto agudo de miocardio. Actualmente en tratamiento con aspirina 100mg, atorvastatina 40mg y bisoprolol 5mg. En la última analítica presenta creatinina elevada."
```

### Ejemplo 2: Solo Extracción

```bash
python main.py --phase1 "El paciente presenta disnea de esfuerzo, edemas en miembros inferiores y se auscultan crepitantes bibasales."
```

### Ejemplo 3: Buscar un Término Específico

```bash
python main.py --phase2 "myocardial infarction"
```

### Ejemplo 4: Búsqueda con Filtros

```bash
# Solo medicamentos estándar
python -m src.phase2.main "aspirin" --domain Drug --standard-only

# Top 20 resultados con relaciones
python -m src.phase2.main "diabetes" --top-k 20 --expand
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

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
```bash
# Crear archivo .env con tu API key
echo OPENAI_API_KEY=sk-tu-key > .env
```

### Error: "Embeddings not found"
```bash
# Generar embeddings (primera vez)
python -m src.phase2.embeddings --max-concepts 100000
```

### Error: "No module named 'langchain_core'"
```bash
pip install langchain langchain-core langchain-openai
```

### Scores bajos para términos en español
Los embeddings están optimizados para inglés. Para mejores resultados con español:
- Usa términos en inglés cuando sea posible
- O acepta que los scores serán ~10-20% más bajos

---

## Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Tests con coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Referencias

- [OMOP Common Data Model](https://ohdsi.github.io/CommonDataModel/)
- [OHDSI Athena Vocabulary](https://athena.ohdsi.org/)
- [SapBERT Paper](https://arxiv.org/abs/2010.11784)
- [NetworkX Documentation](https://networkx.org/)

---

## Licencia

MIT License - Ver [LICENSE](LICENSE)

## Contribuciones

Pull requests son bienvenidos. Para cambios mayores, abre un issue primero.