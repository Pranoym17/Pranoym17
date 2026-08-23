#!/usr/bin/env python3
"""
make_ascii_svg.py <prepped.png>

Downsamples the prepped grayscale image to a character grid, maps each
cell's brightness to a density-ramp glyph, and emits a self-contained
animated SVG: each row wipes in left-to-right with a small cursor block
riding the edge, staggered top to bottom. Plays once, freezes (no loop).

Writes: pranoym17-ascii.svg
"""
import os
import sys
import numpy as np
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

FILL_COLOR = "#c9d1d9"      # light gray, monochrome
BG_COLOR = "none"
FONT_FAMILY = "'SF Mono','Consolas','Menlo',monospace"

def image_to_ascii_grid(img_path, cols=90):
    img = Image.open(img_path).convert("L")
    w, h = img.size
    # monospace glyphs are roughly 0.55 as wide as they are tall,
    # so correct rows to keep the portrait's proportions looking right
    char_aspect = 0.55
    rows = max(1, round(cols * (h / w) * char_aspect))
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small).astype(np.float32)

    grid = []
    n = len(RAMP) - 1
    for row in arr:
        line = []
        for val in row:
            # val: 0=black(dense) .. 255=white(sparse/background)
            idx = n - int((val / 255.0) * n)
            idx = max(0, min(n, idx))
            line.append(RAMP[idx])
        grid.append("".join(line))
    return grid

def escape(ch):
    return {"<": "&lt;", ">": "&gt;", "&": "&amp;"}.get(ch, ch)

def build_svg(grid, cell_w=7.0, cell_h=13.5, font_size=13, static=False):
    cols = len(grid[0])
    rows = len(grid)
    width = cols * cell_w + 20
    height = rows * cell_h + 20

    row_duration = 0.55       # seconds per row wipe
    row_stagger = 0.028       # seconds between each row's start
    total_typing = row_stagger * rows + row_duration

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT_FAMILY}">'
    )
    parts.append(
        f'<style>'
        f'.ascii-row {{ font-size:{font_size}px; fill:{FILL_COLOR}; '
        f'white-space:pre; }}'
        f'</style>'
    )

    if static:
        # frozen end-state: full text, no clip/animation -- used for
        # local previews (STATIC=1) so you can sanity-check the art
        # without a SMIL-capable renderer.
        for r, line in enumerate(grid):
            y = 15 + r * cell_h + font_size * 0.8
            text = "".join(escape(c) for c in line)
            parts.append(f'<text x="10" y="{y:.1f}" class="ascii-row">{text}</text>')
        parts.append('</svg>')
        return "\n".join(parts)

    for r, line in enumerate(grid):
        y = 15 + r * cell_h + font_size * 0.8
        row_w = len(line) * cell_w
        start = r * row_stagger
        text = "".join(escape(c) for c in line)

        clip_id = f"clip{r}"
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="10" y="{y - font_size:.1f}" width="0" height="{font_size * 1.4:.1f}">')
        parts.append(
            f'    <animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{start:.3f}s" dur="{row_duration:.2f}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
        parts.append(f'  </rect>')
        parts.append(f'</clipPath>')

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="10" y="{y:.1f}" class="ascii-row">{text}</text>')
        parts.append(f'</g>')

        # small cursor block riding the wipe edge, same duration, then fades
        cursor_w = cell_w * 0.9
        parts.append(
            f'<rect x="10" y="{y - font_size:.1f}" width="{cursor_w:.1f}" '
            f'height="{font_size * 1.3:.1f}" fill="{FILL_COLOR}" opacity="0">'
        )
        parts.append(
            f'  <animate attributeName="x" from="10" to="{10 + row_w - cursor_w:.1f}" '
            f'begin="{start:.3f}s" dur="{row_duration:.2f}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
        parts.append(
            f'  <animate attributeName="opacity" values="0;0.9;0.9;0" '
            f'keyTimes="0;0.05;0.85;1" '
            f'begin="{start:.3f}s" dur="{row_duration + 0.12:.2f}s" fill="freeze"/>'
        )
        parts.append(f'</rect>')

    parts.append('</svg>')
    return "\n".join(parts)

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "pranoym17-ascii.svg"
    static = os.environ.get("STATIC") == "1"
    grid = image_to_ascii_grid(src, cols=90)
    svg = build_svg(grid, static=static)
    with open(out, "w") as f:
        f.write(svg)
    print(f"Wrote {out}  ({len(grid[0])} cols x {len(grid)} rows)" + (" [static]" if static else ""))
