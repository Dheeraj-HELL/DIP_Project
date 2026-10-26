"""
Example script demonstrating how to use the adaptive compression on real images.
This script shows common use cases and best practices.
"""

import cv2
import numpy as np
from adaptive_compression import (
    AdaptiveImageCompressor,
    calculate_psnr,
    calculate_mse,
    calculate_ssim
)
import os


def example_single_image_compression():
    """Example: Compress a single image and display results."""
    print("="*70)
    print("Example 1: Single Image Compression")
    print("="*70)

    # Create compressor
    compressor = AdaptiveImageCompressor(block_size=8)

    # Load image (replace with your image path)
    image_path = "test_image.png"  # Created by test_compression.py

    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        print("Run 'python test_compression.py' first to generate test images.")
        return

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    print(f"\nLoaded image: {image_path}")
    print(f"Size: {image.shape}")
    print(f"Original size: {image.nbytes:,} bytes ({image.nbytes/1024:.2f} KB)")

    # Compress with adaptive method
    quality = 75
    print(f"\nCompressing with quality={quality}...")
    compressed = compressor.compress_adaptive(image, quality=quality)

    # Get compressed size
    compressed_size = compressor.get_compressed_size(compressed)
    ratio = image.nbytes / compressed_size

    print(f"Compressed size: {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)")
    print(f"Compression ratio: {ratio:.2f}x")

    # Decompress
    reconstructed = compressor.decompress(compressed)

    # Calculate quality metrics
    psnr = calculate_psnr(image, reconstructed)
    mse = calculate_mse(image, reconstructed)
    ssim = calculate_ssim(image, reconstructed)

    print(f"\nQuality Metrics:")
    print(f"  PSNR: {psnr:.2f} dB")
    print(f"  MSE: {mse:.2f}")
    print(f"  SSIM: {ssim:.4f}")

    # Save results
    cv2.imwrite("example_reconstructed.png", reconstructed)
    compressor.save_compressed(compressed, "example_compressed.pkl")
    print(f"\nSaved files:")
    print(f"  - example_reconstructed.png")
    print(f"  - example_compressed.pkl")


def example_quality_comparison():
    """Example: Compare different quality settings."""
    print("\n" + "="*70)
    print("Example 2: Quality Comparison (Different Settings)")
    print("="*70)

    image_path = "test_image.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    compressor = AdaptiveImageCompressor(block_size=8)

    quality_levels = [30, 50, 75, 90]

    print(f"\n{'Quality':<10} {'Size (KB)':<12} {'Ratio':<10} {'PSNR (dB)':<12} {'SSIM'}")
    print("-"*60)

    for quality in quality_levels:
        # Compress
        compressed = compressor.compress_adaptive(image, quality=quality)
        reconstructed = compressor.decompress(compressed)

        # Metrics
        size = compressor.get_compressed_size(compressed)
        ratio = image.nbytes / size
        psnr = calculate_psnr(image, reconstructed)
        ssim = calculate_ssim(image, reconstructed)

        print(f"{quality:<10} {size/1024:<12.2f} {ratio:<10.2f} {psnr:<12.2f} {ssim:.4f}")


def example_adaptive_vs_standard():
    """Example: Compare adaptive vs standard compression."""
    print("\n" + "="*70)
    print("Example 3: Adaptive vs Standard Compression")
    print("="*70)

    image_path = "test_image.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    compressor = AdaptiveImageCompressor(block_size=8)

    quality = 75
    print(f"\nCompressing with quality={quality}...")

    # Adaptive compression
    compressed_adaptive = compressor.compress_adaptive(image, quality=quality)
    reconstructed_adaptive = compressor.decompress(compressed_adaptive)

    size_adaptive = compressor.get_compressed_size(compressed_adaptive)
    psnr_adaptive = calculate_psnr(image, reconstructed_adaptive)
    ssim_adaptive = calculate_ssim(image, reconstructed_adaptive)

    # Standard compression
    compressed_standard = compressor.compress_standard(image, quality=quality)
    reconstructed_standard = compressor.decompress(compressed_standard)

    size_standard = compressor.get_compressed_size(compressed_standard)
    psnr_standard = calculate_psnr(image, reconstructed_standard)
    ssim_standard = calculate_ssim(image, reconstructed_standard)

    # Display comparison
    print(f"\n{'Metric':<25} {'Adaptive':<15} {'Standard':<15} {'Winner'}")
    print("-"*70)
    print(f"{'Size (KB)':<25} {size_adaptive/1024:<15.2f} {size_standard/1024:<15.2f} {'Adaptive' if size_adaptive < size_standard else 'Standard'}")
    print(f"{'Ratio':<25} {image.nbytes/size_adaptive:<15.2f} {image.nbytes/size_standard:<15.2f} {'Adaptive' if size_adaptive < size_standard else 'Standard'}")
    print(f"{'PSNR (dB)':<25} {psnr_adaptive:<15.2f} {psnr_standard:<15.2f} {'Adaptive' if psnr_adaptive > psnr_standard else 'Standard'}")
    print(f"{'SSIM':<25} {ssim_adaptive:<15.4f} {ssim_standard:<15.4f} {'Adaptive' if ssim_adaptive > ssim_standard else 'Standard'}")

    # Save both reconstructions for visual comparison
    cv2.imwrite("example_adaptive.png", reconstructed_adaptive)
    cv2.imwrite("example_standard.png", reconstructed_standard)
    print(f"\nSaved comparison images:")
    print(f"  - example_adaptive.png")
    print(f"  - example_standard.png")


def example_load_and_decompress():
    """Example: Load compressed data and decompress."""
    print("\n" + "="*70)
    print("Example 4: Load and Decompress Saved File")
    print("="*70)

    compressed_file = "example_compressed.pkl"

    if not os.path.exists(compressed_file):
        print(f"Error: {compressed_file} not found.")
        print("Run Example 1 first to generate the compressed file.")
        return

    compressor = AdaptiveImageCompressor()

    print(f"\nLoading compressed file: {compressed_file}")
    compressed_data = compressor.load_compressed(compressed_file)

    print(f"Compressed data info:")
    print(f"  Method: {compressed_data['method']}")
    print(f"  Original shape: {compressed_data['original_shape']}")
    print(f"  Block size: {compressed_data['block_size']}")
    print(f"  Number of blocks: {len(compressed_data['blocks'])}")

    print(f"\nDecompressing...")
    reconstructed = compressor.decompress(compressed_data)

    print(f"Reconstructed image shape: {reconstructed.shape}")
    print(f"Min pixel value: {reconstructed.min()}")
    print(f"Max pixel value: {reconstructed.max()}")

    cv2.imwrite("example_loaded_reconstructed.png", reconstructed)
    print(f"\nSaved: example_loaded_reconstructed.png")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ADAPTIVE IMAGE COMPRESSION - USAGE EXAMPLES")
    print("="*70)
    print("\nThis script demonstrates common use cases for the compression library.")
    print("Make sure you've run 'python test_compression.py' first to generate")
    print("test images, or replace image paths with your own images.")
    print()

    try:
        # Run examples
        example_single_image_compression()
        example_quality_comparison()
        example_adaptive_vs_standard()
        example_load_and_decompress()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        print("\nGenerated files:")
        print("  - example_reconstructed.png")
        print("  - example_compressed.pkl")
        print("  - example_adaptive.png")
        print("  - example_standard.png")
        print("  - example_loaded_reconstructed.png")
        print("\nNext: Run 'python gui.py' for the interactive GUI application")
        print("="*70)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Installed dependencies: pip install -r requirements.txt")
        print("2. Run test script first: python test_compression.py")


if __name__ == "__main__":
    main()
