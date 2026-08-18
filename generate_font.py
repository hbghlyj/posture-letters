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
# The kneeling glyphs (L, J, Z) put a whole leg flat on the floor, and the
# resulting bottom bar is drawn as one foot lying on its side: deepest at the
# heel behind the stem, thinning forward through the arch, and then carried to
# a point at the toe tip by the foot's own outline. Both numbers are depths
# above the bar's single ground line, so the sole stays dead straight.
BAR_HEEL_DEPTH = 74.0
BAR_ARCH_DEPTH = 50.0
# The one ground line those bars sit on, shared so L, J and Z land together.
BAR_GROUND = 72.0
# Where the kneeling base's ankles sit. E's lower prong is one long shin
# running from a grounded knee out to the ankle, so this value is effectively
# the shin's length, and therefore the width of the prong. L shares it.
ANKLE_X = 548.0
# Where the grounded knee sits along that run. The femur and tibia divide the
# prong's horizontal reach between them, so this sets the shin's length: far
# enough forward that shin and thigh come out close to equal, as a real leg
# and the print's seated figure both are.
KNEE_X = 320.0

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
    cap: "BarProfile | None" = None,
) -> list[Point]:
    """Expand a centerline using a width profile instead of a uniform stroke.

    ``cap`` optionally holds the expanded stroke inside a flat bar's own top
    edge, so a limb lying along the baseline cannot swell up through the
    silhouette it is supposed to be drawing.
    """
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
        if cap is not None:
            width = cap.cap((x, y), (dx, dy), width)
        half = width / 2
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left + list(reversed(right))


class BarProfile:
    """The upper edge of a limb lying flat along the baseline.

    The kneeling glyphs (L, J, Z) put a whole lower limb on the floor, so the
    letter's bottom bar has to behave like one drawn stroke rather than like a
    stack of separately swelling body parts. This owns that stroke's depth.
    Everything is measured up from the single ground line the whole bar shares,
    so the sole is straight by construction and only the top edge is shaped:
    deepest at the heel, thinning forward through the arch, and from there run
    out by the foot's own outline to a point at the toe.

    The edge is a monotone cubic through those three depths, so it can only
    ever fall as it runs forward — no bump, no step, no reversal anywhere
    between heel and toe. Its tangent at the heel is held level so the heel
    bulge can turn off it cleanly, and the two spans meet with a shared
    tangent so the handover to the foot leaves no corner.
    """

    def __init__(
        self, ground: float, heel_x: float, arch_x: float, toe_x: float,
        heel_depth: float = 74.0, arch_depth: float = 50.0,
        calf_x: float | None = None,
    ) -> None:
        self.ground = ground
        self.heel_x = heel_x
        self.arch_x = arch_x
        self.toe_x = toe_x
        self.heel_depth = heel_depth
        self.arch_depth = arch_depth
        # +1 when the bar runs right from the heel (L, Z), -1 when left (J).
        self.step = 1.0 if toe_x >= heel_x else -1.0
        # Work in distance-from-heel so both directions share one curve.
        self.arch_s = abs(arch_x - heel_x) or 1.0
        self.toe_s = abs(toe_x - heel_x) or 1.0
        h1 = max(1e-6, self.toe_s - self.arch_s)
        m1 = (0.0 - arch_depth) / h1
        self._arch_span = (h1, m1)
        # Where the calf's muscle belly sits along the run. The glyph knows
        # this from its own leg centreline, so it is passed in rather than
        # assumed to be a fixed fraction of the heel-to-arch distance —
        # bars of different lengths otherwise put the swell in the wrong place.
        self.calf_s = (
            self.arch_s * 0.66 if calf_x is None
            else abs(calf_x - heel_x)
        )

    @property
    def heel_top(self) -> float:
        return self.ground + self.heel_depth

    # The kneeling body sits over the back of its own bar, so the first
    # stretch of the run is buried behind the stem, thigh and knee: in L
    # roughly a fifth of the heel-to-arch distance never shows at all. The
    # depth is therefore held at the full heel value across that stretch, so
    # the deepest part of the band is still at full depth at the moment it
    # emerges into daylight. Spending the taper inside the hidden zone was
    # what made "deepest at the heel" impossible to see.
    HEEL_HOLD = 0.22
    # How the remaining drop is distributed. Above 1 it is front-loaded —
    # steep as it leaves the heel, flattening into the arch — which pulls the
    # band well clear of the calf before the muscle belly arrives. A straight
    # ease put the profile's own depth at its highest right where the calf
    # rises, so the two met and the bar read as uniform.
    HEEL_FALLOFF = 2.2

    def depth(self, x: float) -> float:
        s = min(self.toe_s, max(0.0, (x - self.heel_x) * self.step))
        if s <= self.arch_s:
            plateau = self.arch_s * self.HEEL_HOLD
            if s <= plateau:
                return self.heel_depth
            u = (s - plateau) / max(1e-6, self.arch_s - plateau)
            fall = 1.0 - (1.0 - u) ** self.HEEL_FALLOFF
            return self.heel_depth + (self.arch_depth - self.heel_depth) * fall
        # Arch to toe: a Hermite run that leaves the arch level, so the
        # handover from the span above shows no corner, and lands on the
        # baseline at the toe point.
        h1, m1 = self._arch_span
        u = (s - self.arch_s) / h1
        u2 = u * u
        u3 = u2 * u
        return (
            (2 * u3 - 3 * u2 + 1) * self.arch_depth
            + (-2 * u3 + 3 * u2) * 0.0
            + (u3 - u2) * h1 * m1
        )

    def top(self, x: float) -> float:
        return self.ground + max(0.0, self.depth(x))

    def covers(self, x: float) -> bool:
        return -1e-6 <= (x - self.heel_x) * self.step <= self.toe_s + 1e-6

    def ceiling(self, x: float) -> float | None:
        """The highest a flat-lying stroke may reach at ``x``, if governed.

        Over the bar itself that is the profile. It also reaches a little way
        behind the heel, held at the heel's own depth: the outline back there
        belongs to the heel bulge, so a limb turning into the bar must not
        poke over it and leave a spike where the two meet. Beyond that lead-in
        the stroke is climbing away out of the bar and is left alone.
        """
        travelled = (x - self.heel_x) * self.step
        if travelled < -self.heel_depth:
            return None
        if travelled > self.toe_s:
            return None
        if travelled < 0.0:
            return self.heel_top
        return self.top(x)

    def edge(self, samples: int = 96) -> list[Point]:
        """The top edge sampled from the heel forward to the toe point."""
        pts = [
            (
                self.heel_x + self.step * self.toe_s * i / samples,
                self.top(self.heel_x + self.step * self.toe_s * i / samples),
            )
            for i in range(samples)
        ]
        pts.append((self.toe_x, self.ground))
        return pts

    def heel_outline(
        self, rise: float, bulge: float, samples: int = 26,
    ) -> list[Point]:
        """The rear end of the bar, run as a heel rather than a squared slab.

        Leaving the ankle the outline swells backward past the line of the
        stem into one full rounded bulge, reaches its furthest point at
        mid-height between the ankle and the floor — exactly where a heel is
        widest — and then curves back in to meet the ground.

        It is traced as part of the band's own contour and it starts up inside
        the leg, on the limb's own back edge above the ankle, so the swell
        grows out of the leg's outline. That is what stops it reading as a
        separate blob hung off the back of the stem: there is no seam where
        one shape is stuck onto another, just the band's rear end bulging.

        Both ends of the curve are flat-tangent — at the leg, so it continues
        the back edge rather than stepping off it, and at the widest point,
        so the two halves meet without a crease.

        The bulge is deliberately **small and local**: it is the calcaneus,
        not a wedge under the whole ankle. It comes and goes within the height
        of the heel itself, and by the time the outline reaches the floor it
        has drawn most of the way back in, so the projection stays confined to
        the heel area instead of running forward under the arch or up the leg.
        """
        # Start ``rise`` above the ankle and finish on the floor. That anchor
        # is set deliberately *inside* the leg rather than on its edge: the
        # curve then emerges from within the limb's own ink, so however the
        # leg tapers there is no seam or spike where the two meet.
        anchor_y = self.heel_top + rise
        span = anchor_y - self.ground
        # The widest point falls at mid-height between the ankle and the
        # floor, which is exactly where a heel carries its mass.
        peak_at = (anchor_y - (self.heel_top + self.ground) * 0.5) / span
        # Where the outline sits at each end, as a fraction of the full swell.
        at_leg = min(0.5, rise * 0.5 / bulge)
        # Pulled well in at the floor so the bone rolls onto the sole and the
        # swell stays a compact heel rather than a broad skirt reaching
        # forward along the bar.
        at_floor = 0.30
        pts: list[Point] = []
        for i in range(samples + 1):
            t = i / samples
            if t <= peak_at:
                u = t / peak_at
                swell = at_leg + (1.0 - at_leg) * math.sin(math.pi * 0.5 * u) ** 2
            else:
                u = (t - peak_at) / (1.0 - peak_at)
                swell = at_floor + (1.0 - at_floor) * math.cos(math.pi * 0.5 * u) ** 2
            pts.append((
                self.heel_x - self.step * bulge * swell,
                anchor_y - span * t,
            ))
        return pts

    # How far a flat-lying leg stroke may ride proud of the band's top edge.
    # This is deliberately not zero: the calf is a real muscle belly and the
    # print shows it, so the bar's upper outline is meant to carry that one
    # soft swell. Clamping the strokes flat onto the profile erased it and
    # left the whole run reading as a drawn stroke rather than a leg.
    SWELL_ALLOWANCE = 12.0

    def headroom(self, x: float) -> float:
        """How far a leg stroke may ride proud of the edge at ``x``.

        The allowance is not constant along the bar. It is full over the calf,
        where the muscle belly is, and eases to nothing before the ankle: past
        there the strokes are ending, and any headroom lets a squared-off
        stroke tip poke through the profile as a step in the outline. Fading
        it out means the calf keeps its swell while the run into the foot
        stays governed entirely by the band.
        """
        travelled = (x - self.heel_x) * self.step
        # The allowance is a window centred on the calf belly, not a blanket
        # over the whole rear half of the bar. It ramps in behind the muscle,
        # is full across it, and eases out before the ankle.
        #
        # Both edges matter. Without the fade-out a squared-off stroke tip
        # near the foot pokes through as a step; without the fade-in the knee
        # joint mass and the breeches cuff — which sit just behind the calf —
        # keep their full height while the band tapers past them, and the
        # outline steps where those shapes end.
        #
        # The window is placed against the calf's *own* position rather than
        # a fixed fraction of the run. The leg strokes are laid out in glyph
        # coordinates, so on a bar whose heel-to-arch distance differs from
        # L's the fractional window drifts off the muscle: on Z it used to
        # open only after the band had already tapered away, pinching the bar
        # to a waist and then inflating it again past the muscle. Anchoring
        # the window to ``calf_s`` keeps the swell over the belly on every
        # glyph, so the bar thins once, evenly, from heel to toe.
        centre = self.calf_s
        rise = self.arch_s * 0.30
        fall = self.arch_s * 0.20
        if travelled <= centre - rise or travelled >= centre + fall:
            return 0.0
        if travelled < centre:
            u = (travelled - (centre - rise)) / rise
        else:
            u = 1.0 - (travelled - centre) / fall
        ease = u * u * (3.0 - 2.0 * u)
        return self.SWELL_ALLOWANCE * ease

    def cap(self, point: Point, tangent: Point, width: float) -> float:
        """Keep a flat-lying stroke close to the bar's top edge.

        Thigh and shin are tapered strokes that swell about their centrelines
        — the breeches at the top of the thigh, the calf below the knee — so a
        limb laid along the floor pushes those swells up through the bar. Left
        alone they roll the outline up and down and put a step where the two
        strokes meet; clamped hard onto the profile they vanish and the leg
        stops reading as a leg.

        So the profile sets a ceiling with headroom rather than a hard lid: a
        stroke may stand up to ``SWELL_ALLOWANCE`` above the band's own edge
        over the calf, which is enough for the muscle belly to show as one
        soft rise but not enough for the breeches or a stroke end to reappear
        as a lump. The sole is unaffected either way — it is the band's
        straight underside, not these strokes.

        The cap is weighted by how level the stroke is running, not by an
        arbitrary cut-off: a horizontal stroke is fully governed, while the
        stroke climbing away into the stem is left completely alone. Nothing
        is trimmed with a step.
        """
        x, y = point
        ceiling = self.ceiling(x)
        if ceiling is None:
            return width
        tx, ty = tangent
        length = math.hypot(tx, ty)
        if length < 1e-9:
            return width
        level = abs(tx) / length
        if level <= 0.55:
            return width
        blend = min(1.0, (level - 0.55) / 0.30)
        blend = blend * blend * (3.0 - 2.0 * blend)
        allowed = max(8.0, 2.0 * (ceiling + self.headroom(x) - y))
        return width + (min(width, allowed) - width) * blend


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
        hole: bool = False, cap: "BarProfile | None" = None,
    ) -> None:
        c, s = math.cos(angle), math.sin(angle)
        pts = []
        for i in range(20):
            t = 2 * math.pi * i / 20
            px, py = rx * math.cos(t), ry * math.sin(t)
            pts.append((x + px * c - py * s, y + px * s + py * c))
        if cap is not None:
            # Joint masses on a limb lying along the floor are part of the
            # bar's silhouette, so they answer to its top edge like the
            # strokes do. Without this a knee ball or breeches cuff keeps its
            # full height while the band tapers past it, and the outline
            # steps where the ellipse ends.
            pts = [
                (px, min(py, cap.top(px) + cap.headroom(px)))
                if cap.ceiling(px) is not None else (px, py)
                for px, py in pts
            ]
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

    def flat_bar(self, profile: BarProfile, anchor_rise: float) -> None:
        """Fill the bar of a leg lying along the ground, heel to toe point.

        The kneeling glyphs put a whole lower limb on the floor, and the
        letter's bottom bar is that limb's silhouette, so the bar is drawn
        here in one piece rather than left to emerge from separately swelling
        body parts. Its underside is the single ground line, giving a straight
        sole; its top edge is the profile — deepest at the heel, thinning
        forward through the arch, then run out to a point at the toe — so the
        whole stroke reads as one flat, evenly tapering band.

        The rear end is the heel. Leaving the ankle the outline swells
        backward past the line of the stem into a full rounded bulge, widest
        at mid-height between ankle and floor, and curves back in to meet the
        ground. It is generated as part of this contour, so it belongs to the
        band rather than reading as a separate blob hung off the leg.

        ``anchor_rise`` is how far up the limb the heel curve starts, above
        the bar's own top edge. It is set per glyph because the limb above the
        heel differs: L and J turn up into a tall vertical stem, so the curve
        can start well inside it, while Z's leg runs away on a shallow
        diagonal and the curve has to start close to the bar to stay covered.
        """
        ground = profile.ground
        # How far the outline swells back past the line of the stem. Scaled
        # off the bar's own depth so the heel stays in proportion to it, and
        # It is still a compact calcaneus rather than a mass carrying the
        # whole ankle, but it has to survive the specimen sheet: there a glyph
        # is rastered at roughly five font units per pixel, so a bulge that
        # measured a plausible-looking 16 units came out barely three pixels
        # proud of the ankle and simply vanished.
        #
        # It cannot be sized off legibility alone, though. The swell starts on
        # the limb's own back edge, so once it is wider than the limb the
        # curve begins *outside* the leg and has to travel back in to reach
        # the floor. On J that put the widest point at x≈524 against a back
        # edge of x≈499 — a bulge two dozen units proud of the shin, with a
        # concave notch under it where the outline cut back, reading as a
        # block bolted onto the leg rather than the leg's own heel. Held to
        # the limb's width the swell still shows as a heel but stays part of
        # the stroke, which is what the print shows.
        bulge = profile.heel_depth * 0.30
        heel = profile.heel_outline(anchor_rise, bulge)
        edge = profile.edge()
        # One closed loop, traced the whole way round: out of the leg and down
        # around the heel to the floor, forward along the sole to the toe
        # point, then back along the top edge and in to close inside the limb.
        # The bulge is a stretch of this contour rather than a shape stuck on
        # the end of it, so it reads as the band's own rear end.
        self.polygon(
            list(heel)
            + [(profile.toe_x, ground)]
            + list(reversed(edge))
        )

    def kneeling_foot(
        self, profile: BarProfile, ankle_x: float, width: float,
    ) -> None:
        """The foot at the front of a limb lying flat along the ground.

        These kneeling legs put the whole lower limb on the floor, so the
        letter's bottom bar has to read as one straight stroke. The foot is
        therefore set flush with the shin rather than bent away from it: its
        upper surface continues the bar's own profile and its sole rests on
        the same ground line, so nothing steps above or below the bar.

        The foot shape is carved out of the bottom bar as an anatomically
        correct silhouette: rounded heel bulge rising from the ground, arch
        curving upward, ball of foot, and toes tapering down to the ground.
        The foot interior is cut away (white), leaving only the outline
        visible against the bar's filled body.
        """
        k = width / 52.0
        ground = profile.ground
        step = profile.step
        run = (profile.toe_x - ankle_x) * step

        def at(fraction: float) -> float:
            return ankle_x + step * run * fraction

        # Carve out the foot shape as an anatomically correct silhouette.
        # The foot runs from the ankle (0%) to the toe (100%).
        
        # Build the foot outline as a closed polygon that will be cut out
        # (reverse winding = hole). The outline follows anatomical features:
        # - Heel: rounded bulge rising from ground at 0-15%
        # - Arch: curves upward from ground at 15-45%
        # - Ball: slight swelling at 45-65%
        # - Toes: taper down to ground at 65-100%
        
        foot_outline = []
        
        # Start at ground level just behind the heel
        heel_start_x = at(0.0)
        foot_outline.append((heel_start_x, ground))
        
        # Heel bulge: rises up in a rounded curve
        # The heel is prominent and rounded, rising to about 60% of foot height
        for i in range(8):
            frac = 0.0 + 0.15 * i / 7.0  # 0% to 15%
            x = at(frac)
            # Heel rises in a smooth curve (sine-like)
            rise_frac = i / 7.0
            heel_height = math.sin(rise_frac * math.pi * 0.5) * 0.60
            y = ground + (profile.top(x) - ground) * heel_height
            foot_outline.append((x, y))
        
        # Arch: curves upward, creating a concave hollow
        # The arch rises to about 85% of foot height at its peak
        for i in range(10):
            frac = 0.15 + 0.30 * i / 9.0  # 15% to 45%
            x = at(frac)
            # Arch rises then falls slightly (bell curve)
            arch_frac = i / 9.0
            arch_height = 0.60 + 0.25 * math.sin(arch_frac * math.pi)
            y = ground + (profile.top(x) - ground) * arch_height
            foot_outline.append((x, y))
        
        # Ball of foot: slight swelling
        for i in range(6):
            frac = 0.45 + 0.20 * i / 5.0  # 45% to 65%
            x = at(frac)
            # Ball maintains height with slight rise
            ball_frac = i / 5.0
            ball_height = 0.85 + 0.05 * math.sin(ball_frac * math.pi)
            y = ground + (profile.top(x) - ground) * ball_height
            foot_outline.append((x, y))
        
        # Toes: taper down to ground
        for i in range(8):
            frac = 0.65 + 0.35 * i / 7.0  # 65% to 100%
            x = at(frac)
            # Toes slope down to ground
            toe_frac = i / 7.0
            toe_height = 0.90 * (1.0 - toe_frac)
            y = ground + (profile.top(x) - ground) * toe_height
            foot_outline.append((x, y))
        
        # Close the polygon back along the ground
        foot_outline.append((at(1.0), ground))
        foot_outline.append((at(0.0), ground))
        
        # Cut out the foot shape (reverse winding creates a hole)
        if len(foot_outline) >= 3:
            self.polygon(foot_outline, hole=True)

    def cut_path(self, pts: list[Point], width: float = 6, smooth: bool = True) -> None:
        """Punch a fine engraved line through a filled body contour."""
        poly = ribbon(pts, width, smooth)
        if poly:
            self.polygon(poly, hole=True)

    def tapered_path(
        self, pts: list[Point], widths: list[float], smooth: bool = True,
        cap: "BarProfile | None" = None,
    ) -> None:
        """Draw a continuous body part with a controlled anatomical profile."""
        poly = tapered_ribbon(pts, widths, smooth, cap=cap)
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
        bar: "BarProfile | None" = None,
    ) -> None:
        """Draw short breeches, a knee cuff, muscular calf, ankle, and shoe.

        Every historical foot-ending limb uses this construction. The trousers
        stay full through the thigh and stop just below the indexed knee; the
        stockinged lower leg then swells at the gastrocnemius before narrowing
        decisively into the ankle. The centerline and shoe endpoint remain the
        source pose's own, so anatomy does not regularize the letter geometry.

        ``bar`` marks the limb as lying flat along the baseline. The kneeling
        poses draw their bottom bar as one band, so along that run the band's
        profile owns the silhouette and the leg's own swells are held inside
        it — otherwise the calf and the breeches push up through the stroke
        that is supposed to read as flat.
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
            True, cap=bar,
        )
        self.tapered_path(
            lower_profile,
            [width * 0.78, width * 0.90, width * 1.22, width * 0.82, width * 0.50],
            True, cap=bar,
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
                math.atan2(by, bx), cap=bar,
            )

        next_point = lower_profile[1]
        dx, dy = next_point[0] - knee[0], next_point[1] - knee[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        cuff_angle = math.atan2(dy, dx) + math.pi / 2
        self.ellipse(
            knee[0], knee[1], breeches * 0.43, max(6.0, breeches * 0.105),
            cuff_angle, cap=bar,
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


def kneeling_base(stem_x: float, hip_y: float) -> Drawer:
    """E's lower prong: thighs to grounded knees, shins flat, heel serif.

    Factored out so E and L build their base from one definition rather than
    two parallel copies. It is drawn in E's own coordinates, keyed off the
    stem, and returned as a standalone Drawer so a caller can transform the
    whole component — L flips it — before merging it into the glyph.
    """
    d = Drawer()
    # The knee is carried forward along the floor rather than tucked under the
    # hip. With it directly beneath the stem the prong was one enormous shin —
    # 370-386 units against a 188 thigh, a ratio near 2.0, which the audit
    # flagged as the worst limb in the font and which the print does not show:
    # the source figure sits with the legs extended, shin and thigh roughly
    # comparable. This is the same fault L was rebuilt for.
    #
    # Advancing the knee splits the horizontal run between femur and tibia
    # instead of making the tibia carry all of it, so the proportions come
    # back into range while the prong keeps its full reach and the letter its
    # width. It also matches the grounded-knee construction L, J and Z use.
    # The thigh keeps its original vertical drop from the hip to the floor,
    # because that drop is the letter's own left edge: run diagonally to a
    # forward knee it peels the stem away below the middle prong and E stops
    # having a straight spine or a bottom-left corner. So the leg is given a
    # third point — hip, floor, grounded knee, raised ankle — exactly the
    # four-point form L, J and Z use with ``knee_index=2``.
    ankles = []
    for spread, width, breeches in ((-16, 54, 62), (16, 42, 50)):
        ankle = (ANKLE_X + spread, 104)
        ankles.append(ankle)
        d.leg(
            [
                (stem_x + spread * 0.4, hip_y),
                (stem_x - 2 + spread * 0.5, 118),
                (KNEE_X + spread * 0.5, 108),
                ankle,
            ],
            width, knee_index=2, breeches_width=breeches, shoe_scale=0.0,
        )
    # Heel serif: the ankles flex up at the back of the base stroke and
    # taper to a sharp point, the bottom-right terminal of the letter. It is
    # placed relative to the outermost ankle so it travels with the foot
    # rather than sitting at a fixed coordinate.
    toe = max(x for x, _ in ankles)
    d.circle(toe - 12, 114, 26, n=24)
    d.tapered_path(
        [(toe - 12, 108), (toe + 4, 150), (toe + 16, 194)], [48, 38, 20], True,
    )
    d.cut_path([(toe - 30, 128), (toe + 2, 136)], 3.4, False)
    return d


def _column_spans(
    contours: list[tuple[list[Point], bool]], x: float,
) -> list[tuple[float, float]]:
    """Vertical runs of ink at ``x`` under the nonzero fill rule.

    The same scanline rule the renderer and the proof tools use, so a shape
    fitted to a stroke's edge with this lands where the glyph actually has
    ink rather than where its control points happen to sit.
    """
    crossings: list[tuple[float, int]] = []
    for polygon, _ in contours:
        count = len(polygon)
        for index in range(count):
            (x1, y1), (x2, y2) = polygon[index], polygon[(index + 1) % count]
            if x1 == x2:
                continue
            if (x1 <= x < x2) or (x2 <= x < x1):
                t = (x - x1) / (x2 - x1)
                crossings.append((y1 + (y2 - y1) * t, 1 if x2 > x1 else -1))
    crossings.sort()
    spans: list[tuple[float, float]] = []
    winding, start = 0, 0.0
    for y, direction in crossings:
        previous = winding
        winding += direction
        if previous == 0 and winding != 0:
            start = y
        elif previous != 0 and winding == 0:
            spans.append((start, y))
    return spans


def merge_transformed(
    target: Drawer, source: Drawer,
    flip: bool = False, dx: float = 0.0, dy: float = 0.0,
    floor: float | None = None,
    floor_from: float | None = None,
) -> None:
    """Copy a component into a glyph, optionally mirrored about its own axis.

    ``flip`` turns the component upside down about its own vertical centre, so
    it keeps its position rather than swinging away. Contours are re-emitted
    through ``polygon`` so winding is recomputed for the new orientation —
    mirroring reverses signed area, and a contour left as-is would punch a
    hole where it should fill. Tracked anatomy follows the same transform so
    the audit still measures the limb where it now sits.

    ``floor`` clips the transformed component to a ground line. Seating an
    inverted limb by its working edge can leave another part of it hanging
    past the baseline — the flip turns a thigh that ran downward into one
    that runs down from the far side — and a glyph may not dip below the
    line it stands on. Vertices below the floor are pulled onto it, so the
    overhang is cut off flush instead of the whole component being lifted
    and the working edge floating clear of the ground.

    ``floor_from`` raises that clip to the component's own underside ahead of
    the given x. Clipping at the baseline alone keeps the glyph inside its
    box but still lets the inverted thigh hang *below the bar* just past the
    stem, which reads as a spur dropping out of the knee. Past ``floor_from``
    the clip follows the bar's sole instead of the baseline, so the underside
    of the stroke stays a single clean line and the overhang is confined to
    the column the trunk covers.
    """
    ys = [y for contour, _ in source.contours for _, y in contour]
    if not ys:
        return
    axis = min(ys) + max(ys)

    def move(point: Point) -> Point:
        x, y = point
        return (x + dx, (axis - y if flip else y) + dy)

    # The bar's underside just ahead of the trunk, which is the line the
    # stroke should keep. It is sampled from the shin's own contour over a
    # short window clear of the stem: the spur being trimmed lies behind that
    # window, so it cannot define the line it is measured against, and the
    # heel serif at the far end — which legitimately drops to the floor — is
    # outside it too.
    sole = None
    if floor_from is not None:
        window = [
            (axis - y if flip else y) + dy
            for contour, _ in source.contours for x, y in contour
            if floor_from + 60 < (x + dx) < floor_from + 200
        ]
        sole = min(window) if window else None

    def clip(point: Point) -> Point:
        x, y = point
        limit = floor
        if sole is not None and x > floor_from:
            limit = sole if limit is None else max(limit, sole)
        return (x, y) if limit is None else (x, max(y, limit))

    for contour, hole in source.contours:
        moved = [clip(move(p)) for p in contour]
        # A contour lying wholly under the floor collapses onto the line and
        # would emit a degenerate slab; drop it rather than draw a sliver.
        if floor is not None and max(y for _, y in moved) <= floor + 1e-6:
            continue
        target.polygon(moved, hole)
    for entry in source.anatomy:
        moved = dict(entry)
        if "points" in moved:
            moved["points"] = [move(p) for p in moved["points"]]  # type: ignore[arg-type]
        if "center" in moved:
            moved["center"] = move(moved["center"])  # type: ignore[arg-type]
        target.anatomy.append(moved)


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
        # knees the shins lie flat along the ground running right, finishing
        # in the upward heel serif. L reuses this same component.
        merge_transformed(d, kneeling_base(stem_x, hip_y))
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
        # Thighs drop to bent knees that turn forward onto the ground, and
        # from there the shins lie flat along the floor running left as the
        # hook. Previously the shins swung diagonally up behind the body,
        # which put the knees in the air and left the ankles nowhere to bend.
        # Mirror of L's bottom bar, running left instead of right: one band on
        # a single ground line, deepest at the heel under the stem, thinning
        # forward through the arch, and taken out to a point at the toe.
        #
        # The heel is registered on the back of the widest leg rather than on
        # the stem centre. J's rear thigh is set out at spread +20 and carries
        # full breeches, so its outer edge stands at x≈499; a heel anchored
        # further forward bulged only to x≈464 and sat *inside* that edge,
        # reading as a notch under the leg instead of a heel behind it. Put
        # the anchor on the leg's own back edge and the bulge clears it.
        bar = BarProfile(
            ground=BAR_GROUND, heel_x=478, arch_x=144, toe_x=18,
            heel_depth=BAR_HEEL_DEPTH, arch_depth=BAR_ARCH_DEPTH,
            calf_x=241,
        )
        for spread, width, breeches in ((-18, 52, 60), (20, 44, 52)):
            d.leg(
                [
                    (stem_x + spread * 0.5, hip[1]),
                    (stem_x + spread, 126),
                    (300 - spread * 0.30, 112),
                    (144 - spread * 0.20, 112),
                ],
                width, knee_index=2, breeches_width=breeches,
                shoe_scale=0.0, bar=bar,
            )
        # The heel curve starts further up the shin than it did. Anchored low
        # it left the leg at x≈489 while the leg's own back edge there stands
        # at ≈496, so the swell began seven units *inside* the limb: climbing
        # the flank the outline ran out to the heel's peak, pulled back into a
        # waist where the band ended, then swelled out again as the leg
        # resumed — a double reversal, where L's flank is strictly monotone
        # from the stem to the floor. Starting the curve higher lets it leave
        # along the limb's own edge instead of stepping off it, which takes
        # the mean tangent break from 0.256 to 0.232 and shallows the waist.
        # It is not carried further than this: the same move keeps flattening
        # the flank, but it does so by eating the calcaneus, and past here the
        # heel stops reading as a heel at specimen scale.
        d.flat_bar(bar, anchor_rise=54.0)
        d.kneeling_foot(bar, 144, 52)

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
        # The hip sits where the flipped base's thigh tops now are, so the
        # trunk lands on the component instead of running past it to the
        # floor. E's prong is drawn hip-down, and inverting it puts those
        # thigh tops at the upper edge of the base rather than the lower.
        # The hip sits down on the bar now that the base is seated on the
        # floor, so the trunk meets the stroke instead of stopping short of
        # it and leaving the letter in two disconnected pieces. It follows the
        # bar down: with the base resting on the baseline rather than hanging
        # off its heel serif, a hip still set for the old height would leave
        # the trunk ending in mid-air above the stroke.
        hip = (stem_x, 134)
        d.torso([hip, (stem_x, 419), (stem_x, 642)], 84, False)
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
        # Bottom bar: E's lower prong, taken whole and turned upside down.
        # The two letters now share one base component (``kneeling_base``)
        # so their kneeling anatomy is defined in a single place.
        #
        # The flip is the point of the exercise and it is what the shape is
        # built around, but it does invert the leg: E's prong rises into its
        # heel serif at the right-hand end, so inverted that terminal drops
        # instead, and the calf and breeches swap sides top to bottom.
        #
        # Seating it matters as much as flipping it. Registering the whole
        # component by its lowest ink left the shin bar floating at
        # mid-height, because after the flip the lowest ink is not the bar —
        # it is E's thigh, which ran hip-downward and now runs down from the
        # far side of the base. The bar is therefore registered on its own
        # underside, measured over the run where the shin actually lies, so
        # the stroke lands flat on the shared ground line the way every other
        # glyph's base does. That drops the thigh past the baseline, and
        # ``floor`` cuts it off flush there: it occupies the same column as
        # the stem, so the trunk covers the join and nothing dips below the
        # line the letter stands on.
        base = kneeling_base(stem_x, hip[1])
        # Mirror about the component's own global axis — the same one
        # ``merge_transformed`` uses. Taking each contour about its own centre
        # instead leaves every piece where it started and measures nothing.
        base_ys = [y for contour, _ in base.contours for _, y in contour]
        base_axis = min(base_ys) + max(base_ys)
        # Register on the shin itself. ``x > 300`` was meant to name the bar,
        # but after the flip the lowest ink past that line is not the shin —
        # it is the heel serif, which E draws rising off the floor and which
        # inverting turns into the component's deepest point. Seating the
        # component on that tip parked the whole horizontal stroke 57 units
        # in the air, leaving only the seat and the patched corner touching
        # the ground. Naming the shin run explicitly puts the stroke that is
        # supposed to be the bar on the baseline, the way J and Z do.
        bar_low = min(
            base_axis - y
            for contour, _ in base.contours for x, y in contour
            if 320 < x < 520
        )
        # Ahead of the trunk the clip follows the bar's own sole, so the
        # inverted thigh cannot hang below the stroke and read as a spur
        # dropping out of the knee. Behind that line it still clips to the
        # baseline, where the trunk covers the cut.
        merge_transformed(
            d, base, flip=True, dy=BAR_GROUND - bar_low, floor=BAR_GROUND,
            floor_from=stem_x + 42,
        )
        # Level the sole, and finish the stroke with a foot.
        #
        # Seating the component puts the shin's lowest point on the baseline,
        # but the shin does not lie level: E draws the leg tapering from a
        # deep knee to a shallow ankle, and the flip turns that taper upside
        # down, so the underside sags away from the ground in a shallow arch
        # — about twenty units at its worst, a quarter of the stroke's own
        # depth — and the letter ends up balanced on the two points where the
        # arch happens to touch. No offset can fix that, because the edge is
        # sloped rather than displaced.
        #
        # Filling that crescent column by column does flatten the sole, but
        # on its own it flattens the *whole* stroke: run out to the end of the
        # component it swallows the ankle and buries the terminal, and L ends
        # in a blunt slab where the other kneeling glyphs end in a foot. So
        # the fill is stopped at the ankle, and the foot is drawn past it the
        # way J and Z draw theirs — from a shared ``BarProfile``, whose top
        # edge thins forward from the arch and runs out to a point at the toe.
        bar = BarProfile(
            ground=BAR_GROUND, heel_x=246.0, arch_x=ANKLE_X, toe_x=665.0,
            heel_depth=BAR_HEEL_DEPTH, arch_depth=BAR_ARCH_DEPTH,
        )
        sole = []
        for index in range(49):
            x = 246.0 + (ANKLE_X - 246.0) * index / 48.0
            spans = [
                span for span in _column_spans(d.contours, x)
                if span[0] < 260.0
            ]
            if spans:
                sole.append((x, min(lo for lo, _ in spans)))
        if sole:
            d.polygon(sole + [(x, BAR_GROUND) for x, _ in reversed(sole)])
        # The foot itself: ankle to toe point, sole on the same ground line so
        # it continues the bar rather than stepping out of it. The heel end is
        # already the shin behind it, so only the forward span is filled here.
        toe_edge = [
            point for point in bar.edge(64) if point[0] >= ANKLE_X - 1.0
        ]
        if toe_edge:
            d.polygon(
                toe_edge + [(x, BAR_GROUND) for x, _ in reversed(toe_edge)]
            )
        d.kneeling_foot(bar, ANKLE_X, 52)
        # The corner fillet that used to sit here is gone with the cause it
        # patched. It spanned the baseline up to y=129 because the bar's sole
        # settled that high, so the trunk's foot stood clear underneath the
        # stroke and the gap between them read as a block hanging off the
        # knee. Now that the bar is registered on the shin it rests on the
        # baseline itself, the trunk meets it along their shared edge, and
        # there is no re-entrant angle left to fill: keeping the polygon would
        # only re-add a wedge of ink under a stroke that is already flat on
        # the ground.

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
        # The knees rest ON the baseline, so their control points sit a joint
        # radius above it rather than on it. Authored at y=0 the knee mass and
        # its cuff straddled the line and bulged 44 units underneath as two
        # rounded lobes — the only ink in the alphabet below the baseline,
        # and not something the print shows: there all four strokes finish
        # together on one line. Lifting the point puts the bottom of the joint
        # on y=0 instead of its centre.
        d.leg(
            [(315, 430), (150, 44), (74, 606)], 62, knee_index=1,
            shoe_direction=(-0.92, 0.40),
        )
        d.leg(
            [(385, 430), (550, 44), (626, 606)], 62, knee_index=1,
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
        # The same bottom bar L uses: one band on a single ground line, its
        # heel at the back under the kneeling corner, thinning forward through
        # the arch and carried to a point at the toe. The top surface of the
        # foot is therefore continuous with the shin and the stroke is flat.
        #
        # The heel is registered at the kneeling corner itself, not forward of
        # it. Anchored at 316 the band began seventy units ahead of where the
        # torso actually lands, so between the corner and the band's start the
        # bar was carried only by the tapering leg strokes: it necked to 35
        # units against the band's 74 and its sole rode up to y=120 instead of
        # resting on the floor, which reads as a thin, notched section beside
        # the knee. Starting the band at the corner fills that run.
        #
        # 266 was still too far forward. The band's rear end is a vertical
        # face, so wherever it starts the silhouette drops to the floor in one
        # step; put that face out at 266 and it landed in open space beyond
        # the knee, cutting a cliff twenty units deep across the underside
        # just where the limb should be flowing into the bar. Tucked back
        # under the corner the face is buried inside the thigh and the leg
        # runs down into the band continuously, which is what the print shows.
        bar = BarProfile(
            ground=BAR_GROUND, heel_x=200, arch_x=584, toe_x=710,
            heel_depth=BAR_HEEL_DEPTH, arch_depth=BAR_ARCH_DEPTH,
        )
        for spread, width, breeches in ((-20, 56, 66), (18, 46, 54)):
            d.leg(
                [
                    # Both thighs start from inside the torso's own end cap
                    # rather than from a point offset along the spread. Offset
                    # starts put the two strokes 19 units apart at the corner,
                    # and because a tapered stroke is at its thinnest where it
                    # begins, neither reached the other: a hairline of white
                    # ran between them and on into the bar, which read as a
                    # seam splitting the diagonal from the base. Starting both
                    # at the knee buries the join under the cap, where the
                    # nonzero fill merges the strokes into one mass.
                    (knee[0], knee[1]),
                    (330 + spread, 118),
                    (430 + spread * 0.30, 112),
                    (584 + spread * 0.20, 112),
                ],
                width, knee_index=2, breeches_width=breeches,
                shoe_scale=0.0, bar=bar,
            )
        d.flat_bar(bar, anchor_rise=0.0)
        # Carry the limb's underside from the kneeling corner into the bar.
        #
        # Thigh and shin are separate tapered strokes that swell about their
        # own centrelines, so where they meet their two undersides do not line
        # up: the thigh's runs down to about y=98 and the shin's picks up
        # again at about y=114, leaving a step in the silhouette right at the
        # joint. On the other kneeling glyphs the band hides that step, but
        # here it cannot — the bar is registered at x=266 and its top edge
        # sits at y=146, well *above* both, so the mismatch stays exposed
        # underneath the band and the knee reads as two components pushed
        # together at the wrong angle rather than one limb bending.
        #
        # Filling between the leg's own underside and the band's top edge
        # closes it. The lower edge is sampled off whatever ink is actually
        # there, column by column, so it follows the thigh down, across the
        # joint and onto the shin without inventing an outline of its own;
        # the upper edge is the band, which the strokes already reach. The
        # run stops where the band takes over the silhouette, so the open
        # counter above the bar is untouched.
        joint = []
        for index in range(65):
            x = knee[0] + (360.0 - knee[0]) * index / 64.0
            spans = [
                span for span in _column_spans(d.contours, x)
                if span[0] < bar.top(x) + 1.0
            ]
            if not spans:
                continue
            joint.append((x, min(span[0] for span in spans)))
        if joint:
            d.polygon(
                [(x, min(bar.top(x), knee[1] + (x - knee[0]) * 1.4483 + 6))
                 for x, _ in joint]
                + joint[::-1]
            )
        # Give the knee a joint mass, the way L's corner has one.
        #
        # L is the smooth one of the three kneeling glyphs and the reason is
        # structural: its trunk ends in a round cap that sits *in* the corner,
        # so a single arc owns the whole turn and the rear flank falls in one
        # decelerating curve — x=219 at y=74 easing to 166 by y=134 — with a
        # worst tangent break of 1.5 and a mean of 0.11.
        #
        # Z had two arcs competing for that corner instead. Climbing the rear
        # flank the outline followed the heel out to x≈176, then the trunk's
        # cap took over at y=122 and the edge jumped ten units inward in a
        # single step: a break of 4.5, three times L's, and the one place the
        # joint read as two parts pushed together rather than a limb bending.
        # Neither moving the heel anchor nor resizing the bulge helps, because
        # the step is where the two arcs hand over, not how big either is.
        #
        # A joint mass spanning the handover gives the corner the single
        # dominant radius L gets from its cap: it covers the last of the heel
        # and the first of the cap, so the flank crosses between them on the
        # mass's own arc. Sized and placed by sweeping both against the
        # tangent metric, this is the best that keeps the sole on the
        # baseline — the break falls from 4.5 to 2.0 and the mean from 0.41
        # to 0.25, against L's 1.5 and 0.11.
        d.ellipse(knee[0] + 20.0, knee[1] - 36.0, 60.0, 60.0, 0.0)
        # Round the back of the knee, where the torso's cap meets the heel.
        #
        # The trunk ends in a round cap of its own half-width, and its lowest
        # point sits at y=122 — above the band, and behind the heel curve that
        # drops from the band's top edge to the floor. Where the two outlines
        # cross, the silhouette turns from level to five units per column in a
        # single step, so the back of the knee showed a shelf: the diagonal
        # looked cut off square against the bar rather than folded onto it.
        #
        # This fills the pocket between the cap's trailing underside and the
        # heel, so the outline runs from the cap into the heel curve as one
        # sweep. Both bounds are outlines already drawn here, and the fill is
        # confined to the columns where the cap is genuinely the silhouette,
        # so it cannot reach the sole or the counter.
        # The cap's underside and the heel's descent cross at a very shallow
        # angle — around x=185 they are barely two units apart — so instead of
        # meeting at a rounded turn they clip each other and leave a concave
        # nick in the outline. A circular arc struck between the two, tangent
        # to the cap where it is still level and running down to the heel
        # where that is already falling, replaces the nick with the fillet a
        # real joint would show. It is bounded by ink on both sides, so it
        # only fills the hollow between them.
        fold = []
        for index in range(65):
            x = knee[0] + (bar.heel_x - knee[0]) * index / 64.0
            reach = 46.0 ** 2 - (x - knee[0]) ** 2
            if reach <= 0.0:
                continue
            cap_low = knee[1] - math.sqrt(reach)
            spans = [
                span for span in _column_spans(d.contours, x)
                if span[0] < bar.top(x) + 1.0
            ]
            if not spans:
                continue
            below = min(span[0] for span in spans)
            # Sweep a fillet of the trunk's own quarter-width through the
            # turn: level under the cap, easing into the heel's slope.
            t = (x - knee[0]) / max(1.0, bar.heel_x - knee[0])
            blend = cap_low + (below - cap_low) * (t * t * (3.0 - 2.0 * t))
            fold.append((x, min(below, blend), max(below, blend)))
        if len(fold) > 1:
            d.polygon(
                [(x, low) for x, low, _ in fold]
                + [(x, high) for x, _, high in reversed(fold)]
            )
        # Weld the limb to the band where the two graze.
        #
        # Leaving the corner the band's top edge runs level at y=146 while the
        # thigh above it falls away toward the ankle, and for a short stretch
        # past the knee the two pass within a couple of units of each other
        # before the thigh lifts clear and the letter's open counter begins.
        # Over that stretch they never quite touch: a tapering hairline of
        # white is threaded between them, widest at about two units and
        # narrowing to nothing, and at text sizes it breaks the diagonal away
        # from the bar exactly where the knee should read as solid.
        #
        # The counter past that run is the letter's own shape and is left
        # alone — only a gap narrow enough to be a rendering artefact rather
        # than drawn white is closed. The weld is bounded by the two edges
        # themselves, so it adds no outline of its own.
        weld = []
        for index in range(97):
            x = 190.0 + (240.0 - 190.0) * index / 96.0
            spans = sorted(_column_spans(d.contours, x))
            if len(spans) < 2:
                continue
            for lower, upper in zip(spans, spans[1:]):
                gap = upper[0] - lower[1]
                if 0.0 < gap < 6.0:
                    weld.append((x, lower[1], upper[0]))
                    break
        if len(weld) > 1:
            d.polygon(
                [(x, lo) for x, lo, _ in weld]
                + [(x, hi) for x, _, hi in reversed(weld)]
            )
        if len(weld) > 1:
            d.polygon(
                [(x, lo) for x, lo, _ in weld]
                + [(x, hi) for x, _, hi in reversed(weld)]
            )
        d.kneeling_foot(bar, 584, 56)

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
