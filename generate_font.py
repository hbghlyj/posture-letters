#!/usr/bin/env python3
"""Build Posture Master, a deliberately bendy human-alphabet display font.

Most letterforms are traced from modern gymnast and yoga photographs.
Punctuation still uses a few body-part primitives.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from outline_points import LETTERS

ROOT = Path(__file__).resolve().parent
UPM = 1000
ADVANCE = 700
# Constant space kept on each side of a glyph's ink when fitting its advance.
SIDEBEARING = 72
# Shared baseline: every traced letter sits on this line.
BAR_GROUND = 72.0


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
    points: list[Point], widths: list[float], smooth: bool = True, steps: int = 8,
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

    def ellipse(
        self, x: float, y: float, rx: float, ry: float, angle: float = 0,
        hole: bool = False,
    ) -> None:
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
        self, pts: list[Point], widths: list[float], smooth: bool = True,
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
        draw_shin: bool = True,
    ) -> None:
        """Draw short breeches, a knee cuff, muscular calf, ankle, and shoe.

        Every historical foot-ending limb uses this construction. The trousers
        stay full through the thigh and stop just below the indexed knee; the
        stockinged lower leg then swells at the gastrocnemius before narrowing
        decisively into the ankle. The centerline and shoe endpoint remain the
        source pose's own, so anatomy does not regularize the letter geometry.

        ``draw_shin`` controls whether to draw the shin (lower leg) portion.
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
        if draw_shin:
            self.tapered_path(
                lower_profile,
                [width * 0.78, width * 0.90, width * 1.22, width * 0.82, width * 0.50],
                True,
            )

        # Thigh and shin are separate tapered strokes with flat ends, so at a
        # bent knee their two square ends leave a sharp beveled wedge. A joint
        # mass at the knee point fills that wedge and gives the outline the
        # continuous curve of a real knee instead of a blocky corner.
        #
        # A plain circle sized to the widest limb overfills a shallow bend: it
        # protrudes past both strokes and the knee reads as a ball stuck on
        # the leg. How much fill the bevel actually needs depends on the angle
        # of the bend, so the mass is sized from that angle and drawn as an
        # ellipse aligned to the limb — long along the leg, tight across it —
        # so it swells over the kneecap without bulging out sideways.
        knee = pts[knee_index]
        before = self.polyline_point(upper, 0.86)
        after = lower_profile[1]
        v1 = (before[0] - knee[0], before[1] - knee[1])
        v2 = (after[0] - knee[0], after[1] - knee[1])
        n1 = math.hypot(*v1) or 1.0
        n2 = math.hypot(*v2) or 1.0
        cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        bend = math.acos(max(-1.0, min(1.0, cosine)))
        # A straight leg (bend = pi) needs nothing; a right angle needs a mass
        # about as wide as the limb. Half the exterior angle drives the fill.
        fill = math.sin(max(0.0, (math.pi - bend)) * 0.5)
        limb = max(width, breeches * 0.82)
        joint_r = limb * (0.40 + 0.24 * fill)
        # The kneecap sits on the outside of the bend, so the mass is offset
        # along the outward bisector and its long axis runs across the leg,
        # square to that bisector: it swells over the joint the way a knee
        # does without ballooning out to either side of the limb.
        bx = -(v1[0] / n1 + v2[0] / n2)
        by = -(v1[1] / n1 + v2[1] / n2)
        bn = math.hypot(bx, by)
        if bn < 1e-6:
            self.circle(knee[0], knee[1], joint_r, n=24)
        else:
            bx, by = bx / bn, by / bn
            centre = (knee[0] + bx * joint_r * 0.16, knee[1] + by * joint_r * 0.16)
            self.ellipse(
                centre[0], centre[1], joint_r * 0.98, joint_r * 1.04,
                math.atan2(by, bx),
            )

        next_point = lower_profile[1]
        dx, dy = next_point[0] - knee[0], next_point[1] - knee[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        cuff_angle = math.atan2(dy, dx) + math.pi / 2
        self.ellipse(
            knee[0], knee[1], breeches * 0.43, max(6.0, breeches * 0.105),
            cuff_angle,
        )
        # A short inset hem line defines the below-knee end without severing it.
        self.cut_path([
            (knee[0] - nx * breeches * 0.20, knee[1] - ny * breeches * 0.20),
            (knee[0] + nx * breeches * 0.20, knee[1] + ny * breeches * 0.20),
        ], max(2.8, width * 0.055), False)

        if draw_shin:
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
        if draw_shin:
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
        upside_down: bool = False, gaze_up: bool = False, hat: bool = True,
    ) -> None:
        """A compact aerial/front-facing head, optionally with a serif-hat.

        ``upside_down`` rotates the facial hierarchy inside a fixed head, while
        ``gaze_up`` adds pupils at the upper edge of the eye sockets. These are
        independent of ``hair_down`` so an inverted recumbent face can retain
        the source-visible hair silhouette beneath the skull. ``hat`` drops
        the cocked brim and crown — Q's print is bareheaded.
        """
        self.anatomy.append({"part": "head", "diameter": radius * 2, "center": (x, y)})
        self.ellipse(x, y, radius, radius * 0.9)
        self.circle(x - radius * 0.88, y, radius * 0.19)
        self.circle(x + radius * 0.88, y, radius * 0.19)
        hat_sign = -1 if hair_down else 1
        if hat:
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
        else:
            # A hair cap on the skull, not a cocked hat: the print's Q has
            # dark hair on the outer (bottom) side of the inverted head.
            self.ellipse(
                x, y + hat_sign * radius * 0.52,
                radius * 0.92, radius * 0.42,
            )
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
        # Editorial yoga-alphabet A, imported like L. A standing wide-legged
        # forward fold: the lifted hips are the apex, the two spread legs run
        # down and outward as the diagonals, and the folded torso and
        # reaching arms lie across the middle as the crossbar, enclosing a
        # triangular counter.
        pts, holes = LETTERS["A"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)


    elif letter == "B":
        # Editorial yoga-alphabet B, imported like L. Seen from behind:
        # the standing leg and torso are the stem, the hand-on-hip
        # elbow is the upper bowl, and the bent knee is the lower bowl.
        pts, holes = LETTERS["B"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "C":
        # Editorial yoga-alphabet C, imported like L. A kneeling
        # backbend: shins on the floor, thighs the left stem, arched
        # torso and thrown-back head opening to the right.
        pts, holes = LETTERS["C"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "D":
        # Ustrasana (camel pose) in place of the print's impossible ring
        # backbend. The 1782 D closed the bowl by folding the legs up to
        # meet a descending hand — past a real spine. This glyph is a
        # traced silhouette of a kneeling camel: head thrown back on the
        # left, thighs the right pillar, hands on the heels. The source
        # photo faces this way; the first import was mirrored.
        # Same import path as L: one closed outline (plus the natural
        # counter) scaled uniformly onto BAR_GROUND.
        pts, holes = LETTERS["D"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (right - x) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "E":
        # Editorial yoga-alphabet E, imported like L. Kneeling with the
        # upright spine as the stem, the raised arm above the head as the
        # top bar, the forward arm at chest height as the middle bar, and
        # the folded legs along the floor as the bottom bar.
        pts, holes = LETTERS["E"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "F":
        # Editorial yoga-alphabet F, imported like L. Standing on one
        # straight leg as the stem, both arms extended forward at the top
        # as the upper bar, and the folded lifted leg — thigh forward,
        # shin tucked down — as the middle bar.
        pts, holes = LETTERS["F"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "G":
        # Editorial yoga-alphabet G / Vrischikasana (scorpion), imported
        # like L. An inverted backbend: arms and hanging head at the
        # bottom, arched torso the bowl, feet the spur.
        pts, holes = LETTERS["G"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "H":
        # Editorial yoga-alphabet H, imported like L. The horizontal torso
        # is the crossbar; the raised leg above and the kneeling shin below
        # make the left stem; the raised arm above and the planted arm
        # below make the right stem.
        pts, holes = LETTERS["H"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "I":
        # Editorial yoga-alphabet I, imported like L. Standing upright with
        # the legs pressed together as the stem, both arms raised and crossed
        # above the head so the forearms and open hands make the top serif,
        # and the feet turned outward to make the bottom serif.
        pts, holes = LETTERS["I"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "J":
        # Editorial yoga-alphabet J, imported like L. The joined upright legs
        # make the single tall right stem and the flexed feet point left as a
        # short top serif. Hips, back, and merged arms sweep through the open
        # bottom hook; its naturally upright profile head and smooth neck make
        # the compact lower-left terminal without closing the counter.
        pts, holes = LETTERS["J"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "K":
        # Editorial yoga-alphabet K, imported like L. The upright torso
        # over a kneeling leg is the vertical stem, the raised arm is the
        # upper diagonal, and the extended straight leg is the lower
        # diagonal.
        pts, holes = LETTERS["K"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "L":
        # Kneeling side profile, imported as a traced silhouette rather than
        # assembled from body-part primitives. The outline is VTracer's spline
        # trace of vector_kneeling_upright_torso.png — a female figure in
        # strict side profile, high-kneeling with the upper torso perfectly
        # upright and vertical (head with a low bun, straight erect spine, arm
        # relaxed at the side), the shin and pointed foot lying flat along the
        # floor to the right as the letter's bottom bar. The figure's own
        # anatomy supplies the letterform: the vertical trunk is the stem and
        # the grounded lower leg is the bar, so no synthetic strokes, serifs
        # or engraved cuts are added on top of the trace. The single closed
        # contour is scaled uniformly from SVG pixel space (y-down) into font
        # units (y-up), seated on the shared kneeling ground line BAR_GROUND
        # and reaching the same 788-unit cap height as the previous L.
        pts = LETTERS["L"][0]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)
        d.polygon([
            (SIDEBEARING + (x - left) * scale, BAR_GROUND + (bottom - y) * scale)
            for x, y in pts
        ])

    elif letter == "M":
        # Editorial yoga-alphabet M, imported like L, following the 1782
        # print's own M: a figure folded completely double and seen from
        # behind, the two raised knees making the peaks, the calves dropping
        # to flat feet as the outer stems, and the thighs sloping down and
        # inward to the hanging hips to make the central V.
        pts, holes = LETTERS["M"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)


    elif letter == "N":
        # Editorial yoga-alphabet N, imported like L from the 2 Way Stretch
        # crop. A straight supporting arm and planted hand make the left stem;
        # the profile head, chest, waist, abdomen, and pelvis descend as the
        # organic diagonal; and the joined raised leg makes the right stem.
        pts, holes = LETTERS["N"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "O":
        # Editorial yoga-alphabet O, imported like L. A full bow whose
        # raised feet and both grasping arms close a ring, with a large
        # natural counter.
        pts, holes = LETTERS["O"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "P":
        # Editorial yoga-alphabet P, imported like L. A standing
        # backbend whose planted legs are the stem and whose arched
        # torso, hanging head and clasped hands close the bowl.
        pts, holes = LETTERS["P"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "Q":
        # Editorial bow-as-Q, imported like L. A prone backbend whose
        # raised feet and grasping arm close the ring, while the other
        # arm plants on the floor as the tail. The print's inverted
        # ring is replaced because this pose is more legible as a Q.
        pts, holes = LETTERS["Q"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "R":
        # Editorial yoga-alphabet R, imported like L. The same standing
        # backbend as P, with the front leg stepped forward as the
        # diagonal of the letter.
        pts, holes = LETTERS["R"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "S":
        # Historic S, reconstructed through a corrected photographic gymnast
        # and direct monochrome conversion. Grounded shins and feet sweep left
        # as the lower terminal; thighs rise at lower right; the backbend and
        # profile head form the middle curve; closely overlapped arms continue
        # overhead into the upper-right terminal.
        pts, holes = LETTERS["S"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "T":
        # Editorial yoga-alphabet T, imported like L. Standing upright
        # seen from behind: legs together as the vertical stem, both arms
        # stretched straight out level with the shoulders as the bar.
        pts, holes = LETTERS["T"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "U":
        # Editorial yoga-alphabet U, imported like L from
        # image_6a52f7c6.png. A side-profile gymnast on the back: arms
        # rise as the left stem with an inward hand serif, the rounded
        # hips and torso make the bowl, and joined legs rise as the
        # right stem to pointed feet. The profile head sits on the left
        # stem without closing the open counter.
        pts, holes = LETTERS["U"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "V":
        # Editorial yoga-alphabet V, imported like L from two-way-stretch/V.png.
        # Two equal legs rise from a compact buttocks apex as the strokes of
        # a capital V; outward-turned shod feet are the upper terminals.
        pts, holes = LETTERS["V"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "W":
        # Traced gymnast W, imported like L. The figure hinges forward so the
        # compact head and shoulders make the centre peak. Arms overlap the
        # long inner thighs;
        # concealed grounded knees make uncarved low vertices; naturally
        # shorter calves stay visibly slimmer than the muscular thighs as they
        # taper to forward-facing ankles, then the pointed feet
        # turn modestly outward at the outer terminals.
        pts, holes = LETTERS["W"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)


    elif letter == "X":
        # Editorial yoga-alphabet X, imported like L. A wide forward fold seen
        # from behind: legs spread into an inverted V with both feet on the
        # floor, torso folded down so the head hangs at the centre, and both
        # arms stretched up and out to the upper corners.
        pts, holes = LETTERS["X"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)


    elif letter == "Y":
        # Editorial yoga-alphabet Y, imported like L. A headstand with
        # the torso as the stem and the two legs split wide into a V as
        # the arms of the letter.
        pts, holes = LETTERS["Y"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "Z":
        # Editorial yoga-alphabet Z, imported like L. Kneeling with both
        # arms reaching horizontally at head height as the top bar, the
        # leaning torso and thighs as the diagonal, and the shins and
        # feet flat along the floor as the bottom bar.
        pts, holes = LETTERS["Z"]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, top, bottom = min(xs), min(ys), max(ys)
        cap_height = 788.0
        scale = (cap_height - BAR_GROUND) / (bottom - top)

        def placed(x: float, y: float) -> Point:
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (bottom - y) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in holes:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    return d


def punctuation(name: str) -> Drawer:
    d = Drawer()
    if name == "period":
        # Plain solid disc, matching the dot used by ! and ?.
        d.circle(350, 90, 55)
    elif name == "comma":
        # Plain disc with a descending tail — no hat, nose, or eye.
        d.circle(340, 90, 55)
        d.path([(355, 55), (330, -15), (285, -65)], 36)
    elif name == "exclam":
        # Plain solid disc dot and a straight vertical stroke.
        d.circle(350, 90, 55)
        d.torso([(350, 720), (350, 250)], 80, False)
        d.circle(350, 760, 34)
    elif name == "question":
        d.circle(350, 90, 55)
        d.path([(170, 620), (250, 750), (455, 730), (530, 600), (470, 475), (355, 400), (350, 260)], 72)
        d.circle(170, 620, 28)
    elif name == "hyphen":
        # A plain horizontal dash — no head or limb anatomy needed.
        d.path([(180, 380), (520, 380)], 52, False, joints=False, track=False)
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
            "designer": "Designed on Arena.ai from modern gymnast and yoga references",
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
        # Preserve the fixed release timestamp above in the webfont builds too.
        # TTFont otherwise refreshes head.modified while saving each flavor,
        # making byte-identical source builds produce different WOFF files.
        font = TTFont(ttf_path, recalcTimestamp=False)
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
        xs = [px for contour, _ in drawings[letter].contours for px, _ in contour]
        ys = [py for contour, _ in drawings[letter].contours for _, py in contour]
        gw = max(xs) - min(xs) if xs else 1.0
        gh = max(ys) - min(ys) if ys else 1.0
        sc = min(176.0 / gw, 188.0 / gh, 0.29)
        ox = x + 105 - (min(xs) + gw / 2) * sc
        oy = y + 148 + (min(ys) + gh / 2) * sc
        cards.append(
            f'<rect x="{x + 7}" y="{y + 7}" width="196" height="238" rx="10" '
            f'fill="none" stroke="#d3bea0" stroke-width="2"/>'
        )
        cards.append(
            f'<g transform="translate({ox:.1f},{oy:.1f}) scale({sc:.4f})">'
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

