# GraphRAG-OMOP: Proof of Concept for Medical Concept Linking

**Author:** Adolfo Viguera Varea
**Created:** January 2026

A Proof of Concept system that converts medical terms into standardized OMOP concept IDs and retrieves their relationships using embeddings and graph traversal.

## Overview

This project implements a GraphRAG (Graph-based Retrieval Augmented Generation) approach for the OMOP Common Data Model vocabulary. Given a medical term (e.g., "metformina", "diabetes", "creatinina"), the system:

1. Finds the most relevant standardized OMOP concept using semantic embeddings
2. Retrieves the concept's metadata (concept_id, vocabulary, domain)
3. Expands to 1-hop neighbors in the OMOP relationship graph
4. Returns structured context for downstream use (e.g., LLM queries)

## Project Structure

```
GraphRAG-OMOP/
├── src/                      # Source code
│   ├── preprocess.py        # Phase 1: CSV preprocessing pipeline
│   ├── graph.py             # Phase 1: NetworkX graph construction
│   ├── embeddings.py        # Phase 2: SapBERT embedding generation
│   └── retrieve.py          # Phase 2: Semantic search engine
├── data/                     # Data files (generated + source)
│   ├── CONCEPT.csv          # OMOP source (user-provided)
│   ├── CONCEPT_RELATIONSHIP.csv  # OMOP source (user-provided)
│   ├── RELATIONSHIP.csv     # OMOP source (user-provided)
│   ├── nodes.csv            # Processed concepts (generated)
│   ├── edges.csv            # Processed relationships (generated)
│   ├── omop_graph.pkl       # NetworkX graph cache (generated)
│   ├── embeddings.npy       # SapBERT embeddings (generated)
│   └── concept_id_to_index.pkl  # Embedding index (generated)
├── tests/                    # Unit & integration tests
│   ├── test_preprocess.py   # Phase 1 preprocessing tests
│   ├── test_graph.py        # Phase 1 graph tests
│   ├── test_embeddings_basic.py  # Phase 2 embedding tests
│   └── test_retrieve_quick.py    # Phase 2 retrieval tests
├── scripts/                  # Validation & utility scripts
│   ├── validate_poc.py      # Phase 1 validation
│   ├── validate_setup.py    # Setup validation
│   └── debug_relationships.py  # Debugging tool
├── context/                  # Project documentation
│   ├── PHASE1_COMPLETE.md   # Phase 1 completion report
│   ├── PHASE2_PLAN.md       # Phase 2 implementation plan
│   └── ARCHITECTURE.md      # System architecture
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add OMOP Vocabulary Files

Place the following OMOP CDM vocabulary files in the `data/` directory:

- `CONCEPT.csv` - All medical concepts
- `CONCEPT_RELATIONSHIP.csv` - Relationships between concepts
- `RELATIONSHIP.csv` - Relationship type definitions

These files can be obtained from [OHDSI Athena](https://athena.ohdsi.org/).

**Important**: When preprocessing, ensure `CONCEPT.csv` is not open in Excel or other programs to avoid permission errors.

### 3. Preprocess the Data

Run the preprocessing script to generate `nodes.csv` and `edges.csv`:

```bash
python preprocess.py
```

This will:

- Extract relevant columns from OMOP files
- Translate relationship IDs to human-readable names
- Create simplified CSV files for graph construction

### 4. Load the Graph

Test that the graph loads correctly:

```bash
python graph.py
```

This will display graph statistics and sample node information.

## Usage

### Preprocessing

The `preprocess.py` module converts raw OMOP files into simplified formats:

```python
from preprocess import preprocess

# Run preprocessing
nodes_df, edges_df = preprocess()
```

**Input:**

- `data/CONCEPT.csv`
- `data/CONCEPT_RELATIONSHIP.csv`
- `data/RELATIONSHIP.csv`

**Output:**

- `nodes.csv` - Concepts with: concept_id, concept_name, vocabulary_id, domain_id
- `edges.csv` - Relationships with: concept_id_1, relationship_name, concept_id_2

### Graph Construction

The `graph.py` module builds a NetworkX MultiDiGraph:

```python
from graph import load_graph, get_concept_info, get_neighbors

# Load the graph (automatically uses cache if available)
G = load_graph()

# Force rebuild from CSVs (ignores cache)
G = load_graph(force_rebuild=True)

# Load without using cache
G = load_graph(use_cache=False)

# Get concept information
info = get_concept_info(G, concept_id=1503297)
print(info)
# {'concept_id': 1503297, 'concept_name': 'Metformin',
#  'vocabulary_id': 'RxNorm', 'domain_id': 'Drug'}

# Get neighboring concepts (1-hop)
neighbors = get_neighbors(G, concept_id=1503297, max_neighbors=5)
for neighbor in neighbors:
    print(f"{neighbor['relationship']}: {neighbor.get('target_name', neighbor.get('source_name'))}")
```

**Performance Note:** The graph is automatically cached as `omop_graph.pkl` after the first build. Subsequent loads are ~100x faster (seconds instead of minutes). The cache is automatically used on subsequent runs.

## Testing

Run all unit tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=. --cov-report=html
```

## Development Guidelines

This project follows the guidelines in `CLAUDE.md`:

- Files should not exceed 500 lines
- All features must have unit tests (expected use, edge case, failure case)
- Use clear module separation (agent.py, tools.py, prompts.py pattern)
- Comment non-obvious logic with `# Reason:` explanations
- Use python-dotenv for environment variables

## Next Steps

The following modules still need to be implemented:

1. **embeddings.py** - Generate sentence-transformer embeddings for concept_name fields
2. **retrieve.py** - Semantic search + graph expansion
3. **main.py** - CLI interface for end-to-end queries

See `context/PRD.md` for detailed requirements.

## Technical Stack

- **NetworkX** - Graph data structure and traversal
- **Pandas** - CSV processing
- **Sentence-Transformers** - Semantic embeddings (to be implemented)
- **Pytest** - Unit testing
- **Python 3.8+**

## License

See LICENSE file for details.

## References

- [OMOP Common Data Model](https://ohdsi.github.io/CommonDataModel/)
- [OHDSI Athena Vocabulary](https://athena.ohdsi.org/)
- [NetworkX Documentation](https://networkx.org/)
