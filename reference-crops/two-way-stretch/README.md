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
- `N.png` - row 3, first cell, cropped from source box `(31, 307, 80, 371)`
  and enlarged from 49×64 to 588×768 pixels for reference. Balancing in side
  profile, one straight supporting arm descends to a planted hand as the left
  stem, the head and torso travel diagonally down into the low hips, and one
  joined raised leg makes the tall right stem. This crop is the source of the
  shipped N; its chest, waist, pelvis, thigh, and calf remain organically
  curved so the diagonal does not become a ruled bar.
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
- `U.png` - photographic study matching the current U construction: a
  side-profile gymnast lying on the back, arms rising as one stem and
  joined legs rising as the other, with a rounded hip-and-torso bowl.
- `image_6a52f7c6.png` - current high-resolution silhouette source for
  the shipped U. Both arms rise as the left stem and finish in a compact
  inward hand serif; the rounded hips and torso make the bowl; both
  joined legs rise as the right stem to pointed feet. The profile head
  sits on the left stem without closing the open counter, and both stems
  reach the same height. Trace this file rather than the softer poster
  crop.
- `image_fc2e377e.png` - previous high-resolution photographic reference
  for J, retained for provenance. Its joined upright legs and compact
  lower-left terminal informed the superseded trace, but its pointed feet
  supplied no clear upper serif.
- `image_91f51c7c.png` - previous high-resolution photographic reference for
  J, retained for provenance. Its joined legs, left-pointing feet, and broad
  hook informed the superseded trace.
- `image_89bd1753.png` - current high-resolution photographic reference for
  J. In profile, both straight joined legs rise as the single tall right
  stem; the flexed feet point left as a short top serif; and the hips, back,
  and merged arms sweep through the broad bottom hook. Its naturally neutral
  head and cervical alignment make the compact lower-left terminal without
  bridging the open counter. The shipped glyph is a simplified one-piece
  exterior derived from this pose, with clothing, hand, toe, and facial
  details flattened for reliable text-size rendering.
