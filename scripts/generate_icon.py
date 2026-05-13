#!/usr/bin/env python3
"""
Generate a compact square icon for Agon (no text).

Usage:
    python scripts/generate_icon.py
"""
import math
from pathlib import Path
import cairo

# Resolve project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "docs" / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SVG_PATH = OUT_DIR / "agon-icon.svg"
PNG_PATH = OUT_DIR / "agon-icon.png"
W, H = 256, 256

BG = (0.098, 0.11, 0.145, 1.0)
GOLD = (0.85, 0.65, 0.13, 1.0)
LIGHT_GOLD = (0.93, 0.84, 0.60, 1.0)
WHITE = (0.95, 0.96, 0.98, 1.0)
ACCENT = (0.18, 0.72, 0.68, 1.0)

def draw_icon(ctx):
    ctx.set_source_rgba(*BG)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    cx, cy = W / 2, H / 2

    # Outer rings
    ctx.set_line_width(3)
    ctx.set_source_rgba(*GOLD)
    ctx.arc(cx, cy, 100, 0, 2 * math.pi)
    ctx.stroke()
    ctx.set_line_width(1)
    ctx.arc(cx, cy, 88, 0, 2 * math.pi)
    ctx.stroke()

    # Stylized A / alpha
    a_size = 60
    ctx.set_line_width(7)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*WHITE)
    ctx.move_to(cx - a_size * 0.6, cy + a_size * 0.7)
    ctx.line_to(cx, cy - a_size * 0.7)
    ctx.line_to(cx + a_size * 0.6, cy + a_size * 0.7)
    ctx.stroke()

    # Crossbar
    ctx.set_source_rgba(*ACCENT)
    ctx.set_line_width(5)
    ctx.move_to(cx - a_size * 0.35, cy + a_size * 0.1)
    ctx.line_to(cx + a_size * 0.35, cy + a_size * 0.1)
    ctx.stroke()

# SVG
s1 = cairo.SVGSurface(str(SVG_PATH), W, H)
c1 = cairo.Context(s1)
draw_icon(c1)
s1.finish()

# PNG
s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
c2 = cairo.Context(s2)
draw_icon(c2)
s2.write_to_png(str(PNG_PATH))

print(f"Icon saved to:\n  SVG: {SVG_PATH}\n  PNG: {PNG_PATH}")
