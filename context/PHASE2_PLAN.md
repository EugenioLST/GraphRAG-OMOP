# Phase 2: Semantic Search Implementation Plan

## Goal
Implement semantic search capabilities using medical domain embeddings (SapBERT) to enable natural language queries for OMOP concepts, handling typos, synonyms, and multi-lingual input.

## Current State (Phase 1 Complete ✅)
- Graph infrastructure built: 3.8M nodes, 17M edges
- NetworkX MultiDiGraph with caching
- Substring-based search working
- All 5 mandatory terms validated

## Phase 2 Objectives
1. Generate embeddings for all concept names using SapBERT
2. Implement semantic search with cosine similarity
3. Add graph expansion for contextual results
4. Create CLI interface for end users
5. Validate improvements over Phase 1 substring search

---

## Implementation Strategy: Incremental Approach

**⚠️ IMPORTANT: Start Small, Scale Up**

We will follow an incremental approach to validate functionality before processing the full dataset:

1. **Small Test (10k concepts)** → ~1-2 minutes → Validate code works
2. **Medium Test (100k concepts)** → ~10-15 minutes → Complete testing & validation
3. **Full Dataset (3.8M concepts)** → ~4-8 hours CPU → Production ready

**Rationale:**
- No GPU/CUDA available → CPU processing is slower
- Early validation catches bugs quickly
- Subset testing allows rapid iteration
- Full dataset only after confirming everything works

---

## Implementation Plan

### Step 1: Setup Dependencies
**File:** `requirements.txt`

**Tasks:**
- [ ] Add `torch` (CPU-only version, ~200 MB)
- [ ] Add `sentence-transformers>=2.2.0`
- [ ] Add `scikit-learn>=1.3.0` (cosine similarity)
- [ ] Test installation on Windows environment

**Installation Commands:**
```bash
# CPU-only PyTorch (smaller, no CUDA)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
pip install scikit-learn
```

**Considerations:**
- **CPU-only PyTorch:** ~200 MB (no CUDA libraries needed)
- sentence-transformers includes transformers, tokenizers automatically
- SapBERT model auto-downloaded: ~440 MB
- **Total disk space:** ~700 MB for dependencies + models

---

### Step 2: Create `embeddings.py` - Generate Embeddings with Subset Support
**Purpose:** Generate and cache embeddings with support for testing subsets

**Input:**
- `nodes.csv` (3.8M concepts with names)
- SapBERT model from HuggingFace: `cambridgeltl/SapBERT-from-PubMedBERT-fulltext`

**Output:**
- `embeddings.npy` (~3.8M x 768 float32 = ~11 GB)
- `concept_id_to_index.pkl` (mapping: concept_id → embedding row index)

**Key Functions:**

1. **`load_sapbert_model()`**
   - Load pre-trained SapBERT from HuggingFace
   - Device: CUDA if available, else CPU
   - Return: model + tokenizer

2. **`generate_embeddings(concept_names, batch_size=256)`**
   - Batch encode concept names
   - Progress bar for user visibility
   - Handle long texts (truncate to 512 tokens)
   - Return: numpy array (N x 768)

3. **`build_embedding_index(nodes_csv_path, output_dir='.', max_concepts=None)`**
   - Load nodes.csv
   - **NEW: `max_concepts` parameter for subset testing**
   - Extract concept_id + concept_name
   - Generate embeddings in batches
   - Save embeddings.npy + concept_id_to_index.pkl
   - Handle errors gracefully (skip malformed names)

4. **`load_embeddings(output_dir='.')`**
   - Load embeddings.npy + mapping
   - Return: embeddings array + concept_id_to_index dict

**Performance Estimates (CPU):**

| Dataset | Concepts | Time | Disk Space | Use Case |
|---------|----------|------|------------|----------|
| **Small** | 10k | 1-2 min | ~30 MB | Validate code works |
| **Medium** | 100k | 10-15 min | ~300 MB | Complete testing |
| **Full** | 3.8M | 4-8 hours | ~11 GB | Production |

**Memory:** ~8-10 GB peak during generation (same for all sizes)

**Design Decisions:**
- **Why SapBERT?** Medical domain BERT, proven best for UMLS/OMOP concepts
- **Why numpy array?** Efficient for cosine similarity computation
- **Why batch processing?** Memory efficiency + progress visibility
- **Why cache?** One-time cost, then instant loading

**Error Handling:**
- Empty concept names → skip with warning
- Very long names → truncate to 512 tokens
- CUDA out of memory → fallback to CPU with smaller batches

---

### Step 3: Create `retrieve.py` - Semantic Search Engine
**Purpose:** Convert user query → ranked list of relevant concepts

**Input:**
- User query (string, any language)
- Embeddings from `embeddings.py`
- Graph from `graph.py`

**Output:**
- Ranked list of concepts with scores and metadata

**Key Functions:**

1. **`SemanticRetriever` class**
   ```python
   class SemanticRetriever:
       def __init__(self, embeddings_path, graph_path, nodes_csv_path):
           # Load embeddings, graph, concept metadata

       def search(self, query, top_k=10, filters=None):
           # Semantic search with optional filters

       def expand_graph(self, concept_id, depth=1):
           # Get related concepts via graph

       def rank_results(self, candidates, query):
           # Combine semantic + structural signals
   ```

2. **`search(query, top_k=10, filters=None)`**
   - Encode query using SapBERT
   - Compute cosine similarity with all embeddings
   - Get top-k candidates
   - Apply filters (vocabulary, domain, standard_only)
   - Return: list of dicts with concept_id, score, metadata

3. **`expand_graph(concept_id, depth=1)`**
   - Get neighbors from NetworkX graph
   - Follow "Is a" hierarchies (parents/children)
   - Follow "Maps to" relationships (standard mappings)
   - Return: list of related concept_ids with relationship types

4. **`rank_results(candidates, query, use_graph=True)`**
   - Primary score: cosine similarity (semantic)
   - Boost score: graph connectivity (PageRank, degree)
   - Boost score: standard concepts (+0.1)
   - Sort by combined score
   - Return: sorted list

**Filtering Options:**
- `vocabulary`: Filter to SNOMED / RxNorm / LOINC
- `domain`: Filter to Drug / Condition / Measurement
- `standard_only`: Only return standard concepts
- `min_score`: Minimum cosine similarity threshold (e.g., 0.5)

**Performance Targets:**
- Query → results: <1 second (single query)
- Cosine similarity: ~100ms for 3.8M vectors (numpy optimized)
- Graph expansion: ~10ms per concept (cached NetworkX)

**Design Decisions:**
- **Why cosine similarity?** Standard for semantic search, range [0,1]
- **Why filters?** Users may want SNOMED only, or drugs only
- **Why graph expansion?** Provides contextual related concepts
- **Why ranking combination?** Semantic + structural = better results

---

### Step 4: Create `main.py` - CLI Interface
**Purpose:** User-friendly command-line tool for concept search

**Usage Examples:**
```bash
# Single query
python main.py "metformina"

# With filters
python main.py "diabetes" --vocabulary SNOMED --standard-only

# Specify top-k
python main.py "creatinine" --top-k 20

# Batch mode
python main.py --batch queries.csv --output results.csv

# Verbose mode
python main.py "ibuprofen" --verbose
```

**Key Features:**

1. **Argument Parsing**
   - Required: query text OR --batch file
   - Optional: --top-k, --vocabulary, --domain, --standard-only, --verbose
   - Output: --output (for batch mode)

2. **Pretty Printing**
   - Display top-k results in readable format
   - Show: rank, score, concept_id, name, vocabulary, domain
   - Show relationships (if verbose)
   - Show standard mapping (if non-standard)

3. **Batch Mode**
   - Input CSV: query column
   - Output CSV: query, rank, concept_id, name, score, vocabulary, domain
   - Progress bar for large batches

4. **Error Handling**
   - Invalid query → friendly error message
   - No results → suggest relaxing filters
   - Missing files → instructions to run embeddings.py first

**Example Output:**
```
Query: "metformina"
================================================================================
Results (top 10):

 1. [Score: 0.98] Metformin [1503297]
    Vocabulary: RxNorm | Domain: Drug | Standard: Yes

 2. [Score: 0.95] Metformin hydrochloride [1586346]
    Vocabulary: RxNorm | Domain: Drug | Standard: Yes

 3. [Score: 0.92] Metformin 500 MG Oral Tablet [860975]
    Vocabulary: RxNorm | Domain: Drug | Standard: Yes

 ... (7 more results)

================================================================================
```

**Design Decisions:**
- **Why CLI?** Fast prototyping, easy testing, scriptable
- **Why batch mode?** Evaluate on test sets, process multiple queries
- **Why verbose?** Debugging, understanding results
- **Future:** Web UI could wrap this CLI logic

---

### Step 5: Testing & Validation

**Test Suite 1: Unit Tests (`tests/test_embeddings.py`)**
- [ ] Test SapBERT model loading
- [ ] Test embedding generation (small batch)
- [ ] Test embedding dimensions (768)
- [ ] Test caching (save/load)

**Test Suite 2: Integration Tests (`tests/test_retrieve.py`)**
- [ ] Test semantic search (known query → expected concept)
- [ ] Test filters (vocabulary, domain, standard_only)
- [ ] Test graph expansion
- [ ] Test ranking

**Test Suite 3: End-to-End Validation (`validate_phase2.py`)**
- [ ] Run all 5 mandatory terms through semantic search
- [ ] Compare Phase 1 (substring) vs Phase 2 (semantic)
- [ ] Test typos: "metfornin", "diabeetes", "creatinne"
- [ ] Test Spanish: "metformina", "hipertensión"
- [ ] Test synonyms: "high blood pressure" → hypertension
- [ ] Measure recall@10, MRR, precision

**Success Criteria:**
- All 5 mandatory terms found in top-10 (semantic search)
- Typos handled correctly (target concept in top-3)
- Spanish queries work (target concept in top-5)
- Performance: <1 second per query
- Recall@10 > 80% on evaluation set

---

## Implementation Timeline

### Session 1: Setup + Small Test ✅ COMPLETE
- [x] Create Phase 2 plan document
- [x] Document incremental approach
- [x] Update requirements.txt (CPU-only torch)
- [x] Install dependencies
- [x] Create embeddings.py with `max_concepts` parameter
- [x] **Generate embeddings for 10k concepts (~1-2 min)**
- [x] Test embedding load time

### Session 2: Retrieval + Medium Test ✅ COMPLETE
- [x] Reorganize file structure (src/, data/, tests/, scripts/)
- [x] Update all imports with sys.path fixes
- [x] Update ARCHITECTURE.md with new structure
- [x] Create retrieve.py
- [x] Implement SemanticRetriever class
- [x] **Generate embeddings for 100k concepts (~10-15 min)**
- [x] Test semantic search with mandatory terms on 100k subset
- [x] Implement filtering
- [x] Fix critical bug: graph expansion now uses full 3.8M graph metadata
- [x] Create validate_phase2.py script

### Session 3: CLI + Validation on 100k ✅ COMPLETE
- [x] Create main.py
- [x] Implement argument parsing + pretty printing
- [x] Create validate_phase2.py (completed in Session 2)
- [x] Run end-to-end validation on 100k subset
- [x] Compare Phase 1 vs Phase 2 results
- [x] Create compare_phase1_phase2.py script

### Session 4: Full Dataset (Optional, after validation)
- [ ] **Generate embeddings for full 3.8M concepts (~4-8 hours)**
- [ ] Run validation on full dataset
- [ ] Document final results
- [ ] Performance optimization if needed

### Session 5: Alternative Model Comparison (Optional)
- [ ] Add ModernPubMedBERT support to embeddings.py
- [ ] Generate embeddings with ModernPubMedBERT (100k subset)
- [ ] Compare SapBERT vs ModernPubMedBERT on mandatory terms
- [ ] Benchmark: accuracy, speed, memory usage
- [ ] Document which model performs better for OMOP use case
- [ ] Decision: keep SapBERT or switch to ModernPubMedBERT

---

## Technical Specifications

### Primary Model: SapBERT (Recommended)
- **Name:** `cambridgeltl/SapBERT-from-PubMedBERT-fulltext`
- **Base:** PubMedBERT (trained on biomedical literature)
- **Fine-tuning:** UMLS synonyms (medical concepts)
- **Embedding Dim:** 768
- **Max Tokens:** 512
- **Size:** ~440 MB
- **Performance:** State-of-the-art on UMLS/SNOMED CT entity linking (2024)
- **Best for:** OMOP concept linking, SNOMED CT, medical entity normalization

**Why SapBERT?**
- ✅ Specifically trained on UMLS (OMOP foundation)
- ✅ Proven state-of-the-art for SNOMED CT (56% of dataset)
- ✅ F1-Score 0.853 on medical concept normalization
- ✅ Multiple 2024 papers confirm production use

### Alternative Model: ModernPubMedBERT (Optional Comparison)
- **Name:** `lokeshch19/ModernPubMedBERT`
- **Base:** Clinical ModernBERT
- **Fine-tuning:** InfoNCE contrastive learning on PubMed
- **Embedding Dim:** 768
- **Max Tokens:** 2048 (4x longer context than SapBERT)
- **Size:** ~440 MB
- **Performance:** +12.7% vs baseline on medical concepts, -58% false positives

**Why ModernPubMedBERT could be better?**
- ✅ Longer context (2048 tokens vs 512)
- ✅ Better discrimination of medical vs non-medical terms
- ✅ Recent architecture (ModernBERT, 2024)
- ⚠️ Less benchmarks for UMLS/SNOMED CT specifically
- ⚠️ Newer, less production validation

**Comparison Plan (Session 5):**
```python
# Test both models on same 100k concepts
sapbert_results = test_model('cambridgeltl/SapBERT-from-PubMedBERT-fulltext')
modern_results = test_model('lokeshch19/ModernPubMedBERT')

# Compare on mandatory terms
for term in ['metformin', 'diabetes', 'creatinine', 'ibuprofen', 'hypertension']:
    compare_ranking(sapbert_results[term], modern_results[term])

# Metrics: Recall@10, MRR, precision, speed
```

### Other Alternatives Considered
1. **BioBERT:** Good but older, SapBERT outperforms on UMLS
2. **PubMedBERT:** Base model, SapBERT adds synonym alignment
3. **All-MiniLM-L6-v2:** Fast but general domain, not medical
4. **UmlsBERT:** UMLS-focused but older (2021)
5. **MedEIR:** Very new (2025), less validation

### File Structure (Phase 2)
```
GraphRAG-OMOP/
├── embeddings.py          # NEW: Generate embeddings
├── retrieve.py            # NEW: Semantic search
├── main.py                # NEW: CLI interface
├── validate_phase2.py     # NEW: Phase 2 validation
│
├── embeddings.npy         # Generated: 3.8M x 768 (~11 GB)
├── concept_id_to_index.pkl # Generated: mapping (~50 MB)
│
├── tests/
│   ├── test_embeddings.py # NEW: Embedding tests
│   └── test_retrieve.py   # NEW: Retrieval tests
│
└── context/
    └── PHASE2_PLAN.md     # This file
```

---

## Risk Assessment & Mitigation

### Risk 1: Large Embedding File (~11 GB)
**Impact:** Disk space, memory usage, load time
**Mitigation:**
- Use float32 (not float64) for smaller size
- Load embeddings memory-mapped (np.load with mmap_mode)
- Document minimum system requirements (16 GB RAM recommended)

### Risk 2: Slow Embedding Generation (4-8 hours on CPU)
**Impact:** Long wait time for first-time setup
**Mitigation:**
- Clear progress bar with ETA
- Support for resuming (save checkpoints)
- Document GPU speedup benefits
- Provide pre-computed embeddings (future)

### Risk 3: SapBERT Model Download Fails
**Impact:** Cannot generate embeddings
**Mitigation:**
- Retry logic with exponential backoff
- Manual download instructions
- Fallback to local model path

### Risk 4: Query Performance (<1s target)
**Impact:** Slow user experience
**Mitigation:**
- Numpy vectorized operations (fast)
- Pre-load embeddings at startup (one-time cost)
- Consider FAISS for approximate nearest neighbors (future optimization)

---

## Success Metrics

### Quantitative Metrics
- **Recall@10:** >80% (target concept in top-10 results)
- **MRR (Mean Reciprocal Rank):** >0.7 (target concept rank)
- **Query Latency:** <1 second (95th percentile)
- **Typo Tolerance:** >70% recall with 1-2 character errors

### Qualitative Metrics
- Handles Spanish queries correctly
- Handles synonyms (e.g., "high blood pressure" → hypertension)
- Returns clinically relevant results (not just string matches)
- Standard mappings work correctly

### Comparison: Phase 1 vs Phase 2
| Metric | Phase 1 (Substring) | Phase 2 (Semantic) | Improvement |
|--------|---------------------|-----------------------|-------------|
| Exact match | ✅ 100% | ✅ 100% | - |
| Typo tolerance | ❌ 0% | ✅ 70%+ | +70% |
| Spanish queries | ⚠️ 50% | ✅ 90%+ | +40% |
| Synonym matching | ❌ 0% | ✅ 60%+ | +60% |
| Query speed | <10ms | <1000ms | -990ms |

---

## Future Enhancements (Post-Phase 2)

### Phase 3: Advanced Features
- [ ] Multi-hop graph reasoning (2-3 hops)
- [ ] Query expansion (synonym enrichment)
- [ ] Negative filtering ("diabetes NOT type 1")
- [ ] Approximate nearest neighbors (FAISS for speed)

### Phase 4: Production Ready
- [ ] Web API (FastAPI)
- [ ] Web UI (React frontend)
- [ ] Authentication & rate limiting
- [ ] Monitoring & logging
- [ ] Docker deployment

### Phase 5: Evaluation & Optimization
- [ ] Create gold standard evaluation dataset (100+ queries)
- [ ] Compare multiple embedding models (SapBERT vs BioBERT vs PubMedBERT)
- [ ] Hyperparameter tuning (batch size, top-k, scoring weights)
- [ ] Publish results & methodology

---

## References

### Papers & Models
- [SapBERT Paper (2020)](https://arxiv.org/abs/2010.11784) - Self-Alignment Pretraining for BERT
- [PubMedBERT Paper (2020)](https://arxiv.org/abs/2007.15779) - Domain-specific BERT
- [HuggingFace SapBERT](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext)

### Tools & Libraries
- [sentence-transformers](https://www.sbert.net/) - Easy BERT embeddings
- [NetworkX](https://networkx.org/) - Graph algorithms
- [NumPy](https://numpy.org/) - Fast array operations

---

## Document Metadata
**Version:** 1.0
**Created:** 2025-01-14
**Status:** Planning Complete, Ready for Implementation
**Estimated Total Time:** 6-10 hours (including embedding generation)
