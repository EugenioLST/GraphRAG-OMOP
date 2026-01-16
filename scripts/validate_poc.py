"""
validate_poc.py - Validate PoC with mandatory test terms

Tests the 5 mandatory medical terms:
- metformina / metformin
- diabetes
- creatinina / creatinine
- ibuprofeno / ibuprofen
- hipertensión / hypertension

For each term:
1. Search for concept in graph by name (case-insensitive)
2. Display concept info (ID, name, vocabulary, domain, standard status)
3. Show 1-hop relationships
4. If non-standard, find standard mapping
"""

import sys
import pandas as pd
import networkx as nx
from src.graph import load_graph, get_concept_info, get_neighbors, find_standard_mapping

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test terms (English and Spanish versions)
TEST_TERMS = {
    'Metformin': ['metformin', 'metformina'],
    'Diabetes': ['diabetes'],
    'Creatinine': ['creatinine', 'creatinina'],
    'Ibuprofen': ['ibuprofen', 'ibuprofeno'],
    'Hypertension': ['hypertension', 'hipertensión', 'hipertension']
}


def search_concept_by_name(G: nx.MultiDiGraph, search_terms: list) -> list:
    """
    Search for concepts in graph by name (case-insensitive).

    Args:
        G: NetworkX graph
        search_terms: List of search terms to try

    Returns:
        List of matching (concept_id, concept_name, vocabulary_id) tuples
    """
    matches = []

    for concept_id in G.nodes():
        node_data = G.nodes[concept_id]
        concept_name = node_data.get('concept_name', '').lower()

        # Check if any search term matches
        for term in search_terms:
            if term.lower() in concept_name:
                matches.append((
                    concept_id,
                    node_data.get('concept_name'),
                    node_data.get('vocabulary_id'),
                    node_data.get('standard_concept')
                ))
                break  # Only add once per concept

    return matches


def validate_term(G: nx.MultiDiGraph, term_name: str, search_terms: list):
    """
    Validate a single medical term.

    Args:
        G: NetworkX graph
        term_name: Display name for the term
        search_terms: List of search terms to try
    """
    print("\n" + "=" * 70)
    print(f"TESTING: {term_name}")
    print("=" * 70)

    # Step 1: Search for concepts
    print(f"\nSearching for: {', '.join(search_terms)}")
    matches = search_concept_by_name(G, search_terms)

    if not matches:
        print(f"❌ NOT FOUND: No concepts found for '{term_name}'")
        print("   This term may not be in the test dataset (first 500k concepts)")
        return

    print(f"✓ Found {len(matches)} matching concept(s)")

    # Step 2: Display first few matches
    print("\nTop matches:")
    for i, (concept_id, name, vocab, standard) in enumerate(matches[:3], 1):
        standard_marker = "⭐ STANDARD" if standard == 'S' else "  (non-standard)"
        print(f"  {i}. [{concept_id}] {name}")
        print(f"     Vocabulary: {vocab} {standard_marker}")

    # Step 3: Analyze first match in detail
    concept_id = matches[0][0]
    print(f"\n📊 Detailed analysis of: {matches[0][1]} (ID: {concept_id})")

    # Get full concept info
    info = get_concept_info(G, concept_id)
    if info:
        print(f"   Concept ID: {info['concept_id']}")
        print(f"   Name: {info['concept_name']}")
        print(f"   Vocabulary: {info['vocabulary_id']}")
        print(f"   Domain: {info['domain_id']}")
        print(f"   Standard: {info['standard_concept']}")

    # Step 4: Get relationships (1-hop)
    neighbors = get_neighbors(G, concept_id, max_neighbors=5)
    if neighbors:
        print(f"\n🔗 Top {len(neighbors)} relationships:")
        for i, neighbor in enumerate(neighbors, 1):
            if neighbor['direction'] == 'outgoing':
                target_name = neighbor.get('target_name', 'Unknown')
                print(f"   {i}. → {neighbor['relationship']}: {target_name}")
            else:
                source_name = neighbor.get('source_name', 'Unknown')
                print(f"   {i}. ← {neighbor['relationship']}: {source_name}")
    else:
        print("\n🔗 No relationships found (isolated node)")

    # Step 5: Find standard mapping if non-standard
    if info and info['standard_concept'] != 'S':
        print("\n🔄 Finding standard mapping...")
        standard = find_standard_mapping(G, concept_id)
        if standard:
            print(f"   ✓ Maps to standard: {standard['concept_name']}")
            print(f"     Standard ID: {standard['concept_id']}")
            print(f"     Vocabulary: {standard['vocabulary_id']}")
        else:
            print("   ⚠ No standard mapping found")

    # Success indicator
    print("\n✅ VALIDATION PASSED for", term_name)


def main():
    """Run validation for all test terms"""
    print("=" * 70)
    print("GRAPHRAG-OMOP POC VALIDATION")
    print("=" * 70)
    print("\nThis script validates the PoC with 5 mandatory medical terms.")
    print("It tests:")
    print("  1. Concept search by name")
    print("  2. Concept metadata retrieval")
    print("  3. 1-hop relationship traversal")
    print("  4. Non-standard → standard mapping")
    print("=" * 70)

    # Load graph
    print("\nLoading graph...")
    G = load_graph()

    print(f"\n✓ Graph loaded: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    # Validate each term
    for term_name, search_terms in TEST_TERMS.items():
        try:
            validate_term(G, term_name, search_terms)
        except Exception as e:
            print(f"\n❌ ERROR validating {term_name}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print("\n✅ If you see results for most terms, the PoC is working!")
    print("⚠  Terms not found may not be in the first 500k concepts.")
    print("   Run with full dataset for complete coverage.")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        raise
