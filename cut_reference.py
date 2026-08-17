#!/usr/bin/env python3
"""Cut the 1782 print into its historical 24-letter cells."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets" / "original-print.png"
OUT = ROOT / "reference-crops"
FULL = OUT / "full"
POSE = OUT / "pose"
FULL.mkdir(parents=True, exist_ok=True)
POSE.mkdir(parents=True, exist_ok=True)

# The print uses the pre-modern 24-letter sequence: J and U are absent.
ROWS = ["ABCDEFGH", "IKLMNOPQ", "RSTVWXYZ"]
X = [8, 119, 229, 340, 450, 561, 672, 782, 894]
Y = [6, 198, 389, 579]
POSE_BOTTOM = [177, 367, 557]

im = Image.open(SOURCE).convert("RGB")
resample = Image.Resampling.LANCZOS
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 30)

for row_index, letters in enumerate(ROWS):
    for col_index, letter in enumerate(letters):
        full_box = (X[col_index], Y[row_index], X[col_index + 1], Y[row_index + 1])
        pose_box = (X[col_index], Y[row_index], X[col_index + 1], POSE_BOTTOM[row_index])
        full = im.crop(full_box)
        pose = im.crop(pose_box)
        full.resize((full.width * 4, full.height * 4), resample).save(FULL / f"{letter}.png")
        pose.resize((pose.width * 5, pose.height * 5), resample).save(POSE / f"{letter}.png")

# Review sheets retain generous tile size so each figure can be inspected.
def sheet(name: str, letters: str) -> None:
    tiles = [Image.open(POSE / f"{letter}.png") for letter in letters]
    tile_w = max(tile.width for tile in tiles)
    tile_h = max(tile.height for tile in tiles)
    canvas = Image.new("RGB", (tile_w * 4, (tile_h + 52) * 2), "#f5edda")
    draw = ImageDraw.Draw(canvas)
    for i, (letter, tile) in enumerate(zip(letters, tiles)):
        x = (i % 4) * tile_w
        y = (i // 4) * (tile_h + 52)
        canvas.paste(tile, (x, y + 44))
        draw.text((x + 12, y + 7), letter, font=font, fill="#9f3026")
    canvas.save(OUT / name)

sheet("review-top-A-H.png", ROWS[0])
sheet("review-middle-I-Q.png", ROWS[1])
sheet("review-bottom-R-Z.png", ROWS[2])

manifest = OUT / "README.md"
manifest.write_text(
    "# Historical reference crops\n\n"
    "The 1782 print contains 24 letter cells: A–I, K–T, V–Z; J and U are absent.\n\n"
    "- `full/`: complete cells including each rhyme.\n"
    "- `pose/`: enlarged pose-and-label crops for anatomical review.\n"
    "- `review-*.png`: eight-pose review sheets.\n",
    encoding="utf-8",
)
print("Cut 24 full cells, 24 pose crops, and 3 review sheets")
