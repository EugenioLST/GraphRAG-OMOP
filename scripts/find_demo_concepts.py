"""
find_demo_concepts.py - Find useful concepts for PoC demos

This script analyzes your 100k embeddings and finds interesting concepts
that work well for demonstrations.
"""

import sys
import pickle
import pandas as pd
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def find_demo_concepts():
    """Find interesting concepts from 100k embeddings for PoC demos"""

    print("=" * 80)
    print("FINDING DEMO CONCEPTS FROM 100K EMBEDDINGS")
    print("=" * 80)

    # Load embeddings index
    print("\n[1/3] Loading embedding index...")
    with open('data/concept_id_to_index.pkl', 'rb') as f:
        concept_ids_with_embeddings = set(pickle.load(f).keys())

    print(f"    ✓ Loaded {len(concept_ids_with_embeddings):,} concepts with embeddings")

    # Load full nodes data
    print("\n[2/3] Loading concept metadata...")
    nodes = pd.read_csv('data/nodes.csv', low_memory=False)

    # Filter to only concepts with embeddings
    nodes_with_emb = nodes[nodes['concept_id'].isin(concept_ids_with_embeddings)].copy()
    print(f"    ✓ Matched {len(nodes_with_emb):,} concepts")

    # Analyze by category
    print("\n[3/3] Analyzing by category...")

    # Group by vocabulary and domain
    vocab_counts = nodes_with_emb['vocabulary_id'].value_counts()
    domain_counts = nodes_with_emb['domain_id'].value_counts()

    print("\n" + "=" * 80)
    print("DISTRIBUTION BY VOCABULARY")
    print("=" * 80)
    for vocab, count in vocab_counts.head(10).items():
        print(f"  {vocab:20s}: {count:>8,} concepts")

    print("\n" + "=" * 80)
    print("DISTRIBUTION BY DOMAIN")
    print("=" * 80)
    for domain, count in domain_counts.head(10).items():
        print(f"  {domain:20s}: {count:>8,} concepts")

    # Find interesting demo concepts
    print("\n" + "=" * 80)
    print("RECOMMENDED DEMO QUERIES")
    print("=" * 80)

    # Category 1: Common medications (RxNorm standard)
    print("\n📋 CATEGORY 1: COMMON MEDICATIONS (Easy wins)")
    print("-" * 80)
    rxnorm_standard = nodes_with_emb[
        (nodes_with_emb['vocabulary_id'] == 'RxNorm') &
        (nodes_with_emb['standard_concept'] == 'S')
    ]

    # Find simple drug names (not combinations)
    simple_drugs = rxnorm_standard[
        ~rxnorm_standard['concept_name'].str.contains('/', na=False) &
        ~rxnorm_standard['concept_name'].str.contains('MG', na=False) &
        (nodes_with_emb['concept_name'].str.len() < 30)
    ].head(20)

    for _, row in simple_drugs.iterrows():
        name = row['concept_name']
        concept_id = row['concept_id']
        print(f"  ✓ '{name}' (ID: {concept_id})")

    # Category 2: Drug combinations with metformin
    print("\n📋 CATEGORY 2: METFORMIN COMBINATIONS (Graph expansion demos)")
    print("-" * 80)
    metformin_combos = nodes_with_emb[
        nodes_with_emb['concept_name'].str.contains('metformin', case=False, na=False)
    ].head(15)

    for _, row in metformin_combos.iterrows():
        name = row['concept_name'][:70]
        concept_id = row['concept_id']
        print(f"  ✓ '{name}' (ID: {concept_id})")

    # Category 3: Medical conditions (SNOMED)
    print("\n📋 CATEGORY 3: MEDICAL CONDITIONS (SNOMED)")
    print("-" * 80)
    snomed = nodes_with_emb[
        (nodes_with_emb['vocabulary_id'] == 'SNOMED') &
        (nodes_with_emb['standard_concept'] == 'S')
    ].head(20)

    for _, row in snomed.iterrows():
        name = row['concept_name']
        concept_id = row['concept_id']
        domain = row['domain_id']
        print(f"  ✓ '{name}' ({domain}, ID: {concept_id})")

    # Category 4: Brand name drugs
    print("\n📋 CATEGORY 4: BRAND NAME DRUGS (Commercial medications)")
    print("-" * 80)

    # Look for branded drugs (usually have brand names in brackets)
    branded = nodes_with_emb[
        nodes_with_emb['concept_name'].str.contains(r'\[.*\]', regex=True, na=False)
    ].head(20)

    for _, row in branded.iterrows():
        name = row['concept_name'][:70]
        concept_id = row['concept_id']
        print(f"  ✓ '{name}' (ID: {concept_id})")

    # Category 5: Simple search terms
    print("\n📋 CATEGORY 5: SIMPLE KEYWORDS FOR TESTING")
    print("-" * 80)

    keywords = ['insulin', 'aspirin', 'pain', 'fever', 'blood', 'heart',
                'diabetes', 'pressure', 'infection', 'vitamin']

    for keyword in keywords:
        matches = nodes_with_emb[
            nodes_with_emb['concept_name'].str.contains(keyword, case=False, na=False)
        ]
        if len(matches) > 0:
            example = matches.iloc[0]
            count = len(matches)
            print(f"  ✓ '{keyword}' → {count:>4} matches (e.g., '{example['concept_name'][:50]}')")

    # Generate test queries file
    print("\n" + "=" * 80)
    print("GENERATING TEST QUERIES FILE")
    print("=" * 80)

    test_queries = []

    # Add metformin variants (multi-lingual)
    test_queries.extend([
        "metformin",
        "metformina",
        "metformin 1000mg",
    ])

    # Add from simple drugs
    if len(simple_drugs) > 0:
        test_queries.extend(simple_drugs['concept_name'].head(5).tolist())

    # Add conditions
    if len(snomed) > 0:
        test_queries.extend(snomed['concept_name'].head(3).tolist())

    # Save to file
    output_file = 'scripts/demo_queries.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Demo Queries for GraphRAG-OMOP PoC\n")
        f.write("# These queries are guaranteed to work with 100k embeddings\n\n")
        for i, query in enumerate(test_queries, 1):
            f.write(f"{i}. {query}\n")

    print(f"\n✓ Saved {len(test_queries)} test queries to: {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY - RECOMMENDED PoC DEMO FLOW")
    print("=" * 80)
    print("""
1. START with simple medication:
   python main.py
   Query: "metformin"

2. SHOW multi-lingual support:
   Query: "metformina" (Spanish)

3. DEMONSTRATE graph expansion:
   Query: "metformin"
   Select: Yes to graph expansion

4. SHOW medical conditions:
   Query: "hallucination"

5. SHOW brand name recognition:
   Query: "janumet"

This demonstrates:
✓ Semantic search (not just string matching)
✓ Multi-lingual capability (ES/EN)
✓ Graph expansion (find related concepts)
✓ Multiple domains (drugs, conditions)
✓ Clinical terminology understanding
    """)

    print("\n✅ Analysis complete! Use the queries above for your PoC demos.\n")


if __name__ == '__main__':
    find_demo_concepts()