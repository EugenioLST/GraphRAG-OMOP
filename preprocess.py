"""
preprocess.py - OMOP CSV Preprocessing Module

Processes raw OMOP vocabulary files and generates simplified nodes/edges for graph construction.
Filters to keep only relevant vocabularies (SNOMED, RxNorm, LOINC) and relationships.

Input:
    - data/CONCEPT.csv (565 MB)
    - data/RELATIONSHIP.csv (53 KB)
    - data/CONCEPT_RELATIONSHIP.csv (1.7 GB)

Output:
    - nodes.csv: concept_id, concept_name, vocabulary_id, domain_id, standard_concept
    - edges.csv: concept_id_1, relationship_name, concept_id_2
"""

from pathlib import Path
import pandas as pd
from typing import Tuple


# File paths
DATA_DIR = Path('data')
CONCEPT_FILE = DATA_DIR / 'CONCEPT.csv'
RELATIONSHIP_FILE = DATA_DIR / 'RELATIONSHIP.csv'
CONCEPT_RELATIONSHIP_FILE = DATA_DIR / 'CONCEPT_RELATIONSHIP.csv'

OUTPUT_NODES = Path('nodes.csv')
OUTPUT_EDGES = Path('edges.csv')

# Vocabularies to keep
RELEVANT_VOCABULARIES = {'SNOMED', 'RxNorm', 'LOINC', 'RxNorm Extension'}

# Relationships whitelist - focusing on mapping and key medical relationships
# Reason: These are the most relevant for mapping non-standard -> standard terms
RELEVANT_RELATIONSHIPS = {
    # Core hierarchies (confirmed available)
    'Is a',                           # Hierarchical relationships
    'Subsumes',                       # Reverse hierarchy
    
    # Standard mapping relationships (using actual names from CSV)
    'Concept replaced by',            # Non-standard -> standard mapping
    'Concept replaces',               # Standard -> non-standard mapping  
    'Non-standard to Standard map (OMOP)',  # OMOP standard mappings
    'Standard to Non-standard map (OMOP)',  # Reverse mappings
    
    # RxNorm relationships (using actual names)
    'Is a (RxNorm)',                  # RxNorm hierarchies
    'Inverse is a (RxNorm)',          # Reverse RxNorm hierarchy
    'Has ingredient (RxNorm)',        # Drug ingredients
    'Ingredient of (RxNorm)',         # Reverse ingredient
    'Has form (RxNorm)',              # Drug forms
    'Form of (RxNorm)',               # Reverse forms
    'Has dose form (RxNorm)',         # Dose forms
    'Dose form of (RxNorm)',          # Reverse dose forms
    'Contains (RxNorm)',              # Composition
    'Consists of (RxNorm)',           # Alternative composition
    'Constitutes (RxNorm)',           # Reverse composition
    'Has tradename (RxNorm)',         # Brand names
    'Tradename of (RxNorm)',          # Reverse tradenames
    
    # SNOMED relationships
    'Has active ingredient (SNOMED)', # Active ingredients
    'Active ingredient of (SNOMED)',  # Reverse active ingredients
    'Has basic dose form (SNOMED)',   # Basic dose forms
    'Basic dose form of (SNOMED)',    # Reverse dose forms
}

# Chunk size for processing large files
CHUNK_SIZE = 500_000


def validate_input_files() -> None:
    """
    Validate that required OMOP CSV files exist.

    Raises:
        FileNotFoundError: If any required file is missing
    """
    required_files = [CONCEPT_FILE, RELATIONSHIP_FILE, CONCEPT_RELATIONSHIP_FILE]
    missing_files = [f for f in required_files if not f.exists()]

    if missing_files:
        missing_names = [f.name for f in missing_files]
        raise FileNotFoundError(
            f"Missing required OMOP files in {DATA_DIR}/: {missing_names}"
        )

    print("[OK] All required OMOP files found")


def load_concept_data(nrows: int = None) -> pd.DataFrame:
    """
    Load and filter CONCEPT.csv.

    Args:
        nrows: Optional limit on number of rows to read (for testing). None = read all.

    Filters:
        - Only SNOMED, RxNorm, LOINC vocabularies
        - Keeps both standard and non-standard concepts

    Returns:
        DataFrame with columns: concept_id, concept_name, vocabulary_id, domain_id, standard_concept
    """
    print(f"Loading {CONCEPT_FILE.name}...")
    if nrows:
        print(f"  [TEST MODE] Limiting to first {nrows:,} rows")

    try:
        # Try tab-separated first - Fix: Add low_memory=False and specify dtypes
        df = pd.read_csv(
            CONCEPT_FILE,
            sep='\t',
            usecols=['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept'],
            dtype={
                'concept_id': 'int32',
                'concept_name': 'str',
                'vocabulary_id': 'str',
                'domain_id': 'str',
                'standard_concept': 'str'
            },
            low_memory=False,
            on_bad_lines='skip',
            nrows=nrows
        )
    except ValueError:
        # Fallback to comma-separated
        df = pd.read_csv(
            CONCEPT_FILE,
            usecols=['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept'],
            dtype={
                'concept_id': 'int32',
                'concept_name': 'str',
                'vocabulary_id': 'str',
                'domain_id': 'str',
                'standard_concept': 'str'
            },
            low_memory=False,
            on_bad_lines='skip',
            nrows=nrows
        )

    print(f"  Loaded {len(df):,} concepts")

    # Filter by vocabulary
    df = df[df['vocabulary_id'].isin(RELEVANT_VOCABULARIES)]
    print(f"  Filtered to {len(df):,} concepts (SNOMED/RxNorm/LOINC only)")

    # Remove concepts with null names
    initial_count = len(df)
    df = df.dropna(subset=['concept_name'])
    removed = initial_count - len(df)
    if removed > 0:
        print(f"  Removed {removed:,} concepts with null names")

    # Ensure column order is consistent (fix for test compatibility)
    df = df[['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept']]

    return df


def load_relationship_mapping() -> dict:
    """
    Load RELATIONSHIP.csv and create mapping of relationship_id -> relationship_name.
    Only includes relationships in the RELEVANT_RELATIONSHIPS whitelist.

    Returns:
        dict: {relationship_id: relationship_name} for relevant relationships only
    """
    print(f"Loading {RELATIONSHIP_FILE.name}...")

    try:
        # Try tab-separated first
        df = pd.read_csv(
            RELATIONSHIP_FILE,
            sep='\t',
            usecols=['relationship_id', 'relationship_name'],
            on_bad_lines='skip'
        )
    except ValueError:
        # Fallback to comma-separated
        df = pd.read_csv(
            RELATIONSHIP_FILE,
            usecols=['relationship_id', 'relationship_name'],
            on_bad_lines='skip'
        )

    print(f"  Loaded {len(df):,} relationship types")

    # Filter to only relevant relationships
    df = df[df['relationship_name'].isin(RELEVANT_RELATIONSHIPS)]
    print(f"  Filtered to {len(df):,} relevant relationship types")

    # Create mapping
    mapping = dict(zip(df['relationship_id'], df['relationship_name']))

    return mapping


def load_concept_relationships(
    valid_concept_ids: set,
    relationship_mapping: dict,
    nrows: int = None
) -> pd.DataFrame:
    """
    Load CONCEPT_RELATIONSHIP.csv with filtering.
    Processes file in chunks to handle large size (1.7 GB).

    Args:
        valid_concept_ids: Set of concept_ids from filtered CONCEPT.csv
        relationship_mapping: Dict of relationship_id -> relationship_name
        nrows: Optional limit on number of rows to read (for testing). None = read all.

    Returns:
        DataFrame with columns: concept_id_1, relationship_name, concept_id_2
    """
    print(f"Loading {CONCEPT_RELATIONSHIP_FILE.name} (processing in chunks)...")
    if nrows:
        print(f"  [TEST MODE] Limiting to first {nrows:,} rows")

    valid_relationship_ids = set(relationship_mapping.keys())
    chunks = []
    total_rows = 0
    filtered_rows = 0

    try:
        # Try tab-separated first
        reader = pd.read_csv(
            CONCEPT_RELATIONSHIP_FILE,
            sep='\t',
            usecols=['concept_id_1', 'concept_id_2', 'relationship_id'],
            dtype={'concept_id_1': 'int32', 'concept_id_2': 'int32'},
            chunksize=CHUNK_SIZE,
            on_bad_lines='skip',
            nrows=nrows
        )
    except ValueError:
        # Fallback to comma-separated
        reader = pd.read_csv(
            CONCEPT_RELATIONSHIP_FILE,
            usecols=['concept_id_1', 'concept_id_2', 'relationship_id'],
            dtype={'concept_id_1': 'int32', 'concept_id_2': 'int32'},
            chunksize=CHUNK_SIZE,
            on_bad_lines='skip',
            nrows=nrows
        )

    for i, chunk in enumerate(reader, 1):
        total_rows += len(chunk)

        # Filter: both concepts must be in valid set, relationship must be relevant
        filtered = chunk[
            chunk['concept_id_1'].isin(valid_concept_ids) &
            chunk['concept_id_2'].isin(valid_concept_ids) &
            chunk['relationship_id'].isin(valid_relationship_ids)
        ]

        filtered_rows += len(filtered)

        if len(filtered) > 0:
            # Map relationship_id to relationship_name
            filtered = filtered.copy()  # Fix SettingWithCopyWarning
            filtered['relationship_name'] = filtered['relationship_id'].map(relationship_mapping)
            filtered = filtered.drop(columns=['relationship_id'])
            # Ensure column order is consistent (fix for test compatibility)
            filtered = filtered[['concept_id_1', 'relationship_name', 'concept_id_2']]
            chunks.append(filtered)

        if i % 10 == 0:
            print(f"  Processed {total_rows:,} rows, kept {filtered_rows:,} relevant relationships...")

    print(f"  Total processed: {total_rows:,} rows")
    print(f"  Kept: {filtered_rows:,} relevant relationships")

    if not chunks:
        print("  WARNING: No relevant relationships found!")
        return pd.DataFrame(columns=['concept_id_1', 'relationship_name', 'concept_id_2'])

    # Concatenate all chunks
    edges_df = pd.concat(chunks, ignore_index=True)

    return edges_df


def preprocess(nrows_concepts: int = None, nrows_relationships: int = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main preprocessing pipeline.

    Args:
        nrows_concepts: Optional limit on CONCEPT.csv rows (for testing). None = read all.
        nrows_relationships: Optional limit on CONCEPT_RELATIONSHIP.csv rows (for testing). None = read all.

    Steps:
        1. Validate input files exist
        2. Load and filter CONCEPT.csv
        3. Load and filter RELATIONSHIP.csv
        4. Load and filter CONCEPT_RELATIONSHIP.csv (by chunks)
        5. Save nodes.csv and edges.csv

    Returns:
        Tuple of (nodes_df, edges_df)
    """
    print("=" * 60)
    print("OMOP Preprocessing Pipeline")
    if nrows_concepts or nrows_relationships:
        print("[TEST MODE - LIMITED ROWS]")
    print("=" * 60)

    # Step 1: Validate
    validate_input_files()
    print()

    # Step 2: Load concepts
    nodes_df = load_concept_data(nrows=nrows_concepts)
    print()

    # Step 3: Load relationship mapping
    relationship_mapping = load_relationship_mapping()
    print()

    # Step 4: Load concept relationships
    valid_concept_ids = set(nodes_df['concept_id'].values)
    edges_df = load_concept_relationships(valid_concept_ids, relationship_mapping, nrows=nrows_relationships)
    print()

    # Step 5: Save output files
    print("Saving output files...")
    nodes_df.to_csv(OUTPUT_NODES, index=False)
    print(f"  [OK] Saved {OUTPUT_NODES} ({len(nodes_df):,} nodes)")

    edges_df.to_csv(OUTPUT_EDGES, index=False)
    print(f"  [OK] Saved {OUTPUT_EDGES} ({len(edges_df):,} edges)")
    print()

    # Statistics
    print("=" * 60)
    print("Preprocessing Complete")
    print("=" * 60)
    print(f"Nodes: {len(nodes_df):,}")
    print(f"  - SNOMED: {len(nodes_df[nodes_df['vocabulary_id'] == 'SNOMED']):,}")
    print(f"  - RxNorm: {len(nodes_df[nodes_df['vocabulary_id'] == 'RxNorm']):,}")
    print(f"  - LOINC: {len(nodes_df[nodes_df['vocabulary_id'] == 'LOINC']):,}")
    print(f"  - RxNorm Extension: {len(nodes_df[nodes_df['vocabulary_id'] == 'RxNorm Extension']):,}")
    print(f"  - Standard concepts: {len(nodes_df[nodes_df['standard_concept'] == 'S']):,}")
    print(f"  - Non-standard concepts: {len(nodes_df[nodes_df['standard_concept'] != 'S']):,}")
    print(f"\nEdges: {len(edges_df):,}")
    print(f"\nTop 5 relationship types:")
    if len(edges_df) > 0:
        top_rels = edges_df['relationship_name'].value_counts().head()
        for rel, count in top_rels.items():
            print(f"  - {rel}: {count:,}")
    print("=" * 60)

    return nodes_df, edges_df


if __name__ == '__main__':
    # Run preprocessing
    # For testing with limited data, uncomment and adjust these values:
    # Small test: 100k concepts, 2M relationships (~2-3 minutes)
    # Medium test: 500k concepts, 10M relationships (~10-15 minutes)
    # Full: None, None (~55+ minutes)

    # Current mode - FULL DATASET (complete graph with all relationships)
    TEST_CONCEPTS = None              # None = ALL concepts (~3.8M after filtering)
    TEST_RELATIONSHIPS = None         # None = ALL relationships (~17M after filtering)

    try:
        nodes_df, edges_df = preprocess(
            nrows_concepts=TEST_CONCEPTS,
            nrows_relationships=TEST_RELATIONSHIPS
        )
        print("\n[SUCCESS] Preprocessing successful!")
    except Exception as e:
        print(f"\n[ERROR] Preprocessing failed: {e}")
        raise
