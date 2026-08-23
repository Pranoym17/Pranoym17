#!/usr/bin/env python3
"""
prep_photo.py <source.jpg>

1. Remove background with rembg so only the subject remains.
2. Boost local contrast with CLAHE so a flatly-lit face gets real
   highlights/shadows (otherwise it converts to a dark, unreadable blob).
3. Composite onto pure white so the background maps to the blank end
   of the ASCII ramp (white -> space).

Writes: prepped.png (grayscale, white background)
"""
import sys
import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image

def main(src_path, out_path="prepped.png"):
    with open(src_path, "rb") as f:
        input_bytes = f.read()

    print("Removing background (first run downloads the model, be patient)...")
    session = new_session("u2net")
    output_bytes = remove(input_bytes, session=session)

    # Load RGBA result
    rgba = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")
    rgba_np = np.array(rgba)

    # Composite onto pure white using alpha channel
    alpha = rgba_np[:, :, 3:4].astype(np.float32) / 255.0
    rgb = rgba_np[:, :, :3].astype(np.float32)
    white_bg = np.ones_like(rgb) * 255.0
    composited = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)

    # Convert to grayscale
    gray = cv2.cvtColor(composited, cv2.COLOR_RGB2GRAY)

    # CLAHE for real highlight/shadow contrast on the face
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten background to pure white using the alpha mask
    # (CLAHE can slightly darken near-white background pixels)
    alpha_flat = rgba_np[:, :, 3]
    contrasted[alpha_flat < 15] = 255

    # Slight blur to smooth CLAHE noise before ASCII downsampling
    contrasted = cv2.GaussianBlur(contrasted, (3, 3), 0)

    # Auto-crop dead white space (e.g. empty headroom above hair) so the
    # character grid isn't wasted on blank sky. Keep a small padding margin.
    mask = contrasted < 250
    ys, xs = np.where(mask)
    if len(ys) > 0:
        pad_y = int(0.04 * contrasted.shape[0])
        pad_x = int(0.04 * contrasted.shape[1])
        y0 = max(0, ys.min() - pad_y)
        y1 = min(contrasted.shape[0], ys.max() + pad_y)
        x0 = max(0, xs.min() - pad_x)
        x1 = min(contrasted.shape[1], xs.max() + pad_x)
        contrasted = contrasted[y0:y1, x0:x1]

    Image.fromarray(contrasted).save(out_path)
    print(f"Wrote {out_path} ({contrasted.shape[1]}x{contrasted.shape[0]})")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    main(src)
