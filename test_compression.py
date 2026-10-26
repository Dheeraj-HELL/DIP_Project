"""
Test script for adaptive compression implementation.
Creates a synthetic test image and verifies the compression pipeline.
"""

import numpy as np
import cv2
from adaptive_compression import (
    AdaptiveImageCompressor,
    calculate_psnr,
    calculate_mse,
    calculate_ssim
)


def create_test_image():
    """Create a synthetic test image with varying complexity regions."""
    # Create 512x512 test image
    image = np.zeros((512, 512), dtype=np.uint8)

    # Smooth gradient region (low complexity)
    for i in range(256):
        image[0:256, i] = int(i * 255 / 255)

    # Textured region (high complexity)
    texture = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    image[0:256, 256:512] = texture

    # Sharp edges (high complexity)
    image[256:512, 0:256] = 255
    cv2.rectangle(image, (50, 300), (200, 450), 0, -1)
    cv2.circle(image, (128, 400), 50, 128, -1)

    # Smooth region (low complexity)
    image[256:512, 256:512] = 200

    return image


def test_compression():
    """Test the compression pipeline."""
    print("="*70)
    print("Testing Adaptive Image Compression Implementation")
    print("="*70)

    # Create test image
    print("\n1. Creating synthetic test image...")
    test_image = create_test_image()
    print(f"   Image shape: {test_image.shape}")
    print(f"   Image size: {test_image.nbytes} bytes")

    # Save test image
    cv2.imwrite("test_image.png", test_image)
    print("   Saved as: test_image.png")

    # Initialize compressor
    print("\n2. Initializing compressor...")
    compressor = AdaptiveImageCompressor(block_size=8)
    print("   Compressor ready (block_size=8)")

    # Test adaptive compression
    print("\n3. Testing ADAPTIVE compression (Quality=75)...")
    try:
        compressed_adaptive = compressor.compress_adaptive(test_image, quality=75)
        print("   [OK] Compression successful")
        print(f"   - Number of blocks: {len(compressed_adaptive['blocks'])}")
        print(f"   - Padded shape: {compressed_adaptive['padded_shape']}")

        reconstructed_adaptive = compressor.decompress(compressed_adaptive)
        print("   [OK] Decompression successful")
        print(f"   - Reconstructed shape: {reconstructed_adaptive.shape}")

        # Calculate metrics
        adaptive_size = compressor.get_compressed_size(compressed_adaptive)
        adaptive_ratio = test_image.nbytes / adaptive_size
        adaptive_psnr = calculate_psnr(test_image, reconstructed_adaptive)
        adaptive_mse = calculate_mse(test_image, reconstructed_adaptive)
        adaptive_ssim = calculate_ssim(test_image, reconstructed_adaptive)

        print(f"\n   Adaptive Results:")
        print(f"   - Compressed size: {adaptive_size:,} bytes ({adaptive_size/1024:.2f} KB)")
        print(f"   - Compression ratio: {adaptive_ratio:.2f}x")
        print(f"   - PSNR: {adaptive_psnr:.2f} dB")
        print(f"   - MSE: {adaptive_mse:.2f}")
        print(f"   - SSIM: {adaptive_ssim:.4f}")

        cv2.imwrite("test_reconstructed_adaptive.png", reconstructed_adaptive)
        print("   - Saved: test_reconstructed_adaptive.png")

    except Exception as e:
        print(f"   [FAIL] Adaptive compression failed: {e}")
        return False

    # Test standard compression
    print("\n4. Testing STANDARD compression (Quality=75)...")
    try:
        compressed_standard = compressor.compress_standard(test_image, quality=75)
        print("   [OK] Compression successful")

        reconstructed_standard = compressor.decompress(compressed_standard)
        print("   [OK] Decompression successful")

        # Calculate metrics
        standard_size = compressor.get_compressed_size(compressed_standard)
        standard_ratio = test_image.nbytes / standard_size
        standard_psnr = calculate_psnr(test_image, reconstructed_standard)
        standard_mse = calculate_mse(test_image, reconstructed_standard)
        standard_ssim = calculate_ssim(test_image, reconstructed_standard)

        print(f"\n   Standard Results:")
        print(f"   - Compressed size: {standard_size:,} bytes ({standard_size/1024:.2f} KB)")
        print(f"   - Compression ratio: {standard_ratio:.2f}x")
        print(f"   - PSNR: {standard_psnr:.2f} dB")
        print(f"   - MSE: {standard_mse:.2f}")
        print(f"   - SSIM: {standard_ssim:.4f}")

        cv2.imwrite("test_reconstructed_standard.png", reconstructed_standard)
        print("   - Saved: test_reconstructed_standard.png")

    except Exception as e:
        print(f"   [FAIL] Standard compression failed: {e}")
        return False

    # Comparison
    print("\n5. Comparison:")
    print(f"   {'Metric':<25} {'Adaptive':<15} {'Standard':<15} {'Winner'}")
    print("   " + "-"*65)
    print(f"   {'Compressed Size (KB)':<25} {adaptive_size/1024:<15.2f} {standard_size/1024:<15.2f} {'Adaptive' if adaptive_size < standard_size else 'Standard'}")
    print(f"   {'Compression Ratio':<25} {adaptive_ratio:<15.2f} {standard_ratio:<15.2f} {'Adaptive' if adaptive_ratio > standard_ratio else 'Standard'}")
    print(f"   {'PSNR (dB)':<25} {adaptive_psnr:<15.2f} {standard_psnr:<15.2f} {'Adaptive' if adaptive_psnr > standard_psnr else 'Standard'}")
    print(f"   {'MSE':<25} {adaptive_mse:<15.2f} {standard_mse:<15.2f} {'Adaptive' if adaptive_mse < standard_mse else 'Standard'}")
    print(f"   {'SSIM':<25} {adaptive_ssim:<15.4f} {standard_ssim:<15.4f} {'Adaptive' if adaptive_ssim > standard_ssim else 'Standard'}")

    # Test save/load
    print("\n6. Testing save/load functionality...")
    try:
        compressor.save_compressed(compressed_adaptive, "test_compressed.pkl")
        print("   [OK] Saved compressed data")

        loaded_compressed = compressor.load_compressed("test_compressed.pkl")
        print("   [OK] Loaded compressed data")

        reconstructed_loaded = compressor.decompress(loaded_compressed)
        print("   [OK] Decompressed loaded data")

        # Verify it's identical
        if np.array_equal(reconstructed_adaptive, reconstructed_loaded):
            print("   [OK] Loaded reconstruction matches original")
        else:
            print("   [FAIL] Loaded reconstruction differs!")
            return False

    except Exception as e:
        print(f"   [FAIL] Save/load failed: {e}")
        return False

    print("\n" + "="*70)
    print("[SUCCESS] ALL TESTS PASSED")
    print("="*70)
    print("\nGenerated files:")
    print("  - test_image.png (original synthetic image)")
    print("  - test_reconstructed_adaptive.png (adaptive compression)")
    print("  - test_reconstructed_standard.png (standard compression)")
    print("  - test_compressed.pkl (compressed data file)")
    print("\nNext step: Run 'python gui.py' to test the GUI application")
    print("="*70)

    return True


if __name__ == "__main__":
    success = test_compression()
    exit(0 if success else 1)
