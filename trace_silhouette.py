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
- Extracts the largest external contour with OpenCV, resamples it uniformly
  to roughly 3 px of arc length, normalises winding so the area is positive
  in image space (y-down), and writes a Python module exporting
  ``YOGA_<LETTER>_OUTLINE_POINTS`` plus an empty ``YOGA_<LETTER>_HOLES`` list.
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
    """Return a uint8 binary mask (255 = foreground) using Otsu on luminance."""
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
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
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


def trace_exterior(canvas: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(
        canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE,
    )
    if not contours:
        raise SystemExit("no external contour after resampling")
    contour = max(contours, key=cv2.contourArea)
    return contour[:, 0, :].astype(np.float64)


def write_module(
    points: list[tuple[float, float]],
    letter: str,
    description: str,
    output: Path,
) -> None:
    letter = letter.upper()
    text_lines = [
        '"""' + description.strip(),
        '"""',
        "",
        f"YOGA_{letter}_OUTLINE_POINTS = [",
    ]
    text_lines.extend(f"    ({px:.2f}, {py:.2f})," for px, py in points)
    text_lines.extend(["]", "", f"YOGA_{letter}_HOLES = [", "]", ""])
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
    raw = trace_exterior(canvas)
    points = resample_closed([(float(x), float(y)) for x, y in raw], 3.0)
    if signed_area(points) > 0:
        points.reverse()
    write_module(points, args.letter, args.description, Path(args.output))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    print(
        f"component={component} bbox={bbox[:4]} area={bbox[4]} "
        f"trace pts={len(points)} bbox=({min(xs):.0f},{min(ys):.0f},{max(xs):.0f},{max(ys):.0f}) "
        f"area={abs(signed_area(points)):.0f} wrote={args.output}"
    )


if __name__ == "__main__":
    main()
