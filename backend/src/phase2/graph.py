
"""
graph.py - OMOP Graph Construction Module

Builds and queries a NetworkX MultiDiGraph from preprocessed OMOP data.
Provides functions to navigate the graph and find standard concept mappings.

Input:
    - nodes.csv: Preprocessed concept nodes
    - edges.csv: Preprocessed concept relationships

Output:
    - NetworkX MultiDiGraph with concept nodes and relationship edges
"""

from pathlib import Path
import pandas as pd
import networkx as nx
import pickle
from typing import Optional
from collections import deque


# File paths
NODES_FILE = Path('data/processed/nodes.csv')
EDGES_FILE = Path('data/processed/edges.csv')
CACHE_FILE = Path('data/processed/omop_graph.pkl')


def validate_graph_files() -> None:
    """
    Validate that preprocessed graph files exist.

    Raises:
        FileNotFoundError: If nodes.csv or edges.csv is missing
    """
    required_files = [NODES_FILE, EDGES_FILE]
    missing_files = [f for f in required_files if not f.exists()]

    if missing_files:
        missing_names = [f.name for f in missing_files]
        raise FileNotFoundError(
            f"Missing graph files: {missing_names}. Run preprocess.py first."
        )


def load_nodes() -> pd.DataFrame:
    """
    Load nodes.csv.

    Returns:
        DataFrame with concept node data
    """
    print(f"Loading {NODES_FILE}...")
    # Fix: Specify dtypes to avoid mixed type warnings
    df = pd.read_csv(
        NODES_FILE, 
        dtype={
            'concept_id': 'int32',
            'concept_name': 'str',
            'vocabulary_id': 'str',
            'domain_id': 'str', 
            'standard_concept': 'str'  # Column 4 with mixed types
        },
        low_memory=False
    )
    print(f"  Loaded {len(df):,} nodes")
    return df


def load_edges() -> pd.DataFrame:
    """
    Load edges.csv.

    Returns:
        DataFrame with concept relationship edges
    """
    print(f"Loading {EDGES_FILE}...")
    df = pd.read_csv(
        EDGES_FILE,
        dtype={'concept_id_1': 'int32', 'concept_id_2': 'int32'}
    )
    print(f"  Loaded {len(df):,} edges")
    return df


def build_graph(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> nx.MultiDiGraph:
    """
    Build NetworkX MultiDiGraph from nodes and edges DataFrames.

    Args:
        nodes_df: DataFrame with concept nodes
        edges_df: DataFrame with concept relationships

    Returns:
        NetworkX MultiDiGraph with nodes and edges
    """
    print("Building graph...")
    G = nx.MultiDiGraph()

    # Add nodes with attributes
    for _, row in nodes_df.iterrows():
        G.add_node(
            row['concept_id'],
            concept_name=row['concept_name'],
            vocabulary_id=row['vocabulary_id'],
            domain_id=row['domain_id'],
            standard_concept=row.get('standard_concept', None)
        )

    # Add edges with relationship attribute
    for _, row in edges_df.iterrows():
        G.add_edge(
            row['concept_id_1'],
            row['concept_id_2'],
            relationship=row['relationship_name']
        )

    print(f"  Graph built: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    return G


def get_concept_info(G: nx.MultiDiGraph, concept_id: int) -> Optional[dict]:
    """
    Get information about a concept by ID.

    Args:
        G: NetworkX graph
        concept_id: Concept ID to look up

    Returns:
        Dict with concept information, or None if not found
    """
    if concept_id not in G:
        return None

    node_data = G.nodes[concept_id]
    return {
        'concept_id': concept_id,
        'concept_name': node_data.get('concept_name'),
        'vocabulary_id': node_data.get('vocabulary_id'),
        'domain_id': node_data.get('domain_id'),
        'standard_concept': node_data.get('standard_concept')
    }


def get_neighbors(
    G: nx.MultiDiGraph,
    concept_id: int,
    max_neighbors: int = 10
) -> list[dict]:
    """
    Get neighboring concepts (1-hop) for a given concept.

    Args:
        G: NetworkX graph
        concept_id: Source concept ID
        max_neighbors: Maximum number of neighbors to return

    Returns:
        List of dicts with neighbor information:
        {
            'relationship': relationship name,
            'direction': 'outgoing' or 'incoming',
            'target_id': neighbor concept_id,
            'target_name': neighbor concept_name,
            'target_vocabulary': neighbor vocabulary_id,
            'target_standard': neighbor standard_concept
        }
    """
    if concept_id not in G:
        return []

    neighbors = []

    # Outgoing edges (concept_id -> other)
    for target_id in G.successors(concept_id):
        # Get all edges between concept_id and target_id (MultiDiGraph allows multiple)
        edges = G.get_edge_data(concept_id, target_id)
        for edge_key, edge_data in edges.items():
            target_data = G.nodes[target_id]
            neighbors.append({
                'relationship': edge_data.get('relationship'),
                'direction': 'outgoing',
                'target_id': target_id,
                'target_name': target_data.get('concept_name'),
                'target_vocabulary': target_data.get('vocabulary_id'),
                'target_standard': target_data.get('standard_concept')
            })

    # Incoming edges (other -> concept_id)
    for source_id in G.predecessors(concept_id):
        # Get all edges between source_id and concept_id
        edges = G.get_edge_data(source_id, concept_id)
        for edge_key, edge_data in edges.items():
            source_data = G.nodes[source_id]
            neighbors.append({
                'relationship': edge_data.get('relationship'),
                'direction': 'incoming',
                'source_id': source_id,
                'source_name': source_data.get('concept_name'),
                'source_vocabulary': source_data.get('vocabulary_id'),
                'source_standard': source_data.get('standard_concept')
            })

    # Limit number of neighbors
    if len(neighbors) > max_neighbors:
        neighbors = neighbors[:max_neighbors]

    return neighbors


def _resolve_classification_to_standard(
    G: nx.MultiDiGraph,
    classification_concept_id: int,
    max_depth: int = 3
) -> Optional[dict]:
    """
    Try to navigate down the hierarchy from a Classification (C) concept
    to find a unique Standard (S) concept.

    Uses BFS following only hierarchy-down relationships (Subsumes, Has ingredient).
    Returns the S concept if exactly one is found at the shallowest level.
    Returns None if ambiguous (multiple S at same level) or no S found.

    Args:
        G: NetworkX graph
        classification_concept_id: The C concept to resolve
        max_depth: Maximum BFS depth (default: 3)

    Returns:
        Dict with standard concept info (with 'resolved_from_classification': True),
        or None if resolution failed
    """
    HIERARCHY_DOWN_RELATIONSHIPS = {
        'Subsumes',
        'Has ingredient (RxNorm)',
        'Has active ingredient (SNOMED)',
    }

    visited = {classification_concept_id}
    queue = deque([(classification_concept_id, 0)])

    current_depth_standards = []
    current_depth_level = -1

    while queue:
        node_id, depth = queue.popleft()

        if depth >= max_depth:
            break

        # If we already found S concepts at a shallower depth, stop
        if current_depth_standards and depth >= current_depth_level:
            break

        # Explore outgoing hierarchy-down edges
        for target_id in G.successors(node_id):
            if target_id in visited:
                continue

            edges = G.get_edge_data(node_id, target_id)
            has_hierarchy_edge = False
            for _, edge_data in edges.items():
                if edge_data.get('relationship') in HIERARCHY_DOWN_RELATIONSHIPS:
                    has_hierarchy_edge = True
                    break

            if not has_hierarchy_edge:
                continue

            visited.add(target_id)
            target_data = G.nodes.get(target_id, {})

            if target_data.get('standard_concept') == 'S':
                if current_depth_level == -1:
                    current_depth_level = depth + 1
                current_depth_standards.append(target_id)
            else:
                # Continue BFS through non-S nodes
                if depth + 1 <= max_depth:
                    queue.append((target_id, depth + 1))

    # Exactly one S concept found -> return it
    if len(current_depth_standards) == 1:
        info = get_concept_info(G, current_depth_standards[0])
        if info:
            info['resolved_from_classification'] = True
        return info

    # Zero or multiple -> ambiguous, return None
    return None


def find_standard_mapping(G: nx.MultiDiGraph, concept_id: int) -> Optional[dict]:
    """
    Find the standard concept mapping for a given concept.

    If the concept is already standard (S), returns its own info.
    If classification (C), attempts to navigate down the hierarchy
    (via Subsumes, Has ingredient) to find a unique Standard (S) concept.
    Returns None if no standard found or if multiple candidates exist (ambiguous).
    If non-standard (NULL), follows 'Maps to' relationships to find standard concept.

    Args:
        G: NetworkX graph
        concept_id: Concept ID to find standard mapping for

    Returns:
        Dict with standard concept info, or None if no mapping found
    """
    if concept_id not in G:
        return None

    # Check if already standard or classification
    node_data = G.nodes[concept_id]
    if node_data.get('standard_concept') == 'S':
        return get_concept_info(G, concept_id)

    # Classification concepts (C) - try to resolve down hierarchy to Standard (S)
    if node_data.get('standard_concept') == 'C':
        resolved = _resolve_classification_to_standard(G, concept_id)
        if resolved:
            return resolved
        # Could not resolve to a unique S concept
        return None

    # Follow mapping relationships to find standard concept
    # Reason: Non-standard concepts map to standard via mapping relationships
    # Note: OMOP uses "Non-standard to Standard map (OMOP)" instead of "Maps to"
    MAPPING_RELATIONSHIPS = {
        'Maps to',
        'Non-standard to Standard map (OMOP)',
        'Concept replaced by'
    }

    visited = set()  # Avoid infinite loops
    current_id = concept_id

    while current_id not in visited:
        visited.add(current_id)

        # Look for outgoing mapping edges
        found_mapping = False
        for target_id in G.successors(current_id):
            edges = G.get_edge_data(current_id, target_id)
            for edge_key, edge_data in edges.items():
                if edge_data.get('relationship') in MAPPING_RELATIONSHIPS:
                    target_data = G.nodes[target_id]
                    # Check if target is standard
                    if target_data.get('standard_concept') == 'S':
                        return get_concept_info(G, target_id)
                    else:
                        # Continue following the chain
                        current_id = target_id
                        found_mapping = True
                        break
            if found_mapping:
                break

        if not found_mapping:
            # No more mapping edges, mapping not found
            break

    return None


def load_graph(use_cache: bool = True, force_rebuild: bool = False) -> nx.MultiDiGraph:
    """
    Load and build the complete OMOP graph.

    Uses pickle cache to avoid rebuilding from CSVs every time.
    Cache is automatically created after first build.

    Args:
        use_cache: If True, use cached graph if available (default: True)
        force_rebuild: If True, rebuild from CSVs even if cache exists (default: False)

    Returns:
        NetworkX MultiDiGraph ready for querying
    """
    print("=" * 60)
    print("Loading OMOP Graph")
    print("=" * 60)

    # Check if cache exists and should be used
    if use_cache and CACHE_FILE.exists() and not force_rebuild:
        print(f"\n[CACHE] Loading graph from {CACHE_FILE}...")
        try:
            with open(CACHE_FILE, 'rb') as f:
                G = pickle.load(f)

            print(f"[CACHE] Graph loaded successfully!")
            print()

            # Statistics
            print("=" * 60)
            print("Graph Statistics")
            print("=" * 60)
            print(f"Nodes: {G.number_of_nodes():,}")
            print(f"Edges: {G.number_of_edges():,}")
            print(f"Density: {nx.density(G):.6f}")
            print(f"Is directed: {G.is_directed()}")
            print(f"Is multigraph: {G.is_multigraph()}")
            print("=" * 60)

            return G

        except Exception as e:
            print(f"[WARNING] Failed to load cache: {e}")
            print("[INFO] Rebuilding from CSVs...")

    # Build from CSVs (no cache or forced rebuild)
    if force_rebuild:
        print("\n[INFO] Force rebuild requested, building from CSVs...")
    else:
        print("\n[INFO] No cache found, building from CSVs...")
    print()

    # Validate files
    validate_graph_files()
    print()

    # Load data
    nodes_df = load_nodes()
    edges_df = load_edges()
    print()

    # Build graph
    G = build_graph(nodes_df, edges_df)
    print()

    # Save to cache
    if use_cache:
        print(f"[CACHE] Saving graph to {CACHE_FILE}...")
        try:
            with open(CACHE_FILE, 'wb') as f:
                pickle.dump(G, f)

            cache_size_mb = CACHE_FILE.stat().st_size / (1024 * 1024)
            print(f"[CACHE] Graph saved successfully ({cache_size_mb:.1f} MB)")
        except Exception as e:
            print(f"[WARNING] Failed to save cache: {e}")
    print()

    # Statistics
    print("=" * 60)
    print("Graph Statistics")
    print("=" * 60)
    print(f"Nodes: {G.number_of_nodes():,}")
    print(f"Edges: {G.number_of_edges():,}")
    print(f"Density: {nx.density(G):.6f}")
    print(f"Is directed: {G.is_directed()}")
    print(f"Is multigraph: {G.is_multigraph()}")
    print("=" * 60)

    return G


def clear_cache() -> None:
    """
    Delete the cached graph file.
    Use this when you've updated the source CSVs and need to rebuild.
    """
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print(f"[CACHE] Deleted {CACHE_FILE}")
    else:
        print(f"[CACHE] No cache file found")


if __name__ == '__main__':
    # Load graph
    try:
        G = load_graph()
        print("\n[SUCCESS] Graph loaded successfully!")

        # Example usage
        print("\n" + "=" * 60)
        print("Example Queries")
        print("=" * 60)

        # Try to find some common concepts
        example_ids = [1503297, 201826, 313217]  # Common IDs to try

        for concept_id in example_ids:
            info = get_concept_info(G, concept_id)
            if info:
                print(f"\nConcept ID: {concept_id}")
                print(f"  Name: {info['concept_name']}")
                print(f"  Vocabulary: {info['vocabulary_id']}")
                print(f"  Domain: {info['domain_id']}")
                print(f"  Standard: {info['standard_concept']}")

                # Get neighbors
                neighbors = get_neighbors(G, concept_id, max_neighbors=3)
                if neighbors:
                    print(f"  Top 3 relationships:")
                    for n in neighbors:
                        if n['direction'] == 'outgoing':
                            print(f"    → {n['relationship']}: {n['target_name']}")
                        else:
                            print(f"    ← {n['relationship']}: {n['source_name']}")

                # Try finding standard mapping
                if info['standard_concept'] != 'S':
                    standard = find_standard_mapping(G, concept_id)
                    if standard:
                        print(f"  Maps to standard: {standard['concept_name']} (ID: {standard['concept_id']})")

    except Exception as e:
        print(f"\n[ERROR] Graph loading failed: {e}")
        raise
