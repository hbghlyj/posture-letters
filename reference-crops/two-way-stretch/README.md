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

- `N.png` - row 3, first cell, cropped from source box `(31, 307, 80, 371)`
  and enlarged from 49×64 to 588×768 pixels for reference. Balancing in side
  profile, one straight supporting arm descends to a planted hand as the left
  stem, the head and torso travel diagonally down into the low hips, and one
  joined raised leg makes the tall right stem. This crop is the source of the
  shipped N; its chest, waist, pelvis, thigh, and calf remain organically
  curved so the diagonal does not become a ruled bar.
- `U.png` - photographic study matching the current U construction: a
  side-profile gymnast lying on the back, arms rising as one stem and
  joined legs rising as the other, with a rounded hip-and-torso bowl.
  The traced silhouette is `assets/silhouettes/u.png`.
- `V.png` - current high-resolution photographic reference for the
  shipped V. Two equal legs rise from a compact rounded buttocks apex
  as the strokes of a capital V, with natural thigh-to-calf taper and
  outward-turned shod feet as the upper terminals. The photograph is
  converted to a one-piece silhouette before tracing.

The current J photograph is `assets/j_gymnast_photo.png`.
