"""
Phase 2 Main - Semantic Search for OMOP Concepts

Standalone script to test Phase 2: Find standard OMOP concepts from medical terms.

Usage:
    # Interactive mode
    python -m src.phase2.main

    # With term argument
    python -m src.phase2.main "metformina"

    # With options
    python -m src.phase2.main "diabetes" --top-k 5 --expand
"""

import sys
import argparse

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .retrieve import SemanticRetriever


# Global retriever instance (lazy loaded)
_retriever = None


def get_retriever(load_graph: bool = True) -> SemanticRetriever:
    """Get or create the semantic retriever (singleton)."""
    global _retriever
    if _retriever is None:
        print("\nInitializing SemanticRetriever (this may take ~15 seconds)...")
        _retriever = SemanticRetriever(load_graph_data=load_graph)
    return _retriever


def run_search(term: str, top_k: int = 5, expand: bool = False,
               filters: dict = None, retriever: SemanticRetriever = None) -> dict:
    """
    Run Phase 2 search on a medical term.

    Args:
        term: Medical term to search
        top_k: Number of results to return
        expand: Whether to show related concepts via graph
        filters: Optional filters (vocabulary, domain, standard_only)
        retriever: Optional pre-initialized retriever

    Returns:
        Dictionary with search results
    """
    if retriever is None:
        retriever = get_retriever(load_graph=expand)

    print("\n" + "=" * 70)
    print("PHASE 2: Semantic Search")
    print("=" * 70)
    print(f"\nSearching for: '{term}'")

    if expand:
        response = retriever.search_with_expansion(
            query=term,
            top_k=top_k,
            filters=filters,
            expand_top_n=1
        )
        results = response['primary_results']
        expanded = response['expanded_results']
    else:
        results = retriever.search(
            query=term,
            top_k=top_k,
            filters=filters
        )
        expanded = []

    # Display results
    print("\n" + "=" * 70)
    print(f"TOP {len(results)} RESULTS")
    print("=" * 70 + "\n")

    if not results:
        print("No results found.")
        print("Try:")
        print("  - Using different spelling")
        print("  - Removing filters")
        print("  - Using English terms")
    else:
        for i, r in enumerate(results, 1):
            std = " [STANDARD]" if r['standard_concept'] == 'S' else ""
            print(f"{i:2}. [{r['score']:.4f}] {r['concept_name']}{std}")
            print(f"    ID: {r['concept_id']} | {r['vocabulary_id']} | {r['domain_id']}")

    # Display expanded results
    if expanded:
        print("\n" + "-" * 70)
        print("RELATED CONCEPTS (via graph)")
        print("-" * 70 + "\n")

        for i, r in enumerate(expanded[:10], 1):
            print(f"  {i}. [{r['relationship']}] {r['concept_name']}")

    print("\n" + "=" * 70)

    return {
        'query': term,
        'results': results,
        'expanded': expanded
    }


def interactive_mode():
    """Run Phase 2 in interactive mode."""
    print("\n" + "=" * 70)
    print("PHASE 2: Semantic Search (Interactive Mode)")
    print("=" * 70)

    # Initialize retriever once
    retriever = get_retriever(load_graph=True)

    print("\nEnter medical terms to search.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        print("-" * 40)
        term = input("Medical term: ").strip()

        if term.lower() in ('quit', 'exit', 'q'):
            print("\nGoodbye!")
            break

        if not term:
            print("Please enter a term.")
            continue

        try:
            # Ask for options
            expand_input = input("Show related concepts? (y/n, default=n): ").strip().lower()
            expand = expand_input in ('y', 'yes', 's', 'si')

            run_search(term, top_k=5, expand=expand, retriever=retriever)
        except Exception as e:
            print(f"\n[ERROR] {e}")

        print()


def main():
    """Main entry point for Phase 2."""
    parser = argparse.ArgumentParser(
        description='Phase 2: Semantic search for OMOP concepts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m src.phase2.main

  # Direct search
  python -m src.phase2.main "metformina"

  # With options
  python -m src.phase2.main "diabetes" --top-k 10 --expand

  # With filters
  python -m src.phase2.main "aspirina" --domain Drug --standard-only
        """
    )

    parser.add_argument(
        'term',
        nargs='?',
        help='Medical term to search (optional, enters interactive mode if not provided)'
    )

    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=5,
        help='Number of results (default: 5)'
    )

    parser.add_argument(
        '--expand', '-e',
        action='store_true',
        help='Show related concepts via graph'
    )

    parser.add_argument(
        '--vocabulary', '-v',
        help='Filter by vocabulary (SNOMED, RxNorm, LOINC)'
    )

    parser.add_argument(
        '--domain', '-d',
        help='Filter by domain (Drug, Condition, Measurement)'
    )

    parser.add_argument(
        '--standard-only', '-s',
        action='store_true',
        help='Only show standard concepts'
    )

    args = parser.parse_args()

    # Build filters
    filters = {}
    if args.vocabulary:
        filters['vocabulary'] = args.vocabulary
    if args.domain:
        filters['domain'] = args.domain
    if args.standard_only:
        filters['standard_only'] = True

    if args.term:
        # Direct search
        run_search(
            term=args.term,
            top_k=args.top_k,
            expand=args.expand,
            filters=filters or None
        )
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()