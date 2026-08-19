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

from profile_loader import LOWER_LIMB_OUTLINE_POINTS
from upright_torso_outline_points import UPRIGHT_TORSO_OUTLINE_POINTS
from navasana_outline_points import NAVASANA_HOLES, NAVASANA_OUTLINE_POINTS
from rajakapotasana_outline_points import (
    RAJAKAPOTASANA_HOLES,
    RAJAKAPOTASANA_OUTLINE_POINTS,
)
from ustrasana_outline_points import USTRASANA_HOLES, USTRASANA_OUTLINE_POINTS
from yoga_n_outline_points import YOGA_N_HOLES, YOGA_N_OUTLINE_POINTS
from yoga_p_outline_points import YOGA_P_HOLES, YOGA_P_OUTLINE_POINTS
from yoga_r_outline_points import YOGA_R_HOLES, YOGA_R_OUTLINE_POINTS
from yoga_g_outline_points import YOGA_G_HOLES, YOGA_G_OUTLINE_POINTS
from yoga_v_outline_points import YOGA_V_HOLES, YOGA_V_OUTLINE_POINTS

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

# Normalized foot profile points from vectorized reference
# (fraction_along_foot, height_from_ground) where 0=ground, 1=top



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

    def flat_bar(self, profile: BarProfile, anchor_rise: float, stop_at: float = 1.0) -> None:
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
        
        ``stop_at`` is a fraction (0.0 to 1.0) specifying where to stop drawing
        the bar along the heel-to-toe run. Use this to stop before the foot
        region so the foot can be drawn separately as its own filled shape.
        Default is 1.0 (draw all the way to the toe).
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
        # Sample the top edge only up to stop_at fraction
        samples = int(96 * stop_at)
        edge = [
            (
                profile.heel_x + profile.step * profile.toe_s * i / 96,
                profile.top(profile.heel_x + profile.step * profile.toe_s * i / 96),
            )
            for i in range(samples)
        ]
        # Add the stopping point
        stop_x = profile.heel_x + profile.step * profile.toe_s * stop_at
        edge.append((stop_x, profile.top(stop_x)))
        # Add ground point at stop location
        edge.append((stop_x, ground))
        # One closed loop, traced the whole way round: out of the leg and down
        # around the heel to the floor, forward along the sole to the stop point,
        # then back along the top edge and in to close inside the limb.
        # The bulge is a stretch of this contour rather than a shape stuck on
        # the end of it, so it reads as the band's own rear end.
        self.polygon(
            list(heel)
            + [(profile.toe_x, ground)]
            + list(reversed(edge))
        )

        # Draw the foot shape as filled geometry (not a cutout).
        # The shin has already been drawn separately and stopped before
        # the foot region, so the foot is its own filled shape.
        if len(foot_outline) >= 3:
            self.polygon(foot_outline)

    def kneeling_shin(
        self, profile: BarProfile, knee_x: float, width: float, torso_width: float = 84.0, hip_x: float = 452.0, hip_y: float = 300.0,
    ) -> None:
        """The lower limb (thigh + knee + shin + foot) in kneeling position.

        Uses the complete lower limb outline from LOWER_LIMB_OUTLINE_POINTS, which
        contains the thigh, knee bend, shin, and foot as one continuous shape.
        The outline is scaled so the thigh width matches the torso width, and
        positioned so that:
        - The thigh top connects to the hip
        - The knee is at ground level
        - The shin lies flat on the ground from knee to ankle
        - The foot extends from the ankle

        The popliteal crease (skin fold behind the knee) is engraved as
        anatomical detail.
        """
        k = width / 52.0
        ground = profile.ground
        step = profile.step
        # The shin runs from knee to ankle
        ankle_x = profile.arch_x  # Ankle is at the arch position
        run = (ankle_x - knee_x) * step

        # Original outline dimensions (from lower_limb_outline.svg)
        # Bounding box: x=[131, 1354], y=[0, 611]
        # The outline contains: thigh (x~131-400), knee (x~400), shin (x~400-1000), foot (x~1000-1354)
        original_x_min = 131.0
        original_x_max = 1354.0
        original_y_min = 0.0
        original_y_max = 611.0
        original_width = original_x_max - original_x_min
        original_height = original_y_max - original_y_min
        
        # The thigh portion is roughly x=[131, 400] in the original outline
        # Scale so the thigh width matches the torso width
        thigh_x_min = 131.0
        thigh_x_max = 400.0
        thigh_width = thigh_x_max - thigh_x_min
        
        # Scale factor: thigh width -> torso width
        uniform_scale = torso_width / thigh_width
        
        # Calculate the actual dimensions after scaling
        scaled_width = original_width * uniform_scale
        scaled_height = original_height * uniform_scale
        
        # Position the outline so the thigh section aligns with the torso
        # The thigh section in the scaled outline is 84 units wide (matching torso width)
        # For L (step=1), the thigh is at the left end (x=0 to x=84)
        # For J (step=-1), the thigh is at the right end (after transformation)
        
        # We want the thigh section to align with the torso
        # The torso spans from hip_x - torso_width/2 to hip_x + torso_width/2
        
        if step > 0:  # L: thigh at left end (norm_x 0 to 0.22)
            # After transformation, thigh maps to x from knee_offset_x to knee_offset_x + 84
            # We want this to be hip_x - 42 to hip_x + 42
            # So knee_offset_x = hip_x - 42
            knee_offset_x = hip_x - torso_width / 2
        else:  # J: thigh at left end (norm_x 0 to 0.22), but step=-1 flips it
            # After transformation with step=-1, thigh maps to x from knee_offset_x to knee_offset_x - 84
            # We want this to be hip_x - 42 to hip_x + 42
            # So knee_offset_x - 84 = hip_x - 42  =>  knee_offset_x = hip_x + 42
            # And knee_offset_x = hip_x + 42  =>  knee_offset_x = hip_x + 42
            knee_offset_x = hip_x + torso_width / 2
        
        # For y positioning, we need the thigh top to be at the hip y-coordinate
        # The thigh top in the original is at y=0 (the very top of the outline)
        # After scaling and inverting, it's at: (611 - 0) * uniform_scale = 611 * uniform_scale from the ground
        # We want this to be at hip_y
        # So: ground_offset_y = hip_y - (611 * uniform_scale)
        
        # The thigh top y in the original outline (minimum y)
        original_thigh_top_y = 0.0
        
        # Calculate the scaled position of the thigh top (from the bottom/ground)
        scaled_thigh_top_y_from_ground = (original_y_max - original_thigh_top_y) * uniform_scale
        
        # We want the thigh top to be at hip_y in the glyph
        # So: ground_offset_y = hip_y - scaled_thigh_top_y_from_ground
        ground_offset_y = hip_y - scaled_thigh_top_y_from_ground
        
        # Transform the outline
        shin_outline = []
        for x, y in LOWER_LIMB_OUTLINE_POINTS:
            # Normalize to [0, 1]
            norm_x = (x - original_x_min) / original_width
            norm_y = (y - original_y_min) / original_height
            
            # Apply uniform scale and position
            new_x = knee_offset_x + norm_x * scaled_width * step
            # Invert y (SVG y goes down, we want y to go up from ground)
            new_y = ground_offset_y + (1.0 - norm_y) * scaled_height
            
            shin_outline.append((new_x, new_y))
        
        # Draw the shin shape as filled geometry
        if len(shin_outline) >= 3:
            self.polygon(shin_outline)
        
        # Note: Popliteal crease engraving removed for now as it was causing
        # floating artifacts. The crease position calculation needs to be
        # updated to work with the transformed shin outline coordinates.

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
        draw_shin: bool = True,
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
        
        ``draw_shin`` controls whether to draw the shin (lower leg) portion.
        Set to False when the shin will be drawn separately (e.g., using
        kneeling_shin() with a traced profile).
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
        if draw_shin:
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
        # Editorial Paripurna Navasana (full boat), imported like L and
        # then flipped vertically so the sit bones become the apex of
        # the A. The source silhouette is a woman balanced on the sit
        # bones, torso leaning back, both legs raised straight, both
        # hands grasping the knees. After the flip the head and feet
        # land on the baseline and the clasped knees read as the bar.
        pts = NAVASANA_OUTLINE_POINTS
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        # The boat is much wider than it is tall. Scaling it to L/D's
        # 788 cap made the head hang out of the glyph-sheet cell. Fit
        # the width to the other wide letters (~X) instead; height
        # follows, still seated on BAR_GROUND.
        target_width = 780.0
        scale = target_width / (right - left)

        def placed(x: float, y: float) -> Point:
            # Extra vertical flip vs L: image-bottom (the sit) goes to
            # the cap, image-top (head and feet) goes to BAR_GROUND.
            return (
                SIDEBEARING + (x - left) * scale,
                BAR_GROUND + (y - top) * scale,
            )

        d.polygon([placed(x, y) for x, y in pts])
        for hole in NAVASANA_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "B":
        # Print's B: a crouched standing figure, not an I-stem with a hat
        # on top. The head sits at the upper-left — the cocked hat is the
        # top-left of the letter — and both arms loop out to clasp at the
        # right, closing the upper bowl. The standing leg is the left stem;
        # the other leg lifts, bows out at the knee and tucks its foot back
        # onto the toe beside the standing ankle, closing the lower bowl.
        # The previous build used one rubbery arm to the waist and left the
        # far arm hanging unused, which the print does not show.
        stem_x = 210
        hip_y = 400
        d.head(stem_x - 2, 636, 1, -0.06)
        d.path([(stem_x + 6, 580), (stem_x + 4, 598)], 50, False, False, track=False)
        d.torso([(stem_x + 6, 576), (stem_x - 6, 488), (stem_x + 6, hip_y)], 86, True)
        # Hip / breech bulge on the left of the stem, as in the print.
        d.ellipse(stem_x - 16, hip_y + 12, 44, 48, 0.30)
        d.ellipse(stem_x, hip_y - 6, 38, 36, 0.12)
        # Upper bowl: both arms. The high arm leaves the shoulder below the
        # head, rises to hat height and turns down to the clasp. The low
        # arm leaves the chest and rises to meet it, so the two bowls of
        # the B stack instead of the upper one swallowing the letter.
        shoulder = (stem_x + 42, 586)
        clasp = (438, 528)
        upper_draw = [shoulder, (318, 662), (416, 652), clasp]
        lower_draw = [(stem_x + 30, 536), (328, 498), (392, 504), clasp]
        d.tapered_path(upper_draw, [44, 38, 34, 28], True)
        d.tapered_path(lower_draw, [42, 36, 32, 28], True)
        upper_arm = [shoulder, (360, 658), clasp]
        lower_arm = [(stem_x + 30, 536), (348, 500), clasp]
        for arm, root_r in ((upper_arm, 22), (lower_arm, 20)):
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], root_r)
        d.circle(416, 646, 17)
        d.circle(348, 502, 16)
        d.cut_path([(408, 664), (426, 646), (420, 624)], 3.6, True)
        d.cut_path([(334, 516), (354, 500), (350, 482)], 3.4, True)
        # Clasped hands: a solid mass split by one thin seam, as on A/H.
        d.ellipse(clasp[0] + 12, clasp[1] + 2, 28, 24, 0.70)
        d.cut_path([
            (clasp[0] - 2, clasp[1] + 18),
            (clasp[0] + 14, clasp[1] + 2),
            (clasp[0] + 10, clasp[1] - 16),
        ], 4.4, True)
        # Standing leg: crouched, slightly bent. Shoe points right.
        d.leg(
            [(stem_x - 12, hip_y + 4), (stem_x - 26, 232), (stem_x + 8, 66)], 52,
            knee_index=1, breeches_width=62, shoe_direction=(1, -0.08),
        )
        # Lower bowl: thigh bows out almost level, knee is the lower-right
        # bulge, calf comes back so the foot stands on the toe beside the
        # standing shoe.
        lifted_hip = (stem_x + 30, hip_y + 4)
        lifted_knee = (444, 268)
        lifted_ankle = (296, 78)
        d.leg(
            [lifted_hip, (344, 368), lifted_knee, lifted_ankle],
            56, knee_index=2, breeches_width=74, shoe_scale=0.0,
            anatomy_points=[lifted_hip, lifted_knee, lifted_ankle],
        )
        d.shoe(lifted_ankle[0], lifted_ankle[1], lifted_knee, (0.58, -0.81), 0.64)

    elif letter == "C":
        # Historical kneeling back-arch: face inside the upper-left opening,
        # arms over the top, and paired shins running right along the ground.
        # The print's lower-left is a full rounded breech, not a tucked-in
        # waist handing off to two skinny thighs. The previous hip sat
        # inward of the waist, so the outer C kinked and the inner counter
        # notched where the torso cap met the legs.
        hip = (176, 224)
        spine = [(235, 555), (176, 458), (152, 344), hip]
        # Coat stays near torso width; the stroke itself widens into the
        # breeches so the hip is a swell of the C, not a ball stuck on it.
        d.tapered_path(spine, [86, 84, 90, 118], True)
        segments, length = d.centerline_measurements(spine)
        d.anatomy.append({
            "part": "torso", "segments": segments, "length": length,
            "points": spine,
        })
        # Elongated breech, long axis along the spine. Fills the outer
        # curve and the inner notch without reading as a separate blob.
        d.ellipse(158, 228, 72, 48, -1.18)
        d.ellipse(186, 206, 40, 34, -0.85)
        # Fillets at the hip-to-thigh handover: the inner counter was a
        # notch, and the outer curve dented where the ellipse met the
        # breeches stroke.
        d.ellipse(214, 216, 40, 32, -0.55)
        d.ellipse(176, 176, 46, 34, -0.22)
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
        d.leg(
            [(hip[0] + 6, hip[1] + 4), (328, 118), (555, 105)],
            58, knee_index=1, breeches_width=80,
        )
        d.leg(
            [(hip[0] + 26, hip[1] + 10), (348, 150), (525, 140)],
            48, knee_index=1, breeches_width=66,
        )

    elif letter == "D":
        # Ustrasana (camel pose) in place of the print's impossible ring
        # backbend. The 1782 D closed the bowl by folding the legs up to
        # meet a descending hand — past a real spine. This glyph is a
        # traced silhouette of a kneeling camel: head thrown back on the
        # left, thighs the right pillar, hands on the heels. The source
        # photo faces this way; the first import was mirrored.
        # Same import path as L: one closed outline (plus the natural
        # counter) scaled uniformly onto BAR_GROUND.
        pts = USTRASANA_OUTLINE_POINTS
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
        for hole in USTRASANA_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "E":
        # Print's E: a seated figure, not a kneeling I-stem with an arm
        # arched over a bare head. The cocked hat is the top-left; the
        # near arm runs straight out from the shoulder at hat height as
        # the top prong, hand drooping at the tip; the far arm throws
        # the forearm out at chest height as the shorter middle prong;
        # the sitting breech is the bottom-left, and both legs extend
        # right as the bottom bar, feet pointing up-right.
        stem_x = 214
        # One sit-line for breech, thighs and shins. The letter's bottom
        # bar is that bench: flat on BAR_GROUND, not a downhill ramp.
        sit_y = BAR_GROUND + 36
        d.head(stem_x - 4, 528, 1, -0.10)
        # Coat tapers into the sit so the stem does not pinch off the
        # breech. Slight recline, as in the print — not a standing I-stem.
        spine = [
            (stem_x + 14, 470), (stem_x - 2, 346),
            (stem_x - 4, 248), (stem_x + 10, sit_y + 18),
        ]
        d.tapered_path(spine, [82, 80, 98, 118], True)
        segments, length = d.centerline_measurements(spine)
        d.anatomy.append({
            "part": "torso", "segments": segments, "length": length,
            "points": spine,
        })
        # Sitting breech elongated along the bar so it is the bottom-left
        # of the E, on the same plane as the thighs.
        d.ellipse(stem_x - 18, sit_y + 20, 54, 46, 0.48)
        d.ellipse(stem_x + 12, sit_y + 8, 62, 40, 0.10)
        d.ellipse(stem_x + 38, sit_y + 2, 46, 34, 0.04)
        # Top prong: a real arm straight out from the shoulder, at hat
        # height — not an arch over the crown.
        shoulder = (stem_x + 42, 478)
        top_wrist = (500, 486)
        top_arm = [shoulder, (356, 492), top_wrist]
        d.tapered_path(top_arm, [42, 36, 30], True)
        segments, length = d.centerline_measurements(top_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": top_arm,
        })
        d.circle(shoulder[0], shoulder[1], 22)
        d.circle(top_wrist[0], top_wrist[1], 16)
        # Hand droops at the tip as the top-right terminal.
        d.tapered_path(
            [(top_wrist[0] + 4, top_wrist[1] - 2),
             (top_wrist[0] + 14, top_wrist[1] - 28),
             (top_wrist[0] + 16, top_wrist[1] - 52)],
            [24, 18, 12], True,
        )
        d.cut_path(
            [(top_wrist[0] - 6, top_wrist[1] - 10),
             (top_wrist[0] + 10, top_wrist[1] - 10)],
            3.2, False,
        )
        # Middle prong: the far arm, shorter, open palm facing out.
        mid_shoulder = (stem_x + 24, 358)
        mid_elbow = (308, 328)
        mid_hand = (390, 338)
        mid_arm = [mid_shoulder, mid_elbow, mid_hand]
        d.tapered_path(mid_arm, [38, 34, 28], True)
        segments, length = d.centerline_measurements(mid_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": mid_arm,
        })
        d.circle(mid_shoulder[0], mid_shoulder[1], 19)
        d.circle(mid_elbow[0], mid_elbow[1], 17)
        d.cut_path([
            (mid_elbow[0] + 6, mid_elbow[1] + 14),
            (mid_elbow[0] + 16, mid_elbow[1] + 2),
            (mid_elbow[0] + 8, mid_elbow[1] - 12),
        ], 3.4, True)
        d.ellipse(mid_hand[0] + 10, mid_hand[1] + 2, 18, 15, 0.10)
        for dx, dy in ((10, 12), (20, 6), (22, -4), (14, -12)):
            d.polygon([
                (mid_hand[0] + 2, mid_hand[1]),
                (mid_hand[0] + dx, mid_hand[1] + dy),
                (mid_hand[0] + dx + 6, mid_hand[1] + dy + 4),
            ])
        # Bottom prong: legs leave the front of the sit and run level.
        # The previous build dropped the ankles to y=88, so the bar
        # ramped downhill; only the feet kick up-right, as in the print.
        near_knee = (392, sit_y)
        far_knee = (406, sit_y + 16)
        near_ankle = (568, sit_y)
        far_ankle = (544, sit_y + 16)
        d.leg(
            [(stem_x + 28, sit_y + 14), near_knee, near_ankle],
            56, knee_index=1, breeches_width=74, shoe_scale=0.0,
        )
        d.leg(
            [(stem_x + 46, sit_y + 24), far_knee, far_ankle],
            48, knee_index=1, breeches_width=62, shoe_scale=0.0,
        )
        d.shoe(near_ankle[0], near_ankle[1], near_knee, (0.62, 0.78), 0.86)
        d.shoe(far_ankle[0], far_ankle[1], far_knee, (0.70, 0.72), 0.78)
    elif letter == "F":
        # Standing F on I's body ratios. The previous build had a 256 torso
        # over 368-unit legs and two rubber arms (406 and 306) — the top one
        # nearly twice a real arm, the middle one almost at the hip. The print
        # is an ordinary standing figure: hips near mid-stem, a normal reach
        # for the top prong, and a short forearm across the chest for the
        # middle one.
        stem_x = 172
        hip_y = 450
        d.head(stem_x, 742, 1)
        d.torso([(stem_x, 675), (stem_x, 562), (stem_x, hip_y)], 80, False)
        # Top prong: a real arm straight out from the shoulder. Length matches
        # I's hanging arm (~274) instead of stretching past 400.
        top_y = 638
        top_reach = stem_x + 296
        top_arm = [(stem_x + 22, top_y), (stem_x + 160, top_y), (top_reach, top_y)]
        d.path(top_arm, 42, False, False, track=False)
        segments, length = d.centerline_measurements(top_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": top_arm,
        })
        d.circle(top_arm[0][0], top_arm[0][1], 23)
        # Hand at the tip, fingers slightly down as in the print — a serif
        # without turning the bar into T's hanging terminal.
        d.ellipse(top_reach + 10, top_y - 4, 20, 16, -0.15)
        d.tapered_path(
            [(top_reach + 6, top_y - 2), (top_reach + 14, top_y - 22),
             (top_reach + 16, top_y - 38)],
            [22, 16, 11], True,
        )
        d.cut_path([(top_reach - 6, top_y - 12), (top_reach - 6, top_y + 12)], 3.4, False)
        # Middle prong: the far arm crosses the chest and throws only the
        # forearm out, so the bar sits at chest height and stays short —
        # the print's hand barely clears the torso.
        mid_y = 548
        mid_reach = stem_x + 168
        mid_arm = [(stem_x + 18, mid_y), (stem_x + 92, mid_y), (mid_reach, mid_y)]
        d.path(mid_arm, 36, False, False, track=False)
        segments, length = d.centerline_measurements(mid_arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": mid_arm,
        })
        d.circle(mid_arm[0][0], mid_arm[0][1], 19)
        d.ellipse(mid_reach + 8, mid_y, 16, 15, 0.0)
        d.cut_path([(mid_reach - 6, mid_y - 12), (mid_reach - 6, mid_y + 12)], 3.2, False)
        # Seam where the far arm crosses the trunk.
        d.cut_path([
            (stem_x - 16, mid_y + 28), (stem_x + 4, mid_y + 8),
            (stem_x + 8, mid_y - 14),
        ], 4.0, True)
        # Legs match I: ~400 units, hip at 450, so the trunk is no longer
        # longer than the thigh. Feet flare as serifs, like I, P and T.
        d.leg(
            [(stem_x - 18, 455), (stem_x - 22, 255), (stem_x - 26, 55)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(-1, 0)
        )
        d.leg(
            [(stem_x + 18, 455), (stem_x + 22, 255), (stem_x + 26, 55)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(1, 0)
        )

    elif letter == "G":
        # Editorial yoga-alphabet G / Vrischikasana (scorpion), imported
        # like L. An inverted backbend: arms and hanging head at the
        # bottom, arched torso the bowl, feet the spur.
        pts = YOGA_G_OUTLINE_POINTS
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
        for hole in YOGA_G_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

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
        torso_width = 84
        # Cut torso at hip to avoid overlap with thigh in lower limb outline
        hip = (stem_x, 300)
        d.torso([hip, (stem_x, 466), (stem_x, 632)], torso_width, False)
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
        # Bottom bar: use the complete lower limb outline (thigh + knee + shin + foot)
        # The outline is scaled to match the torso width for seamless integration
        # Mirror of L's bottom bar, running left instead of right
        bar = BarProfile(
            ground=BAR_GROUND, heel_x=478, arch_x=144, toe_x=18,
            heel_depth=BAR_HEEL_DEPTH, arch_depth=BAR_ARCH_DEPTH,
            calf_x=241,
        )
        # Draw the complete lower limb (thigh + knee + shin + foot) scaled to torso width
        d.kneeling_shin(bar, 478, 52, torso_width=torso_width, hip_x=hip[0], hip_y=hip[1])

    elif letter == "K":
        # Standing profile K, matching the print. Head, upright torso and the
        # planted standing leg make the left stem. The near arm reaches up and
        # out as the upper branch, ending in a pointing hand. The other leg
        # kicks down and out from the hip as the lower branch, foot planted.
        # The previous build was a cartwheel on one hand, which the print
        # does not show.
        stem_x = 196
        hip_y = 448
        d.head(stem_x + 8, 718, 1)
        d.torso([(stem_x, 658), (stem_x, 554), (stem_x, hip_y)], 82, False)
        # Far arm hangs along the stem, blending into the pillar.
        far_arm = [(stem_x - 28, 622), (stem_x - 34, 530), (stem_x - 30, 448)]
        d.path(far_arm, 26, True, False, track=False)
        d.circle(far_arm[-1][0], far_arm[-1][1], 14)
        # Upper branch: the pointing arm. Shoulder, elbow, wrist — a real
        # reach, not a rubber stroke.
        shoulder = (stem_x + 28, 624)
        elbow = (338, 698)
        wrist = (478, 748)
        arm = [shoulder, elbow, wrist]
        d.tapered_path(arm, [40, 34, 28], True)
        segments, length = d.centerline_measurements(arm)
        d.anatomy.append({
            "part": "limb", "segments": segments, "length": length,
            "points": arm,
        })
        d.circle(shoulder[0], shoulder[1], 21)
        d.circle(elbow[0], elbow[1], 18)
        d.cut_path([
            (elbow[0] + 6, elbow[1] + 16), (elbow[0] + 16, elbow[1] + 2),
            (elbow[0] + 8, elbow[1] - 14),
        ], 3.6, True)
        # Pointing hand: index out as the terminal, the other fingers folded.
        d.ellipse(wrist[0] + 6, wrist[1] + 2, 18, 14, 0.28)
        d.tapered_path(
            [(wrist[0] + 10, wrist[1] + 4), (wrist[0] + 48, wrist[1] + 16),
             (wrist[0] + 78, wrist[1] + 22)],
            [16, 12, 7], True,
        )
        d.polygon([
            (wrist[0] + 4, wrist[1] - 6), (wrist[0] + 18, wrist[1] - 18),
            (wrist[0] + 24, wrist[1] - 12), (wrist[0] + 12, wrist[1] + 2),
        ])
        d.cut_path([(wrist[0] - 4, wrist[1] + 10), (wrist[0] + 8, wrist[1] - 6)],
                   3.0, False)
        # Standing leg: continues the stem to the baseline.
        d.leg(
            [(stem_x - 16, hip_y), (stem_x - 18, 252), (stem_x - 14, 56)], 52,
            knee_index=1, breeches_width=58, shoe_direction=(1, 0),
        )
        # Lower branch: the kicked leg, knee clearly bent, foot planted right.
        d.leg(
            [(stem_x + 20, hip_y - 8), (348, 292), (518, 72)], 54,
            knee_index=1, breeches_width=64, shoe_scale=0.0,
        )
        d.ellipse(534, 64, 22, 16, -0.28)
        for dx, dy in ((20, -2), (18, -12), (10, -20)):
            d.polygon([
                (530, 66), (534 + dx, 64 + dy), (538 + dx, 72 + dy),
            ])
        d.cut_path([(518, 70), (534, 56), (542, 44)], 3.2, True)

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
        pts = UPRIGHT_TORSO_OUTLINE_POINTS
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
        # Print's M: two legs only. Stockinged calves are the outer
        # stems, breeched thighs the inner V, paired buttocks and a
        # small hatless face sit in the valley, and the hands cup the
        # sit. The previous build put a cocked hat on the left peak and
        # used arms as the left stem, which the print does not show.
        # Drawn as separate tapers so the sharp knee fold does not spawn
        # a limb-width ball on each peak. The sit is the crotch of the
        # two thighs, not a sack hung under a pointed V.
        sit = (350, 312)
        for sign in (-1, 1):
            hip = (sit[0] + sign * 22, sit[1] + 8)
            knee = (350 + sign * 182, 698)
            ankle = (350 + sign * 204, 74)
            thigh = [hip, knee]
            shin = [knee, (350 + sign * 196, 380), ankle]
            d.tapered_path(thigh, [98, 76], True)
            d.tapered_path(shin, [58, 68, 40], True)
            segments, length = d.centerline_measurements(thigh + shin[1:])
            d.anatomy.append({
                "part": "limb", "segments": [
                    math.dist(thigh[0], thigh[1]),
                    math.dist(shin[0], shin[1]) + math.dist(shin[1], shin[2]),
                ], "length": length, "points": [hip, knee, ankle],
            })
            # Rounded kneecap, sized to the limb, not a ball on a stick.
            d.ellipse(knee[0], knee[1] + 6, 34, 30, 0.0)
            d.ellipse(knee[0], knee[1] - 4, 30, 8, 0.0)
            d.cut_path([
                (knee[0] - sign * 16, knee[1] - 2),
                (knee[0] + sign * 16, knee[1] - 4),
            ], 3.2, False)
            d.shoe(ankle[0], ankle[1], shin[1], (sign, -0.06), 0.92)
        # Paired buttocks are the valley floor.
        d.ellipse(318, sit[1] - 6, 48, 40, 0.22)
        d.ellipse(382, sit[1] - 6, 48, 40, -0.22)
        d.ellipse(350, sit[1] - 18, 54, 32, 0.0)
        d.cut_path([(350, sit[1] + 16), (350, sit[1] - 36)], 5.0, False)
        # Small hatless face nestled in the dip, looking up.
        d.front_head(350, sit[1] + 28, 32, hair_down=False, hat=False,
                     gaze_up=True)
        # Hands cup the underside of the sit.
        for sign in (-1, 1):
            hx, hy = 350 + sign * 52, sit[1] - 36
            d.ellipse(hx, hy, 20, 15, sign * 0.28)
            for dx, dy in ((-4, -12), (4, -16), (10, -8)):
                d.polygon([
                    (hx, hy),
                    (hx + sign * dx, hy + dy),
                    (hx + sign * (dx + 5), hy + dy + 4),
                ])

    elif letter == "N":
        # Editorial yoga-alphabet N, imported like L. A backbend / bridge
        # whose planted legs are the left stem, the arched torso the
        # diagonal, and the raised joined arms the right stem. The head
        # rests on the floor at the foot of the arm stem.
        pts = YOGA_N_OUTLINE_POINTS
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
        for hole in YOGA_N_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

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
        # Editorial yoga-alphabet P, imported like L. A standing
        # backbend whose planted legs are the stem and whose arched
        # torso, hanging head and clasped hands close the bowl.
        pts = YOGA_P_OUTLINE_POINTS
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
        for hole in YOGA_P_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "Q":
        # Editorial bow-as-Q, imported like L. A prone backbend whose
        # raised feet and grasping arm close the ring, while the other
        # arm plants on the floor as the tail. The print's inverted
        # ring is replaced because this pose is more legible as a Q.
        pts = RAJAKAPOTASANA_OUTLINE_POINTS
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
        for hole in RAJAKAPOTASANA_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "R":
        # Editorial yoga-alphabet R, imported like L. The same standing
        # backbend as P, with the front leg stepped forward as the
        # diagonal of the letter.
        pts = YOGA_R_OUTLINE_POINTS
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
        for hole in YOGA_R_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "S":
        # Print's S: the arms sweep the upper hook, the head sits in the
        # upper-left opening facing right, the torso is the diagonal spine,
        # and the legs carry the lower hook left to the shoes. The previous
        # build inverted that — legs on top, head on the floor, arms as two
        # nubs tucked into the lower curve.
        shoulder = (248, 488)
        hip = (498, 278)
        # Upper hook: both arms leave the shoulder, arch over the head and
        # run out to the right, tapering to a reaching hand.
        for spread, width in ((16, 50), (-14, 40)):
            arm = [
                (shoulder[0] + 10, shoulder[1] + 22 + spread * 0.3),
                (300 + spread, 660 + spread * 0.12),
                (470 + spread * 0.5, 742 + spread * 0.08),
                (618 + spread * 0.2, 668 + spread * 0.3),
            ]
            d.tapered_path(
                arm, [width, width * 0.90, width * 0.70, width * 0.48], True,
            )
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width * 0.46)
            wx, wy = arm[-1]
            d.ellipse(wx + 12, wy - 6, 18, 14, -0.40)
            for dx, dy in ((10, -20), (20, -14), (26, -6)):
                d.polygon([
                    (wx + 4, wy - 4), (wx + dx, wy + dy),
                    (wx + dx + 6, wy + dy + 5),
                ])
        # Head in the upper-left opening, facing right, clear of the arm
        # arch. No hat: the brim would jam the underside of the sleeve.
        d.path([(shoulder[0] - 4, shoulder[1] + 18), (214, 548)], 36,
               False, False, track=False)
        d.head(198, 592, 1, -0.18, hat=False)
        # Diagonal spine, bent so the letter is an S-curve rather than a
        # zigzag: chest turns down, waist eases into the hip.
        d.torso([shoulder, (360, 400), (470, 330), hip], 88, True)
        # Hip mass rounds the lower-right bulge of the S.
        d.ellipse(hip[0] + 16, hip[1] - 4, 48, 44, 0.55)
        d.ellipse(hip[0] + 4, hip[1] - 28, 40, 34, 0.35)
        # Lower hook: thighs drop through the bulge to a grounded knee;
        # the shin+foot is J's traced sitting limb, running left — the
        # print's stocking and shoe, not a blunt sausage.
        knee = (408, 118)
        for spread, width, breeches in ((-8, 56, 70), (14, 46, 56)):
            thigh = [
                (hip[0] + 8 + spread * 0.3, hip[1] - 20),
                (knee[0] + spread * 0.2, knee[1] - 4),
            ]
            d.tapered_path(thigh, [breeches * 0.98, breeches * 0.80], True)
            segments, length = d.centerline_measurements(
                [thigh[0], knee, (148, 74)]
            )
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": [thigh[0], knee, (148, 74)],
            })
        thigh_width = 400.0 - 131.0
        uniform_scale = 84.0 / thigh_width
        shin_src = [(x, y) for x, y in LOWER_LIMB_OUTLINE_POINTS if x >= 410.0]
        src_x0 = min(x for x, _ in shin_src)
        src_y1 = max(y for _, y in shin_src)
        # Flip: J's bar runs left from the knee, same as this hook.
        shin_outline = []
        for x, y in shin_src:
            new_x = knee[0] + 8 - (x - src_x0) * uniform_scale
            new_y = BAR_GROUND + (src_y1 - y) * uniform_scale
            shin_outline.append((new_x, new_y))
        if shin_outline:
            d.polygon([
                (x, min(BAR_GROUND + 108, max(BAR_GROUND, y)))
                for x, y in shin_outline
            ])
        d.ellipse(knee[0] - 6, BAR_GROUND + 42, 40, 36, -0.15)
        d.cut_path([
            (knee[0] - 12, knee[1] + 18),
            (knee[0] - 24, knee[1] + 4),
            (knee[0] - 16, knee[1] - 10),
        ], 3.6, True)
        # Weld the thigh into J's bar so the hook does not nick.
        d.polygon([
            (knee[0] - 8, knee[1] + 36),
            (knee[0] - 56, BAR_GROUND + 64),
            (knee[0] - 100, BAR_GROUND + 58),
            (knee[0] - 36, knee[1] + 8),
        ])

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
        # Editorial U (the 1782 print has no U). A lying backbend still
        # makes the letter: legs the left bar, arched spine the bowl, arms
        # the right bar. The previous build hung an inverted hatted head
        # off the lower-right and stuck long horizontal feet off the left
        # stem, so the glyph read as a lopsided horseshoe with junk on
        # both sides rather than a U. Head tucks into the counter; both
        # stems are the same height and similar weight; feet point up to
        # answer the hands.
        hip = (198, 328)
        shoulder = (502, 328)
        # A long flat run at the bottom so the offset inner edge is a U,
        # not the V a single apex vertex pinches into.
        d.torso(
            [hip, (222, 210), (258, 128), (310, 80), (390, 80), (442, 128),
             (478, 210), shoulder],
            86, True,
        )
        # Extra fill rounds the inner bottom if the ribbon still creases.
        d.ellipse(350, 122, 74, 36, 0.0)
        # Hip mass stays inside the left join so the stem does not sprout
        # a sideways bulge.
        d.ellipse(hip[0] + 6, hip[1] - 8, 40, 36, 0.15)
        # Head tucked into the shoulder pocket of the counter, facing in.
        # No hat: the brim was what spiked out of the silhouette.
        d.path([(shoulder[0] - 18, shoulder[1] - 4), (468, 278)], 38,
               False, False, track=False)
        d.head(458, 258, -1, 0.25, hat=False)
        # Left bar: both legs straight up, same height, compact shoes
        # pointing up as the terminal.
        for spread, width, breeches in ((-16, 54, 64), (16, 48, 56)):
            ankle = (hip[0] + spread, 708)
            d.leg(
                [
                    (hip[0] + spread * 0.4, hip[1] + 28),
                    (hip[0] + spread, 520),
                    ankle,
                ],
                width, knee_index=1, breeches_width=breeches,
                shoe_scale=0.0,
            )
            d.shoe(ankle[0], ankle[1], (hip[0] + spread, 520), (0.0, 1.0), 0.70)
        # Right bar: both arms vertical, held apart by a real gap so they
        # stay two limbs, thickened so the stems match.
        for spread, width in ((-18, 46), (18, 40)):
            tip = (shoulder[0] + spread, 688)
            arm = [
                (shoulder[0] + spread * 0.4, shoulder[1] + 26),
                (shoulder[0] + spread, 510),
                tip,
            ]
            d.tapered_path(arm, [width, width * 0.90, width * 0.72], True)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], width * 0.48)
            # Hand flat, fingers up — the right-hand terminal.
            d.ellipse(tip[0], tip[1] + 12, 16, 18, 0.0)
            for offset in (-10, -3, 4, 11):
                d.polygon([
                    (tip[0] + offset - 3, tip[1] + 20),
                    (tip[0] + offset + 3, tip[1] + 20),
                    (tip[0] + offset + 2, tip[1] + 44),
                    (tip[0] + offset - 2, tip[1] + 44),
                ])
            d.cut_path([
                (tip[0] - 12, tip[1] + 22), (tip[0] + 12, tip[1] + 22),
            ], 3.2, False)

    elif letter == "V":
        # Editorial yoga-alphabet V, imported like L. A V-sit / boat on
        # the sit bones: raised legs one stroke, leaning torso the other.
        pts = YOGA_V_OUTLINE_POINTS
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
        for hole in YOGA_V_HOLES:
            d.polygon([placed(x, y) for x, y in hole], hole=True)

    elif letter == "W":
        # Print's W: a folded figure whose four strokes are one body. Head
        # at the middle peak; red-sleeved arms drop to planted hands as the
        # inner strokes; thighs drop to baseline knees and calves rise to
        # the outer peaks. The previous build had 987-unit legs against
        # 382-unit arms, giant knee balls, and forked insect hands.
        ground = 64.0
        d.head(350, 548, 1, hat=False)
        d.torso([(350, 500), (350, 410)], 86, False)
        # Inner strokes: arms as thick as the thighs, from the shoulders
        # down to planted hands on the shared ground.
        left_hand = (268, ground + 28)
        right_hand = (432, ground + 28)
        left_arm = [(318, 468), (292, 270), left_hand]
        right_arm = [(382, 468), (408, 270), right_hand]
        for arm in (left_arm, right_arm):
            d.tapered_path(arm, [58, 52, 42], True)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 28)
        # Planted hands: a real palm and four fingers reaching the ground.
        for hx, hy, sign in ((left_hand[0], left_hand[1], -1),
                             (right_hand[0], right_hand[1], 1)):
            d.ellipse(hx + sign * 2, hy + 4, 24, 18, sign * 0.18)
            for fx in (-12, 0, 12):
                d.polygon([
                    (hx + fx - 6, hy + 6), (hx + fx + 6, hy + 6),
                    (hx + fx + 5, ground), (hx + fx - 5, ground),
                ])
            d.cut_path([(hx - 8, hy + 2), (hx + 2, hy + 2)], 2.8, False)
            d.cut_path([(hx - 2, hy + 2), (hx + 8, hy + 2)], 2.8, False)
        # Outer strokes: thigh down to a modest baseline knee, calf up to a
        # foot at about head height so the three peaks of the W sit together.
        # Drawn as separate tapers so the sharp fold does not spawn a
        # limb-width knee ball.
        for sign in (-1, 1):
            hip = (350 + sign * 32, 408)
            knee = (350 + sign * 156, ground + 22)
            foot = (350 + sign * 236, 540)
            thigh = [hip, knee]
            shin = [knee, (350 + sign * 210, 300), foot]
            d.tapered_path(thigh, [64, 50], True)
            d.tapered_path(shin, [46, 38, 30], True)
            segments, length = d.centerline_measurements(thigh + shin[1:])
            d.anatomy.append({
                "part": "limb", "segments": [
                    math.dist(thigh[0], thigh[1]),
                    math.dist(shin[0], shin[1]) + math.dist(shin[1], shin[2]),
                ], "length": length, "points": [hip, knee, foot],
            })
            d.ellipse(knee[0], knee[1], 20, 18, 0.0)
            d.ellipse(knee[0], knee[1], 22, 8, math.pi / 2)
            # Raised shoe, toe pointing up and out.
            d.shoe(foot[0], foot[1], shin[1], (sign * 0.35, 0.94), 0.78)

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
        # Standing Y, matching the print: a normally proportioned upright
        # figure with both arms raised in a V. The previous build was a
        # frontal squat — knees up, a short thick column — which the print
        # does not show. The head sits in the fork, the raised arms are the
        # two branches, and the standing legs are the stem.
        d.head(350, 698, 1, hat=False)
        d.path([(350, 638), (350, 668)], 52, False, False, track=False)
        d.torso([(350, 638), (350, 544), (350, 450)], 80, False)
        for sign in (-1, 1):
            tip = (350 + sign * 236, 792)
            arm = [
                (350 + sign * 38, 618),
                (350 + sign * 128, 708),
                tip,
            ]
            d.tapered_path(arm, [38, 33, 28], True)
            segments, length = d.centerline_measurements(arm)
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": arm,
            })
            d.circle(arm[0][0], arm[0][1], 20)
            # Open palm facing up and slightly out, as in the print.
            d.ellipse(tip[0] + sign * 6, tip[1] + 12, 18, 15, sign * 0.35)
            for dx, dy in ((-10, 16), (-2, 22), (7, 21), (14, 15)):
                d.polygon([
                    (tip[0] + sign * dx - 4, tip[1] + dy),
                    (tip[0] + sign * dx + 4, tip[1] + dy),
                    (tip[0] + sign * dx + 3, tip[1] + dy + 24),
                    (tip[0] + sign * dx - 3, tip[1] + dy + 24),
                ])
            d.cut_path([
                (tip[0] + sign * 2 - 12, tip[1] + 18),
                (tip[0] + sign * 2 + 12, tip[1] + 18),
            ], 3.2, False)
        # Standing legs, same ratio as I, feet flaring as stem serifs.
        d.leg(
            [(332, 455), (328, 255), (324, 55)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(-1, 0),
        )
        d.leg(
            [(368, 455), (372, 255), (376, 55)], 50,
            knee_index=1, breeches_width=56, shoe_direction=(1, 0),
        )

    elif letter == "Z":
        # Side-profile Z: a backward lean over a deep kneel. Both arms reach
        # horizontally from the shoulders as the top bar. The diagonal is one
        # straight line split at the hip — torso above, thighs below — the way
        # the print shows the coat handing off to the breeches. The previous
        # build drew that whole diagonal as torso and bolted L's vertical
        # sitting outline onto the end, so the thigh vanished, the join
        # notched, and the outline dipped below the baseline (yMin −41).
        torso_width = 88
        shoulder = (520, 668)
        # Knee sits a joint-radius above the ground so the corner lands on
        # the baseline rather than straddling it. Hip is the midpoint of the
        # shoulder-to-knee run, giving torso and thigh the same length
        # (~325), comparable to J's trunk instead of one 614-unit pillar.
        knee = (200, 118)
        hip = ((shoulder[0] + knee[0]) * 0.5, (shoulder[1] + knee[1]) * 0.5)
        ankle = (528, 118)
        d.torso([shoulder, hip], torso_width, False)
        d.circle(hip[0], hip[1], torso_width * 0.50)
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
        # Waist seam: the print's coat/breeches line, held inside the stroke.
        d.cut_path([
            (hip[0] - 22, hip[1] + 18),
            (hip[0] + 6, hip[1] + 2),
            (hip[0] + 24, hip[1] - 16),
        ], 4.6, True)
        # Thighs continue the same diagonal down to the grounded knee, as
        # wide as the torso so the letter's stem does not step. Tracked as
        # legs for the anatomy audit; the shin is the bar below, not a
        # second tapered stroke, so it cannot swell a lump through the sole.
        for spread, width, breeches in ((0, 58, torso_width), (12, 48, 74)):
            thigh = [
                (hip[0] + spread * 0.25, hip[1] + spread * 0.12),
                (knee[0] + 18 + spread * 0.12, knee[1] - 6),
            ]
            d.tapered_path(
                thigh,
                [breeches * 0.98, breeches * 0.82],
                True,
            )
            segments, length = d.centerline_measurements(
                [thigh[0], (knee[0] + spread * 0.12, knee[1]), (ankle[0], ankle[1])]
            )
            d.anatomy.append({
                "part": "limb", "segments": segments, "length": length,
                "points": [thigh[0], (knee[0], knee[1]), (ankle[0], ankle[1])],
            })
        # Bottom limb: J's traced sitting shin+foot, running right from the
        # kneeling corner. The previous BarProfile wedge was a typographic
        # taper; the print (and J) show a real calf, arch and pointed toe.
        # Only the shin/foot of the outline is used — rotating the whole
        # sitting limb would tilt the shin off the baseline.
        original_x_min, original_x_max = 131.0, 1354.0
        original_y_min, original_y_max = 0.0, 611.0
        original_width = original_x_max - original_x_min
        original_height = original_y_max - original_y_min
        thigh_width = 400.0 - 131.0
        # Same scale J uses, so the bar's thickness and foot match.
        j_torso_width = 84.0
        uniform_scale = j_torso_width / thigh_width
        # From the knee through the toe. Starting earlier includes the
        # vertical thigh and spikes a hairline up the diagonal.
        shin_src = [(x, y) for x, y in LOWER_LIMB_OUTLINE_POINTS if x >= 410.0]
        src_x0 = min(x for x, _ in shin_src)
        src_y0 = min(y for _, y in shin_src)
        src_y1 = max(y for _, y in shin_src)
        # Place the knee at the letter's left corner, sole on BAR_GROUND.
        knee_x = knee[0] - 8
        shin_outline = []
        for x, y in shin_src:
            new_x = knee_x + (x - src_x0) * uniform_scale
            new_y = BAR_GROUND + (src_y1 - y) * uniform_scale
            shin_outline.append((new_x, new_y))
        if shin_outline:
            # Sole on the ground; drop any leftover thigh that still
            # climbs the diagonal.
            d.polygon([
                (x, min(BAR_GROUND + 108, max(BAR_GROUND, y)))
                for x, y in shin_outline
            ])
        # Rounded kneeling knee — J's fold, not a separate joint ball.
        d.ellipse(knee[0] + 10, BAR_GROUND + 42, 40, 36, 0.15)
        d.cut_path([
            (knee[0] + 16, knee[1] + 20),
            (knee[0] + 28, knee[1] + 6),
            (knee[0] + 22, knee[1] - 8),
        ], 3.6, True)
        # Fillet the inner corner so the diagonal meets J's bar in one turn.
        d.polygon([
            (knee[0] + 8, knee[1] + 36),
            (knee[0] + 56, BAR_GROUND + 64),
            (knee[0] + 100, BAR_GROUND + 58),
            (knee[0] + 36, knee[1] + 8),
        ])

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
# Reordered SHIN_PROFILE - starts at knee (frac near 0, height near 0)

