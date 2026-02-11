"""
main.py - GraphRAG-OMOP Full Pipeline

Complete pipeline from clinical text to standardized OMOP concepts.

Pipeline: Clinical Text → [Phase 1: Extract] → Concepts → [Phase 2: Search] → OMOP Standards

Usage:
    # Full pipeline (interactive)
    python main.py

    # Full pipeline with text
    python main.py --text "Paciente con diabetes tratado con metformina"

    # Phase 1 only (extraction)
    python main.py --phase1 "Paciente con diabetes tratado con metformina"

    # Phase 2 only (search)
    python main.py --phase2 "metformina"
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def run_phase1(clinical_text: str) -> list:
    """
    Phase 1: Extract medical concepts from clinical text.

    Args:
        clinical_text: Clinical text to analyze

    Returns:
        List of extracted concepts with domains
    """
    from src.phase1.extractor import extract_medical_entities

    print("\n" + "=" * 70)
    print("PHASE 1: Clinical Concept Extraction")
    print("=" * 70)
    print(f"\nInput ({len(clinical_text)} chars):")
    print("-" * 50)
    print(clinical_text[:300] + ("..." if len(clinical_text) > 300 else ""))
    print("-" * 50)

    print("\nExtracting concepts with GPT-4...")
    result = extract_medical_entities(clinical_text)
    concepts = result.get("concepts", [])

    print(f"\nExtracted {len(concepts)} concepts:")
    for c in concepts:
        print(f"  - {c['text']} [{c['domain']}]")

    return concepts


def run_phase2(term: str, domain: str = None, retriever=None) -> list:
    """
    Phase 2: Find OMOP standard concepts for a medical term.

    Args:
        term: Medical term to search
        domain: Optional domain filter
        retriever: Optional pre-initialized retriever

    Returns:
        List of matching OMOP concepts
    """
    if retriever is None:
        from src.phase2.retrieve import SemanticRetriever
        retriever = SemanticRetriever(load_graph_data=False)

    filters = {'domain': domain} if domain else None
    results = retriever.search(term, top_k=3, filters=filters)

    return results


def run_full_pipeline(clinical_text: str, save_output: bool = True) -> dict:
    """
    Full pipeline: Extract concepts, find OMOP standards via graph, and save results.

    Pipeline with full traceability:
    1. Phase 1: Extract concepts from clinical text (LLM)
    2. Phase 2: Find best RAG match for each concept
    3. Graph: Follow relationships to find standard OMOP concept
    4. Save: Output JSON with complete mapping chain

    Args:
        clinical_text: Clinical text to process
        save_output: Whether to save results to file (default: True)

    Returns:
        Dict with complete pipeline results
    """
    from src.phase2.retrieve import SemanticRetriever

    # Phase 1: Extract concepts
    concepts = run_phase1(clinical_text)

    if not concepts:
        print("\nNo concepts extracted. Pipeline complete.")
        return {'mappings': [], 'stats': {'total': 0}}

    # Initialize Phase 2 retriever WITH graph for standard mapping
    print("\n" + "=" * 70)
    print("PHASE 2: Semantic Search + Standard Mapping")
    print("=" * 70)
    print("\nInitializing semantic search with graph...")
    retriever = SemanticRetriever(load_graph_data=True)

    # Phase 2: Search and standardize each concept
    print("\n" + "=" * 70)
    print("RESULTS: Clinical Text → RAG Match → OMOP Standard")
    print("=" * 70)

    mappings = []
    stats = {'total': 0, 'mapped_ok': 0, 'needs_review': 0}

    for concept in concepts:
        term = concept['text']
        domain = concept['domain']
        value = concept.get('value')
        unit = concept.get('unit')
        stats['total'] += 1

        # Display with value/unit if present
        value_str = ""
        if value is not None:
            value_str = f" = {value}"
            if unit:
                value_str += f" {unit}"

        print(f"\n[{domain}] {term}{value_str}")
        print("-" * 50)

        # Use search_and_standardize method (returns flat format)
        result = retriever.search_and_standardize(term, domain=domain)

        # Add value and unit to result (pass-through, not searched)
        result['value'] = value
        result['unit'] = unit

        mappings.append(result)

        # Display result
        if result['match_name']:
            print(f"  MATCH:    [{result['score']:.3f}] {result['match_name']}")
            print(f"            ID: {result['match_id']} | {result['match_vocab']}")

            if result['standard_id']:
                if result['standard_id'] == result['match_id']:
                    print(f"  STANDARD: (same as match)")
                else:
                    print(f"  STANDARD: {result['standard_name']}")
                    print(f"            ID: {result['standard_id']} | {result['standard_vocab']}")
            else:
                print(f"  STANDARD: ⚠ Not found")
        else:
            print("  (No matches found)")

        if result['status'] == 'REVIEW':
            stats['needs_review'] += 1
            print(f"  ⚠ REVIEW: {result['note']}")
        else:
            stats['mapped_ok'] += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total concepts: {stats['total']}")
    print(f"  Mapped OK:      {stats['mapped_ok']}")
    print(f"  Needs review:   {stats['needs_review']}")

    # Build output structure
    output = {
        'timestamp': datetime.now().isoformat(),
        'input_text': clinical_text,
        'stats': stats,
        'mappings': mappings
    }

    # Save to file
    if save_output:
        output_dir = Path('data/output')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'pipeline_result_{timestamp}.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n  Results saved to: {output_file}")

    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    return output


def interactive_mode():
    """Interactive mode - step by step pipeline."""
    print("\n" + "=" * 70)
    print("GraphRAG-OMOP - Full Pipeline (Interactive)")
    print("=" * 70)
    print("\nThis tool extracts medical concepts from clinical text")
    print("and maps them to standardized OMOP vocabulary.\n")

    while True:
        print("-" * 70)
        print("\nOptions:")
        print("  1. Full pipeline (text → extract → search)")
        print("  2. Phase 1 only (extract concepts)")
        print("  3. Phase 2 only (search term)")
        print("  q. Quit")

        choice = input("\nSelect option: ").strip().lower()

        if choice in ('q', 'quit', 'exit'):
            print("\nGoodbye!")
            break

        elif choice == '1':
            print("\nEnter clinical text (or 'back' to return):")
            text = input("> ").strip()
            if text.lower() == 'back':
                continue
            if text:
                run_full_pipeline(text)

        elif choice == '2':
            print("\nEnter clinical text to extract concepts:")
            text = input("> ").strip()
            if text:
                run_phase1(text)

        elif choice == '3':
            print("\nEnter medical term to search:")
            term = input("> ").strip()
            if term:
                from src.phase2.retrieve import SemanticRetriever
                print("\nInitializing search...")
                retriever = SemanticRetriever(load_graph_data=False)
                results = retriever.search(term, top_k=5)

                print(f"\nResults for '{term}':")
                for i, r in enumerate(results, 1):
                    std = " ★" if r['standard_concept'] == 'S' else ""
                    print(f"  {i}. [{r['score']:.3f}] {r['concept_name']}{std}")
                    print(f"     ID: {r['concept_id']} | {r['vocabulary_id']} | {r['domain_id']}")

        else:
            print("Invalid option. Please select 1, 2, 3, or q.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='GraphRAG-OMOP: Clinical Text → OMOP Standards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py

  # Full pipeline
  python main.py --text "Paciente con diabetes e hipertensión"

  # Phase 1 only (extraction)
  python main.py --phase1 "Paciente diabético con metformina"

  # Phase 2 only (search)
  python main.py --phase2 "metformina"

Individual phase scripts:
  python -m src.phase1.main    # Phase 1 standalone
  python -m src.phase2.main    # Phase 2 standalone
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--text', '-t',
        help='Clinical text for full pipeline'
    )
    group.add_argument(
        '--phase1', '-p1',
        metavar='TEXT',
        help='Run Phase 1 only: extract concepts from text'
    )
    group.add_argument(
        '--phase2', '-p2',
        metavar='TERM',
        help='Run Phase 2 only: search OMOP for term'
    )

    args = parser.parse_args()

    # Check dependencies
    try:
        if args.phase1 or args.text:
            # Check Phase 1 dependencies
            from src.phase1.extractor import extract_medical_entities
        if args.phase2 or args.text or (not args.phase1 and not args.phase2):
            # Check Phase 2 dependencies
            embeddings_path = Path('data/embeddings/embeddings.npy')
            if not embeddings_path.exists():
                print("\n[ERROR] Embeddings not found for Phase 2")
                print("Run: python -m src.phase2.embeddings --max-concepts 100000")
                if args.phase2:
                    sys.exit(1)
    except ImportError as e:
        print(f"\n[ERROR] Missing dependency: {e}")
        sys.exit(1)

    # Route to appropriate mode
    try:
        if args.text:
            run_full_pipeline(args.text)
        elif args.phase1:
            run_phase1(args.phase1)
        elif args.phase2:
            from src.phase2.retrieve import SemanticRetriever
            print("\nInitializing semantic search...")
            retriever = SemanticRetriever(load_graph_data=False)
            results = retriever.search(args.phase2, top_k=10)

            print(f"\n{'=' * 70}")
            print(f"PHASE 2: Search results for '{args.phase2}'")
            print('=' * 70)
            for i, r in enumerate(results, 1):
                std = " ★" if r['standard_concept'] == 'S' else ""
                print(f"  {i}. [{r['score']:.3f}] {r['concept_name']}{std}")
                print(f"     ID: {r['concept_id']} | {r['vocabulary_id']} | {r['domain_id']}")
            print('=' * 70)
        else:
            interactive_mode()

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()