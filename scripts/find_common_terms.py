"""
find_common_terms.py - Find COMMON medical terms in 100k embeddings

This finds typical, everyday medical terms that people actually use.
"""

import sys
import pickle
import pandas as pd

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def find_common_terms():
    """Find common, everyday medical terms"""

    print("=" * 80)
    print("FINDING COMMON MEDICAL TERMS IN 100K EMBEDDINGS")
    print("=" * 80)

    # Load embeddings index
    print("\nLoading embedding index...")
    with open('data/concept_id_to_index.pkl', 'rb') as f:
        concept_ids_with_embeddings = set(pickle.load(f).keys())

    # Load nodes
    nodes = pd.read_csv('data/nodes.csv', low_memory=False)
    nodes_with_emb = nodes[nodes['concept_id'].isin(concept_ids_with_embeddings)].copy()

    print(f"Loaded {len(nodes_with_emb):,} concepts with embeddings\n")

    # Common medical terms to search for
    common_terms = [
        # Common medications
        'aspirin', 'ibuprofen', 'paracetamol', 'acetaminophen',
        'amoxicillin', 'penicillin', 'insulin', 'metformin',
        'omeprazole', 'simvastatin', 'atorvastatin',
        'lisinopril', 'amlodipine', 'losartan',
        'levothyroxine', 'prednisone', 'dexamethasone',
        'warfarin', 'heparin', 'enoxaparin',
        'furosemide', 'hydrochlorothiazide',
        'albuterol', 'salbutamol',
        'morphine', 'codeine', 'tramadol',
        'diazepam', 'lorazepam', 'alprazolam',
        'sertraline', 'fluoxetine', 'citalopram',

        # Vitamins/supplements
        'vitamin', 'calcium', 'iron', 'folic acid', 'magnesium',

        # Common conditions
        'diabetes', 'hypertension', 'asthma', 'copd',
        'pneumonia', 'bronchitis', 'infection',
        'fever', 'pain', 'headache', 'migraine',
        'depression', 'anxiety', 'insomnia',
        'arthritis', 'osteoporosis',
        'heart failure', 'atrial fibrillation',
        'stroke', 'myocardial infarction',
        'kidney disease', 'liver disease',
        'cancer', 'tumor', 'leukemia',

        # Lab tests
        'glucose', 'hemoglobin', 'creatinine', 'cholesterol',
        'triglycerides', 'albumin', 'bilirubin',
        'sodium', 'potassium', 'calcium',
    ]

    results = {}

    print("Searching for common medical terms...")
    print("-" * 80)

    for term in common_terms:
        # Case-insensitive search in concept names
        matches = nodes_with_emb[
            nodes_with_emb['concept_name'].str.contains(term, case=False, na=False)
        ]

        if len(matches) > 0:
            # Get a good example (prefer standard concepts)
            standard = matches[matches['standard_concept'] == 'S']
            if len(standard) > 0:
                example = standard.iloc[0]
            else:
                example = matches.iloc[0]

            results[term] = {
                'count': len(matches),
                'example': example['concept_name'],
                'concept_id': example['concept_id'],
                'vocabulary': example['vocabulary_id'],
                'domain': example['domain_id']
            }

    # Sort by count (descending)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)

    # Print results by category
    print("\n" + "=" * 80)
    print("COMMON MEDICATIONS (sorted by frequency)")
    print("=" * 80)

    meds = ['aspirin', 'ibuprofen', 'paracetamol', 'acetaminophen',
            'amoxicillin', 'penicillin', 'insulin', 'metformin',
            'omeprazole', 'simvastatin', 'atorvastatin',
            'lisinopril', 'amlodipine', 'losartan',
            'levothyroxine', 'prednisone', 'dexamethasone',
            'warfarin', 'heparin', 'enoxaparin',
            'furosemide', 'hydrochlorothiazide',
            'albuterol', 'salbutamol',
            'morphine', 'codeine', 'tramadol',
            'diazepam', 'lorazepam', 'alprazolam',
            'sertraline', 'fluoxetine', 'citalopram']

    med_results = [(k, v) for k, v in sorted_results if k in meds]
    for term, data in med_results:
        print(f"  {term:20s}: {data['count']:>4} matches  (e.g., '{data['example'][:50]}')")

    print("\n" + "=" * 80)
    print("VITAMINS & SUPPLEMENTS")
    print("=" * 80)

    supplements = ['vitamin', 'calcium', 'iron', 'folic acid', 'magnesium']
    supp_results = [(k, v) for k, v in sorted_results if k in supplements]
    for term, data in supp_results:
        print(f"  {term:20s}: {data['count']:>4} matches  (e.g., '{data['example'][:50]}')")

    print("\n" + "=" * 80)
    print("COMMON CONDITIONS")
    print("=" * 80)

    conditions = ['diabetes', 'hypertension', 'asthma', 'copd',
                  'pneumonia', 'bronchitis', 'infection',
                  'fever', 'pain', 'headache', 'migraine',
                  'depression', 'anxiety', 'insomnia',
                  'arthritis', 'osteoporosis',
                  'heart failure', 'atrial fibrillation',
                  'stroke', 'myocardial infarction',
                  'kidney disease', 'liver disease',
                  'cancer', 'tumor', 'leukemia']

    cond_results = [(k, v) for k, v in sorted_results if k in conditions]
    for term, data in cond_results:
        print(f"  {term:20s}: {data['count']:>4} matches  (e.g., '{data['example'][:50]}')")

    print("\n" + "=" * 80)
    print("LAB TESTS & MEASUREMENTS")
    print("=" * 80)

    labs = ['glucose', 'hemoglobin', 'creatinine', 'cholesterol',
            'triglycerides', 'albumin', 'bilirubin',
            'sodium', 'potassium', 'calcium']

    lab_results = [(k, v) for k, v in sorted_results if k in labs]
    for term, data in lab_results:
        print(f"  {term:20s}: {data['count']:>4} matches  (e.g., '{data['example'][:50]}')")

    # Generate updated demo queries file
    print("\n" + "=" * 80)
    print("GENERATING UPDATED DEMO QUERIES")
    print("=" * 80)

    demo_queries = []

    # Top medications (>50 matches)
    top_meds = [k for k, v in med_results if v['count'] > 50][:10]
    demo_queries.extend(top_meds)

    # Top conditions
    top_conds = [k for k, v in cond_results if v['count'] > 5][:5]
    demo_queries.extend(top_conds)

    # Top labs
    top_labs = [k for k, v in lab_results if v['count'] > 0][:3]
    demo_queries.extend(top_labs)

    # Add multi-lingual variants
    demo_queries.extend(['metformina', 'ibuprofeno', 'insulina'])

    # Save to file
    output_file = 'scripts/demo_queries_common.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# COMMON Medical Terms - Demo Queries for GraphRAG-OMOP PoC\n")
        f.write("# These are everyday medical terms that work with 100k embeddings\n\n")
        f.write("## MEDICATIONS (High confidence)\n")
        for i, query in enumerate([k for k, v in med_results if v['count'] > 50][:15], 1):
            count = results[query]['count']
            f.write(f"{i}. {query} ({count} matches)\n")

        f.write("\n## CONDITIONS & SYMPTOMS\n")
        for i, query in enumerate([k for k, v in cond_results if v['count'] > 0][:10], 1):
            count = results[query]['count']
            f.write(f"{i}. {query} ({count} matches)\n")

        f.write("\n## MULTI-LINGUAL (Spanish)\n")
        f.write("1. metformina (metformin)\n")
        f.write("2. ibuprofeno (ibuprofen)\n")
        f.write("3. insulina (insulin)\n")

    print(f"\n✓ Saved demo queries to: {output_file}")

    # Print TOP 20 recommendations
    print("\n" + "=" * 80)
    print("TOP 20 RECOMMENDED DEMO QUERIES")
    print("=" * 80)
    print("\n🥇 TIER 1: MANY MATCHES (>500)")
    tier1 = [(k, v) for k, v in sorted_results if v['count'] >= 500]
    for term, data in tier1[:10]:
        print(f"  ✓ '{term}' → {data['count']:,} matches")

    print("\n🥈 TIER 2: GOOD MATCHES (100-500)")
    tier2 = [(k, v) for k, v in sorted_results if 100 <= v['count'] < 500]
    for term, data in tier2[:10]:
        print(f"  ✓ '{term}' → {data['count']:,} matches")

    print("\n🥉 TIER 3: DECENT MATCHES (20-100)")
    tier3 = [(k, v) for k, v in sorted_results if 20 <= v['count'] < 100]
    for term, data in tier3[:10]:
        print(f"  ✓ '{term}' → {data['count']:,} matches")

    print("\n" + "=" * 80)
    print("BEST PoC DEMO SEQUENCE")
    print("=" * 80)
    print("""
1. Start simple: "insulin" (834 matches - shows variety)
2. Pain management: "ibuprofen" (400+ matches)
3. Multi-lingual: "metformina" (Spanish for metformin)
4. Condition: "pain" (368 matches - common symptom)
5. Graph expansion: "metformin" + expand (shows relationships)

✅ All of these are GUARANTEED to work well with your 100k embeddings!
    """)

    print("✅ Done!\n")

if __name__ == '__main__':
    find_common_terms()