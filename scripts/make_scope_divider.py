#!/usr/bin/env python3
"""
make_scope_divider.py

An oscilloscope-trace section divider: a sine waveform draws itself
left-to-right once (stroke-dashoffset animation), with a small bright
"beam" dot riding the leading edge that fades out when the trace
finishes. Subtle graticule ticks in the background for authenticity.
Plays once, freezes -- consistent with the rest of the profile's motion.

Writes: scope-divider.svg
"""
import math
import os

ACCENT = "#FFB000"
GRID = "#21262d"
WIDTH = 820
HEIGHT = 60
MID_Y = HEIGHT / 2
AMPLITUDE = 16
CYCLES = 5.5

def build_path_points(n=240):
    pts = []
    for i in range(n + 1):
        x = WIDTH * i / n
        # slight amplitude taper at the very ends so it reads as a
        # captured "burst" rather than an infinite repeating wave
        taper = math.sin(math.pi * i / n)
        y = MID_Y + AMPLITUDE * taper * math.sin(2 * math.pi * CYCLES * i / n)
        pts.append((x, y))
    return pts

def path_length(pts):
    length = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        length += math.hypot(x1 - x0, y1 - y0)
    return length

def build_svg(static=False):
    pts = build_path_points()
    length = path_length(pts)
    d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg">'
    )

    # graticule: faint vertical ticks + center line
    parts.append(f'<line x1="0" y1="{MID_Y}" x2="{WIDTH}" y2="{MID_Y}" stroke="{GRID}" stroke-width="1"/>')
    for i in range(0, 21):
        x = WIDTH * i / 20
        parts.append(f'<line x1="{x:.1f}" y1="{MID_Y-4}" x2="{x:.1f}" y2="{MID_Y+4}" stroke="{GRID}" stroke-width="1"/>')

    if static:
        parts.append(
            f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
        parts.append('</svg>')
        return "\n".join(parts)

    draw_dur = 1.3
    parts.append(
        f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
        f'begin="0.1s" dur="{draw_dur}s" fill="freeze" '
        f'calcMode="spline" keySplines="0.3 0 0.2 1"/>'
        f'</path>'
    )

    # bright beam dot riding the leading edge along the same path, fades
    # out once the trace finishes drawing
    parts.append(
        f'<circle r="3.2" fill="{ACCENT}">'
        f'<animateMotion path="{d}" begin="0.1s" dur="{draw_dur}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.04;0.9;1" '
        f'begin="0.1s" dur="{draw_dur + 0.25}s" fill="freeze"/>'
        f'</circle>'
    )

    parts.append('</svg>')
    return "\n".join(parts)

if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static=static)
    with open("scope-divider.svg", "w") as f:
        f.write(svg)
    print("Wrote scope-divider.svg" + (" [static]" if static else ""))
