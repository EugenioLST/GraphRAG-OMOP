"""
compare_phase1_phase2.py - Compare Phase 1 (substring) vs Phase 2 (semantic search)

Tests the same queries on both systems and compares results.

Phase 1: Substring-based search on full 3.8M concepts
Phase 2: Semantic search on 100k embeddings + graph expansion
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieve import SemanticRetriever
from src.graph import load_graph
import pandas as pd

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Test queries covering different scenarios
TEST_QUERIES = [
    # Direct drug names
    {'query': 'metformina', 'category': 'Direct drug (Spanish)', 'expected_type': 'Drug'},
    {'query': 'metformin', 'category': 'Direct drug (English)', 'expected_type': 'Drug'},
    {'query': 'ibuprofen', 'category': 'Direct drug (English)', 'expected_type': 'Drug'},

    # Medical conditions
    {'query': 'diabetes', 'category': 'Condition', 'expected_type': 'Condition'},
    {'query': 'hypertension', 'category': 'Condition', 'expected_type': 'Condition'},

    # Lab measurements
    {'query': 'creatinine', 'category': 'Measurement', 'expected_type': 'Measurement'},

    # Typos (Phase 2 advantage)
    {'query': 'metfornin', 'category': 'Typo', 'expected_type': 'Drug'},
    {'query': 'diabeetes', 'category': 'Typo', 'expected_type': 'Condition'},

    # Synonyms (Phase 2 advantage)
    {'query': 'high blood pressure', 'category': 'Synonym', 'expected_type': 'Condition'},
]


def phase1_search(query, graph, nodes_df, top_k=10):
    """
    Phase 1: Substring-based search on full 3.8M concepts

    Mimics the original Phase 1 implementation
    """
    query_lower = query.lower()

    # Search in concept names (case-insensitive substring match)
    matches = []

    for idx, row in nodes_df.iterrows():
        concept_name = str(row['concept_name']).lower()

        if query_lower in concept_name:
            matches.append({
                'concept_id': row['concept_id'],
                'concept_name': row['concept_name'],
                'vocabulary_id': row['vocabulary_id'],
                'domain_id': row['domain_id'],
                'standard_concept': row['standard_concept'],
                'score': 1.0 if query_lower == concept_name else 0.5  # Exact match vs substring
            })

            if len(matches) >= top_k * 10:  # Get more candidates for sorting
                break

    # Sort by score (exact matches first), then alphabetically
    matches.sort(key=lambda x: (-x['score'], x['concept_name']))

    return matches[:top_k]


def phase2_search(query, retriever, top_k=10):
    """
    Phase 2: Semantic search on 100k embeddings

    Uses SapBERT embeddings for semantic similarity
    """
    return retriever.search(query, top_k=top_k)


def compare_results(query_info, phase1_results, phase2_results):
    """Compare results from both phases"""
    query = query_info['query']
    category = query_info['category']

    print("=" * 80)
    print(f"Query: '{query}' ({category})")
    print("=" * 80)

    # Phase 1 results
    print("\n📊 PHASE 1 (Substring Search):")
    if phase1_results:
        print(f"   Found {len(phase1_results)} results\n")
        for i, result in enumerate(phase1_results[:3], 1):
            print(f"   {i}. {result['concept_name'][:60]}")
            print(f"      {result['vocabulary_id']} | {result['domain_id']}")
    else:
        print("   ❌ No results found\n")

    # Phase 2 results
    print("\n🔬 PHASE 2 (Semantic Search):")
    if phase2_results:
        print(f"   Found {len(phase2_results)} results\n")
        for i, result in enumerate(phase2_results[:3], 1):
            std = "⭐" if result['standard_concept'] == 'S' else "  "
            print(f"   {i}. [Score: {result['score']:.4f}] {std} {result['concept_name'][:60]}")
            print(f"      {result['vocabulary_id']} | {result['domain_id']}")
    else:
        print("   ❌ No results found\n")

    # Analysis
    print("\n📈 Analysis:")

    # Check if Phase 2 found similar concepts
    if phase1_results and phase2_results:
        phase1_top = phase1_results[0]['concept_name'].lower()
        phase2_top = phase2_results[0]['concept_name'].lower()

        if phase1_top == phase2_top:
            print("   ✅ Both phases found the same top result")
        else:
            print("   ⚠️  Different top results")
            print(f"      Phase 1: {phase1_results[0]['concept_name']}")
            print(f"      Phase 2: {phase2_results[0]['concept_name']}")

    elif not phase1_results and phase2_results:
        print("   ✅ Phase 2 found results where Phase 1 failed")
        print("      (Likely due to semantic similarity or typo tolerance)")

    elif phase1_results and not phase2_results:
        print("   ⚠️  Phase 1 found results but Phase 2 didn't")
        print("      (Likely not in 100k embedding subset)")

    else:
        print("   ❌ Neither phase found results")


def main():
    """Run comparison tests"""
    print("=" * 80)
    print("PHASE 1 vs PHASE 2 COMPARISON")
    print("=" * 80)
    print("\nThis script compares substring search (Phase 1) with semantic search (Phase 2)")
    print("=" * 80)

    # Load data for Phase 1
    print("\n📊 Loading Phase 1 data (substring search)...")
    print("   Loading graph and nodes...")
    graph = load_graph()
    nodes_df = pd.read_csv('data/nodes.csv')
    print(f"   ✓ Loaded {len(nodes_df):,} concepts")

    # Initialize Phase 2
    print("\n🔬 Initializing Phase 2 (semantic search)...")
    print("   (Loading embeddings and model, this may take ~15 seconds)")
    retriever = SemanticRetriever(load_graph_data=False)
    print("   ✓ Phase 2 initialized")

    # Run comparisons
    print("\n" + "=" * 80)
    print("RUNNING COMPARISON TESTS")
    print("=" * 80)

    results_summary = []

    for query_info in TEST_QUERIES:
        query = query_info['query']

        # Phase 1
        phase1_results = phase1_search(query, graph, nodes_df, top_k=10)

        # Phase 2
        phase2_results = phase2_search(query, retriever, top_k=10)

        # Compare
        compare_results(query_info, phase1_results, phase2_results)

        # Store summary
        results_summary.append({
            'query': query,
            'category': query_info['category'],
            'phase1_found': len(phase1_results) > 0,
            'phase2_found': len(phase2_results) > 0,
            'phase1_count': len(phase1_results),
            'phase2_count': len(phase2_results)
        })

        print()

    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    phase1_success = sum(1 for r in results_summary if r['phase1_found'])
    phase2_success = sum(1 for r in results_summary if r['phase2_found'])
    total = len(results_summary)

    print(f"\nQueries tested: {total}")
    print(f"Phase 1 found results: {phase1_success}/{total} ({phase1_success/total*100:.1f}%)")
    print(f"Phase 2 found results: {phase2_success}/{total} ({phase2_success/total*100:.1f}%)")

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES")
    print("=" * 80)

    print("""
Phase 1 (Substring Search):
✅ Fast (<10ms per query)
✅ Works on full 3.8M concepts
❌ No typo tolerance
❌ No semantic understanding
❌ Exact substring match only

Phase 2 (Semantic Search):
✅ Semantic similarity (synonyms, related terms)
✅ Typo tolerance (partial)
✅ Multi-lingual support
⚠️  Slower (~1 second per query)
⚠️  Currently limited to 100k concepts (expandable to 3.8M)
✅ Graph expansion provides related concepts
    """)

    print("=" * 80)
    print("\nRECOMMENDATIONS")
    print("=" * 80)
    print("""
For exact term lookups: Use Phase 1 (faster)
For natural language queries: Use Phase 2 (more flexible)
For typos/synonyms: Use Phase 2 (semantic understanding)
For production: Generate full 3.8M embeddings for Phase 2
    """)
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
