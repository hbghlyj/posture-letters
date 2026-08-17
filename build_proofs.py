#!/usr/bin/env python3
"""Rebuild the general raster proof from the current Posture Master TTF."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG = "#f5edda"
INK = "#17243a"
RED = "#e4473a"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ROOT / "posture-master.ttf"), size)


def centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str,
             face: ImageFont.FreeTypeFont, fill: str, anchor_y: float = 0.5) -> None:
    bbox = draw.textbbox((0, 0), text, font=face)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - tw) / 2 - bbox[0]
    y = box[1] + (box[3] - box[1] - th) * anchor_y - bbox[1]
    draw.text((x, y), text, font=face, fill=fill)


def build_font_proof() -> None:
    im = Image.new("RGB", (1800, 790), BG)
    draw = ImageDraw.Draw(im)
    title = ImageFont.truetype(SERIF, 24)
    draw.text((48, 28), "POSTURE MASTER · 1782 CONSTRUCTION PROOF", font=title, fill="#655d52")
    draw.line((48, 66, 1750, 66), fill="#ad9571", width=2)
    centered(draw, (55, 62, 1745, 255), "BENDY TYPE!", font(176), INK)
    centered(draw, (120, 250, 1680, 392), "ABCDEFGHIJKLM", font(102), RED)
    centered(draw, (120, 378, 1680, 525), "NOPQRSTUVWXYZ", font(102), INK)
    centered(draw, (120, 530, 1680, 710), "HUMAN ALPHABET?", font(105), INK)
    im.save(ROOT / "font-proof.png")


def build_glyph_sheet() -> None:
    """Raster the glyph sheet from the compiled TTF.

    Rendering through the font (rather than re-drawing the generator's raw
    contours) is what the released files should show: the rasteriser applies
    the TrueType nonzero fill rule, so overlapping limbs merge correctly and
    engraved cuts read as fine lines instead of tearing the silhouette apart.
    """
    cols, rows = 7, 4
    cell_w, cell_h = 210, 250
    im = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(im)
    face = font(200)
    for index in range(26):
        letter = chr(ord("A") + index)
        col, row = index % cols, index // cols
        box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
        centered(draw, box, letter, face, INK)
    im.save(ROOT / "glyph-sheet.png")


def main() -> None:
    build_font_proof()
    print("Built font-proof.png")
    build_glyph_sheet()
    print("Built glyph-sheet.png")


if __name__ == "__main__":
    main()
