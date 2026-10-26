"""
GUI for Content-Aware Image Compression Application
Provides an interactive interface to load images, compress using adaptive or standard
methods, and compare results with quality metrics.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
from adaptive_compression import (
    AdaptiveImageCompressor,
    calculate_psnr,
    calculate_mse,
    calculate_ssim
)


class ImageCompressionGUI:
    """Main GUI application for image compression."""

    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Content-Aware Image Compression")

        # Get screen dimensions for better scaling
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Set window size to 90% of screen size for better resolution
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.85)

        # Center the window
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Enable high DPI awareness for sharper rendering
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # Variables
        self.original_image = None
        self.original_gray = None
        self.compressed_adaptive = None
        self.compressed_standard = None
        self.reconstructed_adaptive = None
        self.reconstructed_standard = None
        self.current_filepath = None

        # Compressor
        self.compressor = AdaptiveImageCompressor(block_size=8)

        # Setup GUI
        self.setup_ui()

    def setup_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Title with better font scaling
        title_label = ttk.Label(
            main_frame,
            text="Content-Aware Image Compression Using Adaptive Frequency-Domain Processing",
            font=("Segoe UI", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=15)

        # Control panel with improved styling
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="15")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # Load image button with larger size
        load_btn = ttk.Button(
            control_frame,
            text="📂 Load Image",
            command=self.load_image,
            width=15
        )
        load_btn.grid(row=0, column=0, padx=8, pady=8)

        # Quality slider with better spacing
        ttk.Label(control_frame, text="Quality Factor:", font=("Segoe UI", 10)).grid(row=0, column=1, padx=10)
        self.quality_var = tk.IntVar(value=75)
        quality_slider = ttk.Scale(
            control_frame,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            length=250
        )
        quality_slider.grid(row=0, column=2, padx=8)

        self.quality_label = ttk.Label(control_frame, text="75", font=("Segoe UI", 10, "bold"), width=4)
        self.quality_label.grid(row=0, column=3, padx=8)
        self.quality_var.trace('w', self.update_quality_label)

        # Compress buttons with improved styling
        ttk.Button(
            control_frame,
            text="⚡ Compress (Adaptive)",
            command=self.compress_adaptive,
            width=20
        ).grid(row=0, column=4, padx=8, pady=8)

        ttk.Button(
            control_frame,
            text="📊 Compress (Standard)",
            command=self.compress_standard,
            width=20
        ).grid(row=0, column=5, padx=8, pady=8)

        ttk.Button(
            control_frame,
            text="🔍 Compare Both",
            command=self.compare_both,
            width=18
        ).grid(row=0, column=6, padx=8, pady=8)

        # Download/Save buttons
        ttk.Button(
            control_frame,
            text="💾 Save Adaptive",
            command=self.save_adaptive,
            width=18
        ).grid(row=1, column=4, padx=8, pady=8)

        ttk.Button(
            control_frame,
            text="💾 Save Standard",
            command=self.save_standard,
            width=18
        ).grid(row=1, column=5, padx=8, pady=8)

        ttk.Button(
            control_frame,
            text="📦 Save Compressed Data",
            command=self.save_compressed_data,
            width=20
        ).grid(row=1, column=6, padx=8, pady=8)

        # Image display area
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(2, weight=1)

        # Original image
        self.original_frame = self.create_image_panel(display_frame, "Original Image", 0)

        # Adaptive compressed
        self.adaptive_frame = self.create_image_panel(display_frame, "Adaptive Compression", 1)

        # Standard compressed
        self.standard_frame = self.create_image_panel(display_frame, "Standard Compression", 2)

        # Make columns expandable
        for i in range(3):
            display_frame.columnconfigure(i, weight=1)

        # Metrics panel with better styling
        metrics_frame = ttk.LabelFrame(main_frame, text="Compression Metrics", padding="15")
        metrics_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # Scrollbar for metrics
        metrics_scroll = ttk.Scrollbar(metrics_frame, orient=tk.VERTICAL)

        self.metrics_text = tk.Text(
            metrics_frame,
            height=10,
            font=("Consolas", 10),
            wrap=tk.NONE,
            bg="#f5f5f5",
            fg="#000000",
            padx=10,
            pady=10,
            yscrollcommand=metrics_scroll.set
        )
        metrics_scroll.config(command=self.metrics_text.yview)

        self.metrics_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        metrics_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.rowconfigure(0, weight=1)

    def create_image_panel(self, parent, title, column):
        """Create a panel for displaying an image with title."""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.grid(row=0, column=column, padx=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Calculate canvas size based on screen
        canvas_size = min(int(self.root.winfo_screenwidth() * 0.25), 600)
        canvas = tk.Canvas(frame, width=canvas_size, height=canvas_size, bg="#2b2b2b", highlightthickness=2, highlightbackground="#555")
        canvas.pack(fill=tk.BOTH, expand=True)

        return {"frame": frame, "canvas": canvas}

    def update_quality_label(self, *args):
        """Update quality label when slider moves."""
        self.quality_label.config(text=str(self.quality_var.get()))

    def load_image(self):
        """Load an image from file."""
        filepath = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )

        if not filepath:
            return

        try:
            # Load image
            self.original_image = cv2.imread(filepath)
            if self.original_image is None:
                raise ValueError("Failed to load image")

            # Convert to grayscale for compression
            self.original_gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
            self.current_filepath = filepath

            # Display original
            self.display_image(self.original_gray, self.original_frame["canvas"])

            # Clear previous results
            self.clear_canvas(self.adaptive_frame["canvas"])
            self.clear_canvas(self.standard_frame["canvas"])
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, "Image loaded successfully. Click 'Compress' to process.\n")

            # Reset compressed data
            self.compressed_adaptive = None
            self.compressed_standard = None
            self.reconstructed_adaptive = None
            self.reconstructed_standard = None

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{str(e)}")

    def display_image(self, image, canvas):
        """Display an image on a canvas."""
        # Convert to RGB for display
        if len(image.shape) == 2:
            display_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize to fit canvas
        canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 400
        canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 400

        h, w = display_image.shape[:2]
        scale = min(canvas_width / w, canvas_height / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(display_image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Convert to PIL and display
        pil_image = Image.fromarray(resized)
        photo = ImageTk.PhotoImage(pil_image)

        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor=tk.CENTER)
        canvas.image = photo  # Keep a reference

    def clear_canvas(self, canvas):
        """Clear a canvas."""
        canvas.delete("all")

    def compress_adaptive(self):
        """Compress using adaptive method."""
        if self.original_gray is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        try:
            quality = self.quality_var.get()

            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, "Compressing with adaptive method...\n")
            self.root.update()

            # Compress
            self.compressed_adaptive = self.compressor.compress_adaptive(self.original_gray, quality)

            # Decompress
            self.reconstructed_adaptive = self.compressor.decompress(self.compressed_adaptive)

            # Display
            self.display_image(self.reconstructed_adaptive, self.adaptive_frame["canvas"])

            # Calculate metrics
            self.display_metrics_adaptive()

        except Exception as e:
            messagebox.showerror("Error", f"Compression failed:\n{str(e)}")

    def compress_standard(self):
        """Compress using standard method."""
        if self.original_gray is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        try:
            quality = self.quality_var.get()

            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, "Compressing with standard method...\n")
            self.root.update()

            # Compress
            self.compressed_standard = self.compressor.compress_standard(self.original_gray, quality)

            # Decompress
            self.reconstructed_standard = self.compressor.decompress(self.compressed_standard)

            # Display
            self.display_image(self.reconstructed_standard, self.standard_frame["canvas"])

            # Calculate metrics
            self.display_metrics_standard()

        except Exception as e:
            messagebox.showerror("Error", f"Compression failed:\n{str(e)}")

    def compare_both(self):
        """Compress using both methods and compare."""
        if self.original_gray is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return

        try:
            quality = self.quality_var.get()

            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, "Compressing with both methods...\n")
            self.root.update()

            # Adaptive
            self.compressed_adaptive = self.compressor.compress_adaptive(self.original_gray, quality)
            self.reconstructed_adaptive = self.compressor.decompress(self.compressed_adaptive)
            self.display_image(self.reconstructed_adaptive, self.adaptive_frame["canvas"])

            # Standard
            self.compressed_standard = self.compressor.compress_standard(self.original_gray, quality)
            self.reconstructed_standard = self.compressor.decompress(self.compressed_standard)
            self.display_image(self.reconstructed_standard, self.standard_frame["canvas"])

            # Compare metrics
            self.display_comparison_metrics()

        except Exception as e:
            messagebox.showerror("Error", f"Compression failed:\n{str(e)}")

    def display_metrics_adaptive(self):
        """Display metrics for adaptive compression."""
        original_size = self.original_gray.nbytes
        compressed_size = self.compressor.get_compressed_size(self.compressed_adaptive)
        compression_ratio = original_size / compressed_size

        psnr = calculate_psnr(self.original_gray, self.reconstructed_adaptive)
        mse = calculate_mse(self.original_gray, self.reconstructed_adaptive)
        ssim = calculate_ssim(self.original_gray, self.reconstructed_adaptive)

        metrics = f"""
ADAPTIVE COMPRESSION RESULTS:
{'='*60}
Image: {os.path.basename(self.current_filepath) if self.current_filepath else 'N/A'}
Quality Factor: {self.quality_var.get()}

File Sizes:
  Original Size:       {original_size:,} bytes ({original_size/1024:.2f} KB)
  Compressed Size:     {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)
  Compression Ratio:   {compression_ratio:.2f}x

Quality Metrics:
  PSNR:                {psnr:.2f} dB
  MSE:                 {mse:.2f}
  SSIM:                {ssim:.4f}
{'='*60}
"""
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(1.0, metrics)

    def display_metrics_standard(self):
        """Display metrics for standard compression."""
        original_size = self.original_gray.nbytes
        compressed_size = self.compressor.get_compressed_size(self.compressed_standard)
        compression_ratio = original_size / compressed_size

        psnr = calculate_psnr(self.original_gray, self.reconstructed_standard)
        mse = calculate_mse(self.original_gray, self.reconstructed_standard)
        ssim = calculate_ssim(self.original_gray, self.reconstructed_standard)

        metrics = f"""
STANDARD COMPRESSION RESULTS:
{'='*60}
Image: {os.path.basename(self.current_filepath) if self.current_filepath else 'N/A'}
Quality Factor: {self.quality_var.get()}

File Sizes:
  Original Size:       {original_size:,} bytes ({original_size/1024:.2f} KB)
  Compressed Size:     {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)
  Compression Ratio:   {compression_ratio:.2f}x

Quality Metrics:
  PSNR:                {psnr:.2f} dB
  MSE:                 {mse:.2f}
  SSIM:                {ssim:.4f}
{'='*60}
"""
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(1.0, metrics)

    def display_comparison_metrics(self):
        """Display comparison metrics for both methods."""
        original_size = self.original_gray.nbytes

        # Adaptive metrics
        adaptive_size = self.compressor.get_compressed_size(self.compressed_adaptive)
        adaptive_ratio = original_size / adaptive_size
        adaptive_psnr = calculate_psnr(self.original_gray, self.reconstructed_adaptive)
        adaptive_mse = calculate_mse(self.original_gray, self.reconstructed_adaptive)
        adaptive_ssim = calculate_ssim(self.original_gray, self.reconstructed_adaptive)

        # Standard metrics
        standard_size = self.compressor.get_compressed_size(self.compressed_standard)
        standard_ratio = original_size / standard_size
        standard_psnr = calculate_psnr(self.original_gray, self.reconstructed_standard)
        standard_mse = calculate_mse(self.original_gray, self.reconstructed_standard)
        standard_ssim = calculate_ssim(self.original_gray, self.reconstructed_standard)

        metrics = f"""
COMPARISON: ADAPTIVE vs STANDARD COMPRESSION
{'='*70}
Image: {os.path.basename(self.current_filepath) if self.current_filepath else 'N/A'}
Quality Factor: {self.quality_var.get()}
Original Size: {original_size:,} bytes ({original_size/1024:.2f} KB)

{'Metric':<25} {'Adaptive':<20} {'Standard':<20} {'Winner'}
{'-'*70}
Compressed Size (bytes)   {adaptive_size:<20,} {standard_size:<20,} {'Adaptive' if adaptive_size < standard_size else 'Standard'}
Compressed Size (KB)      {adaptive_size/1024:<20.2f} {standard_size/1024:<20.2f} {'Adaptive' if adaptive_size < standard_size else 'Standard'}
Compression Ratio         {adaptive_ratio:<20.2f} {standard_ratio:<20.2f} {'Adaptive' if adaptive_ratio > standard_ratio else 'Standard'}
PSNR (dB)                 {adaptive_psnr:<20.2f} {standard_psnr:<20.2f} {'Adaptive' if adaptive_psnr > standard_psnr else 'Standard'}
MSE                       {adaptive_mse:<20.2f} {standard_mse:<20.2f} {'Adaptive' if adaptive_mse < standard_mse else 'Standard'}
SSIM                      {adaptive_ssim:<20.4f} {standard_ssim:<20.4f} {'Adaptive' if adaptive_ssim > standard_ssim else 'Standard'}
{'='*70}

INTERPRETATION:
- Higher PSNR = Better quality (typically >30 dB is good)
- Lower MSE = Better quality (closer to 0 is better)
- Higher SSIM = Better quality (closer to 1 is better)
- Higher Compression Ratio = More compression
"""
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(1.0, metrics)

    def save_adaptive(self):
        """Save the adaptive compressed image."""
        if self.reconstructed_adaptive is None:
            messagebox.showwarning("Warning", "Please compress the image using Adaptive method first.")
            return

        try:
            # Ask user for save location
            filepath = filedialog.asksaveasfilename(
                title="Save Adaptive Compressed Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("BMP files", "*.bmp"),
                    ("All files", "*.*")
                ],
                initialfile="adaptive_compressed.png"
            )

            if filepath:
                # Save the reconstructed image
                cv2.imwrite(filepath, self.reconstructed_adaptive)
                messagebox.showinfo("Success", f"Adaptive compressed image saved to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{str(e)}")

    def save_standard(self):
        """Save the standard compressed image."""
        if self.reconstructed_standard is None:
            messagebox.showwarning("Warning", "Please compress the image using Standard method first.")
            return

        try:
            # Ask user for save location
            filepath = filedialog.asksaveasfilename(
                title="Save Standard Compressed Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("BMP files", "*.bmp"),
                    ("All files", "*.*")
                ],
                initialfile="standard_compressed.png"
            )

            if filepath:
                # Save the reconstructed image
                cv2.imwrite(filepath, self.reconstructed_standard)
                messagebox.showinfo("Success", f"Standard compressed image saved to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{str(e)}")

    def save_compressed_data(self):
        """Save the compressed data (pickle format) for both methods."""
        if self.compressed_adaptive is None and self.compressed_standard is None:
            messagebox.showwarning("Warning", "Please compress the image first.")
            return

        try:
            # Create a directory to save all compressed data
            directory = filedialog.askdirectory(
                title="Select Directory to Save Compressed Data"
            )

            if directory:
                saved_files = []

                # Save adaptive compressed data
                if self.compressed_adaptive is not None:
                    adaptive_path = os.path.join(directory, "compressed_adaptive.pkl")
                    self.compressor.save_compressed(self.compressed_adaptive, adaptive_path)
                    saved_files.append("compressed_adaptive.pkl")

                # Save standard compressed data
                if self.compressed_standard is not None:
                    standard_path = os.path.join(directory, "compressed_standard.pkl")
                    self.compressor.save_compressed(self.compressed_standard, standard_path)
                    saved_files.append("compressed_standard.pkl")

                # Save reconstructed images as well
                if self.reconstructed_adaptive is not None:
                    adaptive_img_path = os.path.join(directory, "reconstructed_adaptive.png")
                    cv2.imwrite(adaptive_img_path, self.reconstructed_adaptive)
                    saved_files.append("reconstructed_adaptive.png")

                if self.reconstructed_standard is not None:
                    standard_img_path = os.path.join(directory, "reconstructed_standard.png")
                    cv2.imwrite(standard_img_path, self.reconstructed_standard)
                    saved_files.append("reconstructed_standard.png")

                # Save original grayscale for comparison
                if self.original_gray is not None:
                    original_path = os.path.join(directory, "original_grayscale.png")
                    cv2.imwrite(original_path, self.original_gray)
                    saved_files.append("original_grayscale.png")

                messagebox.showinfo(
                    "Success",
                    f"Compressed data saved to:\n{directory}\n\nFiles saved:\n" + "\n".join(f"• {f}" for f in saved_files)
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save compressed data:\n{str(e)}")


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = ImageCompressionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
