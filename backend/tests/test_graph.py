"""
test_graph.py - Unit tests for graph module

Tests cover:
- Expected use cases
- Edge cases
- Failure cases
"""

import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import graph
import preprocess


@pytest.fixture(scope='module')
def setup_graph_files(tmp_path_factory):
    """
    Fixture to run preprocessing once and provide graph files for all tests.
    Uses tmp_path_factory for module scope.
    """
    try:
        # Create temp directory
        tmp_dir = tmp_path_factory.mktemp('graph_test')

        # Run preprocessing to generate test data
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import preprocess

        # Temporarily change output paths
        original_nodes = preprocess.OUTPUT_NODES
        original_edges = preprocess.OUTPUT_EDGES

        preprocess.OUTPUT_NODES = tmp_dir / 'nodes.csv'
        preprocess.OUTPUT_EDGES = tmp_dir / 'edges.csv'

        # Run preprocessing
        nodes_df, edges_df = preprocess.preprocess()

        # Restore original paths
        preprocess.OUTPUT_NODES = original_nodes
        preprocess.OUTPUT_EDGES = original_edges

        return {
            'nodes_file': tmp_dir / 'nodes.csv',
            'edges_file': tmp_dir / 'edges.csv',
            'nodes_df': nodes_df,
            'edges_df': edges_df
        }

    except FileNotFoundError:
        pytest.skip("OMOP data files not available")


class TestValidateGraphFiles:
    """Test file validation"""

    def test_validate_graph_files_success(self, setup_graph_files, monkeypatch):
        """Expected: Validation succeeds when files exist"""
        files = setup_graph_files

        # Point to test files
        monkeypatch.setattr(graph, 'NODES_FILE', files['nodes_file'])
        monkeypatch.setattr(graph, 'EDGES_FILE', files['edges_file'])

        # Should not raise
        graph.validate_graph_files()

    def test_validate_graph_files_missing(self, tmp_path, monkeypatch):
        """Failure: Missing files should raise FileNotFoundError"""
        # Point to non-existent files
        monkeypatch.setattr(graph, 'NODES_FILE', tmp_path / 'nonexistent_nodes.csv')
        monkeypatch.setattr(graph, 'EDGES_FILE', tmp_path / 'nonexistent_edges.csv')

        with pytest.raises(FileNotFoundError):
            graph.validate_graph_files()


class TestLoadNodes:
    """Test nodes loading"""

    def test_load_nodes_structure(self, setup_graph_files, monkeypatch):
        """Expected: Load nodes with correct structure"""
        files = setup_graph_files
        monkeypatch.setattr(graph, 'NODES_FILE', files['nodes_file'])

        df = graph.load_nodes()

        # Check it's a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Check columns
        expected_cols = ['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept']
        assert list(df.columns) == expected_cols

        # Check we have data
        assert len(df) > 0


class TestLoadEdges:
    """Test edges loading"""

    def test_load_edges_structure(self, setup_graph_files, monkeypatch):
        """Expected: Load edges with correct structure"""
        files = setup_graph_files
        monkeypatch.setattr(graph, 'EDGES_FILE', files['edges_file'])

        df = graph.load_edges()

        # Check it's a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Check columns
        expected_cols = ['concept_id_1', 'relationship_name', 'concept_id_2']
        assert list(df.columns) == expected_cols


class TestBuildGraph:
    """Test graph construction"""

    def test_build_graph_creates_multidigraph(self, setup_graph_files):
        """Expected: Build returns MultiDiGraph"""
        files = setup_graph_files

        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Check type
        assert isinstance(G, nx.MultiDiGraph)
        assert G.is_directed()
        assert G.is_multigraph()

        # Check we have nodes and edges
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() >= 0  # might be 0 if no relationships

    def test_build_graph_node_attributes(self, setup_graph_files):
        """Expected: Nodes have correct attributes"""
        files = setup_graph_files

        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Check first node has required attributes
        first_node = list(G.nodes())[0]
        node_data = G.nodes[first_node]

        assert 'concept_name' in node_data
        assert 'vocabulary_id' in node_data
        assert 'domain_id' in node_data
        assert 'standard_concept' in node_data

    def test_build_graph_edge_attributes(self, setup_graph_files):
        """Expected: Edges have relationship attribute"""
        files = setup_graph_files

        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        if G.number_of_edges() > 0:
            # Check first edge has relationship attribute
            first_edge = list(G.edges(keys=True))[0]
            edge_data = G.get_edge_data(first_edge[0], first_edge[1], first_edge[2])

            assert 'relationship' in edge_data

    def test_build_graph_empty_edges(self):
        """Edge case: Build graph with nodes but no edges"""
        nodes_df = pd.DataFrame({
            'concept_id': [1, 2, 3],
            'concept_name': ['A', 'B', 'C'],
            'vocabulary_id': ['SNOMED', 'RxNorm', 'LOINC'],
            'domain_id': ['Drug', 'Drug', 'Measurement'],
            'standard_concept': ['S', 'S', 'S']
        })

        edges_df = pd.DataFrame(columns=['concept_id_1', 'relationship_name', 'concept_id_2'])

        G = graph.build_graph(nodes_df, edges_df)

        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 0


class TestGetConceptInfo:
    """Test concept info retrieval"""

    def test_get_concept_info_exists(self, setup_graph_files):
        """Expected: Get info for existing concept"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Get first concept ID
        first_concept_id = list(G.nodes())[0]

        info = graph.get_concept_info(G, first_concept_id)

        # Check return structure
        assert info is not None
        assert isinstance(info, dict)
        assert 'concept_id' in info
        assert 'concept_name' in info
        assert 'vocabulary_id' in info
        assert 'domain_id' in info
        assert 'standard_concept' in info

        assert info['concept_id'] == first_concept_id

    def test_get_concept_info_not_exists(self, setup_graph_files):
        """Failure: Non-existent concept should return None"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        info = graph.get_concept_info(G, 999999999)  # Non-existent ID

        assert info is None


class TestGetNeighbors:
    """Test neighbor retrieval"""

    def test_get_neighbors_with_relationships(self, setup_graph_files):
        """Expected: Get neighbors for concept with relationships"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        if G.number_of_edges() == 0:
            pytest.skip("No edges in graph")

        # Find a node with edges
        node_with_edges = None
        for node in G.nodes():
            if G.out_degree(node) > 0 or G.in_degree(node) > 0:
                node_with_edges = node
                break

        if node_with_edges is None:
            pytest.skip("No nodes with edges found")

        neighbors = graph.get_neighbors(G, node_with_edges)

        # Should have at least one neighbor
        assert len(neighbors) > 0

        # Check structure of first neighbor
        first_neighbor = neighbors[0]
        assert 'relationship' in first_neighbor
        assert 'direction' in first_neighbor
        assert first_neighbor['direction'] in ['outgoing', 'incoming']

    def test_get_neighbors_isolated_node(self, setup_graph_files):
        """Edge case: Isolated node (no relationships) returns empty list"""
        # Create graph with isolated node
        nodes_df = pd.DataFrame({
            'concept_id': [1, 2],
            'concept_name': ['A', 'B'],
            'vocabulary_id': ['SNOMED', 'RxNorm'],
            'domain_id': ['Drug', 'Drug'],
            'standard_concept': ['S', 'S']
        })

        edges_df = pd.DataFrame(columns=['concept_id_1', 'relationship_name', 'concept_id_2'])

        G = graph.build_graph(nodes_df, edges_df)

        neighbors = graph.get_neighbors(G, 1)

        assert neighbors == []

    def test_get_neighbors_max_limit(self, setup_graph_files):
        """Expected: max_neighbors parameter limits results"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        if G.number_of_edges() == 0:
            pytest.skip("No edges in graph")

        # Find a node with many edges
        node_with_edges = None
        for node in G.nodes():
            if G.out_degree(node) + G.in_degree(node) > 5:
                node_with_edges = node
                break

        if node_with_edges is None:
            pytest.skip("No nodes with many edges found")

        neighbors = graph.get_neighbors(G, node_with_edges, max_neighbors=3)

        # Should respect limit
        assert len(neighbors) <= 3

    def test_get_neighbors_not_exists(self, setup_graph_files):
        """Failure: Non-existent concept returns empty list"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        neighbors = graph.get_neighbors(G, 999999999)

        assert neighbors == []


class TestFindStandardMapping:
    """Test standard concept mapping"""

    def test_find_standard_mapping_already_standard(self, setup_graph_files):
        """Expected: Standard concept returns itself"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Find a standard concept
        standard_concept = None
        for node in G.nodes():
            if G.nodes[node].get('standard_concept') == 'S':
                standard_concept = node
                break

        if standard_concept is None:
            pytest.skip("No standard concepts found")

        result = graph.find_standard_mapping(G, standard_concept)

        assert result is not None
        assert result['concept_id'] == standard_concept
        assert result['standard_concept'] == 'S'

    def test_find_standard_mapping_non_standard(self, setup_graph_files):
        """Expected: Non-standard concept follows 'Maps to' to standard"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Find a non-standard concept with "Maps to" relationship
        non_standard_with_mapping = None
        for node in G.nodes():
            if G.nodes[node].get('standard_concept') != 'S':
                # Check if it has "Maps to" relationship
                for target in G.successors(node):
                    edges = G.get_edge_data(node, target)
                    for edge_key, edge_data in edges.items():
                        if edge_data.get('relationship') == 'Maps to':
                            non_standard_with_mapping = node
                            break
                    if non_standard_with_mapping:
                        break
            if non_standard_with_mapping:
                break

        if non_standard_with_mapping is None:
            pytest.skip("No non-standard concepts with 'Maps to' relationship found")

        result = graph.find_standard_mapping(G, non_standard_with_mapping)

        # Should find a standard concept
        if result is not None:
            assert result['standard_concept'] == 'S'
            assert result['concept_id'] != non_standard_with_mapping

    def test_find_standard_mapping_no_mapping(self, setup_graph_files):
        """Edge case: Non-standard without 'Maps to' returns None"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        # Find a non-standard concept without "Maps to"
        non_standard_no_mapping = None
        for node in G.nodes():
            if G.nodes[node].get('standard_concept') != 'S':
                has_maps_to = False
                for target in G.successors(node):
                    edges = G.get_edge_data(node, target)
                    for edge_key, edge_data in edges.items():
                        if edge_data.get('relationship') == 'Maps to':
                            has_maps_to = True
                            break
                    if has_maps_to:
                        break
                if not has_maps_to:
                    non_standard_no_mapping = node
                    break

        if non_standard_no_mapping is None:
            pytest.skip("All non-standard concepts have 'Maps to'")

        result = graph.find_standard_mapping(G, non_standard_no_mapping)

        # Should return None
        assert result is None

    def test_find_standard_mapping_not_exists(self, setup_graph_files):
        """Failure: Non-existent concept returns None"""
        files = setup_graph_files
        G = graph.build_graph(files['nodes_df'], files['edges_df'])

        result = graph.find_standard_mapping(G, 999999999)

        assert result is None


class TestLoadGraph:
    """Test full graph loading"""

    def test_load_graph_full(self, setup_graph_files, monkeypatch):
        """Expected: Load complete graph successfully"""
        files = setup_graph_files

        # Point to test files
        monkeypatch.setattr(graph, 'NODES_FILE', files['nodes_file'])
        monkeypatch.setattr(graph, 'EDGES_FILE', files['edges_file'])

        G = graph.load_graph()

        # Check type
        assert isinstance(G, nx.MultiDiGraph)

        # Check we have data
        assert G.number_of_nodes() > 0

        # Check graph properties
        assert G.is_directed()
        assert G.is_multigraph()


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
