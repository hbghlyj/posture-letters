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

    def to_glyph(self):
        pen = TTGlyphPen(None)
        for poly, _hole in self.contours:
            pen.moveTo(poly[0])
            for p in poly[1:]:
                pen.lineTo(p)
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
        # Source-faithful forward fold. Hips make the apex; paired breeched
        # thighs and modeled calves descend on the right while the attached
        # spine, neck, inverted head, and hanging hat continue down the left.
        # Both source shoes turn inward/left beneath the closely paired legs.
        a_legs = [
            [(345, 650), (420, 520), (490, 390), (530, 245), (565, 90)],
            [(375, 645), (445, 510), (515, 375), (565, 235), (610, 90)],
        ]
        for points in a_legs:
            hip, thigh_mid, knee, calf_mid, ankle = points
            d.leg(
                points, 50, knee_index=2, breeches_width=70,
                shoe_direction=(-1, 0), shoe_scale=0.72,
                anatomy_points=[hip, knee, ankle],
            )

        # Inset cuff seams and long engraved calf/shin contours keep the two
        # lower bodies anatomical rather than reading as straight pant strokes.
        for pts, width in (
            ([(466, 401), (486, 412)], 4),
            ([(520, 386), (540, 397)], 4),
            ([(482, 350), (500, 292), (515, 220), (540, 125)], 5),
            ([(512, 320), (526, 258), (540, 185)], 4),
            ([(535, 338), (559, 278), (584, 205), (602, 125)], 5),
            ([(560, 315), (578, 250), (594, 180)], 4),
        ):
            d.cut_path(pts, width, True)

        d.torso(
            [(360, 640), (300, 570), (245, 490), (190, 400), (145, 300), (105, 200)],
            88, True, False
        )
        # Facing -1 under a half-turn keeps the nose/eye looking right while
        # placing the hat below the head, exactly as the inverted source does.
        d.head(105, 145, -1, math.pi)
        d.limb([(175, 410), (325, 410), (500, 410)], 36, False, end="hand")
        d.limb([(165, 372), (325, 372), (505, 372)], 36, False, end="hand")

    elif letter == "B":
        # Upright left side with two shortened clasped arms making the upper
        # bowl. The arms have a shoulder/elbow/hand span near normal anatomy.
        # Below the pelvis the planted left leg stays separate, while the right
        # thigh bends out to a visible knee and the shorter calf descends to a
        # source-directed inward shoe for the lower B.
        d.head(168, 752, 1)
        d.torso([(170, 690), (170, 515), (180, 340)], 88, False)
        upper_arm = [(195, 650), (285, 665), (350, 598)]
        lower_arm = [(175, 560), (290, 540), (350, 598)]
        for arm, width in ((upper_arm, 50), (lower_arm, 46)):
            d.path(arm, width, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        d.cut_path([(282, 662), (305, 648), (320, 626)], 4.5, True)
        d.cut_path([(276, 550), (297, 547), (316, 556)], 4.0, True)
        d.ellipse(355, 601, 22, 27, -0.25)
        d.ellipse(347, 585, 20, 24, -0.25)
        d.cut_path([(338, 613), (353, 605), (370, 610)], 4.5, True)
        d.cut_path([(340, 599), (354, 592), (369, 598)], 4.5, True)
        d.leg(
            [(175, 345), (162, 210), (170, 75)], 58, knee_index=1, shoe_direction=(1, 0)
        )
        d.leg(
            [(195, 345), (385, 280), (330, 95)],
            58, knee_index=1, shoe_direction=(-1, 0)
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
        # Inverted circular fold from the print: head under the lower curve,
        # torso on the right, one long leg over the top and down the left, and
        # an arm reaching up to meet the foot.
        # Mirror only the nose, eye, and cocked-hat asymmetry; the attached
        # head circle and the circular body construction stay in place.
        d.head(355, 105, 1, -math.pi / 2, mirror_details=True)
        d.torso([(355, 165), (500, 220), (565, 385), (515, 570)], 96, True)
        d.leg([(505, 575), (355, 680), (185, 650), (155, 500), (155, 345)], 62, knee_index=2)
        d.limb([(340, 175), (230, 155), (145, 225), (155, 330)], 48, True, end="hand")
        d.limb([(375, 180), (270, 190), (175, 250), (170, 325)], 38, True, end="hand")

    elif letter == "E":
        # Historical seated E. Head and torso form the stem; the top and middle
        # bars are arms. The broad lower leg lies straight along the baseline,
        # while the slimmer near leg remains visibly separate just above it;
        # both source-profile shoes turn upward at their anatomical endpoints.
        d.head(160, 745, 1)
        # Continue the stem directly into the lower leg centerline so the
        # baseline stroke is a seamless seated body connection, not a floater.
        d.torso([(160, 680), (160, 485), (160, 100)], 90, False)
        d.limb([(180, 640), (390, 650), (590, 650)], 50, False, end="hand")
        d.limb([(180, 470), (330, 410), (455, 410)], 48, False, end="hand")
        d.leg(
            [(160, 100), (370, 100), (585, 100)], 58, knee_index=1, shoe_direction=(0.55, 1.0)
        )
        d.leg(
            [(170, 175), (365, 175), (560, 175)], 36, knee_index=1, shoe_direction=(0.55, 1.0)
        )

    elif letter == "F":
        # Upright historical F: top and middle bars are arms; two close legs
        # continue the body stem below the hips.
        d.head(175, 745, 1)
        # Hips sit at mid-stem so the legs below match the trunk in length.
        d.torso([(175, 680), (175, 555), (175, 430)], 90, False)
        d.limb([(190, 635), (390, 650), (600, 650)], 50, False, end="hand")
        d.limb([(185, 470), (320, 420), (465, 420)], 48, False, end="hand")
        # Both profile shoes point right in the historical standing pose.
        d.leg(
            [(158, 432), (152, 245), (145, 62)], 50, knee_index=1,
            breeches_width=56, shoe_direction=(1, 0)
        )
        d.leg(
            [(192, 432), (198, 245), (205, 62)], 50, knee_index=1,
            breeches_width=56, shoe_direction=(1, 0)
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
        # (shoulder to elbow) hangs vertically downward and overlaps the
        # figure's own pillar; only the forearms turn out horizontally at elbow
        # height and clasp at the centre, so the crossbar is made of forearms
        # alone and sits exactly at the elbows.
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
            arm_x = cx + side * 22
            shoulder = (arm_x, 610)
            elbow = (arm_x, bar_y)
            hand = (350 - side * 24, bar_y)
            d.path([shoulder, elbow], 40, False, False, track=False)
            d.path([elbow, hand], 34, False, False, track=False)
            # A joint ball keeps the right-angle bend readable as an elbow.
            d.circle(elbow[0], elbow[1], 23)
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
            back_arm_x = cx - side * 26
            back_shoulder = (back_arm_x, 602)
            back_elbow = (back_arm_x, 500)
            back_hand = (back_arm_x + side * 62, 500)
            d.path([back_shoulder, back_elbow], 32, False, False, track=False)
            d.path([back_elbow, back_hand], 28, False, False, track=False)
            d.circle(back_elbow[0], back_elbow[1], 17)
            d.circle(back_hand[0], back_hand[1], 16)
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
        d.head(350, 742, 1)
        d.torso([(350, 675), (350, 540), (350, 385)], 80, False)
        # Arms hang at the sides, slimmer than the trunk and set just clear of
        # it, so the shoulder-to-hand limb stays legible instead of fusing into
        # one slab. Engraved seams keep the separation readable at text sizes.
        for sign in (-1, 1):
            arm = [
                (350 + sign * 52, 630), (350 + sign * 60, 500),
                (350 + sign * 58, 390),
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
                (350 + sign * 43, 596), (350 + sign * 49, 500),
                (350 + sign * 47, 424),
            ], 4.0, True)
        d.leg([(335, 395), (330, 225), (325, 55)], 52, knee_index=1)
        d.leg([(365, 395), (370, 225), (375, 55)], 52, knee_index=1)

    elif letter == "J":
        d.head(500, 750, -1)
        d.torso([(500, 685), (500, 470), (500, 250), (450, 100), (300, 60), (170, 135)], 88)
        d.limb([(470, 630), (335, 650), (205, 650)], 48, False, end="hand")
        d.limb([(520, 625), (560, 635), (600, 650)], 44, False, end="hand")
        d.leg([(450, 115), (325, 65), (190, 125)], 55, knee_index=1)

    elif letter == "K":
        # Historical standing profile: body/near leg are the stem. The upper
        # arm first drops to a distinct elbow, then the forearm sweeps upward
        # to the source's compact thumb-and-index hand at the upper-right serif.
        d.head(230, 710, 1)
        d.torso([(235, 650), (235, 500), (240, 330)], 90, False)
        upper_arm = [(250, 585), (335, 550), (390, 580), (465, 655), (535, 710)]
        d.path(upper_arm, 48, True, True, track=False)
        segments, length = d.centerline_measurements(upper_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": upper_arm,
        })
        # The source hand is a compact directional serif rather than a five-ray
        # star. Its index finger points sharply right and the thumb opens upward;
        # the other three fingers fold back into the palm as engraved creases.
        d.ellipse(543, 714, 31, 22, 0.55)
        d.polygon([
            (548, 720), (557, 711), (583, 722), (610, 732),
            (626, 742), (608, 744), (579, 735), (552, 731),
        ])
        d.polygon([
            (538, 720), (528, 714), (520, 737), (509, 756),
            (516, 766), (530, 748), (546, 731),
        ])
        for crease in (
            [(552, 716), (563, 710), (573, 714)],
            [(549, 708), (559, 701), (569, 705)],
            [(544, 700), (553, 693), (562, 698)],
        ):
            d.cut_path(crease, 4.4, True)

        # The second arm remains close to the torso instead of becoming an
        # invented fourth ray.
        d.limb([(220, 570), (205, 430), (220, 315)], 40, True, end="hand")
        # Both shoes face right in the source profile, including the planted leg.
        d.leg(
            [(230, 330), (215, 185), (205, 65)], 56, knee_index=1, shoe_direction=(1, 0)
        )
        d.leg(
            [(255, 330), (385, 205), (560, 95)], 58, knee_index=1, shoe_direction=(1, 0)
        )
        # Engraved calf and shin cuts give both lower strokes the modeled
        # stocking anatomy visible in the historical figure.
        for pts, width in (
            ([(220, 290), (225, 245), (217, 205), (211, 140)], 5),
            ([(203, 275), (203, 225), (207, 180)], 4),
            ([(285, 302), (332, 258), (385, 212), (455, 160), (520, 120)], 5),
            ([(325, 284), (370, 240), (420, 200), (475, 158)], 4),
        ):
            d.cut_path(pts, width, True)

    elif letter == "L":
        # Seated profile: the head and shoulders lean back behind the pelvis;
        # both straight legs extend on parallel horizontal centerlines.
        d.head(170, 745, 1)
        d.torso([(170, 680), (175, 485), (210, 210)], 90, False)
        d.leg(
            [(205, 165), (395, 165), (585, 165)], 62, knee_index=1, shoe_direction=(0.7, 1.0)
        )
        d.leg(
            [(215, 205), (385, 205), (555, 205)], 50, knee_index=1, shoe_direction=(0.7, 1.0)
        )
        d.limb([(175, 560), (205, 385), (230, 260)], 46, True, end="hand")
        d.limb([(195, 550), (225, 400), (250, 285)], 38, True, end="hand")

    elif letter == "M":
        # The source's deliberately impossible M: calf-shaped outer pillars
        # rise to bent knees, then enormous thighs descend to the central dip.
        # A distinct upward-facing head peers through that dip above two
        # buttock lobes, which the paired hands visibly brace from beneath.
        left_calf = [
            (92, 710), (76, 625), (76, 520), (85, 405), (95, 300),
            (90, 185), (88, 70), (126, 70), (130, 185), (139, 300),
            (155, 405), (162, 520), (155, 625), (145, 710),
        ]
        right_calf = [(700 - x, y) for x, y in left_calf]
        d.polygon(left_calf)
        d.polygon(right_calf)
        d.anatomy.append({"part": "limb", "segments": [640.0], "length": 640.0,
                          "points": [(119, 710), (107, 70)]})
        d.anatomy.append({"part": "limb", "segments": [640.0], "length": 640.0,
                          "points": [(581, 710), (593, 70)]})
        d.shoe(107, 70, (109, 150), (-1, 0))
        d.shoe(593, 70, (591, 150), (1, 0))
        # Gathered below-knee cuffs separate the vast breeched thighs from the
        # source's already exaggerated stockinged calf pillars.
        for knee_x in (122, 578):
            d.ellipse(knee_x, 700, 39, 11)
            d.cut_path([(knee_x - 28, 700), (knee_x + 28, 700)], 4.5, False)
        # Fine interior cuts reinforce the modeled gastrocnemius and shin.
        d.cut_path([(105, 590), (116, 510), (112, 425), (102, 345)], 6, True)
        d.cut_path([(595, 590), (584, 510), (588, 425), (598, 345)], 6, True)
        d.cut_path([(127, 520), (134, 440), (127, 365)], 4, True)
        d.cut_path([(573, 520), (566, 440), (573, 365)], 4, True)

        d.path([(122, 710), (180, 675), (235, 520), (300, 330)], 112, True, False)
        d.path([(578, 710), (520, 675), (465, 520), (400, 330)], 112, True, False)

        # Separate rounded lobes preserve a narrow central cleft rather than a
        # generic single pelvis oval.
        d.polygon([
            (346, 315), (328, 330), (292, 326), (258, 305), (245, 270),
            (258, 230), (300, 205), (340, 216), (346, 250),
        ])
        d.polygon([
            (354, 315), (372, 330), (408, 326), (442, 305), (455, 270),
            (442, 230), (400, 205), (360, 216), (354, 250),
        ])
        # The source leaves both hands pale against the dark central body.
        # Model them as open negative-space palms on the outside of the two
        # buttock lobes, then redraw black finger separations in each palm so
        # they unmistakably read as hands cupping the two distinct lobes.
        left_hand = [
            (246, 286), (252, 302), (263, 309), (277, 307),
            (287, 296), (282, 282), (268, 270), (252, 269),
        ]
        right_hand = [(700 - x, y) for x, y in left_hand]
        d.polygon(left_hand, hole=True)
        d.polygon(right_hand, hole=True)
        for pts in (
            [(254, 297), (264, 289), (276, 285)],
            [(251, 289), (263, 282), (276, 279)],
            [(446, 297), (436, 289), (424, 285)],
            [(449, 289), (437, 282), (424, 279)],
        ):
            d.path(pts, 3, True, joints=False, track=False)

        # A frontal cameo projects into the open central dip. Its pale face
        # field, symmetric eyes, centered nose, and mouth remain legible at
        # webfont sizes while the black rim joins the impossible M body.
        d.path([(350, 365), (350, 378)], 12, True, joints=False, track=False)
        d.ellipse(350, 400, 35, 29)
        d.ellipse(350, 400, 27, 21, hole=True)
        d.circle(341, 406, 3)
        d.circle(359, 406, 3)
        d.polygon([(350, 402), (346, 394), (354, 394)])
        d.path([(342, 388), (350, 385), (358, 388)], 3, True, joints=False, track=False)
        d.anatomy.append({"part": "head", "diameter": 70.0, "center": (350, 400)})

    elif letter == "N":
        # Historical inverted curl: head and hands at lower-left, a folded
        # limb rises on the left, the body sweeps diagonally down-right, and a
        # stockinged leg rises vertically at the right. The broad bent knee is
        # lowered to the same ground plane as the inverted head, while the high
        # inner corner remains at waist level for a decisive N construction.
        d.torso([(120, 145), (115, 560), (185, 625)], 78, True)
        d.leg(
            [(185, 625), (300, 450), (470, 55), (505, 365), (535, 655)],
            58, knee_index=2, breeches_width=86, shoe_direction=(1, 0),
        )
        d.limb([(175, 165), (140, 145), (110, 150)], 38, True, end="hand")
        # The source sleeve begins at the raised inner corner and descends over
        # the front of the broad blue body. Keep its human-length centerline on
        # that foreground diagonal; the narrower forearm and projecting palm
        # remain visible at the body's right edge even in one-color outlines.
        foreground_arm = [(185, 575), (245, 500), (300, 410), (390, 335)]
        # A narrow negative halo is cut only where the sleeve crosses the blue
        # leg; redrawing the narrower arm inside it gives a true over-under edge
        # without detaching the shoulder or erasing the projecting hand.
        d.cut_path([(220, 540), (245, 500), (300, 410), (355, 365)], 56, True)
        d.path(foreground_arm[:3], 44, True, True, track=False)
        d.path(foreground_arm[2:], 32, True, True, track=False)
        segments, length = d.centerline_measurements(foreground_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": foreground_arm, "role": "N-foreground-arm",
        })
        d.ellipse(300, 410, 24, 10, -0.55)
        d.circle(390, 335, 24)
        d.ellipse(409, 340, 15, 5, 0.10)
        d.ellipse(408, 330, 15, 5, -0.16)
        # The left composite endpoint retains its attached source-direction shoe.
        d.shoe(120, 585, (115, 545))
        # Draw the low head last so the eye is not buried by the diagonal.
        d.head(105, 90, 1, 0.10)

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
        # Standing profile with two compact, separately articulated backward-
        # bending arms making the bowl. Both shoulder-to-hand routes now stay
        # near normal human arm length instead of stretching into rubbery arcs.
        d.head(165, 752, 1)
        # Hips sit at mid-stem so the legs below match the trunk in length.
        d.torso([(165, 690), (165, 555), (165, 425)], 88, False)
        upper_arm = [(190, 650), (275, 675), (350, 650), (415, 585), (440, 525)]
        lower_arm = [(175, 480), (275, 455), (365, 465), (445, 505)]
        for arm, main_width, wrist_width in (
            (upper_arm, 54, 42),
            (lower_arm, 50, 40),
        ):
            d.path(arm[:-1], main_width, True, True, track=False)
            d.path(arm[-2:], wrist_width, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        # Elbow and sleeve creases retain the human articulation inside the
        # typographic loop rather than leaving a single anonymous tube.
        d.cut_path([(360, 646), (385, 626), (404, 602)], 5.0, True)
        d.cut_path([(264, 470), (277, 458), (292, 460)], 4.5, True)
        d.cut_path([(374, 470), (398, 480), (418, 492)], 4.0, True)
        # Overlapping palms and broad wrapped-finger seams make the compact
        # right join an explicit handclasp while preserving a closed P counter.
        d.ellipse(442, 521, 24, 29, -0.15)
        d.ellipse(437, 504, 23, 26, -0.15)
        d.cut_path([(426, 531), (439, 523), (454, 527)], 5.0, True)
        d.cut_path([(426, 518), (439, 511), (455, 516)], 5.0, True)
        d.cut_path([(428, 505), (441, 499), (454, 505)], 4.5, True)
        # The crop shows the planted feet as an outward pair: left foot to the
        # left, near/right foot to the right.
        d.leg(
            [(148, 427), (143, 242), (138, 58)], 52, knee_index=1,
            breeches_width=58, shoe_direction=(-1, 0)
        )
        d.leg(
            [(182, 427), (188, 242), (195, 58)], 52, knee_index=1,
            breeches_width=58, shoe_direction=(1, 0)
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
        # P-like clasped-arm bowl with one planted leg and one stepped leg.
        d.head(165, 752, 1)
        # Hips sit at mid-stem so the legs below match the trunk in length.
        d.torso([(165, 690), (165, 555), (165, 425)], 88, False)
        # Upper bowl, built like B: two shortened clasped arms with a normal
        # shoulder-elbow-hand span, instead of one distorted overlong limb
        # looping all the way out and back.
        upper_arm = [(192, 650), (288, 668), (355, 600)]
        lower_arm = [(175, 505), (290, 492), (355, 600)]
        for arm, width in ((upper_arm, 50), (lower_arm, 46)):
            d.path(arm, width, True, True, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        # Elbow and sleeve creases, as on B. They are kept short and well
        # inside the limb so they read as engraving and never open a white
        # gap through the bowl's outline.
        d.cut_path([(288, 660), (303, 651), (314, 638)], 4.0, True)
        d.cut_path([(284, 501), (299, 499), (312, 506)], 3.6, True)
        # Clasped hands close the bowl at the right. The two palms overlap the
        # arm ends generously so the loop stays one solid, continuous shape.
        d.ellipse(356, 600, 26, 31, -0.25)
        d.ellipse(347, 583, 24, 28, -0.25)
        d.cut_path([(347, 612), (358, 606), (369, 610)], 4.0, True)
        d.cut_path([(348, 598), (359, 593), (369, 597)], 4.0, True)
        d.leg(
            [(180, 428), (350, 250), (585, 55)], 62, knee_index=1, shoe_direction=(1, 0)
        )
        # In the crop the planted shoe projects toe-first to the figure's right;
        # a full horizontal direction makes that outward profile unmistakable
        # and removes the formerly reversed foot.
        d.leg(
            [(152, 425), (146, 240), (140, 55)], 55, knee_index=1,
            breeches_width=60, shoe_direction=(1, 0)
        )

    elif letter == "S":
        # Kneeling profile from the print: close shins run left along the
        # ground, the body curls upward, and one long arm arches over the head.
        d.leg([(455, 185), (315, 110), (110, 110)], 58, knee_index=1)
        d.leg([(440, 205), (305, 145), (135, 145)], 46, knee_index=1)
        d.torso([(450, 190), (475, 340), (405, 470), (300, 535)], 96, True)
        d.limb([(285, 555), (190, 610), (245, 690), (410, 700), (535, 625)], 50, True, end="hand")
        d.limb([(300, 530), (245, 565), (225, 610)], 40, True, end="hand")
        d.head(320, 525, 1, 0.06)

    elif letter == "T":
        # Arms make the crossbar; both legs stay together and descend
        # vertically, matching the upright stance in the historical print.
        # Proportions follow a standing human reference: the torso runs from
        # shoulders to hips at roughly the same length as the legs beneath it,
        # rather than a long trunk on stub legs.
        d.head(350, 700, 1)
        d.torso([(350, 635), (350, 520), (350, 400)], 90, False)
        d.limb([(330, 620), (190, 650), (75, 650)], 50, False, end="hand")
        d.limb([(370, 620), (510, 650), (625, 650)], 50, False, end="hand")
        d.leg([(324, 400), (322, 228), (321, 55)], 44, knee_index=1,
              breeches_width=48)
        d.leg([(376, 400), (378, 228), (379, 55)], 44, knee_index=1,
              breeches_width=48)

    elif letter == "U":
        # The historic print omitted U; this hanging bend puts it back.
        d.head(350, 95, 1)
        d.torso([(350, 155), (350, 255)], 88, False)
        d.limb([(325, 205), (175, 180), (90, 360), (95, 730)], 58, end="hand")
        d.limb([(375, 205), (525, 180), (610, 360), (605, 730)], 58, end="hand")
        d.leg([(340, 250), (210, 260), (120, 430), (120, 725)], 58, knee_index=2)
        d.leg([(360, 250), (490, 260), (580, 430), (580, 725)], 58, knee_index=2)

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
        # Upright Y in the Vitruvian raised-arm pose: head at top, arms
        # diagonally up to the upper forks, paired legs descending together as
        # the stem. Arms and legs share a similar limb width, both visibly
        # slimmer than the torso; the raised hands are open with splayed fingers.
        d.head(350, 700, 1)
        d.torso([(350, 640), (350, 430)], 90, False)
        left_arm = [(335, 630), (240, 700), (135, 742)]
        right_arm = [(365, 630), (460, 700), (565, 742)]
        for arm in (left_arm, right_arm):
            d.path(arm, 42, True, False, track=False)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
        # Open raised hands with fingers splayed toward the upper corners.
        for x, y, s in ((135, 742, -1), (565, 742, 1)):
            d.ellipse(x, y, 22, 15, s * 0.55)
            for dx, dy in (
                (-18, 10), (-20, 0), (-16, -9), (-8, -15), (2, -15),
            ):
                d.polygon([
                    (x - s * 6, y + 4),
                    (x + s * dx, y + dy),
                    (x + s * (dx + 4), y + dy + 3),
                ])
        d.leg([(338, 430), (332, 240), (322, 50)], 58, knee_index=1)
        d.leg([(362, 430), (368, 240), (378, 50)], 58, knee_index=1)

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
        d.head(350, 90, 1)
        d.torso([(350, 720), (350, 250)], 80, False)
        d.circle(350, 760, 34)
    elif name == "question":
        d.head(350, 90, 1)
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

    glyphs = {name: drawings[name].to_glyph() for name in drawings}
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
    metrics = {name: (330 if name == "space" else ADVANCE, 0) for name in order}
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
