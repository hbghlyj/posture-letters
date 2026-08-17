#!/usr/bin/env python3
"""Build side-by-side 1782-reference versus generated-glyph review sheets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
ROWS = [
    ("comparison-A-H.png", "ABCDEFGH"),
    ("comparison-I-Q.png", "IKLMNOPQ"),
    ("comparison-R-Z.png", "RSTVWXYZ"),
]
BG = "#f5edda"
INK = "#17243a"
RED = "#b9362c"
LABEL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
FONT = ImageFont.truetype(str(ROOT / "posture-master.ttf"), 475)
TILE_W, TILE_H = 880, 650


def contain(im: Image.Image, box: tuple[int, int], bg: str = BG) -> Image.Image:
    copy = im.copy()
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", box, bg)
    canvas.paste(copy, ((box[0] - copy.width) // 2, (box[1] - copy.height) // 2))
    return canvas


def glyph_image(letter: str) -> Image.Image:
    canvas = Image.new("RGB", (430, 540), BG)
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), letter, font=FONT)
    x = (430 - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (540 - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), letter, font=FONT, fill=INK)
    return canvas


built_sheets = []
for filename, letters in ROWS:
    sheet = Image.new("RGB", (TILE_W * 4, TILE_H * 2), BG)
    draw = ImageDraw.Draw(sheet)
    for i, letter in enumerate(letters):
        col, row = i % 4, i // 4
        x0, y0 = col * TILE_W, row * TILE_H
        draw.rectangle((x0, y0, x0 + TILE_W - 2, y0 + TILE_H - 2), outline="#b8a681", width=2)
        draw.text((x0 + 18, y0 + 12), letter, font=LABEL, fill=RED)
        draw.text((x0 + 96, y0 + 18), "1782 crop", font=SMALL, fill="#6d6256")
        draw.text((x0 + 545, y0 + 18), "font reconstruction", font=SMALL, fill="#6d6256")
        ref = Image.open(ROOT / "reference-crops" / "pose" / f"{letter}.png").convert("RGB")
        ref_panel = contain(ref, (390, 565))
        glyph_panel = glyph_image(letter)
        sheet.paste(ref_panel, (x0 + 18, y0 + 60))
        sheet.paste(glyph_panel, (x0 + 435, y0 + 60))
    sheet.save(ROOT / "reference-crops" / filename)
    built_sheets.append(sheet)
    print(f"Built reference-crops/{filename}")

all_sheet = Image.new("RGB", (TILE_W * 4, TILE_H * 6), BG)
for index, sheet in enumerate(built_sheets):
    all_sheet.paste(sheet, (0, index * TILE_H * 2))
all_sheet.save(ROOT / "historical-comparison-all.png")
print("Built historical-comparison-all.png")
