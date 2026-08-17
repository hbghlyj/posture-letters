#!/usr/bin/env python3
"""Build Posture Master, a deliberately bendy human-alphabet display font.

The design is an original geometric reinterpretation of the supplied
18th-century posture-master print. All outlines are generated from simple
body-part primitives so the font remains editable and reproducible.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
UPM = 1000
ADVANCE = 700
# Constant space kept on each side of a glyph's ink when fitting its advance.
SIDEBEARING = 72

Point = tuple[float, float]


def area(poly: list[Point]) -> float:
    return sum(
        poly[i][0] * poly[(i + 1) % len(poly)][1]
        - poly[(i + 1) % len(poly)][0] * poly[i][1]
        for i in range(len(poly))
    ) / 2


def catmull_rom(points: list[Point], steps: int = 10) -> list[Point]:
    if len(points) < 3:
        return points
    padded = [points[0], *points, points[-1]]
    out: list[Point] = []
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1 : i + 3]
        for j in range(steps):
            t = j / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            out.append((x, y))
    out.append(points[-1])
    return out


def ribbon(points: list[Point], width: float, smooth: bool = True) -> list[Point]:
    pts = catmull_rom(points, 8) if smooth and len(points) >= 3 else points
    clean: list[Point] = []
    for p in pts:
        if not clean or math.dist(p, clean[-1]) > 0.01:
            clean.append(p)
    if len(clean) < 2:
        return []
    half = width / 2
    left: list[Point] = []
    right: list[Point] = []
    for i, (x, y) in enumerate(clean):
        p0 = clean[max(0, i - 1)]
        p1 = clean[min(len(clean) - 1, i + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left + list(reversed(right))


def tapered_ribbon(
    points: list[Point], widths: list[float], smooth: bool = True, steps: int = 8
) -> list[Point]:
    """Expand a centerline using a width profile instead of a uniform stroke."""
    if len(points) != len(widths):
        raise ValueError("Each tapered-ribbon point needs one width")
    if len(points) < 2:
        return []

    if smooth and len(points) >= 3:
        padded = [points[0], *points, points[-1]]
        dense_points: list[Point] = []
        dense_widths: list[float] = []
        for i in range(1, len(padded) - 2):
            p0, p1, p2, p3 = padded[i - 1 : i + 3]
            for j in range(steps):
                t = j / steps
                t2, t3 = t * t, t * t * t
                dense_points.append((
                    0.5 * (
                        2 * p1[0] + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                    ),
                    0.5 * (
                        2 * p1[1] + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                    ),
                ))
                dense_widths.append(widths[i - 1] + (widths[i] - widths[i - 1]) * t)
        dense_points.append(points[-1])
        dense_widths.append(widths[-1])
    else:
        dense_points = points
        dense_widths = widths

    clean_points: list[Point] = []
    clean_widths: list[float] = []
    for point, width in zip(dense_points, dense_widths):
        if not clean_points or math.dist(point, clean_points[-1]) > 0.01:
            clean_points.append(point)
            clean_widths.append(width)
    if len(clean_points) < 2:
        return []

    left: list[Point] = []
    right: list[Point] = []
    for i, ((x, y), width) in enumerate(zip(clean_points, clean_widths)):
        p0 = clean_points[max(0, i - 1)]
        p1 = clean_points[min(len(clean_points) - 1, i + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        half = width / 2
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left + list(reversed(right))


class Drawer:
    def __init__(self) -> None:
        self.contours: list[tuple[list[Point], bool]] = []
        # Source-level skeletal measurements used by validate_anatomy.py.
        # Lengths follow centerline control points, before stroke expansion.
        self.anatomy: list[dict[str, object]] = []

    @staticmethod
    def centerline_measurements(pts: list[Point]) -> tuple[list[float], float]:
        segments = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        return segments, sum(segments)

    def polygon(self, pts: Iterable[Point], hole: bool = False) -> None:
        poly = [(round(x, 2), round(y, 2)) for x, y in pts]
        if len(poly) < 3:
            return
        # TrueType convention: outer contours clockwise, counters anticlockwise.
        should_be_positive = hole
        if (area(poly) > 0) != should_be_positive:
            poly.reverse()
        self.contours.append((poly, hole))

    def circle(self, x: float, y: float, r: float, hole: bool = False, n: int = 20) -> None:
        self.polygon(
            [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)],
            hole,
        )

    def ellipse(self, x: float, y: float, rx: float, ry: float, angle: float = 0, hole: bool = False) -> None:
        c, s = math.cos(angle), math.sin(angle)
        pts = []
        for i in range(20):
            t = 2 * math.pi * i / 20
            px, py = rx * math.cos(t), ry * math.sin(t)
            pts.append((x + px * c - py * s, y + px * s + py * c))
        self.polygon(pts, hole)

    def path(
        self,
        pts: list[Point],
        width: float = 52,
        smooth: bool = True,
        joints: bool = True,
        track: bool = True,
    ) -> None:
        poly = ribbon(pts, width, smooth)
        if poly:
            self.polygon(poly)
        if joints:
            for x, y in pts:
                self.circle(x, y, width / 2)
        if track:
            segments, length = self.centerline_measurements(pts)
            self.anatomy.append(
                {"part": "composite_path", "segments": segments, "length": length, "points": pts}
            )

    def cut_path(self, pts: list[Point], width: float = 6, smooth: bool = True) -> None:
        """Punch a fine engraved line through a filled body contour."""
        poly = ribbon(pts, width, smooth)
        if poly:
            self.polygon(poly, hole=True)

    def tapered_path(
        self, pts: list[Point], widths: list[float], smooth: bool = True
    ) -> None:
        """Draw a continuous body part with a controlled anatomical profile."""
        poly = tapered_ribbon(pts, widths, smooth)
        if poly:
            self.polygon(poly)

    @staticmethod
    def polyline_point(pts: list[Point], fraction: float) -> Point:
        """Return a point at an arc-length fraction of a control polyline."""
        if not pts:
            raise ValueError("Cannot sample an empty polyline")
        if len(pts) == 1:
            return pts[0]
        lengths = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        total = sum(lengths) or 1.0
        target = max(0.0, min(1.0, fraction)) * total
        walked = 0.0
        for a, b, segment in zip(pts, pts[1:], lengths):
            if walked + segment >= target:
                local = 0.0 if segment == 0 else (target - walked) / segment
                return (a[0] + (b[0] - a[0]) * local,
                        a[1] + (b[1] - a[1]) * local)
            walked += segment
        return pts[-1]

    def leg(
        self,
        pts: list[Point],
        width: float = 54,
        knee_index: int = 1,
        breeches_width: float | None = None,
        shoe_direction: Point | None = None,
        shoe_scale: float = 1.0,
        anatomy_points: list[Point] | None = None,
    ) -> None:
        """Draw short breeches, a knee cuff, muscular calf, ankle, and shoe.

        Every historical foot-ending limb uses this construction. The trousers
        stay full through the thigh and stop just below the indexed knee; the
        stockinged lower leg then swells at the gastrocnemius before narrowing
        decisively into the ankle. The centerline and shoe endpoint remain the
        source pose's own, so anatomy does not regularize the letter geometry.
        """
        if not 0 < knee_index < len(pts) - 1:
            raise ValueError("A leg needs hip, interior knee, and ankle points")
        breeches = breeches_width if breeches_width is not None else width * 1.22
        upper = pts[:knee_index + 1]
        lower = pts[knee_index:]
        upper_fractions = (0.0, 0.32, 0.68, 1.0)
        lower_fractions = (0.0, 0.14, 0.38, 0.66, 1.0)
        upper_profile = [self.polyline_point(upper, f) for f in upper_fractions]
        lower_profile = [self.polyline_point(lower, f) for f in lower_fractions]

        # Full, gathered knee-breeches over a visibly articulated stockinged leg.
        self.tapered_path(
            upper_profile,
            [breeches * 0.94, breeches * 1.10, breeches * 1.02, breeches * 0.78],
            True,
        )
        self.tapered_path(
            lower_profile,
            [width * 0.78, width * 0.90, width * 1.22, width * 0.82, width * 0.50],
            True,
        )

        # Thigh and shin are separate tapered strokes with flat ends, so at a
        # bent knee their two square ends leave a sharp beveled wedge. A round
        # joint mass at the knee point fills that wedge, giving the outline the
        # continuous curve of a real knee instead of a blocky corner.
        knee = pts[knee_index]
        joint_r = max(width, breeches * 0.82) * 0.52
        self.circle(knee[0], knee[1], joint_r, n=24)

        next_point = lower_profile[1]
        dx, dy = next_point[0] - knee[0], next_point[1] - knee[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        cuff_angle = math.atan2(dy, dx) + math.pi / 2
        self.ellipse(
            knee[0], knee[1], breeches * 0.43, max(6.0, breeches * 0.105), cuff_angle
        )
        # A short inset hem line defines the below-knee end without severing it.
        self.cut_path([
            (knee[0] - nx * breeches * 0.20, knee[1] - ny * breeches * 0.20),
            (knee[0] + nx * breeches * 0.20, knee[1] + ny * breeches * 0.20),
        ], max(2.8, width * 0.055), False)

        # One engraved contour rides the outward belly of the calf and makes
        # the muscle readable even where two legs overlap at specimen scale.
        calf_points = [lower_profile[i] for i in (1, 2, 3)]
        calf_mid = calf_points[1]
        # Pull the two ends toward the belly of the calf so the contour is a
        # short interior stroke; a full-length one runs out to the ankle and
        # knee edges and shreds the leg silhouette where limbs overlap.
        calf_points = [
            (
                calf_mid[0] + (point[0] - calf_mid[0]) * 0.40,
                calf_mid[1] + (point[1] - calf_mid[1]) * 0.40,
            )
            for point in calf_points
        ]
        radial = (calf_mid[0] - 350, calf_mid[1] - 400)
        if nx * radial[0] + ny * radial[1] < 0:
            nx, ny = -nx, -ny
        # Offsets are deliberately conservative: the contour must stay inside
        # the calf so it reads as engraving instead of notching the outline.
        offsets = (width * 0.08, width * 0.14, width * 0.07)
        self.cut_path([
            (point[0] + nx * offset, point[1] + ny * offset)
            for point, offset in zip(calf_points, offsets)
        ], max(2.6, width * 0.055), True)

        measured = anatomy_points if anatomy_points is not None else pts
        segments, measured_length = self.centerline_measurements(measured)
        self.anatomy.append({
            "part": "limb", "segments": segments, "length": measured_length,
            "points": measured,
        })
        ankle = pts[-1]
        self.shoe(
            ankle[0], ankle[1], lower_profile[-2], shoe_direction, shoe_scale
        )

    def shoe(
        self, x: float, y: float, previous: Point, direction: Point | None = None,
        scale: float = 1.0,
    ) -> None:
        """Draw a shoe serif, optionally following a source-specific toe direction."""
        dx, dy = x - previous[0], y - previous[1]
        length = math.hypot(dx, dy) or 1.0
        if direction is not None:
            px, py = direction
            direction_length = math.hypot(px, py) or 1.0
            px, py = px / direction_length, py / direction_length
        else:
            # Default to a cross-leg serif and select the side farthest from
            # the glyph center. Historical poses can override this when the
            # source shoe points forward, upward, or toward a local body axis.
            px, py = -dy / length, dx / length
            radial_x, radial_y = x - 350, y - 400
            if px * radial_x + py * radial_y < 0:
                px, py = -px, -py
        angle = math.atan2(py, px)
        cx, cy = x + px * 14 * scale, y + py * 14 * scale
        self.ellipse(cx, cy, 45 * scale, 17 * scale, angle)
        self.circle(x + px * 46 * scale, y + py * 46 * scale, 16 * scale)

    def limb(
        self,
        pts: list[Point],
        width: float = 48,
        smooth: bool = True,
        end: str = "hand",
        shoe_direction: Point | None = None,
    ) -> None:
        self.path(pts, width, smooth, True, track=False)
        segments, length = self.centerline_measurements(pts)
        self.anatomy.append({"part": "limb", "segments": segments, "length": length, "points": pts})
        x, y = pts[-1]
        if end == "foot":
            previous = pts[-2] if len(pts) > 1 else (x, y - 1)
            self.shoe(x, y, previous, shoe_direction)
        elif end == "hand":
            self.circle(x, y, 27)

    def torso(
        self, pts: list[Point], width: float = 88, smooth: bool = True, joints: bool = True
    ) -> None:
        self.path(pts, width, smooth, joints, track=False)
        segments, length = self.centerline_measurements(pts)
        self.anatomy.append({"part": "torso", "segments": segments, "length": length, "points": pts})

    def hat(
        self, x: float, y: float, tilt: float = 0, scale: float = 1.0,
        mirror_details: bool = False,
    ) -> None:
        """Draw a compact cocked hat whose brim acts as a head-mounted serif."""
        c, s = math.cos(tilt), math.sin(tilt)

        def place(lx: float, ly: float) -> Point:
            px, py = x + lx * c - ly * s, y + lx * s + ly * c
            return (2 * x - px, py) if mirror_details else (px, py)

        brim_x, brim_y = place(0, 49 * scale)
        brim_tilt = math.pi - tilt if mirror_details else tilt
        self.ellipse(brim_x, brim_y, 64 * scale, 9 * scale, brim_tilt)
        self.polygon([
            place(-34 * scale, 48 * scale),
            place(34 * scale, 48 * scale),
            place(27 * scale, 79 * scale),
            place(-24 * scale, 82 * scale),
        ])

    def head(
        self, x: float, y: float, facing: int = 1, tilt: float = 0,
        mirror_details: bool = False, hat: bool = True,
    ) -> None:
        # Head, nose and a small cocked hat. ``tilt`` rotates the facial and
        # hat direction; ``mirror_details`` flips only their asymmetry while
        # leaving the head attachment and body construction undisturbed.
        self.anatomy.append({"part": "head", "diameter": 110.0, "center": (x, y)})
        self.circle(x, y, 55)
        c, s = math.cos(tilt), math.sin(tilt)

        def pt(dx: float, dy: float) -> Point:
            px, py = x + dx * c - dy * s, y + dx * s + dy * c
            return (2 * x - px, py) if mirror_details else (px, py)

        nose_base_top = pt(facing * 43, 12)
        nose_tip = pt(facing * 61, 0)
        nose_base_bottom = pt(facing * 43, -8)
        self.polygon([nose_base_top, nose_tip, nose_base_bottom])
        # Poses whose heads sit in a tight corner can drop the brim: there it
        # crowds the neighbouring limb instead of acting as a serif.
        if hat:
            self.hat(x, y, tilt, mirror_details=mirror_details)
        eye_x, eye_y = pt(facing * 20, 10)
        self.circle(eye_x, eye_y, 7, hole=True, n=12)

    def front_head(
        self, x: float, y: float, radius: float = 58, hair_down: bool = True,
        upside_down: bool = False, gaze_up: bool = False,
    ) -> None:
        """A compact aerial/front-facing head with an anatomical serif-hat.

        ``upside_down`` rotates the facial hierarchy inside a fixed head, while
        ``gaze_up`` adds pupils at the upper edge of the eye sockets. These are
        independent of ``hair_down`` so an inverted recumbent face can retain
        the source-visible hair/hat silhouette beneath the skull.
        """
        self.anatomy.append({"part": "head", "diameter": radius * 2, "center": (x, y)})
        self.ellipse(x, y, radius, radius * 0.9)
        self.circle(x - radius * 0.88, y, radius * 0.19)
        self.circle(x + radius * 0.88, y, radius * 0.19)
        hat_sign = -1 if hair_down else 1
        brim_y = y + hat_sign * radius * 0.72
        self.ellipse(x, brim_y, radius * 1.12, radius * 0.13)
        crown_base = y + hat_sign * radius * 0.70
        crown_top = y + hat_sign * radius * 1.30
        self.polygon([
            (x - radius * 0.57, crown_base),
            (x + radius * 0.57, crown_base),
            (x + radius * 0.43, crown_top),
            (x - radius * 0.49, crown_top),
        ])
        face_sign = -1 if upside_down else 1
        eye_y = y + face_sign * radius * 0.15
        eye_radius = max(5.5, radius * 0.105)
        for eye_x in (x - radius * 0.27, x + radius * 0.27):
            self.circle(eye_x, eye_y, eye_radius, hole=True, n=12)
            if gaze_up:
                self.circle(eye_x, eye_y + radius * 0.055, eye_radius * 0.38, n=10)
        self.cut_path([
            (x, y + face_sign * radius * 0.06),
            (x, y - face_sign * radius * 0.18),
        ], 4, False)
        mouth_y = y - face_sign * radius * 0.30
        mouth_bow = y - face_sign * radius * 0.36
        self.cut_path([
            (x - radius * 0.18, mouth_y),
            (x, mouth_bow),
            (x + radius * 0.18, mouth_y),
        ], 4, True)

    def to_glyph(self, dx: float = 0.0):
        """Build the TrueType glyph, optionally shifted along x.

        Spacing has to move the outline itself: setting a left sidebearing in
        hmtx without translating the contours leaves the ink where it was
        drawn, so neighbouring glyphs still collide however the metrics read.
        """
        pen = TTGlyphPen(None)
        for poly, _hole in self.contours:
            pen.moveTo((poly[0][0] + dx, poly[0][1]))
            for p in poly[1:]:
                pen.lineTo((p[0] + dx, p[1]))
            pen.closePath()
        return pen.glyph()

    def svg_path(self) -> str:
        bits = []
        for poly, _ in self.contours:
            bits.append(f"M {poly[0][0]:.1f} {-poly[0][1]:.1f}")
            bits.extend(f"L {x:.1f} {-y:.1f}" for x, y in poly[1:])
            bits.append("Z")
        return " ".join(bits)


def pose(letter: str) -> Drawer:
    d = Drawer()

    if letter == "A":
        # Two figures build the A, as in the Mitelli engraving: they lean
        # toward one another, press their raised palms flat together at a sharp
        # apex, and jointly hold a round object at hip level whose bar reads as
        # the crossbar. A single folded body could not carry this letter at
        # believable proportions, so the load is shared between two people.
        apex_y = 742
        ball = (350, 352)
        for side in (-1, 1):
            # side -1 is the left figure, +1 the right; each is the mirror of
            # the other about the glyph centre.
            def px(x: float) -> float:
                return 350 + side * (x - 350)

            hip = (px(196), 330)
            shoulder = (px(238), 502)
            # Head turned toward the partner, above a torso that leans inward.
            # Each head turns toward the partner: the two figures look at one
            # another across the letter rather than away from it.
            # No hat: the two brims meet at the apex and collide.
            d.head(px(232), 552, side, hat=False)
            d.torso(
                [(px(228), 496), (px(212), 418), (px(198), 336)], 72, True
            )
            # Raised arm: straight from the shoulder up to the apex, where the
            # flat hand presses against the other figure's hand.
            up_arm = [(px(262), 530), (px(304), 638), (px(338), apex_y - 24)]
            d.path(up_arm, 34, True, False, track=False)
            segments, length = d.centerline_measurements(up_arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": up_arm,
            })
            d.circle(up_arm[0][0], up_arm[0][1], 19)
            # Flat pressed hand: fingers extended straight along the apex line.
            d.polygon([
                (px(330), apex_y - 46), (px(348), apex_y - 4),
                (px(340), apex_y + 2), (px(314), apex_y - 38),
            ])
            d.cut_path([
                (px(326), apex_y - 40), (px(338), apex_y - 18),
            ], 3.4, False)
            # Lower arm: down and forward from the shoulder, bending gently at
            # the elbow to meet the partner's hand on the round object.
            low_arm = [(px(238), 504), (px(256), 396), (px(328), 354)]
            d.path(low_arm, 32, True, False, track=False)
            segments, length = d.centerline_measurements(low_arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": low_arm,
            })
            d.cut_path([
                (px(258), 384), (px(272), 380), (px(286), 386),
            ], 3.6, True)
            # Outer leg: straight and firmly planted, carrying the lean.
            d.leg(
                [(px(186), 326), (px(168), 176), (px(152), 32)], 50,
                knee_index=1, breeches_width=58, shoe_direction=(side, 0),
            )
            # Inner leg: set slightly forward with a gentle bend at the knee.
            # The pair is kept close, as on H, so each figure stands on a
            # tight two-leg base instead of a splayed stance.
            d.leg(
                [(px(212), 326), (px(200), 174), (px(198), 32)], 48,
                knee_index=1, breeches_width=56, shoe_direction=(side, 0),
            )
        # Apex: the two flat hands meet in a sharp peak.
        d.polygon([
            (350, apex_y + 16), (368, apex_y - 30), (332, apex_y - 30),
        ])
        # The two hands clasp at the centre. This uses H's crossbar treatment —
        # a solid ellipse split by one thin seam — rather than a circle with a
        # punched centre, which read as a ring rather than gripped hands.
        d.ellipse(ball[0], ball[1], 40, 28, 0.0)
        d.cut_path([
            (ball[0], ball[1] - 24), (ball[0] + 3, ball[1]),
            (ball[0], ball[1] + 24),
        ], 5.0, True)

    elif letter == "B":
        # B is the P/R stance carrying two loops. Head, upright torso and the
        # perfectly straight standing leg make the vertical stem on the left;
        # the near arm loops out from the shoulder in a smooth rubbery curve
        # and tucks back to rest its hand at the waist, closing the upper bowl;
        # and the other leg lifts, bends outward at the knee in a curved arc
        # and tucks back so its foot rests against the standing ankle, closing
        # the lower bowl. The far arm hangs straight down the opposite side.
        stem_x = 168
        hip_y = 452
        d.head(stem_x - 2, 752, 1)
        d.torso([(stem_x, 690), (stem_x, 570), (stem_x, hip_y)], 86, False)
        # Passive far arm, blending into the stem.
        far_arm = [(stem_x - 30, 654), (stem_x - 38, 570), (stem_x - 34, 492)]
        d.path(far_arm, 28, True, False, track=False)
        d.circle(far_arm[-1][0], far_arm[-1][1], 15)
        # Upper loop: the same rubbery arm curve used on P and R, kept a little
        # smaller so the two bowls stack rather than compete.
        loop = [
            (stem_x + 26, 664), (288, 686), (382, 638),
            (406, 560), (356, 502), (248, 476),
        ]
        d.path(loop, 44, True, False, track=False)
        segments, length = d.centerline_measurements(loop)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": loop,
        })
        d.circle(loop[0][0], loop[0][1], 23)
        d.cut_path([(364, 660), (388, 636), (396, 608)], 4.4, True)
        # Hand closes the upper loop at the waist.
        d.ellipse(238, 480, 27, 23, 0.18)
        d.cut_path([(224, 494), (242, 485), (257, 491)], 4.0, True)
        # Standing leg: perfectly straight, continuing the stem to the baseline.
        d.leg(
            [(stem_x - 14, hip_y), (stem_x - 18, 254), (stem_x - 22, 58)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(-1, 0)
        )
        # Lower loop: the lifted leg bows out at the knee and tucks its foot
        # back against the standing ankle.
        lifted = [(stem_x + 20, hip_y - 8), (404, 306), (214, 128)]
        d.leg(
            lifted, 54, knee_index=1, breeches_width=68,
            shoe_direction=(-0.98, -0.20),
        )

    elif letter == "C":
        # Historical kneeling back-arch: face inside the upper-left opening,
        # arms over the top, and paired shins running right along the ground.
        d.torso([(205, 205), (165, 325), (180, 455), (235, 555)], 90, True)
        d.head(245, 555, 1, 0.18)
        # The arms taper toward the wrist and finish in modelled hands rather
        # than a round terminal: a plain circle at the tip came out wider than
        # the forearm itself and read as a blob beside the tapered shins.
        # The far arm is swung clear of the near one: drawn on the same route
        # the two fused into a single slab, and a cut cannot separate stacked
        # shapes under the nonzero fill rule.
        for arm, base_w in (
            ([(256, 592), (394, 682), (552, 606)], 44),
            ([(244, 566), (382, 652), (536, 578)], 34),
        ):
            d.tapered_path(
                arm + [(arm[-1][0] + 4, arm[-1][1] - 6)],
                [base_w, base_w * 0.92, base_w * 0.66, base_w * 0.52],
                True,
            )
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            wx, wy = arm[-1]
            # Hand: a compact palm with fingers reaching on past the wrist.
            d.ellipse(wx + 12, wy - 12, base_w * 0.40, base_w * 0.30, -0.55)
            for dx, dy in ((10, -30), (20, -24), (26, -14)):
                d.polygon([
                    (wx + 2, wy - 10), (wx + dx, wy + dy),
                    (wx + dx + 8, wy + dy + 5),
                ])
            d.cut_path([
                (wx + 2, wy - 4), (wx + 12, wy - 14), (wx + 20, wy - 20),
            ], 3.4, True)
        d.leg([(205, 210), (315, 115), (555, 105)], 58, knee_index=1)
        d.leg([(225, 210), (335, 145), (525, 140)], 46, knee_index=1)

    elif letter == "D":
        # Deep backbend over a kneeling stance. Chest, hips and thighs stack
        # into one straight upright line as the letter's stem, the head facing
        # left at the sharp top-left corner. The arm sweeps up from the
        # shoulder and arches dramatically back and down behind the torso to
        # make the upper curve, while the lower legs fold back at the kneeling
        # knees and rise to meet the descending hand, closing the belly.
        stem_x = 168
        hip = (stem_x, 356)
        knee = (stem_x + 16, 108)
        meet = (506, 322)
        # Vertical spine: chest and hips.
        d.torso([hip, (stem_x, 500), (stem_x, 644)], 86, False)
        d.head(stem_x - 4, 710, -1)
        # Thighs drop from the hips to the kneeling knees on the ground, then
        # the lower legs fold sharply backward and rise to the enclosure point.
        for sign, spread in ((-1, 0), (1, 26)):
            d.leg(
                [
                    (stem_x + spread * 0.5, 350),
                    (knee[0] + spread, knee[1]),
                    (meet[0] - 62 + spread, meet[1] - 10),
                ],
                56, knee_index=1, breeches_width=74,
                shoe_direction=(0.42, 0.91), shoe_scale=0.82,
            )
        # Upper curve: the arm arches back over the top and down behind.
        # Upper arm and forearm are drawn to the same length: the elbow was
        # sitting far round the arch, leaving a short upper arm feeding a
        # forearm half again as long.
        # The elbow is carried further round the arch so the upper arm and the
        # forearm come out near equal; before, the forearm ran half as long
        # again as the upper arm.
        arm = [
            (stem_x + 34, 640), (296, 734), (440, 676),
            (520, 530), (500, 386),
        ]
        d.path(arm[:3], 46, True, False, track=False)
        d.path(arm[2:], 40, True, False, track=False)
        segments, length = d.centerline_measurements(arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": arm,
        })
        d.circle(arm[0][0], arm[0][1], 24)
        # Elbow crease where the arch turns down behind the body.
        d.circle(410, 700, 22)
        d.cut_path([(404, 726), (428, 706), (430, 678)], 4.4, True)
        # Enclosure point: the reaching hand closes on the raised feet. Hand
        # and feet must stay legible as two separate body parts, so the palm
        # sits above the shoes and an engraved seam runs along the contact
        # line, with finger creases across the palm itself.
        d.ellipse(meet[0] - 12, meet[1] + 56, 27, 23, -0.35)
        # Fingers reach down past the palm onto the shoes.
        for dx in (-22, -8, 6):
            d.polygon([
                (meet[0] + dx - 5, meet[1] + 48),
                (meet[0] + dx + 5, meet[1] + 48),
                (meet[0] + dx + 3, meet[1] + 18),
                (meet[0] + dx - 4, meet[1] + 18),
            ])
        # Engraved seam along the contact line keeps hand and feet legible as
        # two separate body parts rather than one fused mass.
        d.cut_path([
            (meet[0] - 52, meet[1] + 6), (meet[0] - 14, meet[1] - 2),
            (meet[0] + 20, meet[1] + 8),
        ], 6.5, True)

    elif letter == "E":
        # Kneeling E, coordinated limb by limb from the source figure. The
        # torso is turned to her right into a partial side profile and stands
        # dead vertical as the spine of the letter. The right arm is rotated
        # fully at the shoulder and arches over the crown of the head to make
        # the upper prong, and at its tip the hand droops straight down as the
        # top-right serif. The head is nestled directly beneath that arch,
        # tilted forward and facing to her right. The left arm hangs down the
        # flank, flexes about ninety degrees at the elbow and throws the
        # forearm out horizontally as the middle prong, set at the height that
        # halves the counter. The figure has dropped into a deep kneel so the
        # shins lie flat along the ground as the lower prong, and at the back
        # of that stroke the heels flex up into a sharp bottom-right serif.
        stem_x = 172
        hip_y = 306
        d.torso([(stem_x, hip_y), (stem_x, 452), (stem_x, 598)], 84, False)
        # Upper prong: the right arm rotated up out of the shoulder, then
        # arching over the crown and running right. The whole arch sits above
        # the torso's own end, so the limb reads clear of the trunk without
        # needing a seam (an engraved seam is cancelled where fills stack).
        upper = [(158, 592), (146, 686), (316, 740), (512, 734)]
        d.path(upper[:2], 42, False, False, track=False)
        d.path(upper[1:], 38, True, False, track=False)
        segments, length = d.centerline_measurements(upper)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": upper,
        })
        # Shoulder ball and deltoid, and the elbow mass at the top of the arch.
        d.circle(upper[0][0], upper[0][1], 22)
        d.circle(upper[1][0], upper[1][1], 21, n=24)
        # Crease inside the elbow, on the underside of the arch.
        d.cut_path([(140, 660), (172, 698), (214, 714)], 4.0, True)
        # Hand serif: the wrist breaks over a rounded joint and the hand hangs
        # straight down, giving the top-right corner a clean vertical terminal.
        d.circle(512, 734, 20, n=24)
        d.tapered_path([(514, 736), (522, 698), (528, 666)], [36, 31, 26], True)
        d.ellipse(529, 658, 18, 15, 0.0)
        for dx in (-11, -1, 9):
            d.polygon([
                (529 + dx - 4, 654), (529 + dx + 4, 654),
                (529 + dx + 3, 628), (529 + dx - 4, 628),
            ])
        d.cut_path([(516, 704), (542, 700)], 3.2, False)
        # Head nestled under the arch, tilted forward, facing to her right.
        # No hat here: the crown and brim jam straight into the underside of
        # the arching arm in this tight corner (the same reason A and G go
        # bare-headed), leaving the head as one merged blob with the prong.
        d.head(stem_x + 46, 624, 1, -0.34, hat=False)
        # Middle prong: the left arm hangs down the flank, then the elbow
        # flexes forward and the forearm runs out horizontally. The bar height
        # is set so the two counters of the letter come out even.
        bar_y = 414
        shoulder = (200, 586)
        elbow = (268, bar_y + 6)
        d.path([shoulder, (250, 494), elbow], 38, True, False, track=False)
        d.path([elbow, (470, bar_y)], 34, False, False, track=False)
        mid_arm = [shoulder, elbow, (470, bar_y)]
        segments, length = d.centerline_measurements(mid_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": mid_arm,
        })
        d.circle(shoulder[0], shoulder[1], 20)
        d.circle(elbow[0], elbow[1], 20)
        d.cut_path([
            (elbow[0] + 20, elbow[1] + 16), (elbow[0] + 24, elbow[1]),
            (elbow[0] + 12, elbow[1] - 17),
        ], 4.0, True)
        d.ellipse(482, bar_y, 17, 18, 0.0)
        d.cut_path([(464, bar_y - 16), (464, bar_y + 16)], 3.4, False)
        # Lower prong: the thighs drop to the knees at the front, and from the
        # knees the shins lie flat along the ground running right.
        knee = (stem_x - 2, 118)
        for spread, width, breeches in ((-16, 54, 62), (16, 42, 50)):
            d.leg(
                [(stem_x + spread * 0.4, hip_y), (knee[0] + spread * 0.5, knee[1]),
                 (548 + spread, 104)],
                width, knee_index=1, breeches_width=breeches, shoe_scale=0.0,
            )
        # Heel serif: the ankles flex up at the back of the base stroke and
        # taper to a sharp point, the bottom-right terminal of the letter.
        d.circle(552, 114, 26, n=24)
        d.tapered_path([(552, 108), (568, 150), (580, 194)], [48, 38, 20], True)
        d.cut_path([(534, 128), (566, 136)], 3.4, False)
    elif letter == "F":
        # Upright F built from both arms. Head, torso and two tightly parallel
        # legs make the vertical trunk; the near arm reaches straight out from
        # the shoulder as the longer top bar, and the far arm crosses the front
        # of the chest and reaches out lower down, dead parallel to it, as the
        # slightly shorter middle bar. Both feet face forward at the base.
        stem_x = 172
        top_y = 646
        mid_y = 470
        d.head(stem_x, 748, 1)
        d.torso([(stem_x, 684), (stem_x, 556), (stem_x, 428)], 86, False)
        # Top bar: the near arm straight out from the shoulder line.
        for bar_y, reach, width in ((top_y, 600, 46), (mid_y, 500, 42)):
            arm = [(stem_x + 22, bar_y), (stem_x + 200, bar_y), (reach, bar_y)]
            d.path(arm, width, False, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width // 2 + 2)
            # Open hand at the end of each prong.
            d.ellipse(reach + 12, bar_y, 20, width * 0.46, 0.0)
            d.cut_path([
                (reach - 4, bar_y - 14), (reach - 4, bar_y + 14),
            ], 3.6, False)
        # The far arm crosses the chest before running out: a short engraved
        # seam marks where it passes over the trunk.
        d.cut_path([
            (stem_x - 18, mid_y + 34), (stem_x + 4, mid_y + 12),
            (stem_x + 8, mid_y - 16),
        ], 4.2, True)
        # Tightly parallel legs. The feet flare out left and right at the base
        # as foot serifs, matching I, P and T; pointing them forward gave the
        # stem a blunt end with no terminal.
        d.leg(
            [(stem_x - 18, 430), (stem_x - 22, 244), (stem_x - 26, 62)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(-1, 0)
        )
        d.leg(
            [(stem_x + 18, 430), (stem_x + 22, 244), (stem_x + 26, 62)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(1, 0)
        )

    elif letter == "G":
        # G built as one continuous body with a deliberate twist at the waist.
        # The arms stretch overhead and curve forward to make the upper crest,
        # the head looking down and the chest turned inward so the top of the
        # letter reads as a rounded, protected profile. The middle torso then
        # twists, reorienting the body so the lower torso faces outward to the
        # left; that puts the hips where the knees can bend up and forward,
        # sweeping the thighs through the wide bottom arc. Finally the shins
        # push up the right side and the feet angle sharply back inward,
        # running horizontally into the counter as G's terminal bar.
        shoulder = (300, 754)
        hip = (170, 232)
        # Upper crest: both arms stretched overhead, curving forward and down
        # to the open terminal at the upper right.
        for spread, width in ((22, 54), (-20, 44)):
            arm = [
                (shoulder[0] + 14, shoulder[1] + spread * 0.4),
                (452 + spread, 790 + spread * 0.3),
                (596 + spread, 690 + spread * 0.6),
            ]
            d.path(arm, width, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width // 2 + 2)
            # Hand terminal closing the top of the arc.
            d.ellipse(arm[-1][0] + 8, arm[-1][1] - 18, 20, 24, -0.35)
            d.cut_path([
                (arm[-1][0] - 12, arm[-1][1] - 6),
                (arm[-1][0] + 16, arm[-1][1] - 14),
            ], 3.6, False)
        # Torso: chest turned inward at the top, twisting through the waist so
        # the lower torso faces outward down the left side.
        d.torso([shoulder, (112, 486), hip], 92, True)
        # An engraved seam marks the rotational shift at the middle torso.
        d.cut_path([(84, 520), (128, 496), (146, 458)], 5.0, True)
        # Lower curve: hips open so the knees bend up and forward, the thighs
        # sweeping the wide bottom arc to the right.
        for spread, width, breeches in ((-18, 56, 68), (20, 46, 56)):
            knee = (474 + spread, 92)
            ankle = (600 + spread * 0.4, 330 + spread)
            d.leg(
                [(hip[0] + spread * 0.5, hip[1] - 24), knee, ankle],
                width, knee_index=1, breeches_width=breeches,
                shoe_direction=(-1, 0), shoe_scale=0.5,
            )
            # The foot turns sharply inward and runs horizontally into the
            # counter: this pair of level feet is the letter's crossbar. The
            # bar is kept to a believable foot length — roughly half the shin
            # rather than matching it — so the terminal reads as feet.
            foot_y = ankle[1] + 24
            d.path([(ankle[0] + 4, foot_y), (462 + spread * 0.5, foot_y)],
                   width * 0.78, False, False, track=False)
            d.ellipse(458 + spread * 0.5, foot_y, 15, width * 0.42, 0.0)
            d.cut_path([
                (ankle[0] - 30, foot_y - 13), (ankle[0] - 30, foot_y + 13),
            ], 3.4, False)
        # The head is tucked into the crest, face turned down into the letter.
        # No hat: the brim crowds the crest of the arch.
        d.head(336, 668, 1, -math.pi / 2, hat=False)

    elif letter == "H":
        # Two standing figures act as the vertical sides of the H; their joined
        # hands at the centre form the horizontal crossbar. Each body is a
        # normally proportioned upright person seen in profile — head, torso,
        # two planted legs. Both arms are bent at the elbow. The upper arm
        # (shoulder to elbow) hangs vertically downward along the figure's own
        # pillar, carried proud of it so the limb stays visible rather than
        # merging into the torso; only the forearms turn out horizontally at
        # elbow height and clasp at the centre, so the crossbar is made of
        # forearms alone and sits exactly at the elbows.
        # Upper arm and forearm are held to the same length, as in a real
        # skeleton: the shoulder and the bar are both dropped and the two
        # figures stand closer together, which shortens the crossbar and
        # lowers it while keeping the two segments equal.
        shoulder_y = 590
        bar_y = 486
        for side in (-1, 1):
            cx = 350 - side * 190
            d.head(cx, 700, side)
            # Upright torso: shoulders below the head, waist, then hips.
            d.torso(
                [(cx, 636), (cx + side * 5, 545), (cx + side * 2, 430)], 78, True
            )
            # Front arm, bent to a right angle at the elbow. The upper arm is
            # strictly vertical: it drops from the shoulder straight down the
            # front of the body, overlapping the pillar. At elbow height the
            # forearm turns out horizontally and runs to the clasp, so the
            # crossbar is carried by the forearms alone.
            # The vertical upper arm is carried on the front face of the body,
            # far enough out that it projects past the torso edge. An engraved
            # line cannot separate them here — under the TrueType nonzero rule
            # a single reverse contour cannot cut through two stacked filled
            # shapes — so the arm is held visibly proud of the pillar and its
            # own silhouette does the work instead.
            arm_x = cx + side * 62
            shoulder = (arm_x, shoulder_y)
            elbow = (arm_x, bar_y)
            hand = (350 - side * 24, bar_y)
            # Deltoid wedge ties the offset arm back into the shoulder so the
            # limb stays attached while remaining a separate silhouette below.
            d.path([(cx + side * 12, 622), shoulder], 34, False, False, track=False)
            d.path([shoulder, elbow], 36, False, False, track=False)
            d.path([elbow, hand], 34, False, False, track=False)
            # A shoulder ball roots the vertical upper arm at the joint.
            d.circle(shoulder[0], shoulder[1], 20)
            # A joint ball keeps the right-angle bend readable as an elbow.
            d.circle(elbow[0], elbow[1], 22)
            arm = [shoulder, elbow, hand]
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            # Engraved crease around the outside of the bent elbow, wrapping
            # from the vertical upper arm onto the horizontal forearm.
            d.cut_path([
                (elbow[0] + side * 21, elbow[1] + 20),
                (elbow[0] + side * 25, elbow[1] + 2),
                (elbow[0] + side * 12, elbow[1] - 20),
            ], 5.0, True)
            # Back arm: bent at the elbow too, but kept in against the body
            # instead of joining the crossbar.
            # Far arm, likewise held proud of the back of the pillar so the
            # shoulder-to-elbow run stays visible on that side too.
            back_arm_x = cx - side * 56
            back_shoulder = (back_arm_x, 586)
            back_elbow = (back_arm_x, 492)
            back_hand = (back_arm_x + side * 42, 492)
            d.path([(cx - side * 12, 622), back_shoulder], 28, False, False, track=False)
            d.path([back_shoulder, back_elbow], 30, False, False, track=False)
            d.path([back_elbow, back_hand], 26, False, False, track=False)
            d.circle(back_shoulder[0], back_shoulder[1], 16)
            d.circle(back_elbow[0], back_elbow[1], 16)
            # Two legs per figure: near leg planted, far leg just behind it.
            d.leg(
                [(cx - side * 15, 430), (cx - side * 22, 235), (cx - side * 26, 40)],
                52, knee_index=1, shoe_direction=(side, 0),
            )
            d.leg(
                [(cx + side * 15, 430), (cx + side * 18, 235), (cx + side * 20, 40)],
                52, knee_index=1, shoe_direction=(side, 0),
            )
        # Clasped hands at the centre of the crossbar.
        d.ellipse(350, bar_y, 38, 26, 0.0)
        d.cut_path([(350, bar_y - 23), (353, bar_y), (350, bar_y + 23)], 5.0, True)

    elif letter == "I":
        # Neutral rigid stance, rebuilt around a realistic seven-head figure.
        # The trunk is shorter than before, while the thighs/calves lengthen so
        # shoulders, pelvis, knees, ankles, and feet align like the source person
        # rather than collapsing into a long column with abbreviated legs.
        # Torso, arms and legs follow the font's own baseline ratios
        # (arm 1.22x torso, leg 1.84x torso), so the glyph whose whole point is
        # ordinary human balance actually measures like a normal figure.
        d.head(350, 742, 1)
        d.torso([(350, 675), (350, 562), (350, 450)], 80, False)
        # Arms hang at the sides, slimmer than the trunk and set just clear of
        # it, so the shoulder-to-hand limb stays legible instead of fusing into
        # one slab. Engraved seams keep the separation readable at text sizes.
        for sign in (-1, 1):
            arm = [
                (350 + sign * 52, 638), (350 + sign * 62, 500),
                (350 + sign * 60, 364),
            ]
            d.path(arm, 26, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[-1][0], arm[-1][1], 15)
            # Seam between the arm and the trunk keeps the two readable. It is
            # held clear of both ends of the arm so it engraves the silhouette
            # instead of slicing the limb off the body.
            d.cut_path([
                (350 + sign * 43, 608), (350 + sign * 50, 500),
                (350 + sign * 48, 396),
            ], 4.0, True)
        d.leg([(335, 455), (330, 255), (325, 55)], 52, knee_index=1)
        d.leg([(365, 455), (370, 255), (375, 55)], 52, knee_index=1)

    elif letter == "J":
        # Kneeling side profile facing right. Head, neck and upright torso
        # align vertically as the straight main stem. At the base the knees
        # turn forward and bend sharply so the lower legs — shins, ankles and
        # feet — swing diagonally upward and backward behind the body, making
        # the upward-turning hook. The arms hang straight down the sides,
        # blending into the vertical line of the stem.
        stem_x = 452
        hip = (stem_x, 300)
        d.torso([hip, (stem_x, 466), (stem_x, 632)], 84, False)
        d.head(stem_x + 2, 696, 1)
        for sign in (-1, 1):
            arm = [
                (stem_x + sign * 52, 612),
                (stem_x + sign * 60, 482),
                (stem_x + sign * 58, 362),
            ]
            d.path(arm, 26, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.path([(stem_x + sign * 24, 630), arm[0]], 24, False, False,
                   track=False)
            d.circle(arm[0][0], arm[0][1], 15)
            d.circle(arm[-1][0], arm[-1][1], 14)
            d.cut_path([
                (stem_x + sign * 44, 592), (stem_x + sign * 50, 482),
                (stem_x + sign * 48, 388),
            ], 3.6, True)
        # Thighs drop to bent knees, then the lower legs rise diagonally back
        # behind the body to close the hook.
        for spread, width, breeches in ((-18, 52, 60), (20, 44, 52)):
            d.leg(
                [
                    (stem_x + spread * 0.5, hip[1]),
                    (stem_x + spread, 116),
                    (188 + spread, 292),
                ],
                width, knee_index=1, breeches_width=breeches,
                shoe_direction=(-0.34, 0.94),
            )

    elif letter == "K":
        # Cartwheel K: the figure balances sideways on one hand. The head lies
        # horizontally out to the left of the shoulders, anchoring the node
        # where every branch meets. Both arms run vertically from that node —
        # one down to the planted hand, one up into the air — and together they
        # make the whole left stem. They are drawn equal in length, each with a
        # marked elbow, and noticeably slimmer than the legs; a handstand
        # stretches them, but they no longer outweigh the branches. Each hand
        # flexes at the wrist into a horizontal serif. The legs split from the
        # hips to the right: one up and out as the northeast branch with the
        # foot flexed up at the ankle, the other down and out as the southeast
        # branch with the foot planted flat on the ground.
        stem_x = 214
        node = (stem_x, 424)
        # Head extends straight left from the shoulders, facing sideways.
        d.path([(stem_x - 8, node[1] + 2), (168, 426)], 42, False, False,
               track=False)
        d.head(122, 428, -1)
        # Left arm: down from the shoulder through a marked elbow to the floor.
        # Upper arm and forearm are the same length, as in a real skeleton.
        down_elbow = (stem_x, 243)
        down_arm = [(stem_x, node[1] - 34), (down_elbow[0], down_elbow[1]),
                    (stem_x, 96)]
        d.tapered_path(down_arm, [38, 33, 28], True)
        segments, length = d.centerline_measurements(down_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": down_arm,
        })
        d.circle(down_arm[0][0], down_arm[0][1], 20)
        d.circle(down_elbow[0], down_elbow[1], 18)
        d.cut_path([
            (stem_x + 15, down_elbow[1] + 16), (stem_x + 19, down_elbow[1]),
            (stem_x + 13, down_elbow[1] - 16),
        ], 3.8, True)
        # Bottom-left serif: the wrist flexes ninety degrees and the hand lies
        # flat on the floor with the fingers spread wide.
        d.ellipse(stem_x - 6, 84, 24, 19, 0.0)
        for fy in (100, 84, 68):
            d.polygon([
                (stem_x - 8, fy + 7), (stem_x - 8, fy - 7),
                (stem_x - 82, fy - 6), (stem_x - 82, fy + 6),
            ])
        for fy in (92, 76):
            d.cut_path([(stem_x - 18, fy), (stem_x - 74, fy)], 3.2, False)
        # Right arm: up from the shoulder through its own elbow, in line.
        up_elbow = (stem_x, 605)
        up_arm = [(stem_x, node[1] + 38), (up_elbow[0], up_elbow[1]),
                  (stem_x, 752)]
        d.tapered_path(up_arm, [36, 31, 26], True)
        segments, length = d.centerline_measurements(up_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": up_arm,
        })
        d.circle(up_elbow[0], up_elbow[1], 17)
        d.cut_path([
            (stem_x + 14, up_elbow[1] - 15), (stem_x + 18, up_elbow[1]),
            (stem_x + 12, up_elbow[1] + 15),
        ], 3.6, True)
        # Top-left serif: the wrist bends sharply, flexing the hand out left.
        d.ellipse(stem_x - 6, 764, 22, 18, 0.0)
        for fy in (777, 762, 747):
            d.polygon([
                (stem_x - 8, fy + 6), (stem_x - 8, fy - 6),
                (stem_x - 74, fy - 5), (stem_x - 74, fy + 5),
            ])
        d.cut_path([(stem_x - 18, 769), (stem_x - 66, 769)], 3.0, False)
        # Short torso carrying the hips a little right of the node.
        d.torso([node, (268, 422), (306, 420)], 78, False)
        # Upper diagonal: the right leg splits up and out, knee straight.
        d.leg(
            [(312, 442), (420, 552), (528, 662)], 52,
            knee_index=1, breeches_width=60, shoe_scale=0.0,
        )
        # The foot flexes up at the ankle: vertical terminal at the upper tip.
        d.path([(536, 668), (552, 744)], 36, False, False, track=False)
        d.ellipse(554, 754, 16, 17, 0.10)
        d.cut_path([(528, 694), (558, 700)], 3.2, False)
        # Lower diagonal: the left leg drives down and out to the lower right.
        d.leg(
            [(312, 398), (428, 282), (552, 160)], 54,
            knee_index=1, breeches_width=62, shoe_scale=0.0,
        )
        # The foot plants flat, heel and arch resting on the ground.
        d.ellipse(566, 144, 22, 18, -0.42)
        for dx, dy in ((20, -8), (16, -19), (6, -27)):
            d.polygon([
                (562, 148), (566 + dx, 144 + dy), (570 + dx, 152 + dy),
            ])
        d.cut_path([(549, 152), (566, 138), (576, 122)], 3.2, True)

    elif letter == "L":
        # Kneeling side profile. The upright upper body — head, straight neck
        # and vertical torso — makes the tall pillar. At its base the posture
        # hinges sharply: the knees turn forward and bend completely so the
        # thighs drop vertically and the lower body pivots into the horizontal
        # plane, the shins and ankles stretching out along the floor as the
        # bottom bar. The feet finish the stroke as a serif, heels and toes
        # adding a slight vertical terminal.
        # The hip is carried lower and the shin pulled in: previously the shin
        # ran 385 units against a 174 thigh (a 2.2 ratio), so the horizontal
        # bar was really one overlong lower leg. Femur and tibia are close to
        # equal in a real leg, and the over-long torso is brought back toward
        # the font's baseline at the same time.
        stem_x = 208
        hip = (stem_x, 400)
        d.torso([hip, (stem_x, 521), (stem_x, 642)], 84, False)
        d.head(stem_x - 2, 706, -1)
        # Arms hang along the sides, carried just clear of the trunk so the
        # shoulder-to-hand run stays legible against the stem.
        for sign in (-1, 1):
            arm = [
                (stem_x + sign * 52, 620),
                (stem_x + sign * 60, 512),
                (stem_x + sign * 58, 404),
            ]
            d.path(arm, 26, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.path([(stem_x + sign * 24, 638), arm[0]], 24, False, False,
                   track=False)
            d.circle(arm[0][0], arm[0][1], 15)
            d.circle(arm[-1][0], arm[-1][1], 14)
            d.cut_path([
                (stem_x + sign * 44, 602), (stem_x + sign * 50, 512),
                (stem_x + sign * 48, 428),
            ], 3.6, True)
        # The knees turn forward and bend right through: thighs vertical, then
        # shins running horizontally out along the floor to the right.
        for spread, width, breeches in ((-18, 52, 60), (20, 44, 52)):
            d.leg(
                [
                    (stem_x + spread * 0.5, hip[1]),
                    (stem_x + spread, 132),
                    (520 + spread, 108),
                ],
                width, knee_index=1, breeches_width=breeches,
                shoe_scale=0.0,
            )
            # In a kneel the shins lie flat and the feet rest on that same
            # floor, so the foot continues the bar forward instead of dangling
            # through the ground: it tapers from the ankle to a rounded toe
            # with its sole flush to the shin's underside, and an engraved
            # ankle crease keeps it legible as a foot.
            ax, ay = 520 + spread, 108
            # Kneeling on flat shins turns the foot over: the instep lies on
            # the floor and the SOLE faces upward. So the arch, the heel pad
            # and the toe pads are all modelled on the foot's upper surface,
            # while its underside stays flat on the ground.
            ground = ay - width * 0.5
            thick = width * 0.62
            mid = ground + thick * 0.5
            d.tapered_path(
                [(ax - 16, mid), (ax + 22, mid + 2), (ax + 58, mid - 1)],
                [thick, thick * 0.92, thick * 0.62], True,
            )
            # Heel pad: a rounded mass raised on the upturned sole.
            d.ellipse(ax + 4, ground + thick + 4, width * 0.24, 11, 0.0)
            # Toe pads: three small pads raised along the sole's far end.
            for tx in (42, 54, 65):
                d.ellipse(ax + tx, ground + thick + 4, 8, 9, 0.0)
            # The arch: a shallow curve engraved into the upturned sole
            # between the heel pad and the toe pads.
            d.cut_path([
                (ax + 16, ground + thick - 3),
                (ax + 26, ground + thick - 9),
                (ax + 36, ground + thick - 3),
            ], 5.0, True)
            # Ankle crease separating the turned foot from the shin.
            d.cut_path([
                (ax - 8, ay + 16), (ax - 4, ay), (ax - 8, ay - 14),
            ], 4.0, True)

    elif letter == "M":
        # Seated M built from the body's own hinges rather than an impossible
        # split figure. The arms drop straight down behind the back as the left
        # stem, locked at the shoulders to carry the torso's weight; the torso
        # then leans back from the hips to make the inner down-slope into the
        # central valley; the thighs pull up toward the chest and the knees
        # flex deeply to throw the sharp apex; and the lower legs descend as
        # the right stem. Hand and foot flatten into the two base serifs.
        shoulder = (150, 646)
        hips = (352, 150)
        knee = (536, 610)
        ankle = (610, 118)
        # Left stem: both arms straight down behind the back, shoulders locked.
        for sign, arm_x in ((-1, 124), (1, 166)):
            arm = [(arm_x, 640), (arm_x, 386), (arm_x, 132)]
            d.path(arm, 34 if sign < 0 else 28, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 18)
        # Left hand serif: bent horizontally at the wrist, pressed flat on the
        # ground so it reads as the left-side base serif.
        d.ellipse(140, 128, 40, 30, 0.0)
        # Fingers splay outward to the left along the floor, mirroring the
        # foot serif at the other base and giving the stem a true left serif.
        for offset, y in ((0, 148), (0, 130), (0, 112), (2, 96)):
            d.polygon([
                (140 + offset, y + 9), (140 + offset, y - 9),
                (140 + offset - 78, y - 7), (140 + offset - 78, y + 7),
            ])
        for y in (139, 121, 103):
            d.cut_path([(70, y), (128, y)], 4.0, False)
        # Head rides the top of the left peak, looking toward the knees.
        d.head(142, 716, 1)
        # Core incline: the torso leans back from the hips into the valley.
        d.torso([hips, (248, 396), shoulder], 86, True)
        # Knee apex and right stem: thighs pull up to deeply flexed knees, then
        # the lower legs drop to the planted foot.
        for spread, width in ((0, 58), (26, 50)):
            d.leg(
                [
                    (hips[0] + spread * 0.6, hips[1] + spread * 0.4),
                    (knee[0] + spread, knee[1]),
                    (ankle[0] + spread, ankle[1]),
                ],
                width, knee_index=1, breeches_width=width * 1.34,
                shoe_direction=(1, 0),
            )

    elif letter == "N":
        # Upside-down back-bend. The figure hangs inverted: the hips are flexed
        # at the top left so both legs drop straight to the floor as the left
        # pillar, the torso then arches down and back in one long sweep from
        # those hips to the shoulders at the lower right as the diagonal, and
        # from there both arms stretch vertically up past the hanging head to
        # make the right pillar. The head hangs straight down at the lower
        # right, anchoring the point where the diagonal meets that bar.
        hip = (156, 686)
        shoulder = (540, 254)
        # Pelvis. The torso stroke ends in a round cap of its own half-width,
        # which is far narrower than the pair of thighs where they leave it, so
        # the two legs used to step out sideways from the trunk in a hard
        # notch. A pelvic mass spanning the full width of both thigh tops
        # carries the trunk into the legs as one continuous buttock-and-hip
        # curve, which is what the flexed hip of an inverted body shows.
        d.ellipse(hip[0] + 5, hip[1] - 4, 43, 46, 0.0)
        d.ellipse(hip[0] + 5, hip[1] - 26, 41, 40, 0.0)
        d.ellipse(hip[0] + 4, hip[1] - 48, 37, 34, 0.0)
        # Left pillar: hips flexed, both legs straight down, knees locked and
        # feet planted flat at the bottom.
        for spread, width, breeches in ((-18, 52, 60), (18, 44, 52)):
            d.leg(
                [
                    (hip[0] + spread * 0.4, hip[1] - 40),
                    (hip[0] + spread, 380),
                    (hip[0] + spread, 74),
                ],
                width, knee_index=1, breeches_width=breeches,
                # Both feet point right: the body faces that way, arching over
                # to the shoulders and hanging head at the lower right, so
                # splaying one foot back to the left contradicts the pose.
                shoe_direction=(1, 0),
            )
        # Diagonal: one long backbend sweeping from the hips down to the
        # shoulders on the right.
        d.torso([(hip[0] + 16, hip[1] - 16), (348, 470), shoulder], 84, True)
        # Right pillar: both arms straight up, parallel, past the hanging head.
        for spread in (-20, 20):
            arm = [
                (shoulder[0] + spread * 0.4, shoulder[1] + 34),
                (shoulder[0] + spread, 470),
                (shoulder[0] + spread, 742),
            ]
            d.path(arm, 34 if spread < 0 else 28, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 18)
            # Hand flat at the top of the bar, fingers reaching up.
            palm_x = arm[-1][0]
            d.ellipse(palm_x, 756, 16, 18, 0.0)
            for dx in (-10, -1, 8):
                d.polygon([
                    (palm_x + dx - 4, 762), (palm_x + dx + 4, 762),
                    (palm_x + dx + 3, 788), (palm_x + dx - 4, 788),
                ])
            d.cut_path([(palm_x - 13, 768), (palm_x + 13, 766)], 3.2, False)
        # The head hangs straight down from the shoulders as the lower-right
        # anchor, on a neck that keeps it attached to the torso.
        d.path([(shoulder[0] - 6, shoulder[1] - 18), (550, 196)], 38,
               False, False, track=False)
        d.head(554, 154, 1, math.pi)

    elif letter == "O":
        # Backbend O. The figure leans back from standing until the body closes
        # into a ring: the deep continuous arch of the spine and torso makes the
        # rounded crest at the top, the buttocks and the backward-sloping thighs
        # and knees sweep down the left and tuck in at the ankles, and the upper
        # back, neck and arms carry the right side down with the hair falling
        # loosely along the outer perimeter. At the bottom the planted hands on
        # the right and the shod feet on the left curve toward one another,
        # leaving only a narrow gap to close the circle.
        hip = (196, 546)
        shoulder = (566, 520)
        # Top curve: the arched spine sweeping hips-to-shoulders over the crest.
        d.torso(
            [hip, (270, 700), (382, 752), (496, 688), shoulder], 96, True
        )
        # Left side curve: thighs and knees sloping back and down, tucking in
        # at the ankles to the planted shoes.
        for spread, width in ((-16, 58), (18, 50)):
            d.leg(
                [
                    (hip[0] + spread * 0.4, hip[1] - 30),
                    (116 + spread, 320),
                    (300 + spread, 84),
                ],
                width, knee_index=1, breeches_width=width * 1.3,
                shoe_direction=(1, -0.24),
            )
        # Right side curve: neck and arms running down to the planted hands.
        for spread, width in ((-16, 52), (16, 44)):
            arm = [
                (shoulder[0] + spread * 0.4, shoulder[1] - 28),
                (628 + spread, 322),
                (438 + spread, 112),
            ]
            d.path(arm, width, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width // 2 + 2)
            # Elbow crease on the outside of the descending arm.
            d.cut_path([
                (642 + spread, 388), (650 + spread, 330),
                (632 + spread, 276),
            ], 4.0, True)
        # Hands planted flat on the ground, fingers reaching toward the feet.
        for spread, hy in ((-18, 126), (18, 92)):
            hx = 438 + spread
            d.ellipse(hx, hy, 25, 19, 0.0)
            # Fingers spread forward along the floor toward the feet.
            for dy in (-11, 0, 11):
                d.polygon([
                    (hx - 6, hy + dy + 5), (hx - 6, hy + dy - 5),
                    (hx - 44, hy + dy - 4), (hx - 44, hy + dy + 4),
                ])
            d.cut_path([(hx - 12, hy - 15), (hx - 12, hy + 15)], 3.4, False)
        # The head hangs back inside the ring beneath the arched shoulders,
        # face turned up toward the crest, with the hair falling outward.
        d.front_head(486, 596, 54, hair_down=True, upside_down=True, gaze_up=True)

    elif letter == "P":
        # Standing upright. Head, straight torso and closely planted legs
        # stack into the solid left stem. The whole upper bowl is made by one
        # arm: it leaves the shoulder, exaggerates into a smooth rubbery curve
        # out and down, and closes on the hand resting on the hip at the
        # torso's midline. The far arm hangs straight down the opposite side,
        # tucked in so it never breaks the letter's silhouette.
        stem_x = 168
        hip_y = 452
        d.head(stem_x - 2, 752, 1)
        d.torso([(stem_x, 690), (stem_x, 570), (stem_x, hip_y)], 86, False)
        # Passive far arm: straight down, held close against the body.
        far_arm = [(stem_x - 30, 654), (stem_x - 38, 570), (stem_x - 34, 492)]
        d.path(far_arm, 28, True, False, track=False)
        d.circle(far_arm[-1][0], far_arm[-1][1], 15)
        # The looping arm: shoulder, out and over, down the outside, then back
        # in to the hand planted on the hip.
        loop = [
            (stem_x + 26, 664), (300, 690), (410, 640),
            (438, 552), (382, 486), (250, 464),
        ]
        d.path(loop, 46, True, False, track=False)
        segments, length = d.centerline_measurements(loop)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": loop,
        })
        d.circle(loop[0][0], loop[0][1], 24)
        # Elbow crease at the top of the rubbery arc.
        d.cut_path([(392, 664), (416, 640), (426, 610)], 4.6, True)
        # Enclosure point: the hand closes the bowl against the hip.
        d.ellipse(238, 468, 28, 24, 0.18)
        d.cut_path([(224, 484), (242, 474), (258, 480)], 4.2, True)
        # Closely planted legs continue the stem to the baseline.
        d.leg(
            [(stem_x - 18, hip_y), (stem_x - 24, 254), (stem_x - 28, 58)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(-1, 0)
        )
        d.leg(
            [(stem_x + 18, hip_y), (stem_x + 22, 254), (stem_x + 26, 58)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(1, 0)
        )

    elif letter == "Q":
        # Inverted lower body: the short-breeched thighs rise around the outer
        # ring, bend visibly at cuffed knees, and taper through calves/ankles to
        # the inward-pointing shoes that meet at the apex. These are articulated
        # legs, not anonymous tubular arms.
        # The shoulder bar stops short of the arm root. Run out to x=435 its
        # rounded cap buried the whole shoulder-to-arm junction under three or
        # four stacked filled shapes, where the nonzero fill rule cancels any
        # engraved cut outright — no seam could ever render there.
        d.path([(245, 185), (330, 203), (386, 193)], 88, True, True, track=False)
        left_leg = [(255, 200), (125, 285), (80, 455), (145, 625), (265, 720), (313, 745)]
        right_leg = [(680 - x, y) for x, y in left_leg]
        d.leg(
            left_leg, 58, knee_index=2, breeches_width=78,
            shoe_direction=(1, 0), shoe_scale=0.48,
        )
        d.leg(
            right_leg, 58, knee_index=2, breeches_width=78,
            shoe_direction=(-1, 0), shoe_scale=0.48,
        )
        d.front_head(340, 108, 62, hair_down=True, upside_down=True, gaze_up=True)
        # The projecting Q tail is the visible arm. Begin it well inside the
        # right shoulder mass, reinforce the socket, and continue outward as one
        # unbroken upper-arm/forearm route so the appendage cannot read detached.
        # The arm emerges from the edge of the shoulder mass rather than being
        # rooted deep inside it: previously its socket circle sat entirely
        # within the shoulder bar, so shoulder, arm and leg piled into one
        # blob with no readable joint. A modest ball marks the joint at the
        # shoulder's edge and the limb tapers away from it.
        d.circle(423, 179, 16)
        tail_arm = [(424, 178), (462, 152), (498, 126), (528, 102), (556, 80)]
        d.tapered_path(tail_arm, [42, 38, 34, 30, 26], True)
        # Engraved seam marking where the arm emerges from the shoulder mass.
        # Measuring the overlap shows the arm's upper edge is buried only for
        # its first quarter, leaving the body at about (479, 174); a seam run
        # any further along the limb cuts open silhouette instead of the
        # shared boundary, which is what made earlier attempts read as a nick
        # in the outline rather than a joint.
        # A cut cannot mark this junction: the arm and the leg are two stacked
        # filled shapes, and under the nonzero fill rule a reverse contour
        # there is simply cancelled. The separation has to be geometric, so
        # the arm is lifted clear of the leg and only a short crease at the
        # shoulder — where a single layer remains — is engraved.
        d.cut_path([
            (436, 194), (450, 184), (464, 173),
        ], 6.0, True)
        segments, length = d.centerline_measurements(tail_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": tail_arm, "role": "Q-tail-arm",
        })
        # Compact tail hand with two visible supporting finger tips; the arm
        # stops just outside the lower-right ring instead of stretching past
        # the descender into a detached line.
        d.ellipse(564, 74, 16, 21, -0.58)
        d.polygon([(558, 62), (571, 51), (588, 46), (582, 58), (568, 67)])
        d.polygon([(573, 70), (585, 64), (596, 71), (587, 80), (576, 77)])
        d.cut_path([(561, 66), (569, 59), (579, 60)], 4.0, True)

    elif letter == "R":
        # R is P's stance with one leg swung out: head, upright torso and the
        # firmly planted straight leg align vertically as the left backbone,
        # the same single arm loops out from the shoulder and hooks back to
        # close on the waist at the body's midline, and the other leg drives
        # sharply down and out to the right, planting at an angle to make the
        # stabilising diagonal.
        stem_x = 168
        hip_y = 452
        d.head(stem_x - 2, 752, 1)
        d.torso([(stem_x, 690), (stem_x, 570), (stem_x, hip_y)], 86, False)
        # Passive far arm: straight down, held close against the body.
        far_arm = [(stem_x - 30, 654), (stem_x - 38, 570), (stem_x - 34, 492)]
        d.path(far_arm, 28, True, False, track=False)
        d.circle(far_arm[-1][0], far_arm[-1][1], 15)
        # The looping arm, exactly as on P: shoulder, out and over, down the
        # outside, then back in to the hand resting flat on the waist.
        loop = [
            (stem_x + 26, 664), (300, 690), (410, 640),
            (438, 552), (382, 486), (250, 464),
        ]
        d.path(loop, 46, True, False, track=False)
        segments, length = d.centerline_measurements(loop)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": loop,
        })
        d.circle(loop[0][0], loop[0][1], 24)
        # Elbow crease at the top of the rubbery arc.
        d.cut_path([(392, 664), (416, 640), (426, 610)], 4.6, True)
        # Midline enclosure: the hand closes the loop against the waist.
        d.ellipse(238, 468, 28, 24, 0.18)
        d.cut_path([(224, 484), (242, 474), (258, 480)], 4.2, True)
        # Planted straight leg: continues the stem to the baseline.
        d.leg(
            [(stem_x - 16, hip_y), (stem_x - 22, 254), (stem_x - 26, 58)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(-1, 0)
        )
        # Lower-right branch, as on K: the leg reaches out from the pelvis and
        # changes direction at the knee to drive down and right, planting flat
        # with spread toes anchoring the base.
        d.leg(
            [(stem_x + 18, hip_y), (334, 262), (520, 68)], 56,
            knee_index=1, breeches_width=64, shoe_scale=0.0,
        )
        d.ellipse(530, 60, 23, 18, -0.5)
        for dx, dy in ((21, -6), (17, -17), (7, -26)):
            d.polygon([
                (526, 64), (530 + dx, 60 + dy), (534 + dx, 68 + dy),
            ])
        d.cut_path([(513, 68), (530, 54), (540, 38)], 3.2, True)

    elif letter == "S":
        # Lying S. The naturally longer lower limbs sweep the biggest curve:
        # the legs and lower torso rise and then arch forward to make the
        # elongated upper hook, the feet pointing up and to the right. The hips
        # flex sharply so the thighs run diagonally down and back as the
        # letter's spine, and the upper torso, neck and head curl along the
        # floor to the left, the head resting at the very bottom facing up to
        # close the lower hook.
        hip = (250, 500)
        shoulder = (470, 286)
        # Upper hook: hips lift, then the long legs arch forward and right.
        for spread, width in ((-16, 56), (14, 48)):
            d.leg(
                [
                    (hip[0] + spread * 0.4, hip[1]),
                    (356 + spread * 0.5, 700),
                    (596 + spread * 0.4, 640),
                ],
                width, knee_index=1, breeches_width=width * 1.28,
                shoe_direction=(0.7, 0.72),
            )
        # Diagonal spine: thighs and trunk carry the centre line down-left.
        d.torso([hip, (352, 392), shoulder], 90, True)
        # Lower hook: chest, neck and head curl along the floor to the left.
        d.path([shoulder, (430, 122), (216, 96)], 82, True, False, track=False)
        # The head rests at the very bottom of the lower hook facing upward:
        # a quarter-turn puts the nose and eye on the vertical, so the face
        # looks up out of the letter rather than back along the floor.
        d.head(154, 110, 1, math.pi / 2)
        # Arms fold in against the chest, following the lower curve.
        for sign in (-1, 1):
            arm = [
                (shoulder[0] - 12, shoulder[1] - 44 + sign * 10),
                (416 + sign * 6, 190 + sign * 14),
                (346 + sign * 4, 148 + sign * 16),
            ]
            d.path(arm, 30, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[-1][0], arm[-1][1], 16)

    elif letter == "T":
        # Upright T. The straight spine, narrow hips and tightly closed legs
        # make the central pillar; both arms extend dead level at ninety
        # degrees from the shoulders to form one continuous top line. At each
        # end the wrist flexes so the hand hangs downward, giving the letter
        # its hanging terminals, and the feet flare outward at the base as
        # stabilising foot serifs.
        bar_y = 646
        d.head(350, 706, 1)
        d.torso([(350, 642), (350, 520), (350, 398)], 84, False)
        for sign in (-1, 1):
            tip = 350 + sign * 268
            arm = [(350 + sign * 26, bar_y), (350 + sign * 150, bar_y), (tip, bar_y)]
            d.path(arm, 44, False, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 24)
            # Wrist flexes down: the hand hangs as a terminal serif.
            # The hand turns down out of the arm through a rounded wrist. A
            # plain vertical stroke butted against the bar left a hard step in
            # the outline, so a joint mass fills the corner and the hand is
            # tapered from wrist to fingertip.
            d.circle(tip + sign * 2, bar_y - 4, 21, n=20)
            d.tapered_path(
                [(tip + sign * 3, bar_y - 2), (tip + sign * 7, bar_y - 36),
                 (tip + sign * 10, bar_y - 66)],
                [34, 30, 24], True,
            )
            d.ellipse(tip + sign * 11, bar_y - 72, 17, 13, 0.0)
            d.cut_path([
                (tip + sign * 10 - 14, bar_y - 30),
                (tip + sign * 10 + 14, bar_y - 32),
            ], 3.6, True)
        # Tightly closed legs down the centre, feet flaring out at the base.
        d.leg([(330, 398), (328, 226), (327, 58)], 44, knee_index=1,
              breeches_width=48, shoe_direction=(-1, 0))
        d.leg([(370, 398), (372, 226), (373, 58)], 44, knee_index=1,
              breeches_width=48, shoe_direction=(1, 0))

    elif letter == "U":
        # Deep backbend performed lying down. The lower torso and glutes arch
        # downward to the ground as the curved base, while the legs rise
        # straight up on the left and the arms rise parallel to them on the
        # right. Knees stay locked and the hands point at the sky, so the two
        # limb pairs read as the letter's parallel bars.
        hip = (140, 260)
        shoulder = (560, 260)
        # Curved bottom base: the arched spine sweeps from hips to shoulders,
        # dipping to the floor between them.
        d.torso(
            [hip, (240, 120), (350, 86), (460, 120), shoulder], 92, True
        )
        # Left bar: both legs straight up from the hips, knees locked.
        for spread, width in ((-16, 56), (14, 48)):
            ankle_x = hip[0] + spread
            d.leg(
                [
                    (hip[0] + spread * 0.5, hip[1] + 34),
                    (ankle_x, 470),
                    (ankle_x, 690 if spread < 0 else 654),
                ],
                width, knee_index=1, breeches_width=width * 1.28,
                shoe_scale=0.0,
            )
            # The foot bends outward at the ankle and the toes run horizontally
            # away from the bar, giving the left upright a terminal serif to
            # answer the splayed fingers closing the right one.
            foot_y = 700 if spread < 0 else 664
            d.ellipse(ankle_x - 4, foot_y, width * 0.32, 17, 0.0)
            d.path([(ankle_x - 4, foot_y + 4), (ankle_x - 58, foot_y + 8)],
                   width * 0.44, False, False, track=False)
            d.ellipse(ankle_x - 60, foot_y + 8, 12, width * 0.24, 0.0)
            d.cut_path([
                (ankle_x - 20, foot_y - 8), (ankle_x - 22, foot_y + 20),
            ], 3.2, False)
        # Right bar: both arms vertical and parallel, hands pointing skyward.
        # The two arms are separately drawn shapes stacked on each other, so an
        # engraved seam is cancelled by the layer beneath under the nonzero
        # fill rule. They are held apart with a real gap instead, as H's arms
        # are, and each is slimmed so the pair still reads as one bar.
        for spread in (-19, 19):
            arm = [
                (shoulder[0] + spread * 0.5, shoulder[1] + 30),
                (shoulder[0] + spread, 460),
                (shoulder[0] + spread, 654),
            ]
            d.path(arm, 30 if spread < 0 else 27, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 21)
            # Hand held flat with the fingers pointing straight up.
            palm_x, palm_y = arm[-1]
            d.ellipse(palm_x, palm_y + 14, 19, 22, 0.0)
            for offset in (-11, -3, 5, 13):
                d.polygon([
                    (palm_x + offset - 3, palm_y + 26),
                    (palm_x + offset + 3, palm_y + 26),
                    (palm_x + offset + 2, palm_y + 50),
                    (palm_x + offset - 2, palm_y + 50),
                ])
            d.cut_path([
                (palm_x - 12, palm_y + 30), (palm_x + 12, palm_y + 30),
            ], 3.4, False)
        # The head hangs back beneath the arched shoulders.
        d.head(556, 168, -1, math.pi)

    elif letter == "V":
        # Upside-down figure: the head is the low apex, legs spread to the two
        # top corners, and the arms lie along and grip the rising legs. As in
        # Q, the inverted head keeps its face upright and the gaze lifted, so
        # the figure looks up out of the apex rather than down into it.
        d.front_head(350, 108, 58, hair_down=True, upside_down=True,
                     gaze_up=True)
        d.torso([(350, 165), (350, 285)], 90, False)
        d.leg([(340, 285), (225, 500), (105, 745)], 64, knee_index=1)
        d.leg([(360, 285), (475, 500), (595, 745)], 64, knee_index=1)
        d.limb([(325, 190), (245, 345), (190, 500)], 44, True, end="hand")
        d.limb([(375, 190), (455, 345), (510, 500)], 44, True, end="hand")

    elif letter == "W":
        # The print's four-stroke W: the inner red-sleeved arms reach to the
        # shared baseline, while the outer stockinged legs bend at baseline
        # knees and rise to high feet. The palms sit exactly on y=0, and their
        # index fingers and thumbs are drawn as distinct supporting digits.
        # The arms are lengthened and the shins shortened: at the old lengths
        # the raised shin ran nearly five times the forearm, so the outer
        # strokes dwarfed the inner ones.
        d.head(350, 660, 1)
        d.torso([(350, 600), (350, 430)], 88, False)
        left_arm = [(320, 448), (278, 250), (252, 72)]
        right_arm = [(380, 448), (422, 250), (448, 72)]
        for arm in (left_arm, right_arm):
            d.path(arm, 54, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        d.leg(
            [(315, 430), (150, 0), (74, 606)], 62, knee_index=1,
            shoe_direction=(-0.92, 0.40),
        )
        d.leg(
            [(385, 430), (550, 0), (626, 606)], 62, knee_index=1,
            shoe_direction=(0.92, 0.40),
        )
        # Draw the supporting hands after the outer legs so the fingertips stay
        # visible. Each palm sits between the baseline knees; the index finger
        # and thumb extend as two separate supports down to y=0.
        d.polygon([
            (242, 75), (258, 80), (275, 70), (272, 50),
            (256, 42), (238, 52),
        ])
        d.polygon([
            (239, 53), (230, 30), (213, 0), (229, 0),
            (244, 26), (250, 54),
        ])
        d.polygon([
            (267, 55), (278, 31), (297, 0), (304, 10),
            (285, 31), (276, 60),
        ])
        d.cut_path([(252, 76), (252, 48), (258, 16)], 5.2, True)
        d.cut_path([(223, 18), (233, 24), (240, 18)], 3.2, True)
        d.cut_path([(281, 18), (288, 25), (296, 18)], 3.2, True)

        d.polygon([
            (458, 75), (442, 80), (425, 70), (428, 50),
            (444, 42), (462, 52),
        ])
        d.polygon([
            (461, 53), (470, 30), (487, 0), (471, 0),
            (456, 26), (450, 54),
        ])
        d.polygon([
            (433, 55), (422, 31), (403, 0), (396, 10),
            (415, 31), (424, 60),
        ])
        d.cut_path([(448, 76), (448, 48), (442, 16)], 5.2, True)
        d.cut_path([(477, 18), (467, 24), (460, 18)], 3.2, True)
        d.cut_path([(419, 18), (412, 25), (404, 18)], 3.2, True)

    elif letter == "X":
        # Spread-eagle X in the Vitruvian diagonal pose: head at center, arms
        # raised to the upper corners and legs spread to the lower corners. Arms
        # and legs are both limbs and share a similar width; both are visibly
        # slimmer than the torso. The raised hands are open with spread fingers.
        d.head(350, 440, 1)
        d.torso([(350, 380), (350, 300)], 86, False)
        left_arm = [(338, 395), (250, 555), (130, 690)]
        right_arm = [(362, 395), (450, 555), (570, 690)]
        for arm in (left_arm, right_arm):
            d.path(arm, 44, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        # Open raised hands with fingers splayed toward the upper corners.
        for x, y, s in ((130, 690, -1), (570, 690, 1)):
            d.ellipse(x, y, 22, 15, s * 0.55)
            for dx, dy in (
                (-18, 10), (-20, 0), (-16, -9), (-8, -15), (2, -15),
            ):
                d.polygon([
                    (x - s * 6, y + 4),
                    (x + s * dx, y + dy),
                    (x + s * (dx + 4), y + dy + 3),
                ])
        d.leg(
            [(338, 300), (225, 170), (70, 45)], 60, knee_index=1, shoe_direction=(-1, 0)
        )
        d.leg(
            [(362, 300), (475, 170), (630, 45)], 60, knee_index=1, shoe_direction=(1, 0)
        )

    elif letter == "Y":
        # Seated Y, deliberately contrasted with the standing T. Both arms
        # extend up and outward from the shoulders in a wide V with the open
        # palms turned upward, instead of T's flat horizontal bar. Below, the
        # body is condensed into a tight frontal squat: the knees come up close
        # against the chest and the shins and feet run vertically down the
        # front of the body, giving a short, thick central column. The head
        # sits centrally between the shoulders, exactly where the upper
        # branches converge on the seated torso.
        fork_y = 392
        d.torso([(350, 212), (350, 302), (350, fork_y)], 92, False)
        d.head(350, 456, 1)
        for sign in (-1, 1):
            tip = (350 + sign * 258, 668)
            arm = [
                (350 + sign * 34, fork_y - 16),
                (350 + sign * 146, 530),
                tip,
            ]
            d.path(arm, 40, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 22)
            # Open palm turned upward, fingers spread at the top of the branch.
            d.ellipse(tip[0], tip[1] + 14, 21, 16, sign * 0.30)
            for dx, dy in ((-16, 20), (-6, 26), (5, 25), (14, 19)):
                d.polygon([
                    (tip[0] + sign * dx - 5, tip[1] + dy),
                    (tip[0] + sign * dx + 5, tip[1] + dy),
                    (tip[0] + sign * dx + 4, tip[1] + dy + 30),
                    (tip[0] + sign * dx - 4, tip[1] + dy + 30),
                ])
            d.cut_path([
                (tip[0] - 15, tip[1] + 22), (tip[0] + 15, tip[1] + 22),
            ], 3.4, False)
        # Frontal squat: knees drawn up toward the chest, then the shins drop
        # vertically down the front of the body to the planted feet.
        # The squat is drawn as real geometry, not engraving: a cut here is
        # cancelled by the torso stacked beneath, so the fold has to live in
        # the silhouette. Each thigh runs outward from the hip to a knee that
        # juts clear of the body, and the shin then drops back inward, cutting
        # a visible notch into the outline on each side.
        for sign in (-1, 1):
            knee = (350 + sign * 74, 252)
            d.leg(
                [(350 + sign * 22, 330), knee, (350 + sign * 26, 56)],
                46, knee_index=1, breeches_width=56,
                shoe_direction=(sign, 0), shoe_scale=0.82,
            )
            # A rounded cap on the projecting knee makes the joint explicit.
            d.ellipse(knee[0] + sign * 3, knee[1] + 6, 26, 23, 0.0)
            # Crease inside the fold, held clear of the outline.
            d.cut_path([
                (350 + sign * 46, 234), (350 + sign * 60, 252),
                (350 + sign * 53, 274),
            ], 4.2, True)

    elif letter == "Z":
        # Side-profile Z: a dramatic backward lean over a deep kneel, with the
        # arms thrown flat out in front. Both arms extend horizontally from the
        # shoulders as the top bar, the hands held completely flat in line with
        # the forearms so the stroke tapers to a thinner tip like a pen stroke.
        # The torso leans back from the knees in one straight diagonal, with no
        # bend at the waist, linking the top bar to the base. The shins and
        # ankles lie flat on the floor as the bottom bar, and at its back end
        # the heels and upturned toes lift into a small vertical foot serif.
        shoulder = (516, 672)
        knee = (166, 168)
        d.head(576, 712, -1)
        # Top bar: two flat arms tapering from shoulder to fingertip.
        # The arms are separately drawn shapes stacked on one another, so a
        # seam would be cancelled: they are held apart by a real gap instead,
        # the far one slimmer, so the top bar reads as two limbs.
        for spread, base_w in ((24, 48), (-22, 38)):
            tip_x = 108 + (0 if spread > 0 else 18)
            d.tapered_path(
                [
                    (shoulder[0] - 8, shoulder[1] + spread),
                    (380, shoulder[1] + spread),
                    (250, shoulder[1] + spread),
                    (tip_x, shoulder[1] + spread),
                ],
                [base_w, base_w * 0.82, base_w * 0.6, base_w * 0.34],
                True,
            )
            arm = [
                (shoulder[0] - 8, shoulder[1] + spread),
                (tip_x, shoulder[1] + spread),
            ]
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(shoulder[0] - 8, shoulder[1] + spread, base_w // 2 + 2)
            # Engraved wrist line where the flat hand continues the forearm.
            d.cut_path([
                (tip_x + 74, shoulder[1] + spread - 13),
                (tip_x + 74, shoulder[1] + spread + 13),
            ], 3.4, False)
        # Diagonal spine: one straight lean from the shoulders back to the knees.
        d.torso([shoulder, (340, 420), knee], 92, False)
        # Bottom bar: shins and ankles flat along the floor, feet turning up at
        # the back end as the serif.
        for spread, width, breeches in ((-20, 56, 66), (18, 46, 54)):
            d.leg(
                [
                    (knee[0] + spread * 0.4, knee[1] + spread * 0.5),
                    (330 + spread, 118),
                    (556 + spread, 108),
                ],
                width, knee_index=1, breeches_width=breeches,
                shoe_scale=0.0,
            )
            # The feet rest on the same floor the shins lie along, continuing
            # the bar forward to a rounded toe rather than hanging below it.
            ax, ay = 556 + spread, 108
            # Kneeling on flat shins turns the foot over: the instep lies on
            # the floor and the SOLE faces upward. So the arch, the heel pad
            # and the toe pads are all modelled on the foot's upper surface,
            # while its underside stays flat on the ground.
            ground = ay - width * 0.5
            thick = width * 0.62
            mid = ground + thick * 0.5
            d.tapered_path(
                [(ax - 16, mid), (ax + 24, mid + 2), (ax + 62, mid - 1)],
                [thick, thick * 0.92, thick * 0.62], True,
            )
            # Heel pad: a rounded mass raised on the upturned sole.
            d.ellipse(ax + 4, ground + thick + 4, width * 0.24, 11, 0.0)
            # Toe pads: three small pads raised along the sole's far end.
            for tx in (46, 58, 69):
                d.ellipse(ax + tx, ground + thick + 4, 8, 9, 0.0)
            # The arch: a shallow curve engraved into the upturned sole
            # between the heel pad and the toe pads.
            d.cut_path([
                (ax + 16, ground + thick - 3),
                (ax + 28, ground + thick - 9),
                (ax + 40, ground + thick - 3),
            ], 5.0, True)
            # Ankle crease separating the turned foot from the shin.
            d.cut_path([
                (ax - 8, ay + 16), (ax - 4, ay), (ax - 8, ay - 14),
            ], 4.0, True)

    return d


def punctuation(name: str) -> Drawer:
    d = Drawer()
    if name == "period":
        d.head(350, 85, 1)
    elif name == "comma":
        d.head(340, 90, 1)
        d.path([(355, 55), (330, -15), (285, -65)], 36)
    elif name == "exclam":
        # The dot is a plain solid disc: a hatted head here reads as a figure
        # rather than punctuation and clutters the mark at text sizes.
        d.circle(350, 90, 55)
        d.torso([(350, 720), (350, 250)], 80, False)
        d.circle(350, 760, 34)
    elif name == "question":
        d.circle(350, 90, 55)
        d.path([(170, 620), (250, 750), (455, 730), (530, 600), (470, 475), (355, 400), (350, 260)], 72)
        d.circle(170, 620, 28)
    elif name == "hyphen":
        d.limb([(180, 380), (520, 380)], 52, False, end="hand")
        d.head(350, 430, 1)
    return d


def notdef() -> Drawer:
    d = Drawer()
    d.polygon([(70, 0), (70, 800), (630, 800), (630, 0)])
    d.polygon([(140, 90), (560, 90), (560, 710), (140, 710)], hole=True)
    d.path([(190, 160), (510, 640)], 55, False)
    d.path([(190, 640), (510, 160)], 55, False)
    return d


def build_font() -> tuple[dict[str, Drawer], Path]:
    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    punct_names = ["period", "comma", "exclam", "question", "hyphen"]
    order = [".notdef", "space", *letters, *punct_names]
    drawings: dict[str, Drawer] = {letter: pose(letter) for letter in letters}
    drawings.update({name: punctuation(name) for name in punct_names})
    drawings[".notdef"] = notdef()

    def ink_bounds(name: str) -> tuple[float, float] | None:
        drawer = drawings.get(name)
        xs = [x for contour, _ in drawer.contours for x, _ in contour] if drawer else []
        return (min(xs), max(xs)) if xs else None

    # Shift each outline so its ink starts exactly one sidebearing from the
    # glyph origin, then give it a matching advance.
    shifts = {}
    for name in drawings:
        bounds = ink_bounds(name)
        shifts[name] = SIDEBEARING - bounds[0] if bounds else 0.0

    glyphs = {name: drawings[name].to_glyph(shifts[name]) for name in drawings}
    glyphs["space"] = TTGlyphPen(None).glyph()

    cmap = {ord(ch): ch for ch in letters}
    cmap.update({ord(ch.lower()): ch for ch in letters})
    cmap.update(
        {
            ord(" "): "space",
            ord("."): "period",
            ord(","): "comma",
            ord("!"): "exclam",
            ord("?"): "question",
            ord("-"): "hyphen",
            0x2013: "hyphen",
            0x2014: "hyphen",
        }
    )

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    # Proportional spacing. A single fixed advance suits the wide poses but
    # strands narrow figures like I and J in a sea of white, so each glyph is
    # fitted to its own ink with a constant sidebearing. Poses that already
    # fill the em keep the full advance.
    def fitted_metrics(name: str) -> tuple[int, int]:
        if name == "space":
            return (330, 0)
        bounds = ink_bounds(name)
        if bounds is None:
            return (ADVANCE, 0)
        left, right = bounds
        # No cap at the em: clamping the advance to ADVANCE squeezed the
        # sidebearings of the widest poses (W and X span nearly the whole em)
        # down to a couple of units, so their limbs collided with the
        # neighbouring letters. Every glyph gets its full sidebearing and the
        # advance grows past the em where the pose needs it.
        advance = round(right - left + 2 * SIDEBEARING)
        return (advance, round(SIDEBEARING))

    metrics = {name: fitted_metrics(name) for name in order}
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=850, descent=-150, lineGap=50)
    fb.setupNameTable(
        {
            "familyName": "Posture Master",
            "styleName": "Regular",
            "uniqueFontIdentifier": "ArenaAI: Posture Master Regular: 1.000",
            "fullName": "Posture Master Regular",
            "psName": "PostureMaster-Regular",
            "version": "Version 1.000",
            "description": "A comic body alphabet with anatomical hat-and-shoe serifs.",
            "designer": "Designed on Arena.ai from a user-supplied 18th-century reference",
            "licenseDescription": "Original generated outlines; free to use and modify.",
        }
    )
    fb.setupOS2(
        sTypoAscender=850,
        sTypoDescender=-150,
        sTypoLineGap=50,
        usWinAscent=900,
        usWinDescent=180,
        usWeightClass=700,
        usWidthClass=5,
        sxHeight=500,
        sCapHeight=800,
        fsSelection=0x40,
    )
    fb.setupPost(italicAngle=0, underlinePosition=-100, underlineThickness=50)
    fb.setupMaxp()
    fb.setupHead()
    # OpenType timestamps count seconds since 1904-01-01. A fixed release date
    # keeps builds reproducible and avoids fontTools' "very low timestamp" warning.
    fb.font["head"].created = 3869769600  # 2026-08-17 00:00:00 UTC
    fb.font["head"].modified = 3869769600

    ttf_path = ROOT / "posture-master.ttf"
    fb.save(ttf_path)

    for flavor, filename in [("woff", "posture-master.woff"), ("woff2", "posture-master.woff2")]:
        font = TTFont(ttf_path)
        font.flavor = flavor
        font.save(ROOT / filename)

    return drawings, ttf_path


def build_svg_sheet(drawings: dict[str, Drawer]) -> None:
    cell_w, cell_h = 210, 255
    cols, rows = 7, 4
    width, height = cols * cell_w, rows * cell_h + 120
    cards = []
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        col, row = i % cols, i // cols
        x = col * cell_w
        y = 90 + row * cell_h
        path = drawings[letter].svg_path()
        cards.append(
            f'<rect x="{x + 7}" y="{y + 7}" width="196" height="238" rx="10" '
            f'fill="none" stroke="#d3bea0" stroke-width="2"/>'
        )
        cards.append(
            f'<g transform="translate({x + 1},{y + 208}) scale(.29)">'
            f'<path d="{path}" fill="#17243a" fill-rule="nonzero"/></g>'
        )
        cards.append(
            f'<text x="{x + 18}" y="{y + 38}" font-family="DejaVu Sans Mono, monospace" '
            f'font-size="22" font-weight="700" fill="#e34f3f">{letter}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f5edda"/>
<text x="24" y="42" font-family="DejaVu Sans, sans-serif" font-size="34" font-weight="800" letter-spacing="5" fill="#17243a">POSTURE MASTER · GLYPH SHEET</text>
<text x="24" y="69" font-family="DejaVu Sans, sans-serif" font-size="16" fill="#6d6256">26 improbable stretches. No spotters. Please do not try this at home.</text>
{''.join(cards)}
</svg>'''
    (ROOT / "glyph-sheet.svg").write_text(svg, encoding="utf-8")


def main() -> None:
    drawings, path = build_font()
    build_svg_sheet(drawings)
    print(f"Built {path}")
    print("Built posture-master.woff, posture-master.woff2 and glyph-sheet.svg")


if __name__ == "__main__":
    main()
