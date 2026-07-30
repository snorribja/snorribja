#!/usr/bin/env python3
"""
Render data/contributions.json (produced by fetch_contributions.py) as a proper
GitHub-style contribution heatmap SVG: a grid of rounded, colored BOXES in the
classic 53-week x 7-day calendar, revealed once with a diagonal line-after-line
slide-down (CSS keyframes, plays on load then freezes -- no looping "glow"), a
snake that winds through the cells, a Less->More legend, and a real stats footer.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# Blue-to-yellow ramp: empty -> brightest.
PALETTE = ["#161b22", "#1f6feb", "#388bfd", "#58a6ff", "#d29922", "#f2cc60"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

BG = "#070b12"
BG2 = "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
ACCENT = "#22d3ee"
BLUE = "#58a6ff"
GOLD = "#f2cc60"

# reveal timing (one-shot)
COL_T = 0.018   # per-column delay contribution (left -> right sweep)
ROW_T = 0.045   # per-row delay contribution (top -> bottom cascade)
CELL_DUR = 0.42


def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # sunday=0
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 88
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD
    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    snake_points = []
    for ri in range(7):
        columns = range(n_cols) if ri % 2 == 0 else range(n_cols - 1, -1, -1)
        snake_points.extend((grid_left + ci * STEP + CELL / 2, grid_top + ri * STEP + CELL / 2)
                            for ci in columns)
    snake_path = "M" + " L".join(f"{x:g},{y:g}" for x, y in snake_points)
    snake_path_length = (len(snake_points) - 1) * STEP
    snake_body_length = 150
    snake_offset = round(snake_path_length * 0.12)

    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes snakeBody {{
  from {{ stroke-dashoffset: -{snake_offset}; }}
  to   {{ stroke-dashoffset: -{snake_offset + snake_path_length}; }}
}}
@keyframes snakeHead {{
  from {{ stroke-dashoffset: -{snake_offset + snake_body_length}; }}
  to   {{ stroke-dashoffset: -{snake_offset + snake_body_length + snake_path_length}; }}
}}
.c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}
.snake-outline, .snake-body {{ animation: snakeBody 24s linear 1.4s infinite; }}
.snake-head {{ animation: snakeHead 24s linear 1.4s infinite; }}
@media (prefers-reduced-motion: reduce) {{
  .c {{ opacity: 1; animation: none; }}
  .snake-outline, .snake-body, .snake-head {{ animation: none; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" role="img" '
        f'aria-labelledby="contribution-title contribution-desc" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<title id="contribution-title">Snorri&apos;s public contribution signal</title>',
        '<desc id="contribution-desc">A blue and gold calendar heatmap of public GitHub '
        'contributions with an animated gold snake.</desc>',
        f'<style>{css}</style>',
        '<defs>'
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">PUBLIC BUILD SIGNAL · LAST 52 WEEKS</text>')
    parts.append(f'<text x="{canvas_w-PAD}" y="{TITLEBAR_H/2 + 3}" fill="{GOLD}" font-size="9" '
                 f'text-anchor="end">SNAKE ONLINE</text>')

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')

    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # the boxes -- each a rounded rect, diagonal slide-down reveal (once, freeze)
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * COL_T + ri * ROW_T
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    parts.append(
        f'<g class="snake" aria-hidden="true" pointer-events="none">'
        f'<path class="snake-outline" d="{snake_path}" fill="none" '
        f'stroke="{BG}" stroke-width="11" stroke-linecap="round" '
        f'stroke-dasharray="{snake_body_length} {snake_path_length - snake_body_length}" '
        f'stroke-dashoffset="-{snake_offset}"/>'
        f'<path class="snake-body" d="{snake_path}" fill="none" '
        f'stroke="{GOLD}" stroke-width="7" stroke-linecap="round" '
        f'stroke-dasharray="{snake_body_length} {snake_path_length - snake_body_length}" '
        f'stroke-dashoffset="-{snake_offset}"/>'
        f'<path class="snake-head" d="{snake_path}" fill="none" '
        f'stroke="#fff4b8" stroke-width="9" stroke-linecap="round" '
        f'stroke-dasharray="10 {snake_path_length - 10}" '
        f'stroke-dashoffset="-{snake_offset + snake_body_length}"/>'
        f'</g>'
    )

    # legend: Less [][][][][] More (bottom-right of the grid)
    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    cs_unit = "day" if cs == 1 else "days"
    ls_unit = "day" if ls == 1 else "days"
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{BLUE}" font-weight="700">'
                 f'{total:,} public contributions in the last year</text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{ACCENT}">'
                 f'current streak {cs} {cs_unit}   &#183;   longest {ls} {ls_unit}</text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{GOLD}" text-anchor="end">'
                 f'best day {best["count"]} on {best["date"]}</text>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    assert 'class="snake-body"' in svg and 'class="snake-head"' in svg
    assert "<animateMotion" not in svg
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
