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

        knee = pts[knee_index]
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
        mirror_details: bool = False,
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
            d.head(px(232), 552, side * -1)
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
                [(px(184), 326), (px(148), 176), (px(112), 32)], 50,
                knee_index=1, breeches_width=58, shoe_direction=(-side, 0),
            )
            # Inner leg: set slightly forward with a gentle bend at the knee.
            d.leg(
                [(px(210), 326), (px(192), 174), (px(206), 32)], 48,
                knee_index=1, breeches_width=56, shoe_direction=(-side, 0),
            )
        # Apex: the two flat hands meet in a sharp peak.
        d.polygon([
            (350, apex_y + 16), (368, apex_y - 30), (332, apex_y - 30),
        ])
        # The jointly held round object reads as the letter's crossbar.
        d.circle(ball[0], ball[1], 36)
        d.circle(ball[0], ball[1], 13, hole=True)

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
        d.limb([(255, 585), (390, 675), (545, 600)], 46, True, end="hand")
        d.limb([(235, 565), (375, 645), (525, 580)], 40, True, end="hand")
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
                    (meet[0] - 44 + spread, meet[1] + 16),
                ],
                56, knee_index=1, breeches_width=74,
                shoe_direction=(0.55, 0.84),
            )
        # Upper curve: the arm arches back over the top and down behind.
        arm = [
            (stem_x + 34, 640), (318, 730), (466, 646),
            (536, 500), (492, 350),
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
        d.cut_path([(470, 682), (500, 654), (516, 620)], 4.6, True)
        # Enclosure point: the reaching hand closes on the raised feet.
        d.ellipse(meet[0] - 22, meet[1] + 28, 28, 30, -0.45)
        d.cut_path([
            (meet[0] - 38, meet[1] + 42), (meet[0] - 20, meet[1] + 32),
            (meet[0] - 6, meet[1] + 38),
        ], 4.2, True)

    elif letter == "E":
        # Historical seated E. Head and torso form the stem; the top and middle
        # bars are arms. The broad lower leg lies straight along the baseline,
        # while the slimmer near leg remains visibly separate just above it;
        # both source-profile shoes turn upward at their anatomical endpoints.
        d.head(160, 745, 1)
        # Continue the stem directly into the lower leg centerline so the
        # baseline stroke is a seamless seated body connection, not a floater.
        d.torso([(160, 680), (160, 485), (160, 100)], 90, False)
        # Both bars are arms and both run dead horizontal, matching F's
        # construction: a sloping prong reads as a droop rather than a
        # deliberate crossbar.
        for bar_y, reach, width in ((648, 590, 46), (470, 486, 42)):
            arm = [(182, bar_y), (380, bar_y), (reach, bar_y)]
            d.path(arm, width, False, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width // 2 + 2)
            d.ellipse(reach + 12, bar_y, 20, width * 0.46, 0.0)
            d.cut_path([
                (reach - 4, bar_y - 14), (reach - 4, bar_y + 14),
            ], 3.6, False)
        d.leg(
            [(160, 100), (370, 100), (585, 100)], 58, knee_index=1, shoe_direction=(0.55, 1.0)
        )
        d.leg(
            [(170, 175), (365, 175), (560, 175)], 36, knee_index=1, shoe_direction=(0.55, 1.0)
        )

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
        # Tightly parallel legs, both feet facing forward at the base.
        d.leg(
            [(stem_x - 18, 430), (stem_x - 22, 244), (stem_x - 26, 62)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(-0.35, -1)
        )
        d.leg(
            [(stem_x + 18, 430), (stem_x + 22, 244), (stem_x + 26, 62)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(0.35, -1)
        )

    elif letter == "G":
        # Aerial recumbent G. The foreshortened body and limbs describe an
        # open ring; the right arm turns sharply inward to make G's terminal.
        d.torso([(205, 225), (120, 335), (115, 485), (205, 585)], 94, True)
        d.limb([(205, 585), (335, 695), (500, 660), (575, 545), (565, 410), (455, 410)], 54, True, end="hand")
        d.limb([(190, 560), (300, 655), (455, 630), (535, 555)], 38, True, end="hand")
        # The source shoes rise at the right opening instead of hanging below it.
        d.leg(
            [(205, 225), (335, 115), (505, 125), (575, 180)], 58, knee_index=1, shoe_direction=(0.4, 1.0)
        )
        d.leg(
            [(225, 245), (345, 150), (500, 165)], 42, knee_index=1, shoe_direction=(0.4, 1.0)
        )
        d.front_head(190, 505, 48, hair_down=False)

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
        bar_y = 505
        for side in (-1, 1):
            cx = 350 - side * 210
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
            arm_x = cx + side * 58
            shoulder = (arm_x, 612)
            elbow = (arm_x, bar_y)
            hand = (350 - side * 24, bar_y)
            # Deltoid wedge ties the offset arm back into the shoulder so the
            # limb stays attached while remaining a separate silhouette below.
            d.path([(cx + side * 12, 626), shoulder], 34, False, False, track=False)
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
            back_shoulder = (back_arm_x, 606)
            back_elbow = (back_arm_x, 508)
            back_hand = (back_arm_x + side * 44, 508)
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
        # Seated J. The torso and head rise straight up as the vertical stem,
        # the head turned to the right so it makes the small top-right serif.
        # Below the waist the hips and upper thighs curve down and sweep
        # forward to the left; the knees then bend so the lower legs run back
        # up slightly, closing the bottom hook. The arms hang straight down
        # along the sides of the torso, carried just proud of it so the
        # shoulder-to-hand run stays visible against the stem.
        stem_x = 430
        hip = (stem_x, 210)
        d.torso([hip, (stem_x, 430), (stem_x, 640)], 84, False)
        d.head(stem_x, 704, 1)
        for sign in (-1, 1):
            arm = [
                (stem_x + sign * 56, 612),
                (stem_x + sign * 62, 470),
                (stem_x + sign * 60, 340),
            ]
            d.path(arm, 28, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            # Deltoid wedge keeps the offset arm attached at the shoulder.
            d.path([(stem_x + sign * 26, 634), arm[0]], 26, False, False,
                   track=False)
            d.circle(arm[0][0], arm[0][1], 16)
            d.circle(arm[-1][0], arm[-1][1], 15)
        # Hips and thighs sweep down-left, then the bent knees send the lower
        # legs back up to finish the hook.
        d.leg(
            [hip, (312, 56), (208, 190)], 54, knee_index=1,
            breeches_width=70, shoe_direction=(0.05, 1.0),
        )
        d.leg(
            [(stem_x - 26, 182), (310, 108), (236, 226)], 44, knee_index=1,
            breeches_width=56, shoe_direction=(0.05, 1.0),
        )

    elif letter == "K":
        # Kneeling K. Torso, neck, head and the kneeling near leg stack into
        # one plumb line: the knee is planted directly under the torso so the
        # left side of the letter is dead vertical. The far leg extends well
        # out to the side at a bent knee, giving the lower diagonal the extra
        # length a K needs to balance. The near arm raises straight up and out
        # at about forty-five degrees as the upper diagonal, ending in an open
        # hand serif, while the far arm is pinned flat along the hip and thigh
        # so the centre of the letter stays solid with no trapped white.
        stem_x = 206
        hip_y = 412
        d.head(stem_x, 742, 1)
        d.torso([(stem_x, 678), (stem_x + 4, 546), (stem_x + 2, hip_y)], 84, False)
        # Upper diagonal: the raised arm at roughly forty-five degrees.
        raised = [(stem_x + 26, 634), (338, 690), (446, 748)]
        d.path(raised, 44, True, False, track=False)
        segments, length = d.centerline_measurements(raised)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": raised,
        })
        d.circle(raised[0][0], raised[0][1], 23)
        d.cut_path([(324, 712), (346, 690), (356, 668)], 4.2, True)
        # Open hand serif at the top of the diagonal, fingers spread outward.
        d.ellipse(458, 754, 22, 17, 0.48)
        for dx, dy in ((26, 18), (30, 4), (24, -10), (12, -20)):
            d.polygon([
                (454, 750), (458 + dx, 754 + dy), (460 + dx, 748 + dy),
            ])
        d.cut_path([(446, 762), (460, 752), (466, 740)], 3.4, True)
        # Closed centre: the far arm lies flat down the hip and thigh.
        pinned = [(stem_x - 30, 642), (stem_x - 38, 528), (stem_x - 34, 424)]
        d.path(pinned, 28, True, False, track=False)
        d.circle(pinned[-1][0], pinned[-1][1], 15)
        d.cut_path([
            (stem_x - 22, 620), (stem_x - 28, 528), (stem_x - 25, 444),
        ], 3.6, True)
        # Kneeling near leg: thigh drops vertically to a knee on the ground,
        # then the shin folds back along the floor.
        d.leg(
            [(stem_x - 12, hip_y), (stem_x - 18, 246), (stem_x - 22, 86)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(-1, 0)
        )
        # Lower diagonal: the far leg reaches well out to the right at a bent
        # knee, its foot planting to make the wide, elongated base.
        d.leg(
            [(stem_x + 20, hip_y), (352, 226), (556, 74)], 56,
            knee_index=1, breeches_width=64, shoe_direction=(1, 0)
        )

    elif letter == "L":
        # Lying flat on the back with the hips flexed to a right angle. The
        # whole lower half of the body is lifted straight up, and because the
        # legs plus lower torso are naturally longer than the upper torso they
        # make the tall vertical stem while the upper back, shoulders and head
        # lie along the ground as the shorter horizontal base. The knees stay
        # locked so the stem is rigid, the toes point up as a terminal peak,
        # and the arms rest on the floor with the hands beside the head.
        hip = (196, 156)
        ground_y = 130
        # Vertical stem: both legs perfectly straight up from the flexed hips,
        # knees locked, feet pointing at the ceiling.
        # The two legs are set far enough apart to leave a real gap between
        # them: an engraved seam cannot separate overlapping shapes under the
        # nonzero fill rule, so the stem would otherwise read as one slab.
        for spread, width, breeches in ((-20, 50, 58), (22, 44, 52)):
            d.leg(
                [
                    (hip[0] + spread * 0.5, hip[1]),
                    (hip[0] + spread, 392),
                    (hip[0] + spread, 626),
                ],
                width, knee_index=1, breeches_width=breeches,
                shoe_direction=(0, 1),
            )
            # Engraved contour down the length of the limb keeps the thigh and
            # shin modelled rather than flat.
            d.cut_path([
                (hip[0] + spread - width * 0.20, 336),
                (hip[0] + spread - width * 0.14, 430),
                (hip[0] + spread - width * 0.20, 524),
            ], 3.6, True)
        # Horizontal base: the upper torso runs right along the ground.
        d.torso([hip, (316, ground_y), (436, ground_y)], 84, False)
        d.head(508, ground_y + 4, -1, math.pi / 2)
        # Arms lie flat on the floor beside the body, hands up by the head.
        for sign in (-1, 1):
            # The arm lies along the floor from the shoulder and reaches back
            # toward the head, the hand coming to rest just short of it. It is
            # carried clear of the torso's own edge so the whole
            # shoulder-to-hand run stays a separate silhouette, with a short
            # deltoid wedge tying it back to the shoulder.
            arm = [
                (336, ground_y + sign * 70),
                (400, ground_y + sign * 76),
                (456, ground_y + sign * 74),
            ]
            d.path([(300, ground_y + sign * 40), arm[0]], 24, False, False,
                   track=False)
            d.path(arm, 26, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 15)
            d.ellipse(arm[-1][0] + 6, arm[-1][1], 18, 14, 0.0)
            # Engraved crease along the forearm.
            d.cut_path([
                (364, ground_y + sign * 64), (404, ground_y + sign * 70),
                (436, ground_y + sign * 68),
            ], 3.6, True)

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
        for sign, arm_x in ((-1, 116), (1, 168)):
            arm = [(arm_x, 640), (arm_x, 386), (arm_x, 132)]
            d.path(arm, 42 if sign < 0 else 34, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 22)
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
        # Dynamic back-bend. The straight arms are planted on the ground and
        # stand vertically to make the left stroke; the torso and thighs slope
        # down-right from the shoulders to the knees as the diagonal; and the
        # knees rest on the ground so both lower legs rise straight up into the
        # air, forming the right stroke.
        shoulder = (150, 640)
        knee = (486, 130)
        # Left stroke: two straight vertical arms bearing weight on the floor.
        for sign, arm_x in ((-1, 116), (1, 178)):
            arm = [(arm_x, 640), (arm_x, 390), (arm_x, 142)]
            d.path(arm, 40 if sign < 0 else 34, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 21)
            # Flat supporting hand pressed on the ground.
            d.ellipse(arm_x, 118, 26, 20, 0.0)
            for offset in (-16, -6, 4, 14):
                d.polygon([
                    (arm_x + offset - 4, 106), (arm_x + offset + 4, 106),
                    (arm_x + offset + 3, 78), (arm_x + offset - 3, 78),
                ])
            d.cut_path([(arm_x - 15, 112), (arm_x + 15, 112)], 3.6, False)
        # Head hangs back and down past the planted shoulders.
        d.head(108, 736, 1, -0.34)
        # Diagonal: the torso leans back from the chest down toward the floor.
        d.torso([shoulder, (300, 430), (430, 216)], 82, True)
        # Right stroke: knees on the ground, lower legs straight up in the air.
        for sign, foot_x in ((-1, 556), (1, 620)):
            d.leg(
                [(430, 216), (knee[0] + sign * 14, knee[1]), (foot_x, 686)],
                54, knee_index=1, breeches_width=74,
                shoe_direction=(0.62, 0.78),
            )

    elif letter == "O":
        # Flat aerial O, closely following the 1782 construction. A broad,
        # shallow shoulder base flows into two rounded arms; each arm keeps a
        # visible outward elbow/knee-like joint so the loop reads as a body
        # rather than an anonymous stroke. The hidden foreshortened torso
        # leaves only its tiny paired feet.
        d.path([(245, 188), (350, 174), (455, 188)], 88, True, True, track=False)
        left_arm = [
            (250, 195), (164, 255), (110, 405),
            (98, 555), (228, 690), (310, 736),
        ]
        right_arm = [(700 - x, y) for x, y in left_arm]
        # Taper each forearm into a narrower wrist rather than ending the ring
        # in generic round terminals; this leaves room for a legible handclasp.
        for arm in (left_arm, right_arm):
            d.path(arm[:-1], 62, True, True, track=False)
            d.path(arm[-2:], 44, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        # Visible articulated side joints: an outward bulb with a transverse
        # cuff/cut marks the knee-like bend on both mirrored sides.
        d.ellipse(96, 402, 36, 24, -0.22)
        d.cut_path([(128, 378), (110, 408), (120, 438)], 6.0, True)
        d.ellipse(604, 402, 36, 24, 0.22)
        d.cut_path([(572, 378), (590, 408), (580, 438)], 6.0, True)
        left_hand = [
            (306, 730), (319, 725), (333, 731), (344, 740),
            (357, 740), (365, 749), (357, 758), (345, 757),
            (336, 750), (324, 759), (311, 752),
        ]
        right_hand = [(700 - x, y) for x, y in left_hand]
        d.polygon(left_hand)
        d.polygon(right_hand)
        # An alternating seam makes the joined silhouette read as fingers
        # wrapped around the opposite hand instead of two touching circles.
        d.cut_path(
            [(329, 748), (340, 754), (350, 747), (360, 754), (371, 748)],
            4.5, True,
        )
        # Foreshortened shoes remain small but turn outward from their actual
        # endpoints as separate bottom serif terminals.
        d.ellipse(304, 238, 27, 11, 0.08)
        d.circle(282, 237, 9)
        d.ellipse(396, 238, 27, 11, -0.08)
        d.circle(418, 237, 9)
        # The head is inverted beneath the shoulders: mouth above eyes, hair
        # below, and pupils lifted toward the ring's interior.
        d.front_head(350, 108, 62, hair_down=True, upside_down=True, gaze_up=True)

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
        d.path([(245, 185), (340, 205), (435, 185)], 90, True, True, track=False)
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
        d.circle(414, 190, 29)
        tail_arm = [(414, 190), (448, 152), (490, 118), (525, 92), (552, 72)]
        d.path(tail_arm, 46, True, True, track=False)
        segments, length = d.centerline_measurements(tail_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": tail_arm, "role": "Q-tail-arm",
        })
        # Compact tail hand with two visible supporting finger tips; the arm
        # stops just outside the lower-right ring instead of stretching past
        # the descender into a detached line.
        d.ellipse(558, 66, 17, 22, -0.58)
        d.polygon([(552, 54), (565, 43), (582, 38), (576, 50), (562, 59)])
        d.polygon([(567, 62), (579, 56), (590, 63), (581, 72), (570, 69)])
        d.cut_path([(555, 58), (563, 51), (573, 52)], 4.0, True)

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
        # Diagonal leg: sharply down and out to the right, foot planted at an
        # angle on the ground.
        d.leg(
            [(stem_x + 18, hip_y), (330, 258), (516, 62)], 56,
            knee_index=1, breeches_width=64, shoe_direction=(1, 0)
        )

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
            d.path([(tip, bar_y + 6), (tip + sign * 8, bar_y - 62)], 34,
                   False, False, track=False)
            d.ellipse(tip + sign * 9, bar_y - 70, 19, 15, 0.0)
            d.cut_path([
                (tip + sign * 9 - 15, bar_y - 34),
                (tip + sign * 9 + 15, bar_y - 34),
            ], 3.6, False)
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
            d.leg(
                [
                    (hip[0] + spread * 0.5, hip[1] + 34),
                    (hip[0] + spread, 470),
                    (hip[0] + spread, 706),
                ],
                width, knee_index=1, breeches_width=width * 1.28,
                shoe_direction=(0, 1),
            )
        # Right bar: both arms vertical and parallel, hands pointing skyward.
        for spread in (-14, 14):
            arm = [
                (shoulder[0] + spread * 0.5, shoulder[1] + 30),
                (shoulder[0] + spread, 460),
                (shoulder[0] + spread, 654),
            ]
            d.path(arm, 40 if spread < 0 else 34, True, False, track=False)
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
        # top corners, and the arms lie along and grip the rising legs.
        d.head(350, 105, 1, -math.pi / 2)
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
        d.head(350, 585, 1)
        d.torso([(350, 525), (350, 390)], 88, False)
        left_arm = [(320, 405), (280, 225), (255, 72)]
        right_arm = [(380, 405), (420, 225), (445, 72)]
        for arm in (left_arm, right_arm):
            d.path(arm, 54, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        d.leg(
            [(315, 390), (145, 0), (60, 725)], 62, knee_index=1,
            shoe_direction=(-0.92, 0.40),
        )
        d.leg(
            [(385, 390), (555, 0), (640, 725)], 62, knee_index=1,
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
        d.leg(
            [(350 - 30, 222), (350 - 34, 300), (350 - 32, 56)], 58,
            knee_index=1, breeches_width=76, shoe_direction=(-1, 0)
        )
        d.leg(
            [(350 + 30, 222), (350 + 34, 300), (350 + 32, 56)], 58,
            knee_index=1, breeches_width=76, shoe_direction=(1, 0)
        )

    elif letter == "Z":
        d.head(530, 710, -1)
        d.limb([(105, 705), (310, 705), (520, 690)], 58, False, end="hand")
        d.torso([(500, 660), (380, 500), (260, 330), (150, 155)], 92)
        d.leg([(160, 150), (350, 105), (600, 105)], 62, knee_index=1)
        d.leg([(180, 180), (340, 150), (555, 150)], 50, knee_index=1)

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
