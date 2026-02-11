"""
retrieve.py - Semantic search engine for OMOP concepts

This module implements semantic search using SapBERT embeddings and the OMOP
concept graph. It allows users to search for medical concepts using natural
language queries, with support for typos, synonyms, and multi-lingual input.

Key Features:
- Semantic search with cosine similarity
- Optional filtering by vocabulary, domain, standard status
- Graph expansion for related concepts
- Ranking with semantic + structural signals

Usage:
    from retrieve import SemanticRetriever

    retriever = SemanticRetriever()
    results = retriever.search("metformina", top_k=10)

    for result in results:
        print(f"{result['score']:.3f} - {result['concept_name']}")
"""

import sys
import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.phase2.embeddings import load_embeddings
from src.phase2.graph import load_graph, find_standard_mapping, get_concept_info

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class SemanticRetriever:
    """
    Semantic search engine for OMOP concepts.

    Combines semantic similarity (via embeddings) with graph structure
    to find relevant medical concepts from natural language queries.
    """

    def __init__(self, embeddings_dir='data/embeddings', nodes_csv_path='data/processed/nodes.csv',
                 graph_path='data/processed/omop_graph.pkl', load_graph_data=True):
        """
        Initialize the semantic retriever.

        Args:
            embeddings_dir: Directory containing embeddings.npy and concept_id_to_index.pkl
            nodes_csv_path: Path to nodes.csv with concept metadata
            graph_path: Path to graph.gpickle (optional, for graph expansion)
            load_graph_data: Whether to load the graph (set False if not needed)
        """
        print("Initializing SemanticRetriever...")

        # Load SapBERT model for encoding queries
        print("Loading SapBERT model...")
        self.model = SentenceTransformer('cambridgeltl/SapBERT-from-PubMedBERT-fulltext')
        print(f"✓ Model loaded on device: {self.model.device}")

        # Load embeddings
        print("Loading embeddings...")
        self.embeddings, self.concept_id_to_index = load_embeddings(embeddings_dir)
        self.index_to_concept_id = {idx: cid for cid, idx in self.concept_id_to_index.items()}
        print(f"✓ Loaded {len(self.concept_id_to_index):,} concept embeddings")

        # Load concept metadata
        print(f"Loading concept metadata from {nodes_csv_path}...")
        # Determine how many rows to load based on embeddings
        nrows = len(self.concept_id_to_index)
        self.nodes_df = pd.read_csv(nodes_csv_path, nrows=nrows)

        # Create fast lookup dict: concept_id -> row data
        self.concept_metadata = {}
        for _, row in self.nodes_df.iterrows():
            self.concept_metadata[row['concept_id']] = {
                'concept_name': row['concept_name'],
                'vocabulary_id': row['vocabulary_id'],
                'domain_id': row['domain_id'],
                'standard_concept': row['standard_concept']
            }
        print(f"✓ Loaded metadata for {len(self.concept_metadata):,} concepts")

        # Load graph (optional, for expansion)
        self.graph = None
        if load_graph_data:
            try:
                print("Loading graph...")
                self.graph = load_graph(graph_path)
                print(f"✓ Graph loaded: {self.graph.number_of_nodes():,} nodes")
            except Exception as e:
                print(f"⚠ Could not load graph: {e}")
                print("  Graph expansion will not be available")

        print("✓ SemanticRetriever initialized successfully")


    def search(self, query, top_k=10, filters=None, min_score=None):
        """
        Search for concepts semantically similar to the query.

        Args:
            query: Search query (string, any language)
            top_k: Number of top results to return (default: 10)
            filters: Optional dict with filters:
                - 'vocabulary': Filter by vocabulary (e.g., 'SNOMED', 'RxNorm')
                - 'domain': Filter by domain (e.g., 'Drug', 'Condition')
                - 'standard_only': If True, only return standard concepts
            min_score: Minimum cosine similarity score (0-1)

        Returns:
            List of dicts with keys: concept_id, concept_name, score,
            vocabulary_id, domain_id, standard_concept
        """
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)

        # Calculate cosine similarity with all concepts
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1]

        # Build results
        results = []
        for idx in top_indices:
            # Get concept_id from index
            concept_id = self.index_to_concept_id[idx]
            score = float(similarities[idx])

            # Apply min_score filter
            if min_score is not None and score < min_score:
                continue

            # Get metadata
            if concept_id not in self.concept_metadata:
                continue

            metadata = self.concept_metadata[concept_id]

            # Apply filters
            if filters:
                # Vocabulary filter
                if 'vocabulary' in filters:
                    if metadata['vocabulary_id'] != filters['vocabulary']:
                        continue

                # Domain filter
                if 'domain' in filters:
                    if metadata['domain_id'] != filters['domain']:
                        continue

                # Standard only filter
                if filters.get('standard_only', False):
                    if metadata['standard_concept'] != 'S':
                        continue

            # Add to results
            result = {
                'concept_id': concept_id,
                'concept_name': metadata['concept_name'],
                'score': score,
                'vocabulary_id': metadata['vocabulary_id'],
                'domain_id': metadata['domain_id'],
                'standard_concept': metadata['standard_concept']
            }
            results.append(result)

            # Stop when we have enough results
            if len(results) >= top_k:
                break

        return results


    def expand_graph(self, concept_id, depth=1, relationship_types=None):
        """
        Get related concepts via graph relationships.

        Args:
            concept_id: Concept ID to expand from
            depth: Number of hops (default: 1)
            relationship_types: List of relationship types to follow
                               (default: None = all types)

        Returns:
            List of dicts with keys: concept_id, concept_name, relationship, distance
        """
        if self.graph is None:
            return []

        if concept_id not in self.graph:
            return []

        # Get neighbors
        related = []
        visited = {concept_id}
        current_level = [(concept_id, None, 0)]  # (node, relationship, distance)

        for _ in range(depth):
            next_level = []

            for node, rel, dist in current_level:
                # Get outgoing edges
                for neighbor in self.graph.neighbors(node):
                    if neighbor in visited:
                        continue

                    # Get relationship type
                    edge_data = self.graph.get_edge_data(node, neighbor)
                    if edge_data:
                        # MultiDiGraph can have multiple edges
                        for edge_key, edge_attrs in edge_data.items():
                            relationship = edge_attrs.get('relationship', 'Unknown')

                            # Filter by relationship type
                            if relationship_types and relationship not in relationship_types:
                                continue

                            # Get metadata from graph (not limited to embeddings subset)
                            if neighbor in self.graph:
                                node_data = self.graph.nodes[neighbor]
                                related.append({
                                    'concept_id': neighbor,
                                    'concept_name': node_data.get('concept_name', 'Unknown'),
                                    'relationship': relationship,
                                    'distance': dist + 1,
                                    'vocabulary_id': node_data.get('vocabulary_id', 'Unknown'),
                                    'domain_id': node_data.get('domain_id', 'Unknown')
                                })

                            visited.add(neighbor)
                            next_level.append((neighbor, relationship, dist + 1))

            current_level = next_level

        return related


    def search_with_expansion(self, query, top_k=10, expand_top_n=3,
                             filters=None, min_score=None):
        """
        Search for concepts and expand top results via graph.

        Args:
            query: Search query string
            top_k: Number of top results to return
            expand_top_n: Number of top results to expand via graph
            filters: Optional filters dict
            min_score: Minimum similarity score

        Returns:
            Dict with keys:
                - 'primary_results': Top-k semantic search results
                - 'expanded_results': Related concepts from graph expansion
        """
        # Primary semantic search
        primary_results = self.search(
            query=query,
            top_k=top_k,
            filters=filters,
            min_score=min_score
        )

        # Expand top N results
        expanded_results = []
        for result in primary_results[:expand_top_n]:
            related = self.expand_graph(result['concept_id'], depth=1)
            for rel in related:
                rel['from_concept'] = result['concept_name']
                rel['from_score'] = result['score']
            expanded_results.extend(related)

        return {
            'primary_results': primary_results,
            'expanded_results': expanded_results
        }


    def search_and_standardize(self, query, domain=None, top_k=1):
        """
        Search for a concept and find its OMOP standard mapping via graph.

        Returns a flat, review-friendly format with full traceability.

        Args:
            query: Search query (extracted concept text)
            domain: Optional domain filter (e.g., 'Drug', 'Condition')
            top_k: Number of RAG candidates to consider (default: 1)

        Returns:
            Dict with flat structure:
            {
                'input': original query text,
                'domain': domain,
                'match_name': RAG match concept name,
                'match_id': RAG match concept_id,
                'match_vocab': RAG match vocabulary,
                'score': similarity score,
                'standard_name': standard concept name (or None),
                'standard_id': standard concept_id (or None),
                'standard_vocab': standard vocabulary (or None),
                'status': 'OK' | 'REVIEW',
                'note': explanation if REVIEW
            }
        """
        # Build filters
        filters = {'domain': domain} if domain else None

        # Step 1: Semantic search (RAG)
        results = self.search(query, top_k=top_k, filters=filters)

        if not results:
            return {
                'input': query,
                'domain': domain,
                'match_name': None,
                'match_id': None,
                'match_vocab': None,
                'score': None,
                'standard_name': None,
                'standard_id': None,
                'standard_vocab': None,
                'status': 'REVIEW',
                'note': 'No RAG match found'
            }

        # Take best match
        best_match = results[0]
        score = round(best_match['score'], 3)

        # Step 2: Find standard concept via graph
        standard_name = None
        standard_id = None
        standard_vocab = None
        status = 'OK'
        note = None

        if self.graph is None:
            # No graph - use RAG match if it's standard
            if best_match['standard_concept'] == 'S':
                standard_name = best_match['concept_name']
                standard_id = best_match['concept_id']
                standard_vocab = best_match['vocabulary_id']
            else:
                status = 'REVIEW'
                note = 'Graph not loaded'
        else:
            # Use graph to find standard mapping
            standard_info = find_standard_mapping(self.graph, best_match['concept_id'])

            if standard_info:
                standard_name = standard_info['concept_name']
                standard_id = standard_info['concept_id']
                standard_vocab = standard_info['vocabulary_id']
            else:
                status = 'REVIEW'
                note = 'No standard mapping found'

        # Flag for review if score is low
        if score < 0.7:
            status = 'REVIEW'
            note = note or f'Low score ({score})'

        return {
            'input': query,
            'domain': domain,
            'match_name': best_match['concept_name'],
            'match_id': best_match['concept_id'],
            'match_vocab': best_match['vocabulary_id'],
            'score': score,
            'standard_name': standard_name,
            'standard_id': standard_id,
            'standard_vocab': standard_vocab,
            'status': status,
            'note': note
        }


def main():
    """
    Simple command-line interface for testing.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Semantic search for OMOP concepts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple query
  python retrieve.py "metformina"

  # With filters
  python retrieve.py "diabetes" --vocabulary SNOMED --standard-only

  # Top 20 results
  python retrieve.py "creatinine" --top-k 20

  # With graph expansion
  python retrieve.py "ibuprofen" --expand
        """
    )

    parser.add_argument('query', help='Search query')
    parser.add_argument('--top-k', type=int, default=10, help='Number of results (default: 10)')
    parser.add_argument('--vocabulary', help='Filter by vocabulary (e.g., SNOMED, RxNorm)')
    parser.add_argument('--domain', help='Filter by domain (e.g., Drug, Condition)')
    parser.add_argument('--standard-only', action='store_true', help='Only standard concepts')
    parser.add_argument('--min-score', type=float, help='Minimum similarity score (0-1)')
    parser.add_argument('--expand', action='store_true', help='Include graph expansion')
    parser.add_argument('--no-graph', action='store_true', help='Do not load graph (faster startup)')

    args = parser.parse_args()

    # Build filters
    filters = {}
    if args.vocabulary:
        filters['vocabulary'] = args.vocabulary
    if args.domain:
        filters['domain'] = args.domain
    if args.standard_only:
        filters['standard_only'] = True

    # Initialize retriever
    retriever = SemanticRetriever(load_graph_data=not args.no_graph)

    print("\n" + "=" * 70)
    print(f"QUERY: {args.query}")
    print("=" * 70)

    # Search
    if args.expand and retriever.graph is not None:
        response = retriever.search_with_expansion(
            query=args.query,
            top_k=args.top_k,
            filters=filters or None,
            min_score=args.min_score
        )
        results = response['primary_results']
        expanded = response['expanded_results']
    else:
        results = retriever.search(
            query=args.query,
            top_k=args.top_k,
            filters=filters or None,
            min_score=args.min_score
        )
        expanded = []

    # Display results
    print(f"\nTop {len(results)} results:")
    print()

    for i, result in enumerate(results, 1):
        std_marker = "⭐" if result['standard_concept'] == 'S' else "  "
        print(f"{i:2}. [Score: {result['score']:.4f}] {std_marker} {result['concept_name']}")
        print(f"    ID: {result['concept_id']} | {result['vocabulary_id']} | {result['domain_id']}")

    # Display expanded results
    if expanded:
        print("\n" + "=" * 70)
        print(f"Related concepts (via graph expansion):")
        print("=" * 70)
        print()

        for i, result in enumerate(expanded[:20], 1):
            print(f"{i:2}. [{result['relationship']}] {result['concept_name']}")
            print(f"    From: {result['from_concept']} (score: {result['from_score']:.4f})")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
