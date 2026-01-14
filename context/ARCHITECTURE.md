# GraphRAG-OMOP Architecture

## Overview

GraphRAG-OMOP is a proof-of-concept system for medical concept linking using OMOP vocabulary. It combines graph-based knowledge representation with semantic search to convert medical terms (in English or Spanish) to standardized OMOP concept IDs with hierarchical relationships.

**Current Status:** Phase 1 Complete ✅

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT DATA                               │
│  OMOP CSV Files (data/)                                          │
│  - CONCEPT.csv           (565 MB, ~5M concepts)                  │
│  - RELATIONSHIP.csv      (53 KB, ~700 relationships)             │
│  - CONCEPT_RELATIONSHIP.csv (1.7 GB, ~34M relationships)         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: GRAPH INFRASTRUCTURE (COMPLETE)      │
├─────────────────────────────────────────────────────────────────┤
│  preprocess.py                                                   │
│  ├─ Filter vocabularies (SNOMED, RxNorm, LOINC)                 │
│  ├─ Filter relationships (~23 relevant types)                    │
│  ├─ Chunk processing (500k rows/chunk)                           │
│  └─ Output: nodes.csv (3.8M), edges.csv (17M)                    │
│                                                                   │
│  graph.py                                                        │
│  ├─ Build NetworkX MultiDiGraph                                  │
│  ├─ Pickle caching (100x faster loading)                         │
│  ├─ Query functions: get_concept_info, get_neighbors            │
│  └─ Standard mapping: find_standard_mapping                      │
│                                                                   │
│  validate_poc.py                                                 │
│  └─ Validate 5 mandatory terms: metformin, diabetes,             │
│     creatinine, ibuprofen, hypertension                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: SEMANTIC SEARCH (TODO)                  │
├─────────────────────────────────────────────────────────────────┤
│  embeddings.py                                                   │
│  ├─ Generate embeddings for all concept names                    │
│  ├─ Model: SapBERT (medical domain specialized)                 │
│  └─ Store: embeddings.npy + index for fast retrieval            │
│                                                                   │
│  retrieve.py                                                     │
│  ├─ Semantic search: query → top-k candidates                    │
│  ├─ Graph expansion: get related concepts                        │
│  └─ Ranking: combine semantic + structural signals              │
│                                                                   │
│  main.py                                                         │
│  └─ CLI interface for end-user queries                           │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: Graph Infrastructure (COMPLETE)

### 1. Data Preprocessing (`preprocess.py`)

**Purpose:** Convert raw OMOP CSVs into filtered graph-ready format.

**Input:**
- `data/CONCEPT.csv` (565 MB, ~5M concepts)
- `data/RELATIONSHIP.csv` (53 KB, ~700 relationships)
- `data/CONCEPT_RELATIONSHIP.csv` (1.7 GB, ~34M relationships)

**Processing Steps:**
1. **Vocabulary Filtering:** Keep only SNOMED, RxNorm, LOINC, RxNorm Extension
2. **Relationship Filtering:** Keep ~23 relevant relationship types (mappings, hierarchies, drug components)
3. **Concept Validation:** Remove concepts with null names
4. **Chunk Processing:** Process CONCEPT_RELATIONSHIP.csv in 500k row chunks for memory efficiency
5. **Cross-filtering:** Only keep relationships where both concepts exist in filtered set

**Output:**
- `nodes.csv` (3,855,450 concepts, ~500-700 MB)
  - Columns: `concept_id`, `concept_name`, `vocabulary_id`, `domain_id`, `standard_concept`
- `edges.csv` (17,124,839 relationships, ~1-2 GB)
  - Columns: `concept_id_1`, `relationship_name`, `concept_id_2`

**Performance:**
- Full dataset processing: ~55 minutes (one-time cost)
- Test dataset (500k concepts, 5M relationships): ~2-3 minutes

**Key Design Decisions:**
- **Keep both standard and non-standard concepts:** Non-standard concepts are needed for mapping user terms → standard OMOP IDs
- **Chunk processing:** Prevents memory overflow when processing 1.7 GB CONCEPT_RELATIONSHIP.csv
- **Vocabulary filtering:** Reduces graph from ~5M → ~3.8M nodes while keeping medical relevance

### 2. Graph Construction (`graph.py`)

**Purpose:** Build and query a NetworkX MultiDiGraph from preprocessed data.

**Graph Type:** `networkx.MultiDiGraph`
- **Directed:** Relationships have directionality (e.g., "Is a" points from child → parent)
- **Multi:** Multiple relationship types can exist between same two nodes

**Node Attributes:**
```python
{
    'concept_name': str,      # e.g., "Metformin"
    'vocabulary_id': str,     # e.g., "RxNorm"
    'domain_id': str,         # e.g., "Drug"
    'standard_concept': str   # 'S' = standard, None/NaN = non-standard
}
```

**Edge Attributes:**
```python
{
    'relationship': str       # e.g., "Is a", "Has ingredient (RxNorm)"
}
```

**Core Functions:**

1. **`load_graph(use_cache=True, force_rebuild=False)`**
   - Loads complete OMOP graph with caching
   - First load: ~2-5 minutes (builds from CSVs + creates cache)
   - Subsequent loads: ~5 seconds (loads from `omop_graph.pkl`)
   - Cache file: ~1-2 GB pickle file

2. **`get_concept_info(G, concept_id)`**
   - Retrieves concept metadata by ID
   - Returns: dict with concept_id, name, vocabulary, domain, standard status

3. **`get_neighbors(G, concept_id, max_neighbors=10)`**
   - Gets 1-hop relationships (both incoming and outgoing)
   - Returns: list of dicts with relationship type, direction, target concept info

4. **`find_standard_mapping(G, concept_id)`**
   - Follows mapping relationships to find standard concept
   - Handles chains: non-standard → non-standard → standard
   - Returns: dict with standard concept info, or None if no mapping found

**Relationship Types (23 filtered from 722 total):**

*Mapping relationships:*
- `Non-standard to Standard map (OMOP)`
- `Standard to Non-standard map (OMOP)`
- `Concept replaced by`
- `Concept replaces`

*Hierarchical relationships:*
- `Is a`
- `Subsumes`
- `Is a (RxNorm)`
- `Inverse is a (RxNorm)`

*RxNorm drug relationships:*
- `Has ingredient (RxNorm)` / `Ingredient of (RxNorm)`
- `Has form (RxNorm)` / `Form of (RxNorm)`
- `Has dose form (RxNorm)` / `Dose form of (RxNorm)`
- `Contains (RxNorm)` / `Consists of (RxNorm)` / `Constitutes (RxNorm)`
- `Has tradename (RxNorm)` / `Tradename of (RxNorm)`

*SNOMED relationships:*
- `Has active ingredient (SNOMED)` / `Active ingredient of (SNOMED)`
- `Has basic dose form (SNOMED)` / `Basic dose form of (SNOMED)`

**Performance Characteristics:**
- **Density:** 0.000001 (sparse graph, efficient for traversal)
- **Nodes:** 3,855,450 concepts
- **Edges:** 17,124,839 relationships
- **Cache load time:** ~5 seconds
- **Node lookup:** O(1) via NetworkX dict-based storage
- **1-hop traversal:** O(k) where k = number of neighbors (~10-100 typically)

### 3. Validation (`validate_poc.py`)

**Purpose:** Validate PoC with 5 mandatory medical terms.

**Test Terms:**
1. **Metformin** (metformin, metformina) → 9,207 matches
2. **Diabetes** (diabetes) → 1,806 matches
3. **Creatinine** (creatinine, creatinina) → 5,054 matches
4. **Ibuprofen** (ibuprofen, ibuprofeno) → 18,174 matches
5. **Hypertension** (hypertension, hipertensión) → 785 matches

**Validation Steps for Each Term:**
1. Search by name (case-insensitive, substring match)
2. Display top 3 matches with concept info
3. Show detailed analysis of first match:
   - Concept metadata (ID, name, vocabulary, domain, standard status)
   - Top 5 relationships (1-hop, both directions)
   - Standard mapping (if non-standard concept)

**Result:** All 5 terms validated ✅
- All terms found with multiple matches
- All have rich relationship networks (hierarchies, mappings, components)
- Standard mappings work correctly for non-standard concepts

### 4. Testing (`tests/test_preprocess.py`)

**Test Coverage:**
- File validation (missing files, file existence)
- CONCEPT.csv loading (structure, vocabularies, standard/non-standard mix)
- RELATIONSHIP.csv loading (structure, mapping relationships present)
- CONCEPT_RELATIONSHIP.csv loading (structure, filtering, empty edge cases)
- Full pipeline (end-to-end, output validation, referential integrity)

**Test Results:** 13/13 tests passing ✅

**Key Test Cases:**
- `test_load_concept_data_keeps_non_standard`: Ensures both standard and non-standard concepts are kept (critical for mapping)
- `test_load_relationship_mapping_contains_maps_to`: Validates presence of critical mapping relationships
- `test_preprocess_edges_valid`: Verifies all edge endpoints exist in nodes (referential integrity)

## Data Flow

```
User Query: "metformina"
        ↓
[Phase 2 - Semantic Search]
        ↓
Top-K Candidates: [concept_id_1, concept_id_2, ...]
        ↓
[Phase 1 - Graph Queries]
        ↓
get_concept_info(concept_id_1) → metadata
get_neighbors(concept_id_1) → 1-hop relationships
find_standard_mapping(concept_id_1) → standard OMOP ID
        ↓
Result: Standardized concept + context
```

## Technical Stack

**Languages & Core Libraries:**
- Python 3.12
- pandas 2.2.3 (CSV processing)
- networkx 3.4.2 (graph structure)
- numpy 2.2.1 (array operations)

**Testing:**
- pytest 8.3.4

**Future (Phase 2):**
- sentence-transformers (SapBERT embeddings)
- torch (deep learning backend)

## File Structure

```
GraphRAG-OMOP/
├── data/                          # Raw OMOP CSV files (not in git)
│   ├── CONCEPT.csv               (565 MB)
│   ├── RELATIONSHIP.csv          (53 KB)
│   └── CONCEPT_RELATIONSHIP.csv  (1.7 GB)
│
├── context/                       # Project documentation
│   ├── ARCHITECTURE.md           (this file)
│   ├── CLAUDE.md                 (project scope & requirements)
│   ├── TASKS.md                  (implementation tasks)
│   └── ACTUAL_FEATURE.md         (feature details)
│
├── tests/                         # Unit tests
│   └── test_preprocess.py        (13 tests, all passing)
│
├── preprocess.py                  # Phase 1: Data preprocessing
├── graph.py                       # Phase 1: Graph construction
├── validate_poc.py                # Phase 1: PoC validation
│
├── nodes.csv                      # Generated: filtered concepts (3.8M, ~700 MB)
├── edges.csv                      # Generated: filtered relationships (17M, ~1-2 GB)
├── omop_graph.pkl                 # Generated: cached NetworkX graph (~1-2 GB)
│
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # Project overview
```

## Performance Metrics

### Memory Usage
- **Peak during preprocessing:** ~4-6 GB RAM
  - Chunk processing keeps memory bounded
  - 500k rows/chunk balance between memory and speed
- **Graph in memory:** ~2-3 GB RAM
  - NetworkX uses dict-based storage (efficient for sparse graphs)
- **Cache file size:** ~1-2 GB on disk

### Processing Time
- **Full preprocessing (one-time):** ~55 minutes
  - CONCEPT.csv load: ~2-3 minutes
  - CONCEPT_RELATIONSHIP.csv chunk processing: ~50 minutes
  - CSV output writing: ~2-3 minutes
- **Graph cache creation (one-time):** ~2-3 minutes
- **Graph load (cached):** ~5 seconds (100x speedup)
- **Single concept lookup:** <1ms
- **1-hop neighbor query:** <10ms (typical)

### Dataset Statistics
- **Input:** 5M concepts, 34M relationships
- **After filtering:** 3.8M concepts, 17M relationships
- **Reduction:** ~25% concepts kept, ~50% relationships kept
- **Vocabularies:** SNOMED (largest), RxNorm, LOINC, RxNorm Extension
- **Relationship types:** 23 relevant types (from 722 total)

## Design Decisions & Rationale

### 1. Why NetworkX instead of Neo4j?
**Decision:** Use NetworkX (in-memory Python graph library)

**Rationale:**
- **Simplicity:** No database setup, pure Python
- **Performance:** In-memory graphs are extremely fast for our scale (~3.8M nodes)
- **Development speed:** Native Python objects, easy to debug
- **Sufficient for PoC:** Full dataset fits comfortably in RAM (2-3 GB)

**Trade-off:** If scaling to 100M+ nodes or needing persistent queries, Neo4j would be better.

### 2. Why keep non-standard concepts?
**Decision:** Keep both standard and non-standard concepts in graph

**Rationale:**
- **User queries may be non-standard:** "metformina" might map to non-standard concept first
- **Mapping chains exist:** non-standard → non-standard → standard
- **Completeness:** Phase 2 semantic search needs all concepts as candidates

**Evidence:** `validate_poc.py` shows several test terms hit non-standard concepts initially, then map to standard.

### 3. Why chunk processing?
**Decision:** Process CONCEPT_RELATIONSHIP.csv in 500k row chunks

**Rationale:**
- **Memory efficiency:** 1.7 GB file, 34M rows - cannot load all at once on typical machines
- **Progress visibility:** Print updates every 10 chunks (~5M rows)
- **Error recovery:** If process fails, can debug specific chunk

**Trade-off:** Slightly slower than full in-memory (concatenating chunks), but enables processing on consumer hardware.

### 4. Why pickle caching?
**Decision:** Cache NetworkX graph as pickle file (`omop_graph.pkl`)

**Rationale:**
- **100x speedup:** 5 seconds vs 2-5 minutes to load
- **Deterministic:** Same CSV input = same graph = same cache
- **Development workflow:** Rapid iteration on Phase 2 without rebuilding graph

**Trade-off:** Cache invalidates if CSVs change (handled by `force_rebuild` flag).

### 5. Why MultiDiGraph?
**Decision:** Use `networkx.MultiDiGraph` (directed multigraph)

**Rationale:**
- **Multiple relationship types:** Same two concepts can have "Is a" AND "Maps to"
- **Directionality matters:** "Is a" points child → parent, not symmetric
- **OMOP structure:** CONCEPT_RELATIONSHIP is inherently directed and multi-typed

**Alternative considered:** Simple DiGraph with edge type as attribute - rejected because it doesn't naturally support multiple edges.

### 6. Why filter to 23 relationship types?
**Decision:** Whitelist ~23 relationship types from 722 total

**Rationale:**
- **Relevance:** Most relationships are vocabulary-specific metadata, not medical semantics
- **Graph size:** Reduces edges from ~34M → ~17M (50% reduction)
- **Query efficiency:** Smaller graph = faster traversal
- **Interpretability:** Users care about "Is a", "Has ingredient", not internal RxNorm codes

**Whitelist criteria:**
- Hierarchical relationships (Is a, Subsumes)
- Mapping relationships (standard ↔ non-standard)
- Drug component relationships (ingredient, dose form, tradename)
- Clinical relationships (SNOMED active ingredient)

## Known Limitations

### Current (Phase 1)
1. **Search is substring-based:** Naive string matching, no fuzzy search or typo tolerance
2. **No ranking:** Multiple matches returned in arbitrary order
3. **English/Spanish only:** Hardcoded test terms, no systematic multi-lingual support
4. **No semantic understanding:** "metformina" won't match "biguanide" (chemical class)

### Future (Phase 2 will address)
1. **Semantic search:** SapBERT embeddings will handle synonyms, paraphrases, typos
2. **Ranking:** Combine semantic similarity + graph structure (PageRank, connectivity)
3. **Multi-lingual:** Embeddings handle multiple languages naturally
4. **Conceptual queries:** "diabetes medication" → retrieve all anti-diabetic drugs

## Next Steps: Phase 2 Implementation

### 1. `embeddings.py` - Generate Concept Embeddings
**Goal:** Create semantic embeddings for all concept names

**Tasks:**
- Load SapBERT model (biomedical BERT fine-tuned on UMLS)
- Generate embeddings for all 3.8M concept names
- Store embeddings as numpy array (`embeddings.npy`)
- Create concept_id → embedding_index mapping
- Estimate: ~2-4 hours on GPU for full dataset

**Key decisions:**
- Model: SapBERT (proven best for medical concepts)
- Batch size: 256 (balance speed vs memory)
- Device: CUDA if available, else CPU

### 2. `retrieve.py` - Semantic Search + Graph Expansion
**Goal:** Convert user query → ranked list of relevant concepts

**Tasks:**
- Implement semantic search (query embedding → cosine similarity → top-k)
- Implement graph expansion (get neighbors, follow hierarchies)
- Implement ranking (combine semantic + structural signals)
- Add filtering by vocabulary, domain, standard status

**Key functions:**
- `semantic_search(query, top_k=10)` → list of candidate concept_ids
- `expand_graph(concept_id, depth=1)` → related concepts
- `rank_results(candidates, query)` → sorted list with scores

### 3. `main.py` - CLI Interface
**Goal:** User-friendly command-line interface

**Tasks:**
- Argument parsing (query text, filters, output format)
- Pretty-print results (concept info + relationships)
- Support batch queries (CSV input → CSV output)
- Add verbose mode for debugging

**Example usage:**
```bash
# Single query
python main.py "metformina"

# Batch mode
python main.py --batch queries.csv --output results.csv

# With filters
python main.py "diabetes" --vocabulary SNOMED --standard-only
```

### 4. Evaluation Dataset
**Goal:** Compare Phase 1 (substring) vs Phase 2 (semantic) performance

**Tasks:**
- Create gold standard: 50-100 test queries with ground truth concept_ids
- Include typos, synonyms, multi-word queries, Spanish terms
- Measure recall@k, MRR (Mean Reciprocal Rank), precision
- Document performance improvements

## Success Criteria

### Phase 1 (ACHIEVED ✅)
- [x] All 5 mandatory terms found in graph
- [x] All terms have relationships (1-hop traversal works)
- [x] Standard mappings work for non-standard concepts
- [x] All tests passing (13/13)
- [x] Full dataset processed and cached

### Phase 2 (TODO)
- [ ] Semantic search handles typos ("metfornin" → "metformin")
- [ ] Multi-lingual support (Spanish queries work)
- [ ] Ranking improves relevance (target concept in top-3)
- [ ] Performance: <1 second for query → results
- [ ] Evaluation: >80% recall@10 on test set

## References

### OMOP Resources
- [OMOP Common Data Model](https://www.ohdsi.org/data-standardization/)
- [OMOP Standardized Vocabularies](https://athena.ohdsi.org/)
- [OMOP Concept Relationships](https://ohdsi.github.io/CommonDataModel/cdm531.html#CONCEPT_RELATIONSHIP)

### Technical Resources
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [SapBERT Paper](https://arxiv.org/abs/2010.11784) - Self-Alignment Pretraining for BERT
- [BioBERT](https://github.com/dmis-lab/biobert) - Alternative medical BERT
- [UMLS](https://www.nlm.nih.gov/research/umls/) - Unified Medical Language System

## Changelog

### 2025-01-13 - Phase 1 Complete
- ✅ Preprocessing pipeline with full dataset support
- ✅ NetworkX graph construction with caching
- ✅ Validation script for 5 mandatory terms
- ✅ 13/13 unit tests passing
- ✅ Documentation complete (this file)
- ✅ Full graph built: 3.8M nodes, 17M edges
- ✅ All validation terms found with rich relationships

### 2025-01-12 - Initial Implementation
- Created preprocessing pipeline (test dataset only)
- Created graph module with basic queries
- Fixed test failures (column ordering, relationship names)
- Optimized test dataset size (500k concepts, 5M relationships)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-13
**Status:** Phase 1 Complete, Phase 2 Pending
