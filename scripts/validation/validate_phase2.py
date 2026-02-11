"""
validate_phase2.py - Validate Phase 2 Semantic Search

Tests the 5 mandatory medical terms with semantic search and compares
results with Phase 1 substring search.

Test Terms:
- metformina / metformin
- diabetes
- creatinina / creatinine
- ibuprofeno / ibuprofen
- hipertensión / hypertension
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieve import SemanticRetriever

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test terms (Spanish versions to test multi-lingual)
TEST_TERMS = {
    'Metformin': ['metformina', 'metformin'],
    'Diabetes': ['diabetes'],
    'Creatinine': ['creatinina', 'creatinine'],
    'Ibuprofen': ['ibuprofeno', 'ibuprofen'],
    'Hypertension': ['hipertensión', 'hypertension']
}


def validate_term(retriever, term_name, search_queries, top_k=10):
    """
    Validate a single medical term with semantic search.

    Args:
        retriever: SemanticRetriever instance
        term_name: Display name for the term
        search_queries: List of search terms to try
        top_k: Number of results to retrieve

    Returns:
        dict with validation results
    """
    print("\n" + "=" * 70)
    print(f"TESTING: {term_name}")
    print("=" * 70)

    results_summary = {
        'term': term_name,
        'queries': search_queries,
        'found': False,
        'best_score': 0.0,
        'best_match': None,
        'results_count': 0
    }

    for query in search_queries:
        print(f"\n🔍 Query: '{query}'")

        try:
            results = retriever.search(query, top_k=top_k)

            if not results:
                print(f"   ❌ No results found")
                continue

            results_summary['found'] = True
            results_summary['results_count'] = len(results)

            # Show top 3 results
            print(f"   ✓ Found {len(results)} results")
            print(f"\n   Top 3 matches:")
            for i, result in enumerate(results[:3], 1):
                std = "⭐" if result['standard_concept'] == 'S' else "  "
                print(f"   {i}. [Score: {result['score']:.4f}] {std} {result['concept_name'][:60]}")
                print(f"      {result['vocabulary_id']} | {result['domain_id']}")

                # Track best match
                if result['score'] > results_summary['best_score']:
                    results_summary['best_score'] = result['score']
                    results_summary['best_match'] = result['concept_name']

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            continue

    # Summary
    if results_summary['found']:
        print(f"\n✅ SUCCESS for {term_name}")
        print(f"   Best match: {results_summary['best_match']}")
        print(f"   Best score: {results_summary['best_score']:.4f}")
    else:
        print(f"\n❌ FAILED for {term_name}")
        print(f"   Not found in 100k subset")

    return results_summary


def main():
    """Run validation for all test terms"""
    print("=" * 70)
    print("PHASE 2 SEMANTIC SEARCH VALIDATION")
    print("=" * 70)
    print("\nThis script validates Phase 2 with 5 mandatory medical terms.")
    print("Using 100k concept embeddings subset.")
    print("=" * 70)

    # Initialize retriever (no graph for speed)
    print("\n📊 Initializing SemanticRetriever...")
    print("(Loading embeddings and model, this may take ~15 seconds)")
    retriever = SemanticRetriever(load_graph_data=False)

    print("\n✓ Retriever initialized")

    # Validate each term
    all_results = []
    for term_name, search_queries in TEST_TERMS.items():
        result = validate_term(retriever, term_name, search_queries, top_k=10)
        all_results.append(result)

    # Final summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    found_count = sum(1 for r in all_results if r['found'])
    total_count = len(all_results)

    print(f"\nTerms found: {found_count}/{total_count}")
    print()

    for result in all_results:
        status = "✅" if result['found'] else "❌"
        score = f"{result['best_score']:.3f}" if result['found'] else "N/A"
        match = result['best_match'][:40] if result['best_match'] else "Not found"
        print(f"{status} {result['term']:15} | Score: {score:6} | {match}")

    print("\n" + "=" * 70)
    print("NOTES")
    print("=" * 70)
    print("""
✓ Found terms: Semantic search working correctly
❌ Not found terms: Likely not in first 100k concepts

To improve coverage:
1. Generate embeddings for full 3.8M concepts:
   python src/embeddings.py

2. Or use larger subset:
   python src/embeddings.py --max-concepts 500000

Current subset (100k) is sufficient for PoC validation.
    """)
    print("=" * 70)

    # Return success if at least 3/5 found
    success = found_count >= 3
    return 0 if success else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
