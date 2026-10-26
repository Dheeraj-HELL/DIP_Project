# Quick Start Guide

## Installation (First Time Setup)

1. **Open Command Prompt/Terminal** and navigate to the project:
   ```bash
   cd C:\ALL_CODES\DIP_Project
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Project

### Option 1: GUI Application (Recommended)
```bash
python gui.py
```

This opens the graphical interface where you can:
- Load images using the "Load Image" button
- Adjust quality with the slider (1-100)
- Compare adaptive vs standard compression
- View metrics and results side-by-side

### Option 2: Test Script (Verification)
```bash
python test_compression.py
```

This creates a synthetic test image and verifies:
- Compression and decompression work correctly
- Metrics are calculated properly
- File save/load functionality

---

## Using the GUI

### Step-by-Step Workflow

1. **Launch the GUI:**
   ```bash
   python gui.py
   ```

2. **Load an Image:**
   - Click "Load Image" button
   - Select a PNG, JPG, BMP, or TIFF file
   - Image appears in the "Original Image" panel

3. **Set Quality:**
   - Use the slider to choose quality (1-100)
   - Higher = better quality, larger file
   - Recommended: 50-85 for good balance

4. **Compress:**
   - **"Compress (Adaptive)"**: Content-aware compression
   - **"Compress (Standard)"**: Fixed compression (JPEG-like)
   - **"Compare Both"**: Run both and compare results

5. **Review Results:**
   - View reconstructed images side-by-side
   - Check metrics panel for:
     - File sizes
     - Compression ratios
     - Quality metrics (PSNR, MSE, SSIM)
   - In comparison mode, see which method wins for each metric

---

## Understanding the Results

### Compression Ratio
```
Compression Ratio = Original Size ÷ Compressed Size
```
- **Higher is better** (more compression)
- Example: 5.0x means file is 5 times smaller

### Quality Metrics

#### PSNR (Peak Signal-to-Noise Ratio)
- **Unit:** Decibels (dB)
- **Range:** Typically 20-50 dB
- **Interpretation:**
  - > 40 dB = Excellent
  - 30-40 dB = Good
  - 20-30 dB = Fair
  - < 20 dB = Poor

#### MSE (Mean Squared Error)
- **Unit:** Squared pixel difference
- **Range:** 0 (perfect) to infinity
- **Lower is better**
- < 100 is generally good

#### SSIM (Structural Similarity Index)
- **Range:** 0 to 1
- **Higher is better**
- **Interpretation:**
  - > 0.95 = Excellent
  - 0.80-0.95 = Good
  - < 0.80 = Noticeable differences

---

## Typical Results

### Natural Photos (landscapes, portraits)
- **Adaptive Method:**
  - Better quality (higher PSNR/SSIM)
  - Preserves facial features and textures
  - Slightly larger file size

- **Standard Method:**
  - Smaller file size
  - Uniform compression across image
  - May lose detail in complex areas

### Graphics/Cartoons (logos, diagrams)
- **Both methods** perform similarly
- Less variation in complexity
- Standard may be sufficient

### Recommended Quality Settings

| Use Case | Quality Setting | Expected Ratio | PSNR |
|----------|----------------|----------------|------|
| Preview/Thumbnail | 30-50 | 8-15x | 25-30 dB |
| Web Display | 60-75 | 4-8x | 30-35 dB |
| High Quality | 80-95 | 2-4x | 35-45 dB |
| Near Lossless | 95-100 | 1-2x | > 45 dB |

---

## Troubleshooting

### Error: "Module not found"
**Solution:**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### GUI doesn't open
**Solution:**
- Check if tkinter is installed (comes with Python)
- On Linux, you may need:
  ```bash
  sudo apt-get install python3-tk
  ```

### Image looks too dark/compressed
**Solution:**
- Increase quality factor (use slider)
- Try quality > 75 for better results
- Note: Currently processes grayscale only

### Out of memory error
**Solution:**
- Resize large images before processing
- Recommended max: 2000×2000 pixels
- Use image editor to resize if needed

### "Permission denied" or file access errors
**Solution:**
- Close any programs viewing the output files
- Run from a directory you have write permissions
- Try running command prompt as administrator

---

## Project Structure

```
DIP_Project/
├── adaptive_compression.py    # Core compression algorithms
├── gui.py                     # GUI application
├── test_compression.py        # Test script
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
├── ALGORITHM_EXPLAINED.md     # Detailed algorithm guide
├── QUICK_START.md            # This file
└── (generated files when you run):
    ├── test_image.png
    ├── test_reconstructed_adaptive.png
    ├── test_reconstructed_standard.png
    └── test_compressed.pkl
```

---

## Sample Test Images

For testing, you can use:
1. **Your own photos** (JPG, PNG)
2. **Free stock images** from:
   - Unsplash.com
   - Pexels.com
   - Pixabay.com
3. **Generated test image** (run test_compression.py)

**Recommended test images:**
- Portrait (face with details)
- Landscape (sky + texture)
- Graphics/logos
- Mixed content

---

## Advanced Usage

### Using as a Library

```python
from adaptive_compression import AdaptiveImageCompressor
import cv2

# Load image
image = cv2.imread('photo.jpg', cv2.IMREAD_GRAYSCALE)

# Create compressor
compressor = AdaptiveImageCompressor(block_size=8)

# Compress with adaptive method
compressed = compressor.compress_adaptive(image, quality=75)

# Get size and metrics
size = compressor.get_compressed_size(compressed)
print(f"Compressed size: {size} bytes")

# Decompress
reconstructed = compressor.decompress(compressed)

# Save results
compressor.save_compressed(compressed, 'output.pkl')
cv2.imwrite('reconstructed.png', reconstructed)
```

### Batch Processing Multiple Images

```python
import os
from adaptive_compression import AdaptiveImageCompressor
import cv2

compressor = AdaptiveImageCompressor()
input_dir = 'input_images/'
output_dir = 'output_images/'

for filename in os.listdir(input_dir):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        # Load and compress
        img = cv2.imread(os.path.join(input_dir, filename), 
                        cv2.IMREAD_GRAYSCALE)
        compressed = compressor.compress_adaptive(img, quality=75)
        
        # Save compressed data
        base_name = os.path.splitext(filename)[0]
        compressor.save_compressed(compressed, 
                                  f'{output_dir}/{base_name}.pkl')
```

---

## Tips for Best Results

1. **Start with quality=75**: Good balance of size and quality
2. **Use adaptive for photos**: Better detail preservation
3. **Use standard for graphics**: Simpler content doesn't need adaptive
4. **Compare both methods**: See which works better for your image
5. **Check SSIM**: Often better indicator than PSNR for perceptual quality

---

## For Your Project Presentation

### Key Points to Highlight:

1. **Problem Statement:**
   - Standard compression treats all regions equally
   - Wastes bits on simple areas, loses detail in complex areas

2. **Our Solution:**
   - Content-aware adaptive quantization
   - Analyzes local complexity (variance + edge strength)
   - Applies appropriate compression per region

3. **Results to Show:**
   - Side-by-side comparison images
   - Metrics comparison table
   - Quality improvement in detailed regions

4. **Technical Implementation:**
   - Block-based DCT (8×8 blocks)
   - JPEG quantization matrices
   - Adaptive scaling based on complexity
   - Python with NumPy, OpenCV, SciPy

### Demo Workflow:
1. Show test results (test_compression.py output)
2. Launch GUI
3. Load a portrait photo
4. Run "Compare Both"
5. Point out quality differences in face details
6. Show metrics comparison

---

## Getting Help

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review README.md for detailed information
3. Read ALGORITHM_EXPLAINED.md for algorithm details
4. Check error messages carefully
5. Verify all dependencies are installed

---

## Next Steps

After getting familiar with the project:
1. Test with different image types
2. Experiment with quality settings
3. Read the algorithm explanation
4. Try batch processing
5. Consider extending with color support or entropy coding

Good luck with your presentation! 🚀
