#!/usr/bin/env python3
"""Trace the largest foreground silhouette into a resampled Python contour.

Used for A–Z except L. Otsu-threshold the raster, keep the largest component,
scale the longest side to 480 with a 16px margin, take the OpenCV exterior
contour, and resample it to about 3px. Writes OUTLINE_POINTS / HOLES to match
outline_points/. L was traced separately with VTracer 0.6.12.
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


def resample_closed(points: list[tuple[float, float]], spacing: float = 3.0) -> list[tuple[float, float]]:
    pts = np.asarray(points, dtype=np.float64)
    closed = np.vstack([pts, pts[0]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    keep = seg > 1e-9
    starts = closed[:-1][keep]
    ends = closed[1:][keep]
    lengths = seg[keep]
    cumulative = np.concatenate([[0.0], np.cumsum(lengths)])
    total = cumulative[-1]
    count = max(3, int(round(total / spacing)))
    distances = np.linspace(0.0, total, count, endpoint=False)
    out: list[tuple[float, float]] = []
    for distance in distances:
        idx = min(np.searchsorted(cumulative, distance, side="right") - 1, len(lengths) - 1)
        fraction = (distance - cumulative[idx]) / lengths[idx]
        point = starts[idx] + fraction * (ends[idx] - starts[idx])
        out.append((float(point[0]), float(point[1])))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("output")
    parser.add_argument("letter")
    parser.add_argument("description")
    args = parser.parse_args()

    gray = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise SystemExit(f"cannot read {args.image}")
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count < 2:
        raise SystemExit("no foreground component")
    component = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    body = np.where(labels == component, 255, 0).astype(np.uint8)

    x, y, width, height, body_area = stats[component]
    cropped = body[y:y + height, x:x + width]
    scale = 480.0 / max(width, height)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    resized = cv2.resize(cropped, (new_width, new_height), interpolation=cv2.INTER_AREA)
    _, resized = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
    canvas = np.zeros((new_height + 32, new_width + 32), dtype=np.uint8)
    canvas[16:16 + new_height, 16:16 + new_width] = resized

    contours, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea)
    points = [(float(p[0][0]), float(p[0][1])) for p in contour]
    points = resample_closed(points, 3.0)
    if signed_area(points) > 0:
        points.reverse()

    letter = args.letter.upper()
    description = args.description.strip()
    lines = [
        f'"""Traced silhouette outline for the {letter} glyph.',
        "",
        description,
        '"""',
        "",
        "OUTLINE_POINTS = [",
    ]
    lines.extend(f"    ({px:.2f}, {py:.2f})," for px, py in points)
    lines.extend(
        [
            "]",
            "",
            "HOLES = [",
            "]",
            "",
        ]
    )
    Path(args.output).write_text("\n".join(lines))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    print(f"components={count - 1} source_body_area={body_area}")
    print(
        f"outer pts={len(points)} bbox=({min(xs):.0f}, {min(ys):.0f}, "
        f"{max(xs):.0f}, {max(ys):.0f}) area={abs(signed_area(points)):.0f}"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
