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


def main() -> None:
    build_font_proof()
    print("Built font-proof.png")


if __name__ == "__main__":
    main()
