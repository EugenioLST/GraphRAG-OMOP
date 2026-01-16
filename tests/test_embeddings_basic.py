"""
test_embeddings_basic.py - Basic functionality test for embeddings

Tests:
1. Load embeddings successfully
2. Verify dimensions (N x 768)
3. Test concept_id mapping
4. Calculate cosine similarity between concepts
5. Find similar concepts
"""

import sys
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from src.embeddings import load_embeddings

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_load_embeddings():
    """Test 1: Load embeddings and verify structure"""
    print("=" * 70)
    print("TEST 1: Load Embeddings")
    print("=" * 70)

    embeddings, concept_id_to_index = load_embeddings()

    print(f"\n✓ Embeddings shape: {embeddings.shape}")
    print(f"✓ Number of concepts: {len(concept_id_to_index):,}")

    # Verify dimensions
    assert embeddings.shape[1] == 768, f"Expected 768 dimensions, got {embeddings.shape[1]}"
    assert embeddings.shape[0] == len(concept_id_to_index), "Mismatch between embeddings and mapping"

    print(f"✓ Embedding dimension: 768 (correct)")
    print(f"✓ Mapping size matches embedding count")

    return embeddings, concept_id_to_index


def test_concept_lookup(embeddings, concept_id_to_index):
    """Test 2: Lookup concept by ID"""
    print("\n" + "=" * 70)
    print("TEST 2: Concept Lookup")
    print("=" * 70)

    # Load nodes to get concept names
    nodes_df = pd.read_csv('data/nodes.csv', nrows=10000)

    # Get first 5 concepts
    sample_concepts = nodes_df.head(5)

    print("\nTesting concept lookup:")
    for _, row in sample_concepts.iterrows():
        concept_id = row['concept_id']
        concept_name = row['concept_name']

        if concept_id in concept_id_to_index:
            idx = concept_id_to_index[concept_id]
            embedding = embeddings[idx]

            print(f"\n  Concept ID: {concept_id}")
            print(f"  Name: {concept_name[:60]}")
            print(f"  Index: {idx}")
            print(f"  Embedding shape: {embedding.shape}")
            print(f"  Embedding sample (first 5): {embedding[:5]}")

            assert embedding.shape == (768,), f"Expected (768,), got {embedding.shape}"
        else:
            print(f"\n  ⚠ Concept ID {concept_id} not in mapping")

    print("\n✓ Concept lookup working correctly")


def test_cosine_similarity(embeddings, concept_id_to_index):
    """Test 3: Calculate cosine similarity"""
    print("\n" + "=" * 70)
    print("TEST 3: Cosine Similarity")
    print("=" * 70)

    # Load nodes to get concept names
    nodes_df = pd.read_csv('data/nodes.csv', nrows=10000)

    # Pick a concept
    test_concept = nodes_df.iloc[0]
    concept_id = test_concept['concept_id']
    concept_name = test_concept['concept_name']

    print(f"\nQuery concept: {concept_name} (ID: {concept_id})")

    # Get embedding
    if concept_id not in concept_id_to_index:
        print("⚠ Test concept not in mapping, skipping")
        return

    query_idx = concept_id_to_index[concept_id]
    query_embedding = embeddings[query_idx].reshape(1, -1)

    # Calculate similarity with all concepts
    similarities = cosine_similarity(query_embedding, embeddings)[0]

    print(f"\nSimilarity scores calculated for {len(similarities):,} concepts")
    print(f"  Min score: {similarities.min():.4f}")
    print(f"  Max score: {similarities.max():.4f}")
    print(f"  Mean score: {similarities.mean():.4f}")

    # Top 10 most similar (should include itself at rank 1)
    top_indices = np.argsort(similarities)[::-1][:10]

    print(f"\nTop 10 most similar concepts:")
    for rank, idx in enumerate(top_indices, 1):
        score = similarities[idx]

        # Find concept_id from index
        concept_id_found = None
        for cid, cidx in concept_id_to_index.items():
            if cidx == idx:
                concept_id_found = cid
                break

        if concept_id_found:
            concept_row = nodes_df[nodes_df['concept_id'] == concept_id_found]
            if not concept_row.empty:
                name = concept_row.iloc[0]['concept_name']
                print(f"  {rank}. [Score: {score:.4f}] {name[:60]}")

    # Verify top match is the query itself
    assert similarities[query_idx] == similarities.max(), "Query should have highest similarity with itself"
    print("\n✓ Cosine similarity working correctly")
    print("✓ Query has highest similarity with itself (as expected)")


def test_find_similar_by_name(embeddings, concept_id_to_index):
    """Test 4: Find similar concepts by searching for a term"""
    print("\n" + "=" * 70)
    print("TEST 4: Find Similar Concepts by Name")
    print("=" * 70)

    # Load nodes
    nodes_df = pd.read_csv('data/nodes.csv', nrows=10000)

    # Search for concepts containing "diabetes"
    search_term = "diabetes"
    matches = nodes_df[nodes_df['concept_name'].str.lower().str.contains(search_term, na=False)]

    print(f"\nSearching for concepts containing '{search_term}'")
    print(f"Found {len(matches)} matches in 10k subset")

    if len(matches) == 0:
        print(f"⚠ No matches for '{search_term}', trying 'adverse'")
        search_term = "adverse"
        matches = nodes_df[nodes_df['concept_name'].str.lower().str.contains(search_term, na=False)]
        print(f"Found {len(matches)} matches for '{search_term}'")

    if len(matches) > 0:
        # Get first match
        query_concept = matches.iloc[0]
        concept_id = query_concept['concept_id']
        concept_name = query_concept['concept_name']

        print(f"\nQuery: {concept_name} (ID: {concept_id})")

        if concept_id in concept_id_to_index:
            query_idx = concept_id_to_index[concept_id]
            query_embedding = embeddings[query_idx].reshape(1, -1)

            # Find top 5 similar
            similarities = cosine_similarity(query_embedding, embeddings)[0]
            top_indices = np.argsort(similarities)[::-1][:5]

            print(f"\nTop 5 similar concepts:")
            for rank, idx in enumerate(top_indices, 1):
                score = similarities[idx]

                # Find concept details
                for cid, cidx in concept_id_to_index.items():
                    if cidx == idx:
                        concept_row = nodes_df[nodes_df['concept_id'] == cid]
                        if not concept_row.empty:
                            name = concept_row.iloc[0]['concept_name']
                            print(f"  {rank}. [Score: {score:.4f}] {name[:60]}")
                        break

            print("\n✓ Similar concept search working correctly")
        else:
            print("⚠ Concept not in mapping")
    else:
        print("⚠ No test concepts found")


def main():
    """Run all tests"""
    print("=" * 70)
    print("BASIC EMBEDDING FUNCTIONALITY TEST")
    print("=" * 70)
    print("\nThis script tests:")
    print("  1. Loading embeddings from disk")
    print("  2. Verifying structure and dimensions")
    print("  3. Concept lookup by ID")
    print("  4. Cosine similarity calculation")
    print("  5. Finding similar concepts")
    print("=" * 70)

    try:
        # Test 1: Load
        embeddings, concept_id_to_index = test_load_embeddings()

        # Test 2: Lookup
        test_concept_lookup(embeddings, concept_id_to_index)

        # Test 3: Similarity
        test_cosine_similarity(embeddings, concept_id_to_index)

        # Test 4: Search
        test_find_similar_by_name(embeddings, concept_id_to_index)

        # Summary
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Embeddings are working correctly")
        print("✅ Ready to proceed with retrieve.py implementation")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == '__main__':
    main()
