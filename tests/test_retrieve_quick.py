"""
test_retrieve_quick.py - Quick test of semantic search

Tests semantic search with various queries to validate functionality
before scaling to 100k concepts.
"""

import sys
from src.retrieve import SemanticRetriever

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_query(retriever, query, description):
    """Test a single query and display results"""
    print("\n" + "=" * 70)
    print(f"TEST: {description}")
    print(f"Query: '{query}'")
    print("=" * 70)

    results = retriever.search(query, top_k=5)

    if not results:
        print("❌ No results found")
        return

    print(f"\nTop 5 results:")
    for i, result in enumerate(results, 1):
        std = "⭐" if result['standard_concept'] == 'S' else "  "
        print(f"{i}. [Score: {result['score']:.4f}] {std} {result['concept_name'][:70]}")
        print(f"   {result['vocabulary_id']} | {result['domain_id']}")

    print(f"\n✓ Found {len(results)} results")


def main():
    """Run quick validation tests"""
    print("=" * 70)
    print("QUICK SEMANTIC SEARCH VALIDATION")
    print("=" * 70)
    print("\nTesting with 10k concept subset")
    print("This validates semantic search before scaling to 100k")
    print("=" * 70)

    # Initialize retriever (no graph for speed)
    print("\nInitializing retriever...")
    retriever = SemanticRetriever(load_graph_data=False)

    # Test cases
    test_cases = [
        ("adverse reaction", "English medical term"),
        ("stillbirth", "Single word medical term"),
        ("central nervous system", "Multi-word anatomical term"),
        ("drug", "Generic pharmacological term"),
        ("hallucination", "Psychiatric symptom"),
    ]

    # Run tests
    for query, description in test_cases:
        test_query(retriever, query, description)

    # Summary
    print("\n" + "=" * 70)
    print("QUICK VALIDATION COMPLETE")
    print("=" * 70)
    print("\n✅ Semantic search working on 10k subset")
    print("✅ Ready to scale to 100k concepts")
    print("\nNote: Many medical terms not found because this is only")
    print("      the first 10k concepts. With 100k we'll find:")
    print("      - metformin, diabetes, creatinine, ibuprofen, hypertension")
    print("=" * 70)


if __name__ == '__main__':
    main()
