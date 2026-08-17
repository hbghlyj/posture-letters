# Posture Master

A comic display font in which **single bodies contort into letterforms**. Its 24 historical poses reconstruct the surreal body constructions in the supplied 1782 print, *The Comical Hotch-Potch, or the Alphabet turn’d Posture-Master*. The engraving’s construction takes priority over modern anatomical plausibility.

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
- `index.html` — interactive, self-contained specimen
- `glyph-sheet.svg` / `glyph-sheet.png` (rastered from the compiled TTF) — A–Z visual overview
- `font-proof.png` — current-font raster overview
- `generate_font.py` — reproducible font and SVG source generator
- `build_proofs.py` — rebuilds the raster overview from the TTF
- `build_specimen.py` — rebuilds the self-contained specimen
- `cut_reference.py` — cuts the print into its 24 historical cells
- `build_reference_comparison.py` — builds source-versus-glyph review sheets
- `reference-crops/` — 24 full cells, 24 enlarged pose crops, review sheets, and the pose-construction map
- `validate_anatomy.py` — source-centerline proportion audit
- `anatomy-validation.md` / `.json` — readable and machine-readable audit results
- `assets/original-print.png` — supplied historical visual reference

## Character coverage

- A–Z
- a–z aliases (same pose outlines as uppercase)
- space
- period, comma, exclamation mark, question mark, hyphen

The period, comma and hyphen keep a figure's head as their body, but the exclamation and question marks use plain solid dots — a hatted head at that size reads as a figure rather than punctuation and clutters the mark in running text.
- en dash and em dash aliases

The original print uses a 24-letter alphabet and omits **J** and **U**. Those two modern-coverage glyphs are editorial interpolations and are not represented as historical reconstructions.

## Hat-and-shoe serif system

The face treats costume as letter anatomy: most head-bearing performers wear a compact cocked hat whose brim projects like a serif, while each shoe follows its source-specific toe direction at the actual foot endpoint. The terminals follow the pose rather than being relocated to conventional typographic corners. A’s paired shoes turn left/inward as in the print; F, K, and R point both profile shoes right; E, G, and L raise their toes; and P and X use outward left/right pairs. O retains deliberately tiny foreshortened shoes, while Q’s two compact shoes turn inward and meet at the apex of its inverted leg ring. M keeps its source-visible upward face at the central dip but does not invent a hat where none is visible; its two outer shoes flare outward from the actual pillar feet.

## Below-knee breeches and calf system

Every visible foot-ending leg now uses the print’s shared costume anatomy rather than a uniform typographic stroke: full short trousers gather into a distinct cuff just below the knee, the stockinged lower leg swells into a noticeable calf muscle, an inset contour marks the gastrocnemius/shin transition, and the silhouette narrows decisively through the ankle into the attached shoe. Each glyph retains its own historical hip, knee, ankle, and toe direction, including horizontal, kneeling, inverted, and foreshortened poses. M keeps its deliberately enormous custom calf pillars with explicit knee cuffs; N grounds its broad bent knee beside the inverted head before raising the gray calf; and Q now builds its ring from two clearly cuffed bent legs whose calves taper into joined apex shoes. O remains the deliberate visibility exception because its lower torso is hidden by the aerial view and only compressed feet are exposed.

## Historical construction notes

- **A:** rebuilt as a two-person letter after the Mitelli engraving. A single folded body could not carry the shape at believable proportions, so two mirrored figures lean toward one another: each raises the inner arm straight to a sharp apex where the flat hands press together, and each lower arm bends gently at the elbow to jointly hold a round object at hip level that reads as the crossbar. Each figure stands on a straight weight-bearing outer leg with the inner leg set slightly forward and softly bent.
- **B:** rebuilt so both bowls actually close and the letter is no longer mistakable for R. The upright stem carries two stacked bowls: the smaller upper one is made by two shortened arms clasping at the right, and the larger lower one by the leg, which sweeps out from the hip, curves down and back in, and plants its foot against the base of the stem to seal the bowl. The second leg stays straight beneath the body, carrying the stem to the baseline.
- **D / H:** only the asymmetric eye, nose, and cocked-hat details are horizontally mirrored; their attached heads and established body constructions remain fixed.
- **H:** rebuilt from a two-person reference: two figures stand straight in profile facing one another, each forming an upright stem with a head, vertical torso, and two planted legs. The two figures act as the vertical sides of the letter. Both arms are bent to a right angle at the elbow: the upper arm — shoulder to elbow — hangs strictly vertically downward alongside the figure's own pillar and is carried proud of it, joined back at the shoulder by a deltoid wedge, so the shoulder-to-elbow run stays a visible separate limb instead of merging into the torso. Only the forearm turns out horizontally. The two front forearms meet and clasp at the centre, so the crossbar is made of forearms alone and sits exactly at elbow height. Each elbow carries a joint ball and an engraved crease wrapping from the vertical upper arm onto the horizontal forearm. The back arm repeats the same vertical-upper-arm bend but its forearm stays short and tucked in, taking no part in the bar.
- **D:** rebuilt as a deep backbend over a kneeling stance. Chest, hips and thighs stack into one straight upright stem with the head facing left at the sharp top-left corner. The arm sweeps up from the shoulder and arches dramatically back and down behind the torso to form the upper curve, while the lower legs fold backward at the kneeling knees and rise to meet the descending hand — hand and feet closing the loop in mid-air behind the body to complete the curved belly.
- **E:** the broad baseline leg joins directly and seamlessly to the vertical seated torso, while the slimmer near leg remains separately visible above it.
- **G:** a flat aerial open ring. The curved body and limbs leave a distinct right-side gap; the right hand returns horizontally inward as the G terminal, while the legs complete the lower loop.
- **Spacing (all glyphs):** the font is proportionally spaced. Each outline is translated so its ink begins exactly one 72-unit sidebearing from the glyph origin, and its advance is that ink width plus a matching sidebearing on the right, so every pair of letters clears by the same gap. The advance is deliberately not capped at the em: the widest poses (W and X span almost the whole em) would otherwise be left with a couple of units of sidebearing and collide with their neighbours.
- **Engraved detail (all glyphs):** knee hems, calf contours, and body seams are now held well inside the limb they model. Previously several ran out to the silhouette edge, where they notched the outline and made overlapping limbs look torn rather than engraved.
- **I:** the source’s rigid straight posture now uses a realistic head, torso, thigh, calf, and arm ratio rather than an overlong trunk above abbreviated legs. The trunk is narrowed and the hanging arms are drawn slimmer and set just clear of it, with an engraved seam down each side, so shoulders, arms, and hands stay legible instead of fusing into one column. Torso, arms and legs are sized on the font's own baseline ratios (arm 1.22x torso, leg ~1.8x torso), so the glyph whose whole point is ordinary human balance actually measures like a normal figure, with the hands reaching mid-thigh.
- **J:** rebuilt as a seated hook. The torso and head rise straight up as the vertical stem, the head turned right to make the small top-right serif. Below the waist the hips and upper thighs curve down and sweep forward to the left, and the bent knees send the lower legs back up to close the bottom hook. The arms hang straight down along the sides of the torso, carried just proud of it — with a deltoid wedge at each shoulder — so the shoulder-to-hand run stays visible against the stem.
- **K:** the upper arm drops to a clear elbow before its forearm rises into an attached hand serif; the thumb and index finger project sharply while the other three fingers fold into the palm. Full short breeches, below-knee cuffs, and long calf/shin cuts model both lower leg strokes.
- **L:** rebuilt as a figure lying flat on its back with the hips flexed to a right angle. Because the legs plus lower torso are naturally longer than the upper torso, lifting them completely straight up makes the tall vertical stem, with the knees locked for rigidity and the toes pointing up as a terminal peak. The upper back, shoulders and head lie flat along the ground running right to form the shorter horizontal base, and the arms rest on the floor with the hands near the head, adding weight to the end of the bar.
- **M:** rebuilt from the body's own hinges instead of the old impossible split figure. Both arms drop straight down behind the back as the left stem, shoulders locked to carry the torso's weight; the torso then leans back from the hips to make the inner down-slope into the central valley; the thighs pull up toward the chest and the knees flex deeply to throw the sharp apex; and the lower legs descend as the right stem. Hand and foot become the typographic serifs: the left hand is bent horizontally at the wrist with fingers splayed flat on the ground, and the right foot extends forward from the ankle, planted flat.
- **N:** rebuilt as a dynamic back-bend. The straight arms are planted on the ground and stand vertically to form the left stroke, with flat supporting hands pressed on the floor; the torso and thighs slope down-right from the shoulders to the knees as the diagonal; and the knees rest on the ground so both lower legs rise straight up into the air as the right stroke. The head hangs back past the planted shoulders.
- **O:** a recumbent aerial ring with smooth shoulder-to-elbow arcs and visible side knee/elbow joints. Its inverted bottom face looks upward, the apex hands visibly clasp, and only two small foreshortened feet remain above the hidden lower torso.
- **P:** rebuilt as a single upright figure. Head, straight torso and closely planted legs stack into the solid left stem. The whole upper bowl is made by one arm, which leaves the shoulder and exaggerates into a smooth rubbery curve out and down, closing on the hand planted on the hip at the torso's midline. The far arm hangs straight down the opposite side, tucked in so it never breaks the letter's silhouette.
- **Q:** two inverted, short-breeched legs form the ring; side knee cuffs articulate the bends and tapered calves meet in small inward apex shoes. Its bottom face is inverted like O. The tail arm is shortened to a normal reach, begins inside a reinforced right shoulder socket, and terminates in a visible hand.
- **R:** the upper bowl is rebuilt on B's construction — two shortened clasped arms with normal shoulder-elbow-hand spans, short interior elbow and sleeve creases that never break the outline, and generously overlapping palms closing the loop as one solid continuous shape — replacing the single distorted overlong arm that looped out and back. Hips were also raised to mid-stem so the legs match the trunk. The planted shoe still projects clearly to the figure's right, matching the crop.
- **F:** hips raised to mid-stem and the legs lengthened and given fuller breeches, so the trunk and legs balance as in T.
- **S:** rebuilt so the naturally longer lower limbs sweep the largest curves. The legs and lower torso rise and arch forward to make the elongated upper hook and top terminal, feet pointing up and to the right; the hips flex sharply so the thighs carry the diagonal spine down and back across the middle; and the upper torso, neck and head curl along the floor to the left, the head resting at the very bottom facing up to close the lower baseline hook.
- **T:** wide horizontal arms form the crossbar while two close legs descend vertically. Torso-to-leg proportion follows a standing human reference: the trunk stops at hip height around the middle of the stem, and the legs below it are the same length as the torso, thickened and set slightly apart so both read individually rather than as one stub.
- **X:** rebuilt against a spread-eagle reference photograph. The figure is a true Vitruvian diagonal — arms raised to the upper corners, legs spread to the lower corners — with arms and legs sharing one limb width that stays clearly under the torso, and open hands with splayed fingers at the raised terminals.
- **Y:** matched to the same reference. The head sits at the cap line, the arms rise diagonally to form the fork, and the paired legs descend as the stem; arms and legs again share a single limb width narrower than the torso, and the hands are open like X's. Cap height is aligned with T and V.
- **W:** the outer knees are lowered to the baseline, where the two inner hands support the figure with visible index fingers and thumbs; the outer stockinged legs retain the source’s raised-foot topology.
- The detailed A–I, K–T, V–Z mapping is recorded in `reference-crops/historical-pose-map.md`.

## Anatomical audit policy

`validate_anatomy.py` measures thigh, calf, arm, torso/spine, and head dimensions from source centerlines against A with a ±5% threshold. The report deliberately flags historical distortions instead of silently normalizing them. It is a **diagnostic**, not the release gate, because strict normalization would destroy the approved surreal constructions—most visibly M, N, O, Q, V, and W.

The standard monochrome TTF/WOFF outlines preserve pose topology rather than the engraving’s paper texture, color, or raster shading. Restrained punched contours supply facial, overlap, cuff, and muscle detail where ordinary scalable font outlines permit; G, O, and Q omit the former dangling decorative artifacts, while O retains a functional clasp seam and Q retains only anatomical knee/calf engraving. Hat brims and shoes are filled vector terminals rather than raster decoration. The face is intended for playful display settings rather than body text. Please treat the poses as typographic fiction, not exercise instructions.
