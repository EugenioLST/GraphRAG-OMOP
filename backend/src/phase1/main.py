"""
Phase 1 Main - Clinical Concept Extraction

Standalone script to test Phase 1: Extract medical concepts from clinical text.

Usage:
    # Interactive mode
    python -m src.phase1.main

    # With text argument
    python -m src.phase1.main "Paciente con diabetes tratado con metformina"

    # From file
    python -m src.phase1.main --file historia_clinica.txt
"""

import sys
import argparse
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from .extractor import extract_medical_entities, visual_json, save_entities


def run_extraction(clinical_text: str, reference_date: str = None, save_output: bool = False) -> dict:
    """
    Run Phase 1 extraction on clinical text.

    Args:
        clinical_text: The clinical text to analyze
        reference_date: Optional reference date (YYYY-MM-DD) for resolving relative temporal expressions
        save_output: Whether to save results to file

    Returns:
        Dictionary with extracted concepts
    """
    print("\n" + "=" * 70)
    print("PHASE 1: Clinical Concept Extraction")
    print("=" * 70)
    print(f"\nInput text ({len(clinical_text)} chars):")
    print("-" * 40)
    print(clinical_text[:500] + ("..." if len(clinical_text) > 500 else ""))
    print("-" * 40)

    print("\nExtracting concepts with GPT-4...")
    result = extract_medical_entities(clinical_text, reference_date=reference_date)

    # Display results
    print("\n" + "=" * 70)
    print("EXTRACTED CONCEPTS")
    print("=" * 70)

    concepts = result.get("concepts", [])
    if not concepts:
        print("\nNo concepts extracted.")
    else:
        print(f"\nFound {len(concepts)} concepts:\n")

        # Group by domain
        by_domain = {}
        for c in concepts:
            domain = c.get("domain", "Unknown")
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(c.get("text", ""))

        for domain, terms in sorted(by_domain.items()):
            print(f"  [{domain}]")
            for term in terms:
                print(f"    - {term}")
            print()

    # Save if requested
    if save_output:
        output_path = "data/output/phase1_extraction.json"
        save_entities(output_path, result)
        print(f"[OK] Results saved to: {output_path}")

    print("=" * 70)
    return result


def interactive_mode():
    """Run Phase 1 in interactive mode."""
    print("\n" + "=" * 70)
    print("PHASE 1: Clinical Concept Extraction (Interactive Mode)")
    print("=" * 70)
    print("\nEnter clinical text to extract concepts.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        print("-" * 40)
        text = input("Clinical text: ").strip()

        if text.lower() in ('quit', 'exit', 'q'):
            print("\nGoodbye!")
            break

        if not text:
            print("Please enter some text.")
            continue

        try:
            run_extraction(text, save_output=False)
        except Exception as e:
            print(f"\n[ERROR] {e}")

        print()


def main():
    """Main entry point for Phase 1."""
    parser = argparse.ArgumentParser(
        description='Phase 1: Extract medical concepts from clinical text',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m src.phase1.main

  # Direct text
  python -m src.phase1.main "Paciente con diabetes e hipertensión"

  # From file
  python -m src.phase1.main --file historia.txt

  # Save output
  python -m src.phase1.main "texto clínico" --save
        """
    )

    parser.add_argument(
        'text',
        nargs='?',
        help='Clinical text to analyze (optional, enters interactive mode if not provided)'
    )

    parser.add_argument(
        '--file', '-f',
        help='Read clinical text from file'
    )

    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Save results to data/output/phase1_extraction.json'
    )

    args = parser.parse_args()

    # Determine input source
    if args.file:
        # Read from file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {args.file}")
            sys.exit(1)
        clinical_text = file_path.read_text(encoding='utf-8')
        run_extraction(clinical_text, save_output=args.save)

    elif args.text:
        # Direct text argument
        run_extraction(args.text, save_output=args.save)

    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()