"""
embeddings.py - Generate and cache concept embeddings using SapBERT

This module generates semantic embeddings for OMOP concept names using the
SapBERT model (cambridgeltl/SapBERT-from-PubMedBERT-fulltext), which is
specifically trained on medical terminology (UMLS).

Key Features:
- Batch processing with progress bars
- Support for subset testing (max_concepts parameter)
- Caching for fast subsequent loads
- GPU acceleration (CUDA) with automatic fallback to CPU

Performance Estimates:
- GPU (CUDA): 10k concepts: ~30s | 100k: ~5min | 3.8M: ~45-60min
- CPU: 10k concepts: ~1-2min | 100k: ~10-15min | 3.8M: ~4-8hours

Output:
- embeddings.npy: numpy array (N x 768 dimensions)
- concept_id_to_index.pkl: mapping from concept_id to embedding row index
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# Fix Windows console encoding for progress bars
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def load_sapbert_model():
    """
    Load pre-trained SapBERT model from HuggingFace.

    Model: cambridgeltl/SapBERT-from-PubMedBERT-fulltext
    - Base: PubMedBERT (biomedical literature)
    - Fine-tuned on: UMLS synonyms (medical concepts)
    - Embedding dim: 768
    - Max tokens: 512
    - Size: ~440 MB

    Returns:
        SentenceTransformer: Loaded model ready for encoding
    """
    print("\n" + "=" * 70)
    print("LOADING SAPBERT MODEL")
    print("=" * 70)
    print("Model: cambridgeltl/SapBERT-from-PubMedBERT-fulltext")
    print("This may take a few minutes on first run (downloads ~440 MB)\n")

    # Detect available device
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"🚀 GPU DETECTED: {gpu_name}")
        print(f"   VRAM: {gpu_memory:.1f} GB")
        print(f"   CUDA Version: {torch.version.cuda}")
    else:
        device = 'cpu'
        print("⚠️  GPU NOT AVAILABLE - Using CPU")
        print("   To enable GPU acceleration:")
        print("   pip install torch --index-url https://download.pytorch.org/whl/cu124")

    print(f"\n🔧 Loading model on device: {device.upper()}")

    # Load model with explicit device
    model = SentenceTransformer('cambridgeltl/SapBERT-from-PubMedBERT-fulltext', device=device)

    print(f"✅ Model loaded successfully on: {model.device}")
    print("=" * 70 + "\n")

    return model


def generate_embeddings(model, concept_names, batch_size=None, show_progress=True):
    """
    Generate embeddings for a list of concept names.

    Args:
        model: SentenceTransformer model
        concept_names: List of concept name strings
        batch_size: Number of concepts to process at once (default: auto-detect based on device)
        show_progress: Show progress bar (default: True)

    Returns:
        numpy.ndarray: Array of shape (N, 768) with embeddings
    """
    # Auto-detect optimal batch size based on device
    if batch_size is None:
        # Conservative batch size works well for both GPU and CPU
        batch_size = 256

    print("\n" + "=" * 70)
    print("GENERATING EMBEDDINGS")
    print("=" * 70)
    print(f"Total concepts: {len(concept_names):,}")
    print(f"Device: {model.device}")
    print(f"Batch size: {batch_size}")

    if torch.cuda.is_available():
        print(f"GPU Memory before: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")

    # Encode in batches with progress bar
    embeddings = model.encode(
        concept_names,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=False  # We'll use raw embeddings for cosine similarity
    )

    print(f"\n✅ Generated embeddings: shape {embeddings.shape}")

    if torch.cuda.is_available():
        print(f"   GPU Memory after: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
        print(f"   GPU Memory peak: {torch.cuda.max_memory_allocated(0) / 1024**2:.1f} MB")

    print("=" * 70 + "\n")

    return embeddings


def build_embedding_index(nodes_csv_path='data/processed/nodes.csv', output_dir='data/embeddings', max_concepts=None):
    """
    Build embedding index from nodes.csv and save to disk.

    This function:
    1. Loads concept data from nodes.csv
    2. Optionally limits to first max_concepts (for testing)
    3. Generates embeddings using SapBERT
    4. Saves embeddings.npy and concept_id_to_index.pkl

    Args:
        nodes_csv_path: Path to nodes.csv (default: 'nodes.csv')
        output_dir: Directory to save outputs (default: '.')
        max_concepts: Maximum number of concepts to process (default: None = all)
                     Use 10000 for small test, 100000 for medium test

    Output Files:
        {output_dir}/embeddings.npy: numpy array (N x 768)
        {output_dir}/concept_id_to_index.pkl: dict mapping concept_id -> row index

    Returns:
        tuple: (embeddings array, concept_id_to_index dict)
    """
    print("=" * 70)
    print("BUILDING EMBEDDING INDEX")
    print("=" * 70)

    # Load nodes.csv
    print(f"\nLoading concepts from: {nodes_csv_path}")

    if max_concepts:
        print(f"⚠ SUBSET MODE: Processing first {max_concepts:,} concepts only")
        nodes_df = pd.read_csv(nodes_csv_path, nrows=max_concepts)
    else:
        nodes_df = pd.read_csv(nodes_csv_path)

    print(f"✓ Loaded {len(nodes_df):,} concepts")

    # Extract concept_id and concept_name
    concept_ids = nodes_df['concept_id'].tolist()
    concept_names = nodes_df['concept_name'].tolist()

    # Create mapping: concept_id -> embedding row index
    concept_id_to_index = {concept_id: idx for idx, concept_id in enumerate(concept_ids)}

    print(f"\nConcept ID range: {min(concept_ids)} to {max(concept_ids)}")
    print(f"Sample concepts:")
    for i in range(min(5, len(concept_names))):
        print(f"  {concept_ids[i]}: {concept_names[i][:60]}...")

    # Load SapBERT model
    model = load_sapbert_model()

    # Generate embeddings (batch_size=None triggers auto-detection: 512 for GPU, 256 for CPU)
    embeddings = generate_embeddings(
        model=model,
        concept_names=concept_names,
        batch_size=None,  # Auto-detect optimal batch size based on device
        show_progress=True
    )

    # Save to disk
    embeddings_path = os.path.join(output_dir, 'embeddings.npy')
    mapping_path = os.path.join(output_dir, 'concept_id_to_index.pkl')

    print("\n" + "=" * 70)
    print("SAVING TO DISK")
    print("=" * 70)
    print(f"Saving embeddings to: {embeddings_path}")
    print(f"(This may take a few minutes for large files...)")
    np.save(embeddings_path, embeddings)
    print("✓ Embeddings saved")

    print(f"\nSaving mapping to: {mapping_path}")
    with open(mapping_path, 'wb') as f:
        pickle.dump(concept_id_to_index, f)
    print("✓ Mapping saved")

    # Calculate file sizes
    embeddings_size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
    mapping_size_mb = os.path.getsize(mapping_path) / (1024 * 1024)

    print(f"\n✅ Embedding index built successfully!")
    print(f"  Embeddings file: {embeddings_size_mb:.1f} MB")
    print(f"  Mapping file: {mapping_size_mb:.1f} MB")
    print(f"  Total disk usage: {embeddings_size_mb + mapping_size_mb:.1f} MB")
    print("=" * 70)

    return embeddings, concept_id_to_index


def load_embeddings(output_dir='data'):
    """
    Load cached embeddings from disk.

    Args:
        output_dir: Directory containing embeddings.npy and concept_id_to_index.pkl

    Returns:
        tuple: (embeddings array, concept_id_to_index dict)

    Raises:
        FileNotFoundError: If embedding files don't exist
    """
    embeddings_path = os.path.join(output_dir, 'embeddings.npy')
    mapping_path = os.path.join(output_dir, 'concept_id_to_index.pkl')

    # Check if files exist
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(
            f"Embeddings file not found: {embeddings_path}\n"
            f"Run build_embedding_index() first to generate embeddings."
        )

    if not os.path.exists(mapping_path):
        raise FileNotFoundError(
            f"Mapping file not found: {mapping_path}\n"
            f"Run build_embedding_index() first to generate embeddings."
        )

    print(f"Loading embeddings from: {embeddings_path}")
    embeddings = np.load(embeddings_path)

    print(f"Loading mapping from: {mapping_path}")
    with open(mapping_path, 'rb') as f:
        concept_id_to_index = pickle.load(f)

    print(f"✓ Loaded {len(concept_id_to_index):,} concept embeddings (shape: {embeddings.shape})")

    return embeddings, concept_id_to_index


def main():
    """
    Main entry point for command-line usage.

    Usage:
        # Generate embeddings for 10k concepts (small test)
        python embeddings.py --max-concepts 10000

        # Generate embeddings for 100k concepts (medium test)
        python embeddings.py --max-concepts 100000

        # Generate embeddings for all concepts (full dataset)
        python embeddings.py
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate semantic embeddings for OMOP concepts using SapBERT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Small test (10k concepts, ~1-2 minutes)
  python embeddings.py --max-concepts 10000

  # Medium test (100k concepts, ~10-15 minutes)
  python embeddings.py --max-concepts 100000

  # Full dataset (3.8M concepts, ~4-8 hours on CPU)
  python embeddings.py
        """
    )

    parser.add_argument(
        '--nodes-csv',
        default='data/processed/nodes.csv',
        help='Path to nodes.csv file (default: data/processed/nodes.csv)'
    )

    parser.add_argument(
        '--output-dir',
        default='data/embeddings',
        help='Directory to save embeddings (default: data/embeddings/)'
    )

    parser.add_argument(
        '--max-concepts',
        type=int,
        default=None,
        help='Maximum number of concepts to process (default: all). Use 10000 for small test, 100000 for medium test.'
    )

    args = parser.parse_args()

    # Build embedding index
    try:
        embeddings, concept_id_to_index = build_embedding_index(
            nodes_csv_path=args.nodes_csv,
            output_dir=args.output_dir,
            max_concepts=args.max_concepts
        )

        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print(f"\nEmbeddings ready for {len(concept_id_to_index):,} concepts")
        print(f"You can now use retrieve.py for semantic search")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == '__main__':
    main()
