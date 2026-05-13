#!/usr/bin/env python3
"""
Generate the Agon project logo.
Theme: Greek god of competitions + code quality assessment.

Usage:
    python scripts/generate_logo.py
"""
import math
from pathlib import Path
import cairo

# Resolve project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "docs" / "assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SVG_PATH = OUT_DIR / "agon-logo.svg"
PNG_PATH = OUT_DIR / "agon-logo.png"

# Canvas dimensions
W, H = 600, 700

# Color palette
BG_COLOR = (0.098, 0.11, 0.145, 1.0)          # Deep navy/charcoal background
GOLD_COLOR = (0.85, 0.65, 0.13, 1.0)          # Gold for victory elements
LIGHT_GOLD = (0.93, 0.84, 0.60, 1.0)          # Light gold highlights
WHITE = (0.95, 0.96, 0.98, 1.0)               # Near-white for text
ACCENT_COLOR = (0.18, 0.72, 0.68, 1.0)        # Teal accent for code/tech feel

surface_svg = cairo.SVGSurface(str(SVG_PATH), W, H)
surface_png = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

def draw_logo(ctx):
    # Background
    ctx.set_source_rgba(*BG_COLOR)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # Center of the emblem area
    cx, cy = W / 2, 270

    # --- Outer ring / compass shape (suggesting assessment/evaluation) ---
    ctx.set_line_width(3.5)
    ctx.set_source_rgba(*GOLD_COLOR)
    ctx.arc(cx, cy, 120, 0, 2 * math.pi)
    ctx.stroke()

    # Inner ring
    ctx.set_line_width(1.5)
    ctx.arc(cx, cy, 105, 0, 2 * math.pi)
    ctx.stroke()

    # --- Greek alpha / lambda hybrid symbol in center ---
    # Represents Greek heritage and also upward arrow / growth / assessment direction
    ctx.set_line_width(8)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*WHITE)

    # Draw "A" shape (stylized Greek alpha)
    a_size = 70
    # Left leg
    ctx.move_to(cx - a_size * 0.6, cy + a_size * 0.7)
    ctx.line_to(cx, cy - a_size * 0.7)
    ctx.line_to(cx + a_size * 0.6, cy + a_size * 0.7)
    ctx.stroke()

    # Crossbar of A (suggest code bracket or evaluation bar)
    ctx.set_source_rgba(*ACCENT_COLOR)
    ctx.set_line_width(6)
    ctx.move_to(cx - a_size * 0.35, cy + a_size * 0.1)
    ctx.line_to(cx + a_size * 0.35, cy + a_size * 0.1)
    ctx.stroke()

    # --- Text "AGON" ---
    ctx.set_source_rgba(*WHITE)
    ctx.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(90)

    text = "AGON"
    ext = ctx.text_extents(text)
    tx = cx - ext.width / 2 - ext.x_bearing
    ty = 540
    ctx.move_to(tx, ty)
    ctx.show_text(text)

    # Subtitle
    ctx.set_source_rgba(*GOLD_COLOR)
    ctx.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(24)
    sub = "CODE ASSESSMENT"
    ext2 = ctx.text_extents(sub)
    sx = cx - ext2.width / 2 - ext2.x_bearing
    sy = 590
    ctx.move_to(sx, sy)
    ctx.show_text(sub)

    # Small decorative line under subtitle
    ctx.set_line_width(2)
    ctx.set_source_rgba(*ACCENT_COLOR)
    ctx.move_to(cx - 60, 615)
    ctx.line_to(cx + 60, 615)
    ctx.stroke()

# Draw to SVG
ctx_svg = cairo.Context(surface_svg)
draw_logo(ctx_svg)
surface_svg.finish()

# Draw to PNG
ctx_png = cairo.Context(surface_png)
draw_logo(ctx_png)
surface_png.write_to_png(str(PNG_PATH))

print(f"Logo saved to:")
print(f"  SVG: {SVG_PATH}")
print(f"  PNG: {PNG_PATH}")
