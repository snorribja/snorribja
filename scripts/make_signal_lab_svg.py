#!/usr/bin/env python3
"""Render Snorri's physiological-signal identity panel as a GitHub-safe SVG."""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "signal-lab.svg")

W, H = 860, 258
X0, X1 = 126, 830
BG, BG2 = "#070b12", "#0d1420"
FRAME, MUTED = "#1f6feb", "#8b949e"
BLUE, CYAN, GOLD, TEXT = "#58a6ff", "#22d3ee", "#f2cc60", "#e6edf3"


def gaussian(x, center, width):
    return math.exp(-((x - center) / width) ** 2)


def eeg(x):
    return (
        0.50 * math.sin(x * 0.12)
        + 0.24 * math.sin(x * 0.31 + 0.8)
        + 0.14 * math.sin(x * 0.67 + 2.1)
    )


def ecg(x):
    t = x % 104
    return (
        0.12 * gaussian(t, 18, 6)
        - 0.16 * gaussian(t, 42, 2.8)
        + 1.35 * gaussian(t, 47, 1.7)
        - 0.38 * gaussian(t, 52, 2.6)
        + 0.32 * gaussian(t, 72, 10)
    )


def rip(x):
    return math.sin(x * 0.040) + 0.14 * math.sin(x * 0.080 + 0.7)


def trace(fn, baseline, amplitude):
    points = [(x, baseline - amplitude * fn(x - X0)) for x in range(X0, X1 + 1, 3)]
    return "M" + " L".join(f"{x},{y:.1f}" for x, y in points)


def render():
    signals = [
        ("EEG", "brain", eeg, 82, 13, BLUE),
        ("ECG", "heart", ecg, 137, 21, GOLD),
        ("RIP", "breath", rip, 192, 12, CYAN),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<title id="title">Signals to systems</title>',
        '<desc id="desc">EEG, ECG, and respiratory traces representing '
        'Snorri Bjarkason&apos;s interests in physiological signals and applied machine learning.</desc>',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        '<linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{BLUE}" stop-opacity="0"/><stop offset=".48" stop-color="{BLUE}" '
        f'stop-opacity=".18"/><stop offset=".72" stop-color="{GOLD}" stop-opacity=".12"/>'
        f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<path d="M0 210 C180 138 280 270 458 185 S720 88 860 146 V258 H0Z" '
        f'fill="url(#aurora)"/>',
        f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="none" '
        f'stroke="{FRAME}" stroke-opacity=".65"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="{FRAME}" stroke-opacity=".35"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{22 + i * 16}" cy="15" r="5" fill="{color}"/>')
    parts.extend([
        f'<text x="{W / 2}" y="19" fill="{MUTED}" font-size="11" text-anchor="middle">'
        'NORTHERN SIGNAL LAB · ICELAND / NEW YORK</text>',
        f'<text x="{W - 22}" y="19" fill="{GOLD}" font-size="9" text-anchor="end">'
        'DUAL U.S.–ICELANDIC CITIZEN</text>',
    ])

    for x in range(X0, X1 + 1, 30):
        parts.append(f'<line x1="{x}" y1="47" x2="{x}" y2="208" stroke="{FRAME}" '
                     f'stroke-opacity=".09"/>')

    for label, meaning, fn, baseline, amplitude, color in signals:
        path = trace(fn, baseline, amplitude)
        parts.extend([
            f'<line x1="{X0}" y1="{baseline}" x2="{X1}" y2="{baseline}" '
            f'stroke="{FRAME}" stroke-opacity=".15"/>',
            f'<text x="22" y="{baseline - 2}" fill="{color}" font-size="13" '
            f'font-weight="700">{label}</text>',
            f'<text x="22" y="{baseline + 13}" fill="{MUTED}" font-size="9">{meaning}</text>',
            f'<path class="trace" d="{path}" fill="none" stroke="{color}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round"/>',
        ])

    parts.extend([
        f'<line x1="0" y1="218" x2="{W}" y2="218" stroke="{FRAME}" stroke-opacity=".25"/>',
        f'<text x="22" y="241" fill="{TEXT}" font-size="13" font-weight="700">'
        'physiological signals  →  representations  →  useful decisions</text>',
        f'<text x="{W - 22}" y="241" fill="{MUTED}" font-size="11" text-anchor="end">'
        'APPLIED ML · DATA · RESEARCH ENGINEERING · SOFTWARE</text>',
        '</svg>',
    ])
    return "".join(parts)


if __name__ == "__main__":
    svg = render()
    assert svg.count('class="trace"') == 3
    assert all(label in svg for label in ("EEG", "ECG", "RIP", "NEW YORK", "CITIZEN"))
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes)")
