"""
Content-Aware Image Compression Using Adaptive Frequency-Domain Processing
This module implements adaptive DCT-based image compression with content analysis.
"""

import numpy as np
import cv2
from scipy.fftpack import dct, idct
from typing import Tuple, Dict
import pickle


class AdaptiveImageCompressor:
    """
    Implements content-aware image compression using adaptive DCT-based quantization.

    The algorithm analyzes local image complexity (variance, edge strength) and applies
    stronger compression to smooth regions while preserving detail in complex areas.
    """

    def __init__(self, block_size: int = 8):
        """
        Initialize the compressor with specified block size.

        Args:
            block_size: Size of DCT blocks (default: 8x8 as in JPEG)
        """
        self.block_size = block_size

        # Standard JPEG quantization matrix (luminance)
        self.base_quantization_matrix = np.array([
            [16, 11, 10, 16, 24, 40, 51, 61],
            [12, 12, 14, 19, 26, 58, 60, 55],
            [14, 13, 16, 24, 40, 57, 69, 56],
            [14, 17, 22, 29, 51, 87, 80, 62],
            [18, 22, 37, 56, 68, 109, 103, 77],
            [24, 35, 55, 64, 81, 104, 113, 92],
            [49, 64, 78, 87, 103, 121, 120, 101],
            [72, 92, 95, 98, 112, 100, 103, 99]
        ], dtype=np.float32)

    def dct2d(self, block: np.ndarray) -> np.ndarray:
        """
        Apply 2D Discrete Cosine Transform to a block.

        Args:
            block: Input block (typically 8x8)

        Returns:
            DCT coefficients
        """
        return dct(dct(block.T, norm='ortho').T, norm='ortho')

    def idct2d(self, block: np.ndarray) -> np.ndarray:
        """
        Apply 2D Inverse Discrete Cosine Transform to a block.

        Args:
            block: DCT coefficients

        Returns:
            Reconstructed spatial domain block
        """
        return idct(idct(block.T, norm='ortho').T, norm='ortho')

    def calculate_block_complexity(self, block: np.ndarray) -> float:
        """
        Calculate the complexity of a block using variance and edge strength.

        Args:
            block: Image block

        Returns:
            Complexity score (higher = more detail/edges)
        """
        # Variance measures local detail
        variance = np.var(block)

        # Sobel edge detection for edge strength
        sobel_x = cv2.Sobel(block, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(block, cv2.CV_64F, 0, 1, ksize=3)
        edge_strength = np.mean(np.sqrt(sobel_x**2 + sobel_y**2))

        # Combined complexity metric
        complexity = 0.6 * variance + 0.4 * edge_strength
        return complexity

    def get_adaptive_quantization_matrix(self, complexity: float, quality_factor: int) -> np.ndarray:
        """
        Generate adaptive quantization matrix based on block complexity.

        Args:
            complexity: Block complexity score
            quality_factor: Base quality factor (1-100, higher = better quality)

        Returns:
            Adaptive quantization matrix
        """
        # Normalize quality factor to scaling factor
        if quality_factor < 50:
            scale = 5000 / quality_factor
        else:
            scale = 200 - 2 * quality_factor

        scale = max(1, scale)

        # Adaptive scaling based on complexity
        # High complexity (edges/details) -> lower quantization (preserve detail)
        # Low complexity (smooth) -> higher quantization (more compression)
        complexity_threshold = 100  # Adjust based on image characteristics

        if complexity > complexity_threshold:
            # Preserve detail: reduce quantization
            adaptive_scale = scale * 0.5
        elif complexity > complexity_threshold * 0.5:
            # Medium detail: moderate quantization
            adaptive_scale = scale * 0.75
        else:
            # Smooth region: aggressive quantization
            adaptive_scale = scale * 1.5

        quant_matrix = np.floor((self.base_quantization_matrix * adaptive_scale + 50) / 100)
        quant_matrix = np.clip(quant_matrix, 1, 255)

        return quant_matrix

    def get_standard_quantization_matrix(self, quality_factor: int) -> np.ndarray:
        """
        Generate standard (non-adaptive) quantization matrix.

        Args:
            quality_factor: Quality factor (1-100)

        Returns:
            Standard quantization matrix
        """
        if quality_factor < 50:
            scale = 5000 / quality_factor
        else:
            scale = 200 - 2 * quality_factor

        scale = max(1, scale)
        quant_matrix = np.floor((self.base_quantization_matrix * scale + 50) / 100)
        quant_matrix = np.clip(quant_matrix, 1, 255)

        return quant_matrix

    def compress_adaptive(self, image: np.ndarray, quality: int = 75) -> Dict:
        """
        Compress image using adaptive quantization based on content analysis.

        Args:
            image: Input grayscale image
            quality: Quality factor (1-100, higher = better quality)

        Returns:
            Dictionary containing compressed data and metadata
        """
        height, width = image.shape

        # Pad image to be divisible by block_size
        pad_height = (self.block_size - height % self.block_size) % self.block_size
        pad_width = (self.block_size - width % self.block_size) % self.block_size

        padded_image = np.pad(image, ((0, pad_height), (0, pad_width)), mode='edge')
        padded_height, padded_width = padded_image.shape

        # Storage for compressed data
        quantized_blocks = []
        quantization_matrices = []
        complexity_map = np.zeros((padded_height // self.block_size,
                                   padded_width // self.block_size))

        # Process each block
        for i in range(0, padded_height, self.block_size):
            for j in range(0, padded_width, self.block_size):
                block = padded_image[i:i+self.block_size, j:j+self.block_size].astype(np.float32)

                # Shift to center around zero
                block = block - 128

                # Calculate complexity
                complexity = self.calculate_block_complexity(block + 128)
                complexity_map[i//self.block_size, j//self.block_size] = complexity

                # Apply DCT
                dct_block = self.dct2d(block)

                # Get adaptive quantization matrix
                quant_matrix = self.get_adaptive_quantization_matrix(complexity, quality)

                # Quantize
                quantized_block = np.round(dct_block / quant_matrix)

                quantized_blocks.append(quantized_block)
                quantization_matrices.append(quant_matrix)

        compressed_data = {
            'blocks': quantized_blocks,
            'quant_matrices': quantization_matrices,
            'original_shape': (height, width),
            'padded_shape': (padded_height, padded_width),
            'block_size': self.block_size,
            'complexity_map': complexity_map,
            'method': 'adaptive'
        }

        return compressed_data

    def compress_standard(self, image: np.ndarray, quality: int = 75) -> Dict:
        """
        Compress image using standard (fixed) quantization.

        Args:
            image: Input grayscale image
            quality: Quality factor (1-100, higher = better quality)

        Returns:
            Dictionary containing compressed data and metadata
        """
        height, width = image.shape

        # Pad image to be divisible by block_size
        pad_height = (self.block_size - height % self.block_size) % self.block_size
        pad_width = (self.block_size - width % self.block_size) % self.block_size

        padded_image = np.pad(image, ((0, pad_height), (0, pad_width)), mode='edge')
        padded_height, padded_width = padded_image.shape

        # Get standard quantization matrix
        quant_matrix = self.get_standard_quantization_matrix(quality)

        # Storage for compressed data
        quantized_blocks = []

        # Process each block
        for i in range(0, padded_height, self.block_size):
            for j in range(0, padded_width, self.block_size):
                block = padded_image[i:i+self.block_size, j:j+self.block_size].astype(np.float32)

                # Shift to center around zero
                block = block - 128

                # Apply DCT
                dct_block = self.dct2d(block)

                # Quantize with standard matrix
                quantized_block = np.round(dct_block / quant_matrix)

                quantized_blocks.append(quantized_block)

        compressed_data = {
            'blocks': quantized_blocks,
            'quant_matrix': quant_matrix,
            'original_shape': (height, width),
            'padded_shape': (padded_height, padded_width),
            'block_size': self.block_size,
            'method': 'standard'
        }

        return compressed_data

    def decompress(self, compressed_data: Dict) -> np.ndarray:
        """
        Decompress image from compressed data.

        Args:
            compressed_data: Dictionary containing compressed blocks and metadata

        Returns:
            Reconstructed image
        """
        padded_height, padded_width = compressed_data['padded_shape']
        original_height, original_width = compressed_data['original_shape']
        block_size = compressed_data['block_size']
        method = compressed_data['method']

        reconstructed_padded = np.zeros((padded_height, padded_width), dtype=np.float32)

        block_idx = 0
        for i in range(0, padded_height, block_size):
            for j in range(0, padded_width, block_size):
                quantized_block = compressed_data['blocks'][block_idx]

                # Dequantize
                if method == 'adaptive':
                    quant_matrix = compressed_data['quant_matrices'][block_idx]
                else:
                    quant_matrix = compressed_data['quant_matrix']

                dequantized_block = quantized_block * quant_matrix

                # Apply inverse DCT
                reconstructed_block = self.idct2d(dequantized_block)

                # Shift back
                reconstructed_block = reconstructed_block + 128

                # Clip values
                reconstructed_block = np.clip(reconstructed_block, 0, 255)

                reconstructed_padded[i:i+block_size, j:j+block_size] = reconstructed_block
                block_idx += 1

        # Remove padding
        reconstructed = reconstructed_padded[:original_height, :original_width]

        return reconstructed.astype(np.uint8)

    def save_compressed(self, compressed_data: Dict, filename: str):
        """Save compressed data to file."""
        with open(filename, 'wb') as f:
            pickle.dump(compressed_data, f)

    def load_compressed(self, filename: str) -> Dict:
        """Load compressed data from file."""
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def get_compressed_size(self, compressed_data: Dict) -> int:
        """
        Calculate the actual compressed data size in bytes.

        This represents the size of the quantized DCT coefficients plus
        essential metadata, approximating a real compressed format.
        """
        # Count quantized coefficient data (stored as int16 for efficiency)
        num_blocks = len(compressed_data['blocks'])
        block_size = compressed_data['block_size']

        # Each coefficient stored as int16 (2 bytes)
        coefficients_size = num_blocks * block_size * block_size * 2

        # Quantization matrix/matrices
        if compressed_data['method'] == 'adaptive':
            # Each block has its own quantization matrix (stored as uint8)
            quant_size = num_blocks * block_size * block_size
        else:
            # Single quantization matrix for all blocks
            quant_size = block_size * block_size

        # Metadata (dimensions, method flag, etc.) - approximately 100 bytes
        metadata_size = 100

        total_size = coefficients_size + quant_size + metadata_size

        return total_size


def calculate_psnr(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio.

    Args:
        original: Original image
        reconstructed: Reconstructed image

    Returns:
        PSNR value in dB
    """
    mse = np.mean((original.astype(np.float32) - reconstructed.astype(np.float32)) ** 2)
    if mse == 0:
        return float('inf')

    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr


def calculate_mse(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Calculate Mean Squared Error.

    Args:
        original: Original image
        reconstructed: Reconstructed image

    Returns:
        MSE value
    """
    return np.mean((original.astype(np.float32) - reconstructed.astype(np.float32)) ** 2)


def calculate_ssim(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """
    Calculate Structural Similarity Index.

    Args:
        original: Original image
        reconstructed: Reconstructed image

    Returns:
        SSIM value (0-1, higher is better)
    """
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    original = original.astype(np.float32)
    reconstructed = reconstructed.astype(np.float32)

    mu1 = cv2.GaussianBlur(original, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(reconstructed, (11, 11), 1.5)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(original ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(reconstructed ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(original * reconstructed, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

    return float(np.mean(ssim_map))
