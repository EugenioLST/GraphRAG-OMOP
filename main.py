"""
main.py - CLI Interface for GraphRAG-OMOP Semantic Search

User-friendly command-line tool for searching OMOP concepts using semantic search.

Usage:
    python main.py "metformina"
    python main.py "diabetes" --vocabulary SNOMED --standard-only
    python main.py "creatinine" --top-k 20
    python main.py --batch queries.csv --output results.csv
"""

import sys
import os
import argparse
import csv
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.retrieve import SemanticRetriever

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='GraphRAG-OMOP Semantic Search - Find medical concepts using natural language',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                            (interactive mode)
  python main.py "metformina"
  python main.py "diabetes" --vocabulary SNOMED --standard-only
  python main.py "creatinine" --top-k 20 --verbose
  python main.py --batch queries.csv --output results.csv

For more information, see context/PHASE2_PLAN.md
        """
    )

    # Query input (mutually exclusive with --batch)
    query_group = parser.add_mutually_exclusive_group(required=False)
    query_group.add_argument(
        'query',
        nargs='?',
        type=str,
        help='Medical term to search (e.g., "metformina", "diabetes")'
    )
    query_group.add_argument(
        '--batch',
        type=str,
        metavar='FILE',
        help='CSV file with queries (must have "query" column)'
    )

    # Search options
    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        metavar='N',
        help='Number of results to return (default: 10)'
    )
    parser.add_argument(
        '--vocabulary',
        type=str,
        metavar='VOCAB',
        help='Filter by vocabulary (e.g., SNOMED, RxNorm, LOINC)'
    )
    parser.add_argument(
        '--domain',
        type=str,
        metavar='DOMAIN',
        help='Filter by domain (e.g., Drug, Condition, Measurement)'
    )
    parser.add_argument(
        '--standard-only',
        action='store_true',
        help='Only return standard concepts'
    )
    parser.add_argument(
        '--min-score',
        type=float,
        metavar='SCORE',
        help='Minimum similarity score (0.0 to 1.0)'
    )

    # Output options
    parser.add_argument(
        '--expand',
        action='store_true',
        help='Show related concepts via graph expansion'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information'
    )
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Output CSV file (for batch mode)'
    )
    parser.add_argument(
        '--no-graph',
        action='store_true',
        help='Skip loading graph data (faster startup)'
    )

    return parser.parse_args()


def format_result(rank, result, verbose=False):
    """Format a single search result for display"""
    # Standard concept indicator
    std_indicator = "⭐" if result['standard_concept'] == 'S' else "  "

    # Main result line
    lines = [
        f"{rank:2d}. [Score: {result['score']:.4f}] {std_indicator} {result['concept_name']}"
    ]

    # Metadata line
    metadata_parts = [
        f"ID: {result['concept_id']}",
        f"Vocab: {result['vocabulary_id']}",
        f"Domain: {result['domain_id']}"
    ]

    if result['standard_concept'] == 'S':
        metadata_parts.append("Standard: Yes")

    lines.append(f"    {' | '.join(metadata_parts)}")

    # Verbose mode: show additional details
    if verbose:
        if 'concept_class_id' in result:
            lines.append(f"    Class: {result['concept_class_id']}")

    return '\n'.join(lines)


def print_results(query, results, expand=False, verbose=False, retriever=None):
    """Pretty print search results"""
    print("\n" + "=" * 80)
    print(f"Query: \"{query}\"")
    print("=" * 80)

    if not results:
        print("\n❌ No results found")
        print("\nSuggestions:")
        print("  - Try a more general term")
        print("  - Check spelling")
        print("  - Remove filters (--vocabulary, --domain, --standard-only)")
        print("=" * 80)
        return

    print(f"\nFound {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(format_result(i, result, verbose))
        print()

    # Graph expansion
    if expand and retriever and results:
        print("=" * 80)
        print("Related Concepts (via graph expansion):")
        print("=" * 80)

        # Get related concepts for top result
        top_concept_id = results[0]['concept_id']
        related = retriever.expand_graph(top_concept_id, depth=1)

        if related:
            print(f"\nConcepts related to: {results[0]['concept_name']}\n")
            for rel in related[:10]:  # Show top 10 related
                rel_type = rel.get('relationship', 'Related to')
                print(f"  → {rel_type}")
                print(f"    {rel['concept_name']}")
                print(f"    {rel['vocabulary_id']} | {rel['domain_id']}")
                print()
        else:
            print("\n(No related concepts found)")

    print("=" * 80)


def get_yes_no_input(prompt, default='n'):
    """Get yes/no input from user"""
    while True:
        response = input(prompt).strip().lower()
        if not response:
            return default == 'y'
        if response in ['y', 'yes', 's', 'si', 'sí']:
            return True
        if response in ['n', 'no']:
            return False
        print("   Please answer y/n")


def get_number_input(prompt, default, min_val=1, max_val=100):
    """Get number input from user"""
    while True:
        response = input(prompt).strip()
        if not response:
            return default
        try:
            value = int(response)
            if min_val <= value <= max_val:
                return value
            print(f"   Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print("   Please enter a valid number")


def interactive_mode(retriever):
    """Interactive mode - ask user for search parameters"""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)

    while True:
        print("\n🔍 Enter medical concept to search (or 'quit' to exit):")
        query = input("   > ").strip()

        if not query or query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        # Ask for number of results
        print("\n📊 How many results do you want? (default: 10)")
        top_k = get_number_input("   > ", 10, 1, 100)

        # Ask for graph expansion
        print("\n🔗 Show related concepts via graph expansion? (y/n, default: n)")
        expand = get_yes_no_input("   > ", 'n')

        # Build filters (optional)
        filters = {}

        # Search and display
        print(f"\n🔍 Searching for: \"{query}\"...")

        results = retriever.search(
            query,
            top_k=top_k,
            filters=filters if filters else None
        )

        # Display results
        print_results(
            query,
            results,
            expand=expand,
            verbose=False,
            retriever=retriever if expand else None
        )

        # Ask if user wants another search
        print("\n❓ Search another concept? (y/n, default: y)")
        if not get_yes_no_input("   > ", 'y'):
            print("\n👋 Goodbye!")
            break


def single_query_mode(args, retriever):
    """Handle single query mode"""
    # Build filters
    filters = {}
    if args.vocabulary:
        filters['vocabulary'] = args.vocabulary
    if args.domain:
        filters['domain'] = args.domain
    if args.standard_only:
        filters['standard_only'] = True
    if args.min_score:
        filters['min_score'] = args.min_score

    # Search
    print(f"\n🔍 Searching for: \"{args.query}\"")
    if filters:
        print(f"   Filters: {filters}")

    results = retriever.search(
        args.query,
        top_k=args.top_k,
        filters=filters if filters else None
    )

    # Display results
    print_results(
        args.query,
        results,
        expand=args.expand,
        verbose=args.verbose,
        retriever=retriever if args.expand else None
    )


def batch_query_mode(args, retriever):
    """Handle batch query mode"""
    # Check input file exists
    if not Path(args.batch).exists():
        print(f"\n❌ ERROR: File not found: {args.batch}")
        sys.exit(1)

    # Read queries from CSV
    print(f"\n📂 Reading queries from: {args.batch}")

    try:
        with open(args.batch, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            queries = list(reader)

            if 'query' not in queries[0]:
                print("\n❌ ERROR: CSV must have a 'query' column")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR reading file: {e}")
        sys.exit(1)

    print(f"   Found {len(queries)} queries")

    # Build filters
    filters = {}
    if args.vocabulary:
        filters['vocabulary'] = args.vocabulary
    if args.domain:
        filters['domain'] = args.domain
    if args.standard_only:
        filters['standard_only'] = True
    if args.min_score:
        filters['min_score'] = args.min_score

    # Process queries
    all_results = []

    print("\n🔍 Processing queries...")
    for i, row in enumerate(queries, 1):
        query = row['query'].strip()
        if not query:
            continue

        print(f"   [{i}/{len(queries)}] {query}")

        results = retriever.search(
            query,
            top_k=args.top_k,
            filters=filters if filters else None
        )

        # Store results
        for rank, result in enumerate(results, 1):
            all_results.append({
                'query': query,
                'rank': rank,
                'concept_id': result['concept_id'],
                'concept_name': result['concept_name'],
                'score': result['score'],
                'vocabulary_id': result['vocabulary_id'],
                'domain_id': result['domain_id'],
                'standard_concept': result['standard_concept']
            })

    # Write output CSV
    if args.output:
        output_path = args.output
    else:
        # Default output filename
        input_stem = Path(args.batch).stem
        output_path = f"{input_stem}_results.csv"

    print(f"\n💾 Writing results to: {output_path}")

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        if all_results:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)

    print(f"✅ Processed {len(queries)} queries, found {len(all_results)} results")
    print("=" * 80)


def main():
    """Main CLI entry point"""
    args = parse_arguments()

    # Check if embeddings exist
    embeddings_path = Path('data/embeddings.npy')
    if not embeddings_path.exists():
        print("\n" + "=" * 80)
        print("❌ ERROR: Embeddings not found")
        print("=" * 80)
        print("\nPlease generate embeddings first:")
        print("  python src/embeddings.py --max-concepts 100000")
        print("\nThis will take ~10-15 minutes on CPU.")
        print("=" * 80)
        sys.exit(1)

    # Initialize retriever
    print("\n" + "=" * 80)
    print("GraphRAG-OMOP Semantic Search")
    print("=" * 80)
    print("\n📊 Initializing retriever...")
    print("   (Loading embeddings and model, this may take ~15 seconds)")

    try:
        retriever = SemanticRetriever(load_graph_data=not args.no_graph)
        print("✅ Retriever initialized successfully\n")
    except Exception as e:
        print(f"\n❌ ERROR initializing retriever: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Route to appropriate mode
    try:
        if args.batch:
            batch_query_mode(args, retriever)
        elif args.query:
            single_query_mode(args, retriever)
        else:
            # No query provided - enter interactive mode
            interactive_mode(retriever)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
