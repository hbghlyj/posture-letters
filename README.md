# Posture Master

![The A–Z glyph set](glyph-sheet.svg)

A comic display font in which **single bodies contort into letterforms**. Every capital is a traced silhouette from a modern gymnast or yoga photograph, chosen for readable letter topology and natural limb proportions. An eighteenth-century body-alphabet print suggested the original joke; it is not the construction source.

The body’s own terminals — bun, hands, pointed feet — finish the letters. There is no hat-and-shoe costume system and no constructed breeches/calf machinery.

## Quick start

Copy `posture-master.css`, `posture-master.woff2`, and `posture-master.woff` into the same directory, then link the stylesheet:

```html
<link rel="stylesheet" href="posture-master.css">
<h1 class="posture-master">BENDY TYPE!</h1>
```

Or declare only the compact WOFF2:

```css
@font-face {
  font-family: "Posture Master";
  src: url("posture-master.woff2") format("woff2");
  font-display: swap;
}
```

## Included files

- `posture-master.woff2` — preferred modern web font
- `posture-master.woff` — legacy web-font fallback
- `posture-master.ttf` — desktop/installable font
- `posture-master.css` — ready-to-use `@font-face` declaration
- `glyph-sheet.svg` — A–Z visual overview
- `generate_font.py` — builds the TTF/WOFF/WOFF2 files and `glyph-sheet.svg`
- `outline_points/` — A–Z traced contours consumed by the generator
- `assets/silhouettes/` — source rasters for those contours
- `assets/j_gymnast_photo.png`, `assets/s_gymnast_photo.png`, `assets/w_gymnast_photo.png` — photographic sources for J, S, and W
- `reference-crops/` — pose references, including modern studies in `two-way-stretch/`

## Character coverage

- A–Z
- a–z aliases (same outlines as uppercase)
- space
- period, comma, exclamation mark, question mark, hyphen
- en dash and em dash aliases (same as hyphen)

Period, comma, and hyphen are plain marks (a disc, a disc with a tail, a dash). Exclamation and question marks use solid dots rather than heads, which read as figures at that size.

## How a letter is built

Each capital lives as `outline_points/{a–z}.py`, exporting `OUTLINE_POINTS` and `HOLES`. Matching rasters sit in `assets/silhouettes/`; L also keeps its VTracer SVG there. `generate_font.py` imports `LETTERS` from the package, scales each contour uniformly to cap height 788, seats it on `BAR_GROUND` (y=72), and gives every glyph 72 units of sidebearing. Advances are proportional and uncapped, so wide poses such as V, W, and Q can exceed the em.

Punctuation is still drawn with a few simple primitives (`path`, `torso`, `circle`). Rebuild with:

```bash
python generate_font.py
```

## Letter notes

- **A** — standing wide-legged forward fold: lifted hips the apex, spread legs the diagonals, folded torso and arms the crossbar.
- **B** — from behind: standing leg and torso the stem, hand-on-hip elbow the upper bowl, bent knee the lower bowl.
- **C** — kneeling backbend, thighs the left stem, arched torso and thrown-back head opening right.
- **D** — kneeling camel: thighs the stem, thrown-back head the top of the bowl, hands on the heels. The import is mirrored to face the conventional D.
- **E** — kneeling: upright spine the stem, raised arm the top bar, forward arm the middle bar, folded legs the bottom bar.
- **F** — standing on one straight leg; both arms the top bar; folded lifted leg the middle bar.
- **G** — inverted scorpion: arms and hanging head at the bottom, arched torso the bowl, feet the spur.
- **H** — horizontal torso the crossbar; raised leg and kneeling shin the left stem; raised and planted arms the right stem.
- **I** — legs pressed together the stem; crossed arms and open hands the top serif; feet turned out the bottom serif.
- **J** — from `assets/j_gymnast_photo.png`. Joined legs the tall right stem, flexed feet a short top serif, hips/back/arms the open bottom hook, upright profile head the lower-left terminal.
- **K** — kneeling upright torso the stem, raised arm the upper diagonal, extended straight leg the lower diagonal.
- **L** — from `assets/silhouettes/l.png` / `l.svg`. High-kneeling side profile: vertical trunk the stem, shin and pointed foot the bottom bar.
- **M** — folded double from behind: raised knees the peaks, calves the outer stems, thighs sloping in to hanging hips the central V.
- **N** — from `reference-crops/two-way-stretch/N.png`. Planted arm the left stem, organic torso the diagonal, raised leg the right stem.
- **O** — full bow whose raised feet and grasping arms close a ring, with a large natural counter.
- **P** — standing backbend: planted legs the stem; arched torso, hanging head, and clasped hands the bowl.
- **Q** — prone bow: raised feet and grasping arm close the ring; the other arm plants as the tail.
- **R** — the same standing backbend as P, with the front leg stepped forward as the diagonal.
- **S** — side-profile gymnast: grounded shins the lower terminal, backbend and head the middle curve, overlapped arms the upper hook.
- **T** — standing from behind: legs together the stem, both arms level with the shoulders the bar.
- **U** — from `assets/silhouettes/u.png`. Arms the left stem with an inward hand serif, hips the bowl, joined legs the right stem to pointed feet; profile head on the left stem, counter left open.
- **V** — from `reference-crops/two-way-stretch/V.png`. Two equal legs rise from a compact buttocks apex; outward-turned shod feet are the upper terminals.
- **W** — forward-hinged gymnast: head and shoulders the centre peak, arms overlapping thighs as inner strokes, shorter slimmer calves as outer strokes. Hands conceal the grounded knees; pointed feet turn modestly outward. One contour, no carved notch.
- **X** — wide forward fold from behind: legs an inverted V, head hanging at the centre, arms to the upper corners.
- **Y** — headstand: torso the stem, split legs the V.
- **Z** — kneeling: both arms the top bar, leaning torso and thighs the diagonal, shins and feet the bottom bar.

Older print-cell crops in `reference-crops/pose/` are comparison only.

The shipped outlines are monochrome letterforms for playful display, not body text. Treat the poses as typographic fiction, not exercise instructions.
