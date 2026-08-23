#!/usr/bin/env python3
"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day grid of
rounded boxes. Reveals once with a diagonal, line-after-line slide-down
(plays once, freezes -- no looping glow), plus a Less->More legend and a
stats footer.

Writes: contrib-heatmap.svg
"""
import os
import json
import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
ACCENT = "#FFB000"
FG = "#c9d1d9"
DIM = "#8b949e"
FONT = "'SF Mono','Consolas','Menlo',monospace"

CELL = 11
GAP = 3
LEFT_PAD = 28
TOP_PAD = 20
MONTH_LABEL_H = 16

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Monday=1 ... Sunday=0/7

def load(path="data/contributions.json"):
    with open(path) as f:
        return json.load(f)

def build_weeks(days):
    """Group days into Sunday-start weeks, padding the first week."""
    by_date = {d["date"]: d for d in days}
    dates = sorted(by_date.keys())
    if not dates:
        return []
    start = datetime.date.fromisoformat(dates[0])
    end = datetime.date.fromisoformat(dates[-1])

    # rewind to the Sunday on/before start
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        key = cur.isoformat()
        entry = by_date.get(key, {"date": key, "level": 0, "count": 0})
        week.append(entry)
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += datetime.timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)
    return weeks

def month_label_positions(weeks):
    labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            d = datetime.date.fromisoformat(day["date"])
            if d.day <= 7 and d.month != last_month:
                labels.append((wi, MONTH_ABBR[d.month - 1]))
                last_month = d.month
            break
    return labels

def build_svg(data, static=False):
    days = data["days"]
    stats = data["stats"]
    username = data.get("username", "")
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    grid_w = n_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = LEFT_PAD + grid_w + 20
    height = TOP_PAD + MONTH_LABEL_H + grid_h + 50  # + legend/footer

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}">'
    )
    parts.append(f'<style>.lbl{{font-size:11px;fill:{DIM};}}</style>')

    # month labels
    for wi, label in month_label_positions(weeks):
        x = LEFT_PAD + wi * (CELL + GAP)
        parts.append(f'<text x="{x}" y="{TOP_PAD + 10}" class="lbl">{label}</text>')

    # day-of-week labels
    for dow, label in DOW_LABELS.items():
        y = TOP_PAD + MONTH_LABEL_H + dow * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="0" y="{y}" class="lbl">{label}</text>')

    # cells -- diagonal stagger: delay grows with (week + day) so the
    # reveal sweeps down-right like a wave, once, then freezes
    max_delay_unit = n_weeks + 7
    dur = 0.35
    total_span = 1.1  # seconds over which the whole diagonal sweep completes

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            level = min(day["level"], len(PALETTE) - 1)
            color = PALETTE[level]
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + MONTH_LABEL_H + di * (CELL + GAP)
            delay = (wi + di) / max_delay_unit * total_span

            if static:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>'
                )
            else:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{color}" opacity="0">'
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'begin="{delay:.3f}s" dur="{dur}s" fill="freeze"/>'
                    f'<animateTransform attributeName="transform" type="translate" '
                    f'from="0 -6" to="0 0" begin="{delay:.3f}s" dur="{dur}s" '
                    f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
                    f'</rect>'
                )

    # legend: Less -> More
    legend_y = TOP_PAD + MONTH_LABEL_H + grid_h + 26
    legend_x = LEFT_PAD
    parts.append(f'<text x="{legend_x}" y="{legend_y+9}" class="lbl">Less</text>')
    lx = legend_x + 34
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx+4}" y="{legend_y+9}" class="lbl">More</text>')

    # stats footer, right-aligned
    footer = f"{stats['total']:,} contributions \u00b7 {stats['longest_streak']}-day best streak"
    parts.append(
        f'<text x="{width-20}" y="{legend_y+9}" text-anchor="end" '
        f'font-size="11" fill="{ACCENT}">{footer}</text>'
    )

    parts.append('</svg>')
    return "\n".join(parts)

if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    data = load()
    svg = build_svg(data, static=static)
    with open("contrib-heatmap.svg", "w") as f:
        f.write(svg)
    print("Wrote contrib-heatmap.svg" + (" [static]" if static else ""))
