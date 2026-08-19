# 2 Way Stretch yoga alphabet

`two-way-stretch-alphabet.jpg` is the full poster: a complete A-Z plus
0-9 alphabet in which every character is formed by one or two people in
a yoga pose, shot in pale leotards against white. It is the source
series that several of this font's letters were matched against.

The poster is only 358x570, so an individual letter crops out at around
70x70 pixels - too soft to feed straight into the tracer. The working
method is to crop the letter, upscale it, and pass that crop to the
image model as a *reference* for a clean silhouette, rather than
tracing the blurred crop directly. The crop fixes the pose and the limb
proportions; the model supplies the sharp edges.

Crops kept here:

- `G.png` - row 2, first cell. Seated in profile, spine curled into a
  deep rounded C as the left bowl, knees drawn up to close the lower
  right, both arms arcing overhead with the hands dropping into a short
  hook as the spur.
- `E.png` - row 1, fifth cell. Kneeling in profile, shins along the
  floor as the bottom bar and the spine upright as the stem, one arm
  stretched straight forward above the head as the long top bar and the
  other stretched straight forward at mid-chest height as a shorter
  middle prong. Neither elbow is tucked.
- `U.png` - row 4, second cell. Lying on the back with the rounded back
  and hips on the floor as the bowl, both legs pressed together and
  raised vertically as one stem and both arms extended vertically as
  the other, the flexed feet and the open flat hands making the two
  serifs at equal height.
