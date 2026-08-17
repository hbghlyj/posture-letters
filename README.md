# Posture Master

![The A–Z glyph set](glyph-sheet.svg)

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
- **B:** rebuilt on the shared P/R stance so the three letters are one family. Head, upright torso and the perfectly straight standing leg make the vertical stem; the near arm loops out from the shoulder in the same smooth rubbery curve and tucks back with its hand at the waist to close the upper bowl; and the other leg lifts, bows outward at the knee and tucks back so its foot rests against the standing ankle, closing the lower bowl. The far arm hangs straight down, blending into the stem.
- **D / H:** only the asymmetric eye, nose, and cocked-hat details are horizontally mirrored; their attached heads and established body constructions remain fixed.
- **H:** rebuilt from a two-person reference: two figures stand straight in profile facing one another, each forming an upright stem with a head, vertical torso, and two planted legs. The two figures act as the vertical sides of the letter. Both arms are bent to a right angle at the elbow: the upper arm — shoulder to elbow — hangs strictly vertically downward alongside the figure's own pillar and is carried proud of it, joined back at the shoulder by a deltoid wedge, so the shoulder-to-elbow run stays a visible separate limb instead of merging into the torso. Only the forearm turns out horizontally. Upper arm and forearm are held to the same length, matching real skeletal proportion: the shoulders and the bar are both dropped and the two figures stand closer together, which shortens the crossbar and lowers it while keeping the two segments equal. The two front forearms meet and clasp at the centre, so the crossbar is made of forearms alone and sits exactly at elbow height. Each elbow carries a joint ball and an engraved crease wrapping from the vertical upper arm onto the horizontal forearm. The back arm repeats the same vertical-upper-arm bend but its forearm stays short and tucked in, taking no part in the bar.
- **D:** rebuilt as a deep backbend over a kneeling stance. Chest, hips and thighs stack into one straight upright stem with the head facing left at the sharp top-left corner. The arm sweeps up from the shoulder and arches dramatically back and down behind the torso to form the upper curve, while the lower legs fold backward at the kneeling knees and rise to meet the descending hand — hand and feet closing the loop in mid-air behind the body to complete the curved belly.
- **E:** the two arm crossbars now run dead horizontal and end in open hands, matching F's construction — previously the top bar rose and the middle bar fell away, so the prongs read as drooping limbs rather than deliberate bars. The seated stem and the paired baseline legs are unchanged.
- **G:** a flat aerial open ring. The curved body and limbs leave a distinct right-side gap; the right hand returns horizontally inward as the G terminal, while the legs complete the lower loop.
- **Spacing (all glyphs):** the font is proportionally spaced. Each outline is translated so its ink begins exactly one 72-unit sidebearing from the glyph origin, and its advance is that ink width plus a matching sidebearing on the right, so every pair of letters clears by the same gap. The advance is deliberately not capped at the em: the widest poses (W and X span almost the whole em) would otherwise be left with a couple of units of sidebearing and collide with their neighbours.
- **Engraved detail (all glyphs):** knee hems, calf contours, and body seams are now held well inside the limb they model. Previously several ran out to the silhouette edge, where they notched the outline and made overlapping limbs look torn rather than engraved.
- **I:** the source’s rigid straight posture now uses a realistic head, torso, thigh, calf, and arm ratio rather than an overlong trunk above abbreviated legs. The trunk is narrowed and the hanging arms are drawn slimmer and set just clear of it, with an engraved seam down each side, so shoulders, arms, and hands stay legible instead of fusing into one column. Torso, arms and legs are sized on the font's own baseline ratios (arm 1.22x torso, leg ~1.8x torso), so the glyph whose whole point is ordinary human balance actually measures like a normal figure, with the hands reaching mid-thigh.
- **J:** rebuilt as a kneeling side profile facing right. Head, neck and upright torso align vertically as the straight main stem. At the base the knees turn forward and bend sharply so the lower legs — shins, ankles and feet — swing diagonally upward and backward behind the body, forming the upward-turning hook. The arms hang straight down the sides, blending into the vertical line of the stem.
- **K:** rebuilt as a kneeling figure. Torso, neck, head and the kneeling near leg stack into one plumb line with the knee planted directly under the torso, giving the letter a dead-vertical left side. The kneel is explicit rather than implied: the thigh drops vertically to a kneecap resting on the ground, drawn as a rounded weight-bearing bulb, and the shin then turns a right angle and lies flat along the floor with the foot trailing behind. The far leg extends well out to the side at a bent knee, so the lower diagonal gets the extra length a K needs to look balanced against the short lower stem. The near arm raises straight up and out at about forty-five degrees as the upper diagonal, ending in an open hand serif, and the far arm is pinned flat along the hip and thigh so the centre stays solid with no trapped white between the two diagonals.
- **L:** rebuilt as a kneeling side profile. The upright upper body — head, straight neck and vertical torso — makes the tall pillar. At its base the posture hinges sharply: the knees turn forward and bend completely so the thighs drop vertically and the lower body pivots into the horizontal plane, the shins and ankles stretching out along the floor as the bottom bar. The feet finish the stroke as a serif, heels and toes adding a slight vertical terminal. The arms hang along the sides, carried just clear of the trunk with an engraved seam so they stay legible against the stem.
- **M:** rebuilt from the body's own hinges instead of the old impossible split figure. Both arms drop straight down behind the back as the left stem, shoulders locked to carry the torso's weight; the torso then leans back from the hips to make the inner down-slope into the central valley; the thighs pull up toward the chest and the knees flex deeply to throw the sharp apex; and the lower legs descend as the right stem. Hand and foot become the typographic serifs: the left hand is bent horizontally at the wrist with fingers splayed flat on the ground, and the right foot extends forward from the ankle, planted flat.
- **N:** rebuilt as a dynamic back-bend. The straight arms are planted on the ground and stand vertically to form the left stroke, with flat supporting hands pressed on the floor; the torso and thighs slope down-right from the shoulders to the knees as the diagonal; and the knees rest on the ground so both lower legs rise straight up into the air as the right stroke. The hands lie flat along the floor as on M, wrists bent and fingers running out horizontally to give the base of the left stroke a serif, and the shin is kept shorter than the whole arm so the right stroke does not out-reach the weight-bearing left one. The head hangs back past the planted shoulders.
- **O:** rebuilt as a backbend ring. The figure leans back from standing until the body closes into a circle: the deep continuous arch of the spine and torso forms the rounded crest at the top, the buttocks and backward-sloping thighs and knees sweep down the left and tuck in at the ankles, and the upper back, neck and arms carry the right side down with the head hanging back inside the ring. At the bottom the planted hands on the right and the shod feet on the left curve toward one another, leaving only a narrow gap to close the shape.
- **P:** rebuilt as a single upright figure. Head, straight torso and closely planted legs stack into the solid left stem. The whole upper bowl is made by one arm, which leaves the shoulder and exaggerates into a smooth rubbery curve out and down, closing on the hand planted on the hip at the torso's midline. The far arm hangs straight down the opposite side, tucked in so it never breaks the letter's silhouette.
- **Q:** two inverted, short-breeched legs form the ring; side knee cuffs articulate the bends and tapered calves meet in small inward apex shoes. Its bottom face is inverted like O. The tail arm is shortened to a normal reach, begins inside a reinforced right shoulder socket, and terminates in a visible hand.
- **R:** built directly on P's stance, differing only in the lower limbs. Head, upright torso and the firmly planted straight leg align vertically as the left backbone; the same single arm arches out from the shoulder in a smooth elongated curve and hooks back in, the hand resting flat against the waist to close the loop at the body's midline; and the other leg extends sharply down and out to the right, its foot planted at an angle to form R's stabilising diagonal.
- **F:** rebuilt so both arms make the crossbars. Head, upright torso and two tightly parallel legs form the solid vertical trunk; the near arm extends horizontally straight out from the shoulder as the longer top prong; and the far arm crosses over the front of the chest — marked by a short engraved seam where it passes the trunk — and runs out lower down, dead parallel to the first, as the slightly shorter middle prong. Both bars are exactly horizontal and both feet face forward at the base.
- **S:** rebuilt so the naturally longer lower limbs sweep the largest curves. The legs and lower torso rise and arch forward to make the elongated upper hook and top terminal, feet pointing up and to the right; the hips flex sharply so the thighs carry the diagonal spine down and back across the middle; and the upper torso, neck and head curl along the floor to the left, the head resting at the very bottom facing up to close the lower baseline hook.
- **T:** the straight spine, narrow hips and tightly closed legs make the central pillar, and both arms now extend dead level at ninety degrees from the shoulders so the crossbar is one continuous top line rather than two drooping limbs. At each end the wrist flexes downward and the hand hangs as a terminal, mimicking the downward serifs of a typographic T, while the feet flare outward at the base as stabilising foot serifs.
- **X:** rebuilt against a spread-eagle reference photograph. The figure is a true Vitruvian diagonal — arms raised to the upper corners, legs spread to the lower corners — with arms and legs sharing one limb width that stays clearly under the torso, and open hands with splayed fingers at the raised terminals.
- **Y:** rebuilt as a seated figure, deliberately contrasted with the standing T. Both arms extend up and outward from the shoulders in a wide V with the open palms turned upward, instead of T's flat horizontal bar. Below, the body is condensed into a tight frontal squat: the knees come up close against the chest and the shins and feet run vertically down the front of the body, giving a short, thick central column that grounds the letter. The head sits centrally between the shoulders, exactly where the upper branches converge on the seated torso.
- **V:** the inverted head at the low apex now keeps its face upright with the gaze lifted, as Q does, so the figure looks up out of the apex rather than down into it.
- **W:** the outer knees are lowered to the baseline, where the two inner hands support the figure with visible index fingers and thumbs; the outer stockinged legs retain the source’s raised-foot topology.
- The detailed A–I, K–T, V–Z mapping is recorded in `reference-crops/historical-pose-map.md`.

## Anatomical audit policy

`validate_anatomy.py` measures thigh, calf, arm, torso/spine, and head dimensions from source centerlines against A with a ±5% threshold. The report deliberately flags historical distortions instead of silently normalizing them. It is a **diagnostic**, not the release gate, because strict normalization would destroy the approved surreal constructions—most visibly M, N, O, Q, V, and W.

The standard monochrome TTF/WOFF outlines preserve pose topology rather than the engraving’s paper texture, color, or raster shading. Restrained punched contours supply facial, overlap, cuff, and muscle detail where ordinary scalable font outlines permit; G, O, and Q omit the former dangling decorative artifacts, while O retains a functional clasp seam and Q retains only anatomical knee/calf engraving. Hat brims and shoes are filled vector terminals rather than raster decoration. The face is intended for playful display settings rather than body text. Please treat the poses as typographic fiction, not exercise instructions.
- **Z:** rebuilt as a side profile combining a dramatic backward lean with flat arm extensions. Both arms reach horizontally out from the shoulders as the top bar, the hands held completely flat in line with the forearms so the stroke tapers to a thinner tip like a stylised pen stroke. The torso leans back from the knees in one straight diagonal with no bend at the waist, linking the top bar to the base. The shins and ankles rest flat along the floor as the bottom bar, and at its back end the heels and upturned toes lift into a vertical foot serif anchoring the corner.
