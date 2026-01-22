"""
clear_gpu.py - Clear GPU memory cache

Run this script before generating embeddings to ensure clean GPU state.
"""
import torch
import gc

print("=" * 60)
print("CLEARING GPU MEMORY")
print("=" * 60)

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory allocated before: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
    print(f"Memory reserved before: {torch.cuda.memory_reserved(0) / 1024**2:.1f} MB")

    # Clear cache
    torch.cuda.empty_cache()

    # Force garbage collection
    gc.collect()

    # Reset peak memory stats
    torch.cuda.reset_peak_memory_stats(0)
    torch.cuda.reset_accumulated_memory_stats(0)

    print("\n✅ GPU cache cleared")
    print(f"Memory allocated after: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
    print(f"Memory reserved after: {torch.cuda.memory_reserved(0) / 1024**2:.1f} MB")
else:
    print("⚠️  No GPU detected - nothing to clear")

print("=" * 60)
