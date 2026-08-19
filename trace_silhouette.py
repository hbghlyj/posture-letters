#!/usr/bin/env python3
"""Trace the largest foreground silhouette in an image into a resampled
closed Python contour suitable for direct import as a yoga-alphabet glyph.

The script:
- Loads the source image (PNG/JPG, with optional alpha) and threshold-masks
  the dominant foreground colour using Otsu on the inverse luminance.
- Keeps only the largest connected component so background speckles do not
  leak into the traced outline.
- Refits the bounding box of that component to a 1024-px portrait, applies
  a 32-px white margin, and binarises the result so the trace is pure
  black-and-white.
- Extracts the largest external contour plus any interior cavities (holes)
  with OpenCV, resamples each uniformly to roughly 3 px of arc length,
  normalises winding so the area is positive in image space (y-down), and
  writes a Python module exporting ``YOGA_<LETTER>_OUTLINE_POINTS`` and
  ``YOGA_<LETTER>_HOLES``.
- Prints the trace statistics (components, body area, outer bbox, area)
  so a downstream caller can validate the topology.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def signed_area(points: list[tuple[float, float]]) -> float:
    return sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    ) / 2


def resample_closed(
    points: list[tuple[float, float]],
    spacing: float = 3.0,
) -> list[tuple[float, float]]:
    """Resample a closed polygon to roughly ``spacing`` units of arc length."""
    arr = np.asarray(points, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 3:
        return [(float(p[0]), float(p[1])) for p in points]
    closed = np.vstack([arr, arr[0]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    keep = seg > 1e-9
    if not keep.any():
        return [(float(p[0]), float(p[1])) for p in points]
    starts = closed[:-1][keep]
    ends = closed[1:][keep]
    lengths = seg[keep]
    cumulative = np.concatenate([[0.0], np.cumsum(lengths)])
    total = cumulative[-1]
    if total <= 0.0:
        return [(float(p[0]), float(p[1])) for p in points]
    count = max(3, int(round(total / spacing)))
    distances = np.linspace(0.0, total, count, endpoint=False)
    out: list[tuple[float, float]] = []
    for distance in distances:
        idx = min(int(np.searchsorted(cumulative, distance, side="right")) - 1, len(lengths) - 1)
        fraction = (distance - cumulative[idx]) / lengths[idx]
        point = starts[idx] + fraction * (ends[idx] - starts[idx])
        out.append((float(point[0]), float(point[1])))
    return out


def build_binary_mask(image_path: Path) -> np.ndarray:
    """Return a uint8 binary mask (255 = foreground) using Otsu on luminance.

    The source image is expected to follow the conventional "body brighter
    than background" convention so that 255-pixel regions mark the body. A
    fall-back fixed threshold is used when the image is already a strict
    0/255 binary, because Otsu would otherwise pick a degenerate threshold
    of 0 and silently invert the body and the background.
    """
    array = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if array is None:
        raise SystemExit(f"cannot read {image_path}")
    if array.ndim == 3 and array.shape[2] == 4:
        # Use the alpha channel as the foreground cue when present.
        alpha = array[..., 3]
        if alpha.max() < 5:
            gray = cv2.cvtColor(array[..., :3], cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
            )
        else:
            _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            mask = 255 - mask  # opaque regions are foreground
    else:
        gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY) if array.ndim == 3 else array
        unique_values = np.unique(gray)
        if int(unique_values.size) <= 2:
            # Already a pure binary (body=255, background=0). Otsu would
            # pick the degenerate threshold 0 and invert the two regions,
            # so apply a fixed threshold at the histogram midpoint.
            threshold_value = 127.0
        else:
            otsu_threshold, _ = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU,
            )
            threshold_value = float(otsu_threshold)
            if threshold_value < 1.0:
                threshold_value = 1.0
        _, mask = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    return mask


def select_largest_component(mask: np.ndarray) -> tuple[np.ndarray, int, tuple[int, int, int, int, int]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count < 2:
        raise SystemExit("no foreground component found")
    areas = stats[1:, cv2.CC_STAT_AREA]
    component = 1 + int(np.argmax(areas))
    x, y, w, h, area = stats[component].tolist()
    body = np.where(labels == component, 255, 0).astype(np.uint8)
    return body, component, (x, y, w, h, area)


def prepare_canvas(
    body: np.ndarray,
    bbox: tuple[int, int, int, int, int],
    long_side: int = 1024,
    margin: int = 32,
) -> np.ndarray:
    """Refit the body component to ``long_side`` with a uniform white margin."""
    x, y, w, h, _ = bbox
    if w <= 0 or h <= 0:
        raise SystemExit("invalid component bbox")
    scale = long_side / float(max(w, h))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    crop = body[y:y + h, x:x + w]
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    _, resized = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
    canvas = np.full((nh + 2 * margin, nw + 2 * margin), 255, dtype=np.uint8)
    canvas[margin:margin + nh, margin:margin + nw] = resized
    return canvas


def trace_outline_with_holes(
    canvas: np.ndarray,
) -> tuple[np.ndarray, list[np.ndarray]]:
    """Find the largest external contour and any interior cavities.

    Returns the outer contour as an Nx2 float array and a list of hole
    contours, also as Nx2 float arrays. We use RETR_TREE so the inner
    cavities of a C-/U-shape silhouette are recovered as children of the
    outer contour.
    """
    contours, hierarchy = cv2.findContours(
        canvas, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE,
    )
    if not contours:
        raise SystemExit("no external contour after resampling")

    # Find the largest contour with no parent (an outermost contour).
    outer_candidates = [
        (i, contours[i])
        for i in range(len(contours))
        if hierarchy[0, i, 3] == -1
    ]
    if not outer_candidates:
        raise SystemExit("no outermost contour found")
    outer_candidates.sort(key=lambda kv: cv2.contourArea(kv[1]), reverse=True)
    outer_idx, outer_ct = outer_candidates[0]

    # Holes are descendants of the outer contour.
    holes: list[np.ndarray] = []
    queue = [outer_idx]
    while queue:
        idx = queue.pop()
        # Every first child of idx becomes part of our tree.
        child = hierarchy[0, idx, 2]
        while child != -1:
            # If this child is a hole (parent is idx, grandparent is not idx),
            # treat as a hole if its sibling index in the traversal is even;
            # otherwise it is an outer of an interior region. For a typical
            # single-outer-multiple-holes shape the children of the outer
            # contour are the holes themselves.
            if hierarchy[0, child, 3] == idx:
                holes.append(contours[child])
            queue.append(child)
            child = hierarchy[0, child, 0]

    return outer_ct[:, 0, :].astype(np.float64), [h[:, 0, :].astype(np.float64) for h in holes]


def write_module(
    points: list[tuple[float, float]],
    holes: list[list[tuple[float, float]]],
    letter: str,
    description: str,
    output: Path,
) -> None:
    letter = letter.upper()
    text_lines = ['"""' + description.strip(), '"""', "",
                   f"YOGA_{letter}_OUTLINE_POINTS = ["]
    text_lines.extend(f"    ({px:.2f}, {py:.2f})," for px, py in points)
    text_lines.extend([']', "", f"YOGA_{letter}_HOLES = ["]
    for hole in holes:
        text_lines.append('    [')
        text_lines.extend(f"        ({px:.2f}, {py:.2f})," for px, py in hole)
        text_lines.append('    ],')
    text_lines.append(']')
    text_lines.append("")
    output.write_text("\n".join(text_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("output")
    parser.add_argument("letter")
    parser.add_argument("description")
    args = parser.parse_args()

    mask = build_binary_mask(Path(args.image))
    body, component, bbox = select_largest_component(mask)
    canvas = prepare_canvas(body, bbox)
    raw, hole_raws = trace_outline_with_holes(canvas)
    points = resample_closed([(float(x), float(y)) for x, y in raw], 3.0)
    if signed_area(points) > 0:
        points.reverse()
    holes: list[list[tuple[float, float]]] = []
    for hole in hole_raws:
        # Skip degenerate "holes" smaller than 1% of the outer area.
        outer_area = cv2.contourArea(raw)
        if cv2.contourArea(hole) < 0.005 * outer_area:
            continue
        hpts = resample_closed([(float(x), float(y)) for x, y in hole], 3.0)
        # Inner holes in y-down image convention have the opposite signed
        # area to the outer contour, so reversing them equalises sign.
        if signed_area(hpts) > 0:
            hpts.reverse()
        holes.append(hpts)
    write_module(points, holes, args.letter, args.description, Path(args.output))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    print(
        f"component={component} bbox={bbox[:4]} area={bbox[4]} "
        f"trace pts={len(points)} bbox=({min(xs):.0f},{min(ys):.0f},{max(xs):.0f},{max(ys):.0f}) "
        f"area={abs(signed_area(points)):.0f} holes={len(holes)} wrote={args.output}"
    )


if __name__ == "__main__":
    main()
