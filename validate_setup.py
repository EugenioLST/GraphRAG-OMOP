"""
validate_setup.py - Validate project setup without running full preprocessing

Checks:
- Required files exist
- Basic file structure
- Dependencies installed
"""

from pathlib import Path
import sys


def check_data_files():
    """Check if OMOP data files exist"""
    print("Checking OMOP data files...")

    data_dir = Path('data')
    required_files = ['CONCEPT.csv', 'RELATIONSHIP.csv', 'CONCEPT_RELATIONSHIP.csv']

    all_exist = True
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  [OK] {filename} ({size_mb:.1f} MB)")
        else:
            print(f"  [MISSING] {filename}")
            all_exist = False

    return all_exist


def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking dependencies...")

    required_packages = [
        'pandas',
        'networkx',
        'numpy',
        'pytest',
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            all_installed = False

    return all_installed


def check_project_structure():
    """Check if project directories and files are in place"""
    print("\nChecking project structure...")

    required_items = [
        ('preprocess.py', 'file'),
        ('graph.py', 'file'),
        ('tests/', 'dir'),
        ('tests/test_preprocess.py', 'file'),
        ('tests/test_graph.py', 'file'),
        ('context/', 'dir'),
        ('context/CLAUDE.md', 'file'),
        ('context/ARCHITECTURE.md', 'file'),
    ]

    all_exist = True
    for item_name, item_type in required_items:
        item_path = Path(item_name)
        if item_type == 'file':
            exists = item_path.is_file()
        else:
            exists = item_path.is_dir()

        if exists:
            print(f"  [OK] {item_name}")
        else:
            print(f"  [MISSING] {item_name}")
            all_exist = False

    return all_exist


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("GraphRAG-OMOP Project Validation")
    print("=" * 60)
    print()

    data_ok = check_data_files()
    deps_ok = check_dependencies()
    structure_ok = check_project_structure()

    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"Data files: {'[OK]' if data_ok else '[INCOMPLETE]'}")
    print(f"Dependencies: {'[OK]' if deps_ok else '[INCOMPLETE]'}")
    print(f"Project structure: {'[OK]' if structure_ok else '[INCOMPLETE]'}")
    print()

    if data_ok and deps_ok and structure_ok:
        print("[SUCCESS] Project setup is complete!")
        print("\nNext steps:")
        print("  1. Run: python preprocess.py (make sure data/CONCEPT.csv is not open)")
        print("  2. Run: python graph.py")
        print("  3. Run: pytest tests/ -v")
        return 0
    else:
        print("[WARNING] Some items are missing. Check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
