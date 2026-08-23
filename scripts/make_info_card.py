#!/usr/bin/env python3
"""
make_info_card.py

Neofetch-style panel: a prompt line, then key/value rows that fade and
slide in on a stagger. A thin amber cursor blinks at the end once typing
finishes (the one intentional loop -- everything else plays once and
freezes). STATIC=1 emits a frozen end-state frame for local previews.

Writes: info-card.svg
"""
import os

ACCENT = "#FFB000"      # phosphor-amber terminal accent
FG = "#c9d1d9"           # light gray body text
DIM = "#6e7681"          # dim gray for punctuation/divider
FONT = "'SF Mono','Consolas','Menlo',monospace"

USERNAME = "pranoym17"
FIELDS = [
    ("now",        "Computer Engineering student @ McMaster University"),
    ("prev",       "Full-stack + fintech platform projects"),
    ("stack",      "Python \u00b7 FastAPI \u00b7 Next.js \u00b7 PyTorch \u00b7 Supabase"),
    ("highlights", "Cortex Lab (neuro sim) \u00b7 Sprintern (intern alerts)"),
]

WIDTH = 600
PAD = 24
ROW_H = 34
PROMPT_H = 40
LABEL_W = 108

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_svg():
    static = os.environ.get("STATIC") == "1"
    height = PAD * 2 + PROMPT_H + ROW_H * len(FIELDS) + 30

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}">'
    )

    # panel background
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="10" '
        f'fill="#0d1117" stroke="#21262d"/>'
    )
    # top accent rule
    parts.append(f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="3" rx="1.5" fill="{ACCENT}"/>')

    # prompt line
    prompt_y = PAD + 20
    parts.append(
        f'<text x="{PAD}" y="{prompt_y}" font-size="15" fill="{ACCENT}" font-weight="600">'
        f'{USERNAME}<tspan fill="{DIM}">@github</tspan>'
        f'<tspan fill="{DIM}">:~$</tspan> <tspan fill="{FG}">whoami</tspan>'
        f'</text>'
    )
    parts.append(f'<line x1="{PAD}" y1="{PAD+34}" x2="{WIDTH-PAD}" y2="{PAD+34}" stroke="#21262d"/>')

    row_start_y = PAD + PROMPT_H + 20
    stagger = 0.12
    fade_dur = 0.45

    for i, (label, value) in enumerate(FIELDS):
        y = row_start_y + i * ROW_H
        begin = 0.35 + i * stagger

        group_attrs = "" if static else f' opacity="0"'
        parts.append(f'<g{group_attrs}>')
        if not static:
            parts.append(
                f'  <animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{fade_dur}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            )
            parts.append(
                f'  <animateTransform attributeName="transform" type="translate" '
                f'from="-8 0" to="0 0" begin="{begin:.2f}s" dur="{fade_dur}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            )
        parts.append(
            f'  <text x="{PAD}" y="{y}" font-size="13.5" fill="{ACCENT}">{label}</text>'
        )
        parts.append(
            f'  <text x="{PAD + LABEL_W}" y="{y}" font-size="13.5" fill="{FG}">{esc(value)}</text>'
        )
        parts.append('</g>')

    # trailing blinking cursor -- the one intentional loop, appears after
    # the last row has finished typing
    cursor_begin = 0.35 + len(FIELDS) * stagger + fade_dur
    cursor_y = row_start_y + len(FIELDS) * ROW_H
    if not static:
        parts.append(
            f'<rect x="{PAD}" y="{cursor_y - 12}" width="8" height="14" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{cursor_begin:.2f}s" '
            f'dur="0.01s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
            f'begin="{cursor_begin:.2f}s" dur="1s" repeatCount="indefinite"/>'
            f'</rect>'
        )
    else:
        parts.append(f'<rect x="{PAD}" y="{cursor_y - 12}" width="8" height="14" fill="{ACCENT}"/>')

    parts.append('</svg>')
    return "\n".join(parts)

if __name__ == "__main__":
    svg = build_svg()
    with open("info-card.svg", "w") as f:
        f.write(svg)
    print("Wrote info-card.svg")
