"""
Find a test case with both non-standard and standard concepts in 100k subset
"""

import pandas as pd
import networkx as nx
from src.graph import load_graph

# Load graph
print("Loading graph...")
G = load_graph()

# Load first 100k concepts
print("Loading first 100k concepts...")
nodes_df = pd.read_csv('data/nodes.csv', nrows=100000)

# Get concept IDs in our subset
concept_ids_in_subset = set(nodes_df['concept_id'].tolist())

print(f"Total concepts in subset: {len(concept_ids_in_subset):,}")

# Find non-standard concepts with "Maps to" relationships
print("\nSearching for non-standard → standard mappings in subset...")

found_cases = []

for concept_id in concept_ids_in_subset:
    if concept_id not in G:
        continue

    # Get concept info
    node_data = G.nodes[concept_id]
    standard = node_data.get('standard_concept')

    # Only check non-standard concepts
    if standard == 'S':
        continue

    # Check outgoing edges for "Maps to" relationships
    for neighbor in G.neighbors(concept_id):
        edge_data = G.get_edge_data(concept_id, neighbor)
        if edge_data:
            for edge_key, edge_attrs in edge_data.items():
                relationship = edge_attrs.get('relationship', '')

                # Check if it's a mapping relationship
                if 'map' in relationship.lower() or 'standard' in relationship.lower():
                    # Check if the target is also in our subset
                    if neighbor in concept_ids_in_subset:
                        # Get target info
                        target_data = G.nodes[neighbor]
                        target_standard = target_data.get('standard_concept')

                        if target_standard == 'S':
                            found_cases.append({
                                'source_id': concept_id,
                                'source_name': node_data.get('concept_name'),
                                'source_vocab': node_data.get('vocabulary_id'),
                                'relationship': relationship,
                                'target_id': neighbor,
                                'target_name': target_data.get('concept_name'),
                                'target_vocab': target_data.get('vocabulary_id')
                            })

                            if len(found_cases) >= 10:
                                break

        if len(found_cases) >= 10:
            break

    if len(found_cases) >= 10:
        break

# Display results
print(f"\n{'='*70}")
print(f"FOUND {len(found_cases)} TEST CASES")
print(f"{'='*70}\n")

for i, case in enumerate(found_cases, 1):
    print(f"{i}. Non-standard: {case['source_name']} (ID: {case['source_id']})")
    print(f"   Vocabulary: {case['source_vocab']}")
    print(f"   → {case['relationship']}")
    print(f"   Standard: {case['target_name']} (ID: {case['target_id']})")
    print(f"   Vocabulary: {case['target_vocab']}")
    print()

if found_cases:
    print(f"{'='*70}")
    print("RECOMMENDED TEST CASE:")
    print(f"{'='*70}")
    best = found_cases[0]
    print(f"\nSearch for: \"{best['source_name']}\"")
    print(f"Expected results:")
    print(f"  1. Direct match: {best['source_name']} (non-standard)")
    print(f"  2. Via graph expansion: {best['target_name']} (⭐ standard)")
    print(f"\nTest command:")
    print(f'python src/retrieve.py "{best["source_name"]}" --top-k 5 --expand')
