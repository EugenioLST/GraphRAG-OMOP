"""
Debug script to check what relationship names are available in RELATIONSHIP.csv
"""
import pandas as pd
from pathlib import Path

# Load RELATIONSHIP.csv
RELATIONSHIP_FILE = Path('data') / 'RELATIONSHIP.csv'

print("Loading RELATIONSHIP.csv to check available relationship names...")

try:
    # Try tab-separated first
    df = pd.read_csv(RELATIONSHIP_FILE, sep='\t', on_bad_lines='skip')
except ValueError:
    # Fallback to comma-separated
    df = pd.read_csv(RELATIONSHIP_FILE, on_bad_lines='skip')

print(f"Total relationships: {len(df)}")
print("\nAll available relationship names:")
print("=" * 50)

for name in sorted(df['relationship_name'].unique()):
    print(f"  '{name}'")

print("\n" + "=" * 50)

# Check which ones from our RELEVANT_RELATIONSHIPS list are actually present
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

available_names = set(df['relationship_name'].unique())
found = RELEVANT_RELATIONSHIPS.intersection(available_names)
not_found = RELEVANT_RELATIONSHIPS - available_names

print(f"\nFrom our RELEVANT_RELATIONSHIPS ({len(RELEVANT_RELATIONSHIPS)} total):")
print(f"  Found: {len(found)} relationships")
for name in sorted(found):
    print(f"    ✓ '{name}'")

print(f"  NOT Found: {len(not_found)} relationships")
for name in sorted(not_found):
    print(f"    ✗ '{name}'")