# GraphRAG-OMOP Architecture

## Overview

GraphRAG-OMOP is a proof-of-concept system for medical concept linking using OMOP vocabulary. It combines graph-based knowledge representation with semantic search to convert medical terms (in English or Spanish) to standardized OMOP concept IDs with hierarchical relationships.

**Current Status:** Phase 2 In Progress (Session 2: 100k embeddings) 🚧

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT DATA (data/)                       │
│  OMOP CSV Files (user-provided)                                  │
│  - CONCEPT.csv           (565 MB, ~5M concepts)                  │
│  - RELATIONSHIP.csv      (53 KB, ~700 relationships)             │
│  - CONCEPT_RELATIONSHIP.csv (1.7 GB, ~34M relationships)         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│         PHASE 1: GRAPH INFRASTRUCTURE (COMPLETE ✅)              │
├─────────────────────────────────────────────────────────────────┤
│  src/preprocess.py                                               │
│  ├─ Filter vocabularies (SNOMED, RxNorm, LOINC)                 │
│  ├─ Filter relationships (~23 relevant types)                    │
│  ├─ Chunk processing (500k rows/chunk)                           │
│  └─ Output: data/nodes.csv (3.8M), data/edges.csv (17M)          │
│                                                                   │
│  src/graph.py                                                    │
│  ├─ Build NetworkX MultiDiGraph                                  │
│  ├─ Pickle caching (100x faster loading)                         │
│  ├─ Query functions: get_concept_info, get_neighbors            │
│  └─ Standard mapping: find_standard_mapping                      │
│                                                                   │
│  scripts/validate_poc.py                                         │
│  └─ Validate 5 mandatory terms: metformin, diabetes,             │
│     creatinine, ibuprofen, hypertension                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│      PHASE 2: SEMANTIC SEARCH (IN PROGRESS 🚧)                   │
├─────────────────────────────────────────────────────────────────┤
│  src/embeddings.py                                               │
│  ├─ Generate embeddings for all concept names                    │
│  ├─ Model: SapBERT (cambridgeltl/SapBERT-from-PubMedBERT)       │
│  ├─ Batch processing with progress bars                          │
│  ├─ Subset support (10k/100k/3.8M concepts)                      │
│  └─ Store: data/embeddings.npy + concept_id_to_index.pkl         │
│                                                                   │
│  src/retrieve.py                                                 │
│  ├─ SemanticRetriever class                                      │
│  ├─ Semantic search: query → top-k candidates via cosine sim    │
│  ├─ Graph expansion: get related concepts (optional)             │
│  ├─ Filtering: vocabulary, domain, standard_only, min_score     │
│  └─ CLI interface for queries                                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: CONCEPT CONTEXT                       │
│  {                                                                │
│    "concept_id": 1503297,                                        │
│    "concept_name": "Metformin",                                  │
│    "score": 0.98,                                                │
│    "vocabulary": "RxNorm",                                       │
│    "domain": "Drug",                                             │
│    "standard": "S",                                              │
│    "relationships": [...]                                        │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
GraphRAG-OMOP/
├── src/                           # Source code modules
│   ├── __init__.py               # Package initialization
│   ├── preprocess.py             # [Phase 1] CSV preprocessing pipeline
│   ├── graph.py                  # [Phase 1] NetworkX graph construction
│   ├── embeddings.py             # [Phase 2] SapBERT embedding generation
│   └── retrieve.py               # [Phase 2] Semantic search engine
│
├── data/                          # Data files (source + generated)
│   ├── CONCEPT.csv               # [Source] OMOP concepts (565 MB, ~5M)
│   ├── CONCEPT_RELATIONSHIP.csv  # [Source] OMOP relationships (1.7 GB, ~34M)
│   ├── RELATIONSHIP.csv          # [Source] OMOP relationship types (53 KB)
│   ├── nodes.csv                 # [Generated] Filtered concepts (700 MB, 3.8M)
│   ├── edges.csv                 # [Generated] Filtered relationships (1.5 GB, 17M)
│   ├── omop_graph.pkl            # [Generated] NetworkX graph cache (1 GB)
│   ├── embeddings.npy            # [Generated] SapBERT embeddings (varies by subset)
│   └── concept_id_to_index.pkl   # [Generated] Embedding index mapping
│
├── tests/                         # Unit & integration tests
│   ├── __init__.py               # Test package init
│   ├── test_preprocess.py        # [Phase 1] Preprocessing tests (13 tests)
│   ├── test_graph.py             # [Phase 1] Graph construction tests
│   ├── test_embeddings_basic.py  # [Phase 2] Embedding functionality tests
│   └── test_retrieve_quick.py    # [Phase 2] Retrieval quick tests
│
├── scripts/                       # Validation & utility scripts
│   ├── validate_poc.py           # [Phase 1] Validate 5 mandatory terms
│   ├── validate_setup.py         # Environment validation
│   └── debug_relationships.py    # Relationship debugging tool
│
├── context/                       # Project documentation
│   ├── ARCHITECTURE.md           # This file - system architecture
│   ├── PHASE1_COMPLETE.md        # Phase 1 completion report
│   ├── PHASE2_PLAN.md            # Phase 2 implementation plan
│   └── [other docs...]
│
├── requirements.txt               # Python dependencies
├── README.md                      # Project overview
├── .gitignore                     # Git ignore rules
└── LICENSE                        # MIT License
```

---

## File-by-File Documentation

### 📁 src/ - Source Code

#### `src/preprocess.py` (Phase 1 ✅)
**Purpose:** Convert raw OMOP CSVs into filtered graph-ready format

**Key Functions:**
- `load_vocabulary_whitelist()` → List of vocabularies to keep (SNOMED, RxNorm, LOINC, RxNorm Extension)
- `load_relationship_mapping()` → Dict mapping relationship_id → relationship_name (23 relevant types)
- `load_concept_data(path, nrows)` → DataFrame of filtered concepts
- `load_concept_relationships(path, nrows, chunk_size)` → DataFrame of filtered relationships
- `preprocess_nodes(concepts_df)` → Cleaned nodes DataFrame for graph
- `preprocess_edges(relationships_df, mapping)` → Cleaned edges DataFrame for graph

**Input:**
- `data/CONCEPT.csv` (565 MB, ~5M concepts)
- `data/RELATIONSHIP.csv` (53 KB, ~700 relationships)
- `data/CONCEPT_RELATIONSHIP.csv` (1.7 GB, ~34M relationships)

**Output:**
- `data/nodes.csv` (700 MB, 3,855,450 concepts)
  - Columns: `concept_id`, `concept_name`, `vocabulary_id`, `domain_id`, `standard_concept`
- `data/edges.csv` (1.5 GB, 17,124,839 relationships)
  - Columns: `concept_id_1`, `relationship_name`, `concept_id_2`

**Performance:**
- Full dataset: ~55 minutes (one-time)
- Test dataset (500k concepts, 5M relationships): ~2-3 minutes

**Design Decisions:**
- **Chunk processing:** 500k rows/chunk to prevent memory overflow on 1.7 GB file
- **Vocabulary filtering:** Reduces 5M → 3.8M concepts while keeping medical relevance
- **Keeps non-standard concepts:** Critical for mapping user queries → standard IDs

---

#### `src/graph.py` (Phase 1 ✅)
**Purpose:** Build and query a NetworkX MultiDiGraph from preprocessed data

**Graph Type:** `networkx.MultiDiGraph`
- Directed (relationships have direction: child → parent)
- Multi (multiple relationship types between same nodes)

**Key Functions:**
- `validate_graph_files()` → Checks if nodes.csv and edges.csv exist
- `load_graph(cache_path, use_cache, force_rebuild)` → Loads or builds graph with caching
- `get_concept_info(G, concept_id)` → Returns concept metadata dict
- `get_neighbors(G, concept_id, max_neighbors)` → Returns 1-hop relationships
- `find_standard_mapping(G, concept_id)` → Follows mapping chains to standard concept

**Node Attributes:**
```python
{
    'concept_name': str,       # e.g., "Metformin"
    'vocabulary_id': str,      # e.g., "RxNorm"
    'domain_id': str,          # e.g., "Drug"
    'standard_concept': str    # 'S' = standard, None = non-standard
}
```

**Edge Attributes:**
```python
{
    'relationship': str  # e.g., "Is a", "Has ingredient (RxNorm)"
}
```

**Performance:**
- **First load:** 2-5 minutes (builds from CSVs + creates cache)
- **Cached load:** ~5 seconds (loads from `data/omop_graph.pkl`)
- **Cache file:** ~1 GB pickle
- **Lookup:** O(1) via NetworkX dict storage
- **1-hop traversal:** O(k) where k = number of neighbors (~10-100 typically)

**Statistics:**
- **Nodes:** 3,855,450 concepts
- **Edges:** 17,124,839 relationships
- **Density:** 0.000001 (very sparse, efficient)

---

#### `src/embeddings.py` (Phase 2 🚧)
**Purpose:** Generate and cache SapBERT embeddings for concept names

**Key Functions:**
- `load_sapbert_model()` → Loads SapBERT from HuggingFace (cambridgeltl/SapBERT-from-PubMedBERT-fulltext)
- `generate_embeddings(model, concept_names, batch_size)` → Generates embeddings in batches with progress bar
- `build_embedding_index(nodes_csv_path, output_dir, max_concepts)` → Full pipeline: load concepts → generate embeddings → save to disk
- `load_embeddings(output_dir)` → Loads cached embeddings from disk

**Model Details:**
- **Name:** `cambridgeltl/SapBERT-from-PubMedBERT-fulltext`
- **Base:** PubMedBERT (biomedical literature)
- **Fine-tuning:** UMLS synonyms (medical concepts)
- **Embedding Dim:** 768
- **Max Tokens:** 512
- **Size:** ~440 MB
- **Device:** CPU (no GPU required, but slower)

**Output:**
- `data/embeddings.npy` - numpy array (N x 768), size varies by subset:
  - 10k concepts: ~30 MB
  - 100k concepts: ~300 MB
  - 3.8M concepts: ~11 GB
- `data/concept_id_to_index.pkl` - dict mapping concept_id → embedding row index

**Performance (CPU):**
- 10k concepts: ~1-2 minutes
- 100k concepts: ~10-15 minutes
- 3.8M concepts: ~4-8 hours

**CLI Usage:**
```bash
# Small test
python src/embeddings.py --max-concepts 10000

# Medium test
python src/embeddings.py --max-concepts 100000

# Full dataset
python src/embeddings.py
```

**Design Decisions:**
- **Subset support:** `max_concepts` parameter for incremental testing (10k → 100k → 3.8M)
- **Batch processing:** 256 concepts/batch for memory efficiency
- **Progress bars:** `tqdm` for visibility during long runs
- **Caching:** One-time generation, fast subsequent loads

---

#### `src/retrieve.py` (Phase 2 🚧)
**Purpose:** Semantic search engine for OMOP concepts

**Main Class:** `SemanticRetriever`

**Initialization:**
```python
retriever = SemanticRetriever(
    embeddings_dir='data',         # Where embeddings.npy is stored
    nodes_csv_path='data/nodes.csv',  # Concept metadata
    graph_path='data/omop_graph.pkl', # Optional, for graph expansion
    load_graph_data=True              # Set False to skip graph loading
)
```

**Key Methods:**
- `search(query, top_k, filters, min_score)` → Returns top-k concepts matching query
- `expand_graph(concept_id, depth, relationship_types)` → Returns related concepts via graph
- `search_with_expansion(query, top_k, expand_top_n)` → Combined semantic + graph search

**Search Process:**
1. Encode query using SapBERT model
2. Compute cosine similarity with all concept embeddings
3. Sort by similarity score (descending)
4. Apply filters (vocabulary, domain, standard_only, min_score)
5. Return top-k results

**Filtering Options:**
- `vocabulary`: Filter by vocabulary (e.g., 'SNOMED', 'RxNorm')
- `domain`: Filter by domain (e.g., 'Drug', 'Condition')
- `standard_only`: Only return standard concepts (S flag)
- `min_score`: Minimum cosine similarity threshold (0-1)

**Return Format:**
```python
[
    {
        'concept_id': 1503297,
        'concept_name': 'Metformin',
        'score': 0.98,
        'vocabulary_id': 'RxNorm',
        'domain_id': 'Drug',
        'standard_concept': 'S'
    },
    ...
]
```

**Performance:**
- Query encoding: ~50ms
- Cosine similarity (100k concepts): ~10ms
- Cosine similarity (3.8M concepts): ~100ms
- Total (100k): <100ms
- Total (3.8M): <200ms

**CLI Usage:**
```bash
# Simple query
python src/retrieve.py "metformina"

# With filters
python src/retrieve.py "diabetes" --vocabulary SNOMED --standard-only

# Top 20 results
python src/retrieve.py "creatinine" --top-k 20

# With graph expansion
python src/retrieve.py "ibuprofen" --expand

# No graph (faster startup)
python src/retrieve.py "adverse reaction" --no-graph
```

**Design Decisions:**
- **Cosine similarity:** Standard for semantic search, range [0,1], interpretable
- **Optional graph:** Can run without graph for speed (semantic search only)
- **Filters:** Enable domain-specific queries (e.g., drugs only)
- **Lazy loading:** Graph loaded only if needed for expansion

---

### 📁 data/ - Data Files

**Source Files (user-provided):**
- `CONCEPT.csv` (565 MB, ~5M concepts) - All OMOP concepts
- `CONCEPT_RELATIONSHIP.csv` (1.7 GB, ~34M relationships) - All concept relationships
- `RELATIONSHIP.csv` (53 KB, ~700 relationships) - Relationship type definitions

**Generated Files (by preprocessing):**
- `nodes.csv` (700 MB, 3.8M concepts) - Filtered concepts
- `edges.csv` (1.5 GB, 17M relationships) - Filtered relationships
- `omop_graph.pkl` (1 GB) - Cached NetworkX graph

**Generated Files (by embeddings):**
- `embeddings.npy` (varies: 30 MB → 11 GB) - SapBERT concept embeddings
- `concept_id_to_index.pkl` (~80 KB → 50 MB) - Concept ID → embedding index mapping

---

### 📁 tests/ - Test Suite

#### `tests/test_preprocess.py` (Phase 1 ✅)
**Coverage:** 13 tests, all passing
- File validation (existence, missing files)
- CONCEPT.csv loading (structure, vocabularies, standard/non-standard mix)
- RELATIONSHIP.csv loading (structure, mapping relationships present)
- CONCEPT_RELATIONSHIP.csv loading (structure, filtering, empty edge cases)
- Full pipeline (end-to-end, output validation, referential integrity)

**Key Tests:**
- `test_load_concept_data_keeps_non_standard` - Ensures non-standard concepts kept (critical)
- `test_load_relationship_mapping_contains_maps_to` - Validates mapping relationships present
- `test_preprocess_edges_valid` - Verifies referential integrity (all edge endpoints exist in nodes)

#### `tests/test_embeddings_basic.py` (Phase 2 🚧)
**Tests:**
1. Load embeddings successfully
2. Verify dimensions (N x 768)
3. Concept lookup by ID
4. Cosine similarity calculation
5. Find similar concepts

**Status:** All tests passing on 10k subset ✅

#### `tests/test_retrieve_quick.py` (Phase 2 🚧)
**Tests:** 5 query scenarios:
1. "adverse reaction" - English medical term
2. "stillbirth" - Single word medical term
3. "central nervous system" - Multi-word anatomical term
4. "drug" - Generic pharmacological term
5. "hallucination" - Psychiatric symptom

**Status:** All tests passing on 10k subset ✅

---

### 📁 scripts/ - Validation Scripts

#### `scripts/validate_poc.py` (Phase 1 ✅)
**Purpose:** Validate PoC with 5 mandatory medical terms

**Test Terms:**
1. **Metformin** (metformin, metformina) → 9,207 matches
2. **Diabetes** (diabetes) → 1,806 matches
3. **Creatinine** (creatinine, creatinina) → 5,054 matches
4. **Ibuprofen** (ibuprofen, ibuprofeno) → 18,174 matches
5. **Hypertension** (hypertension, hipertensión) → 785 matches

**Validation Steps:**
1. Search by name (case-insensitive, substring)
2. Display top 3 matches
3. Detailed analysis of first match:
   - Concept metadata
   - Top 5 relationships (1-hop)
   - Standard mapping (if non-standard)

**Result:** All 5 terms validated ✅

#### `scripts/validate_setup.py`
**Purpose:** Validate environment and file structure

#### `scripts/debug_relationships.py`
**Purpose:** Debug relationship types and filtering

---

### 📁 context/ - Documentation

- `ARCHITECTURE.md` (this file) - System architecture and design
- `PHASE1_COMPLETE.md` - Phase 1 completion report (detailed)
- `PHASE2_PLAN.md` - Phase 2 implementation plan (sessions, tasks, timeline)
- Other docs...

---

## Data Flow: Query to Result

```
User Query: "metformina"
        ↓
[src/retrieve.py - SemanticRetriever]
        ↓
1. Load SapBERT model
2. Encode query → embedding (768 dims)
        ↓
3. Compute cosine similarity with all concept embeddings
   (loaded from data/embeddings.npy)
        ↓
4. Sort by score, get top-k
        ↓
5. Apply filters (vocabulary, domain, standard_only, min_score)
        ↓
6. Lookup metadata from nodes_csv
        ↓
Top-K Results: [
    {concept_id: 1503297, name: "Metformin", score: 0.98, ...},
    {concept_id: 1586346, name: "Metformin hydrochloride", score: 0.95, ...},
    ...
]
        ↓
[Optional: Graph Expansion via src/graph.py]
        ↓
get_neighbors(concept_id) → 1-hop relationships
find_standard_mapping(concept_id) → standard concept
        ↓
Final Result: Concept + metadata + relationships
```

---

## Technical Stack

**Languages:**
- Python 3.11+

**Core Libraries (Phase 1):**
- pandas 2.x - CSV processing
- networkx 3.x - Graph structure
- numpy 2.x - Array operations

**Phase 2 Libraries:**
- sentence-transformers 2.2+ - BERT embeddings wrapper
- torch 2.0+ (CPU-only) - Deep learning backend
- scikit-learn 1.3+ - Cosine similarity

**Testing:**
- pytest 8.x

**Development:**
- tqdm - Progress bars
- pickle - Caching

---

## Performance Metrics

### Memory Usage
- **Preprocessing:** 4-6 GB peak (chunk processing keeps it bounded)
- **Graph in memory:** 2-3 GB
- **Embeddings in memory:**
  - 10k: ~30 MB
  - 100k: ~300 MB
  - 3.8M: ~11 GB
- **Total for full system:** ~14-17 GB RAM recommended

### Processing Time

**Phase 1 (one-time):**
- Full preprocessing: ~55 minutes
- Graph cache creation: ~2-3 minutes
- Graph cached load: ~5 seconds (100x speedup)

**Phase 2 (one-time per subset):**
- 10k embeddings: ~1-2 minutes
- 100k embeddings: ~10-15 minutes
- 3.8M embeddings: ~4-8 hours (CPU)

**Query Time (after setup):**
- Retriever initialization: ~10-15 seconds (load model + embeddings)
- Single query (100k concepts): <100ms
- Single query (3.8M concepts): <200ms
- Graph expansion: ~10ms per concept

### Dataset Statistics
- **Original:** 5M concepts, 34M relationships
- **After filtering:** 3.8M concepts, 17M relationships
- **Reduction:** ~25% concepts, ~50% relationships
- **Vocabularies:** SNOMED (largest), RxNorm, LOINC, RxNorm Extension
- **Relationship types:** 23 relevant (from 722 total)

---

## Design Decisions & Rationale

### 1. File Organization
**Decision:** Separate `src/`, `data/`, `tests/`, `scripts/`

**Rationale:**
- **Clarity:** Clear separation of code vs data vs tests
- **Imports:** Python package structure (`from src.module import ...`)
- **Gitignore:** Easy to exclude large data files from git
- **Scalability:** Room for future modules (e.g., `src/api/`, `src/ui/`)

### 2. Incremental Embedding Generation
**Decision:** Support subset testing (10k → 100k → 3.8M)

**Rationale:**
- **Validation:** Catch bugs early with small dataset (1-2 min vs 4-8 hours)
- **Iteration:** Rapid testing of retrieval logic before full embedding generation
- **Hardware:** Not everyone has 16 GB RAM or GPU
- **Documentation:** Easier to document with small examples

### 3. CPU-only PyTorch
**Decision:** Use CPU-only PyTorch instead of CUDA version

**Rationale:**
- **Accessibility:** Works on all machines (no GPU required)
- **Size:** ~200 MB vs ~2 GB for CUDA version
- **Performance:** 4-8 hours on CPU is acceptable for one-time generation
- **Caching:** Embeddings generated once, then loaded in <1 second

### 4. SapBERT Model Choice
**Decision:** Use SapBERT instead of BioBERT, PubMedBERT, or general BERT

**Rationale:**
- **Medical domain:** Fine-tuned specifically on UMLS (OMOP foundation)
- **State-of-the-art:** Best performance on SNOMED CT entity linking (2024)
- **Proven:** Multiple papers confirm production use for medical concepts
- **OMOP alignment:** UMLS and OMOP share vocabulary (SNOMED, RxNorm)

**Alternatives considered:**
- BioBERT: Good but older, SapBERT outperforms
- PubMedBERT: Base model, SapBERT adds synonym alignment
- ModernPubMedBERT: Newer but less validation (optional Session 5 comparison)

### 5. Separate retrieve.py from embeddings.py
**Decision:** Two modules instead of one monolithic file

**Rationale:**
- **Single responsibility:** `embeddings.py` = generation, `retrieve.py` = search
- **Reusability:** Can generate embeddings once, use retrieve many times
- **Testing:** Easier to test embedding generation separate from search logic
- **CLI:** Each has its own main() for command-line usage

### 6. Optional Graph Loading
**Decision:** `SemanticRetriever(load_graph_data=False)` option

**Rationale:**
- **Speed:** Semantic search doesn't require graph (skip 5 sec load)
- **Memory:** Graph uses 2-3 GB RAM (may not be needed for all queries)
- **Flexibility:** Users can choose semantic-only or semantic+graph

---

## Known Limitations

### Phase 1 (Complete)
1. ✅ Search is substring-based → Addressed in Phase 2 with semantic search
2. ✅ No ranking → Addressed in Phase 2 with cosine similarity scores
3. ✅ No semantic understanding → Addressed in Phase 2 with embeddings

### Phase 2 (Current)
1. **10k/100k subset testing:** Not all medical terms found in small subsets
2. **CPU-only:** Slower embedding generation (acceptable trade-off)
3. **No evaluation dataset:** Need gold standard for quantitative metrics
4. **No main.py yet:** Only CLI in retrieve.py, no unified interface

### Future Enhancements
1. **FAISS for speed:** Approximate nearest neighbors for 3.8M concepts (<10ms queries)
2. **Multi-lingual:** Currently English/Spanish, could expand to more languages
3. **Typo tolerance:** SapBERT handles some typos, but could add fuzzy matching
4. **Graph-enhanced ranking:** Combine semantic score with PageRank, degree centrality

---

## Success Criteria

### Phase 1 (ACHIEVED ✅)
- [x] All 5 mandatory terms found in graph
- [x] All terms have relationships (1-hop traversal works)
- [x] Standard mappings work for non-standard concepts
- [x] All tests passing (13/13)
- [x] Full dataset processed and cached

### Phase 2 Session 1 (ACHIEVED ✅)
- [x] File structure reorganized (src/, data/, tests/, scripts/)
- [x] embeddings.py created with subset support
- [x] retrieve.py created with SemanticRetriever class
- [x] 10k embeddings generated and tested
- [x] Basic semantic search working

### Phase 2 Session 2 (IN PROGRESS 🚧)
- [x] 100k embeddings generated
- [ ] Semantic search tested with mandatory terms on 100k
- [ ] Validation showing improvement over substring search
- [ ] Documentation updated

### Phase 2 Session 3 (PENDING)
- [ ] main.py CLI created
- [ ] validate_phase2.py created
- [ ] End-to-end validation on 100k subset
- [ ] Phase 1 vs Phase 2 comparison documented

### Phase 2 Complete (TODO)
- [ ] Semantic search handles typos ("metfornin" → "metformin")
- [ ] Multi-lingual support (Spanish queries work)
- [ ] Ranking improves relevance (target concept in top-3)
- [ ] Performance: <1 second for query → results
- [ ] Evaluation: >80% recall@10 on test set

---

## Changelog

### 2026-01-16 - Phase 2 Session 2 (In Progress)
- 🚧 Generated 100k concept embeddings (~10-15 min)
- 🚧 Testing semantic search with mandatory terms
- ✅ Reorganized file structure (src/, data/, tests/, scripts/)
- ✅ Updated all imports to use `from src.module`
- ✅ Updated README.md with new structure

### 2026-01-16 - Phase 2 Session 1 (Complete)
- ✅ Created `src/embeddings.py` with SapBERT integration
- ✅ Created `src/retrieve.py` with SemanticRetriever class
- ✅ Generated 10k embeddings (~1-2 min) for testing
- ✅ Created `tests/test_embeddings_basic.py` (all passing)
- ✅ Created `tests/test_retrieve_quick.py` (all passing)
- ✅ Validated semantic search on 10k subset
- ✅ Updated PHASE2_PLAN.md with incremental approach

### 2025-01-14 - Phase 2 Planning
- ✅ Created PHASE2_PLAN.md with detailed implementation plan
- ✅ Researched medical embedding models (SapBERT vs alternatives)
- ✅ Decided on incremental approach (10k → 100k → 3.8M)

### 2025-01-13 - Phase 1 Complete
- ✅ Preprocessing pipeline with full dataset support
- ✅ NetworkX graph construction with caching
- ✅ Validation script for 5 mandatory terms
- ✅ 13/13 unit tests passing
- ✅ Full graph built: 3.8M nodes, 17M edges
- ✅ All validation terms found with rich relationships

### 2025-01-12 - Initial Implementation
- Created preprocessing pipeline (test dataset only)
- Created graph module with basic queries
- Fixed test failures (column ordering, relationship names)
- Optimized test dataset size (500k concepts, 5M relationships)

---

**Document Version:** 2.0
**Last Updated:** 2026-01-16
**Status:** Phase 2 Session 2 In Progress 🚧
**Next:** Test semantic search with mandatory terms on 100k subset
