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
- `glyph-sheet.svg` / `glyph-sheet.png` — A–Z visual overview
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
- en dash and em dash aliases

The original print uses a 24-letter alphabet and omits **J** and **U**. Those two modern-coverage glyphs are editorial interpolations and are not represented as historical reconstructions.

## Hat-and-shoe serif system

The face treats costume as letter anatomy: most head-bearing performers wear a compact cocked hat whose brim projects like a serif, while each shoe follows its source-specific toe direction at the actual foot endpoint. The terminals follow the pose rather than being relocated to conventional typographic corners. A’s paired shoes turn left/inward as in the print; F, K, and R point both profile shoes right; E, G, and L raise their toes; and P and X use outward left/right pairs. O retains deliberately tiny foreshortened shoes, while Q’s two compact shoes turn inward and meet at the apex of its inverted leg ring. M keeps its source-visible upward face at the central dip but does not invent a hat where none is visible; its two outer shoes flare outward from the actual pillar feet.

## Below-knee breeches and calf system

Every visible foot-ending leg now uses the print’s shared costume anatomy rather than a uniform typographic stroke: full short trousers gather into a distinct cuff just below the knee, the stockinged lower leg swells into a noticeable calf muscle, an inset contour marks the gastrocnemius/shin transition, and the silhouette narrows decisively through the ankle into the attached shoe. Each glyph retains its own historical hip, knee, ankle, and toe direction, including horizontal, kneeling, inverted, and foreshortened poses. M keeps its deliberately enormous custom calf pillars with explicit knee cuffs; N grounds its broad bent knee beside the inverted head before raising the gray calf; and Q now builds its ring from two clearly cuffed bent legs whose calves taper into joined apex shoes. O remains the deliberate visibility exception because its lower torso is hidden by the aerial view and only compressed feet are exposed.

## Historical construction notes

- **A:** a complete forward fold. Hips form the apex; full short breeches narrow through below-knee cuffs into engraved, muscular calf/shin contours on the right; both shoes turn left; the attached torso descends on the left to an inverted head; two horizontal arms grip the knees as the crossbar.
- **B:** the left leg remains separately planted while the right leg bends outward at a visible knee and curls inward on a shortened calf to form the lower bowl. Both upper loop arms are shortened to normal anatomical proportions.
- **D / H:** only the asymmetric eye, nose, and cocked-hat details are horizontally mirrored; their attached heads and established body constructions remain fixed.
- **E:** the broad baseline leg joins directly and seamlessly to the vertical seated torso, while the slimmer near leg remains separately visible above it.
- **G:** a flat aerial open ring. The curved body and limbs leave a distinct right-side gap; the right hand returns horizontally inward as the G terminal, while the legs complete the lower loop.
- **I:** the source’s rigid straight posture now uses a realistic head, torso, thigh, calf, and arm ratio rather than an overlong trunk above abbreviated legs.
- **K:** the upper arm drops to a clear elbow before its forearm rises into an attached hand serif; the thumb and index finger project sharply while the other three fingers fold into the palm. Full short breeches, below-knee cuffs, and long calf/shin cuts model both lower leg strokes.
- **M:** the print’s deliberately impossible joke retains its upward face, pale cupping hands, paired buttocks, central cleft, cuffed muscular outer pillars, and outward shoes without the former hanging center appendage.
- **N:** the inverted head and broad bent knee now share one ground plane. A human-length sleeve descends from the raised inner corner across the front of the blue body, with a narrow overlap halo and projecting hand that make the N diagonal explicit before the far calf rises to its shoe.
- **O:** a recumbent aerial ring with smooth shoulder-to-elbow arcs and visible side knee/elbow joints. Its inverted bottom face looks upward, the apex hands visibly clasp, and only two small foreshortened feet remain above the hidden lower torso.
- **P:** two shortened, separately contoured backward-bending arms—with explicit elbows, wrists, and clasped hands—form a compact upper loop at normal anatomical lengths. Gathered cuffs and modeled calves lead to the source-directed outward shoe pair.
- **Q:** two inverted, short-breeched legs form the ring; side knee cuffs articulate the bends and tapered calves meet in small inward apex shoes. The tail arm is shortened to a normal reach, begins inside a reinforced right shoulder socket, and terminates in a visible hand.
- **R:** the planted shoe now projects clearly to the figure’s right, matching the crop instead of appearing reversed.
- **T:** wide horizontal arms form the crossbar while two close legs descend vertically.
- **W:** the outer knees are lowered to the baseline, where the two inner hands support the figure with visible index fingers and thumbs; the outer stockinged legs retain the source’s raised-foot topology.
- The detailed A–I, K–T, V–Z mapping is recorded in `reference-crops/historical-pose-map.md`.

## Anatomical audit policy

`validate_anatomy.py` measures thigh, calf, arm, torso/spine, and head dimensions from source centerlines against A with a ±5% threshold. The report deliberately flags historical distortions instead of silently normalizing them. It is a **diagnostic**, not the release gate, because strict normalization would destroy the approved surreal constructions—most visibly M, N, O, Q, V, and W.

The standard monochrome TTF/WOFF outlines preserve pose topology rather than the engraving’s paper texture, color, or raster shading. Restrained punched contours supply facial, overlap, cuff, and muscle detail where ordinary scalable font outlines permit; G, O, and Q omit the former dangling decorative artifacts, while O retains a functional clasp seam and Q retains only anatomical knee/calf engraving. Hat brims and shoes are filled vector terminals rather than raster decoration. The face is intended for playful display settings rather than body text. Please treat the poses as typographic fiction, not exercise instructions.
