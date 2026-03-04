"""
test_preprocess.py - Unit tests for preprocess module

Tests cover:
- Expected use cases
- Edge cases
- Failure cases
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path to import preprocess
sys.path.insert(0, str(Path(__file__).parent.parent))

import preprocess


class TestValidateInputFiles:
    """Test file validation"""

    def test_validate_input_files_success(self):
        """Expected: All required files exist"""
        # Should not raise exception if files exist
        try:
            preprocess.validate_input_files()
        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_validate_input_files_missing(self, tmp_path, monkeypatch):
        """Failure: Missing required file should raise FileNotFoundError"""
        # Change DATA_DIR to non-existent directory
        monkeypatch.setattr(preprocess, 'DATA_DIR', tmp_path / 'nonexistent')
        monkeypatch.setattr(preprocess, 'CONCEPT_FILE', tmp_path / 'nonexistent' / 'CONCEPT.csv')
        monkeypatch.setattr(preprocess, 'RELATIONSHIP_FILE', tmp_path / 'nonexistent' / 'RELATIONSHIP.csv')
        monkeypatch.setattr(preprocess, 'CONCEPT_RELATIONSHIP_FILE', tmp_path / 'nonexistent' / 'CONCEPT_RELATIONSHIP.csv')

        with pytest.raises(FileNotFoundError):
            preprocess.validate_input_files()


class TestLoadConceptData:
    """Test CONCEPT.csv loading and filtering"""

    def test_load_concept_data_structure(self):
        """Expected: Load concepts and verify structure"""
        try:
            df = preprocess.load_concept_data()

            # Check columns
            expected_cols = ['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept']
            assert list(df.columns) == expected_cols

            # Check types
            assert df['concept_id'].dtype == 'int32'

            # Check no nulls in concept_name
            assert df['concept_name'].notna().all()

            # Check vocabulary filtering
            assert df['vocabulary_id'].isin(preprocess.RELEVANT_VOCABULARIES).all()

            # Check we have data
            assert len(df) > 0

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_load_concept_data_vocabularies(self):
        """Expected: Only relevant vocabularies are loaded"""
        try:
            df = preprocess.load_concept_data()

            vocabularies = set(df['vocabulary_id'].unique())
            assert vocabularies.issubset(preprocess.RELEVANT_VOCABULARIES)

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_load_concept_data_keeps_non_standard(self):
        """Expected: Both standard and non-standard concepts are kept"""
        try:
            df = preprocess.load_concept_data()

            # Should have both standard and non-standard
            standard_concepts = df[df['standard_concept'] == 'S']
            non_standard_concepts = df[df['standard_concept'] != 'S']

            # Reason: We need non-standard concepts for mapping
            assert len(standard_concepts) > 0, "Should have standard concepts"
            assert len(non_standard_concepts) > 0, "Should have non-standard concepts"

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")


class TestLoadRelationshipMapping:
    """Test RELATIONSHIP.csv loading"""

    def test_load_relationship_mapping_structure(self):
        """Expected: Load relationships and verify structure"""
        try:
            mapping = preprocess.load_relationship_mapping()

            # Check it's a dict
            assert isinstance(mapping, dict)

            # Check it has data
            assert len(mapping) > 0

            # Check all values are strings (relationship names)
            assert all(isinstance(v, str) for v in mapping.values())

            # Check all relationship names are in whitelist
            assert set(mapping.values()).issubset(preprocess.RELEVANT_RELATIONSHIPS)

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_load_relationship_mapping_contains_maps_to(self):
        """Expected: Critical mapping relationship is included"""
        try:
            mapping = preprocess.load_relationship_mapping()

            # Reason: Mapping relationship is critical for non-standard -> standard mapping
            # Note: OMOP uses "Non-standard to Standard map (OMOP)" instead of "Maps to"
            mapping_relations = {
                'Maps to',
                'Non-standard to Standard map (OMOP)',
                'Mapped from',
                'Standard to Non-standard map (OMOP)'
            }

            # Check if at least one mapping relationship exists
            has_mapping = any(rel in mapping.values() for rel in mapping_relations)
            assert has_mapping, f"Must include at least one mapping relationship. Found: {list(mapping.values())}"

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")


class TestLoadConceptRelationships:
    """Test CONCEPT_RELATIONSHIP.csv loading"""

    def test_load_concept_relationships_structure(self):
        """Expected: Load relationships and verify structure"""
        try:
            # First load concepts and relationship mapping
            nodes_df = preprocess.load_concept_data()
            relationship_mapping = preprocess.load_relationship_mapping()

            valid_concept_ids = set(nodes_df['concept_id'].values)

            # Load relationships
            edges_df = preprocess.load_concept_relationships(
                valid_concept_ids,
                relationship_mapping
            )

            # Check columns
            expected_cols = ['concept_id_1', 'relationship_name', 'concept_id_2']
            assert list(edges_df.columns) == expected_cols

            # Check types
            assert edges_df['concept_id_1'].dtype == 'int32'
            assert edges_df['concept_id_2'].dtype == 'int32'

            # All concept_ids should be in valid set
            if len(edges_df) > 0:
                assert edges_df['concept_id_1'].isin(valid_concept_ids).all()
                assert edges_df['concept_id_2'].isin(valid_concept_ids).all()

                # All relationships should be in whitelist
                assert edges_df['relationship_name'].isin(preprocess.RELEVANT_RELATIONSHIPS).all()

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_load_concept_relationships_filters_correctly(self):
        """Edge case: Only valid concepts and relationships are included"""
        try:
            nodes_df = preprocess.load_concept_data()
            relationship_mapping = preprocess.load_relationship_mapping()

            valid_concept_ids = set(nodes_df['concept_id'].values)

            edges_df = preprocess.load_concept_relationships(
                valid_concept_ids,
                relationship_mapping
            )

            if len(edges_df) > 0:
                # Verify filtering worked
                invalid_concepts = (
                    ~edges_df['concept_id_1'].isin(valid_concept_ids) |
                    ~edges_df['concept_id_2'].isin(valid_concept_ids)
                )
                assert not invalid_concepts.any(), "Found edges with invalid concept IDs"

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_load_concept_relationships_empty_valid_ids(self):
        """Edge case: Empty valid_concept_ids should return empty DataFrame"""
        try:
            relationship_mapping = preprocess.load_relationship_mapping()

            edges_df = preprocess.load_concept_relationships(
                set(),  # Empty set
                relationship_mapping
            )

            # Should return empty DataFrame
            assert len(edges_df) == 0

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")


class TestPreprocessPipeline:
    """Test full preprocessing pipeline"""

    def test_preprocess_full_pipeline(self, tmp_path, monkeypatch):
        """Expected: Full pipeline generates nodes.csv and edges.csv"""
        try:
            # Change output paths to tmp directory
            monkeypatch.setattr(preprocess, 'OUTPUT_NODES', tmp_path / 'nodes.csv')
            monkeypatch.setattr(preprocess, 'OUTPUT_EDGES', tmp_path / 'edges.csv')

            # Run preprocessing
            nodes_df, edges_df = preprocess.preprocess()

            # Check output files were created
            assert (tmp_path / 'nodes.csv').exists()
            assert (tmp_path / 'edges.csv').exists()

            # Check DataFrames have data
            assert len(nodes_df) > 0
            assert len(edges_df) >= 0  # edges might be 0 if no relationships

            # Check structure
            assert 'concept_id' in nodes_df.columns
            assert 'concept_name' in nodes_df.columns
            assert 'vocabulary_id' in nodes_df.columns

            if len(edges_df) > 0:
                assert 'concept_id_1' in edges_df.columns
                assert 'relationship_name' in edges_df.columns
                assert 'concept_id_2' in edges_df.columns

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_preprocess_nodes_valid(self, tmp_path, monkeypatch):
        """Expected: Generated nodes.csv has valid structure"""
        try:
            monkeypatch.setattr(preprocess, 'OUTPUT_NODES', tmp_path / 'nodes.csv')
            monkeypatch.setattr(preprocess, 'OUTPUT_EDGES', tmp_path / 'edges.csv')

            nodes_df, _ = preprocess.preprocess()

            # No nulls in concept_name
            assert nodes_df['concept_name'].notna().all()

            # All vocabularies are relevant
            assert nodes_df['vocabulary_id'].isin(preprocess.RELEVANT_VOCABULARIES).all()

            # Concept IDs are unique
            assert nodes_df['concept_id'].is_unique

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")

    def test_preprocess_edges_valid(self, tmp_path, monkeypatch):
        """Expected: Generated edges.csv has valid references"""
        try:
            monkeypatch.setattr(preprocess, 'OUTPUT_NODES', tmp_path / 'nodes.csv')
            monkeypatch.setattr(preprocess, 'OUTPUT_EDGES', tmp_path / 'edges.csv')

            nodes_df, edges_df = preprocess.preprocess()

            if len(edges_df) > 0:
                valid_concept_ids = set(nodes_df['concept_id'].values)

                # All concept_id_1 and concept_id_2 must exist in nodes
                assert edges_df['concept_id_1'].isin(valid_concept_ids).all()
                assert edges_df['concept_id_2'].isin(valid_concept_ids).all()

                # All relationships are in whitelist
                assert edges_df['relationship_name'].isin(preprocess.RELEVANT_RELATIONSHIPS).all()

        except FileNotFoundError:
            pytest.skip("OMOP data files not available")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
