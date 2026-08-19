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
  NOTE: this crop is no longer the source of the shipped E. The shipped
  E now comes from a separate reference with both arms folded at the
  elbow and the head tucked low beneath the top forearm, which closes
  the stem-to-top-bar junction and reads better at text sizes. The crop
  is kept here for provenance and comparison.
- `U.png` - row 4, second cell. Lying on the back with the rounded back
  and hips on the floor as the bowl, both legs pressed together and
  raised vertically as one stem and both arms extended vertically as
  the other, the flexed feet and the open flat hands making the two
  serifs at equal height.
- `image_fc2e377e.png` - high-resolution photographic reference for J.
  In profile, both straight joined legs rise as the single tall right
  stem; the curled hips and torso sweep through the bottom hook; and the
  tucked head and bent arms make a compact lower-left terminal. Unlike
  the small poster crops, this reference can anchor natural anatomy
  directly before conversion to a flat silhouette.
