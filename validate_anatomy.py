#!/usr/bin/env python3
"""Audit source-level body proportions in Posture Master.

The validator measures skeletal centerlines before outline expansion. A is the
baseline pose. Every other glyph is checked against its arm, leg, torso, and
head dimensions with a strict +/-5 percent tolerance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from generate_font import pose

ROOT = Path(__file__).resolve().parent
TOLERANCE = 0.05


def pct(value: float, target: float) -> float:
    return (value - target) / target * 100


def outside(value: float, target: float) -> bool:
    return abs(value - target) > target * TOLERANCE


def rounded(values: list[float]) -> list[float]:
    return [round(v, 1) for v in values]


def establish_baseline() -> dict[str, float]:
    entries = pose("A").anatomy
    limbs = [e for e in entries if e["part"] == "limb"]
    torsos = [e for e in entries if e["part"] == "torso"]
    heads = [e for e in entries if e["part"] == "head"]
    if len(limbs) != 4 or len(torsos) != 1 or len(heads) != 1:
        raise RuntimeError("A must expose exactly four limbs, one torso, and one head")

    # A is authored in this order: paired legs, torso/head, paired arms.
    legs, arms = limbs[:2], limbs[2:]
    return {
        "thigh": mean(float(e["segments"][0]) for e in legs),
        "calf": mean(float(e["segments"][1]) for e in legs),
        "leg_total": mean(float(e["length"]) for e in legs),
        "upper_arm": mean(float(e["segments"][0]) for e in arms),
        "forearm": mean(float(e["segments"][1]) for e in arms),
        "arm_total": mean(float(e["length"]) for e in arms),
        "torso": float(torsos[0]["length"]),
        "head": float(heads[0]["diameter"]),
    }


def audit_letter(letter: str, baseline: dict[str, float]) -> dict[str, Any]:
    entries = pose(letter).anatomy
    limbs = [e for e in entries if e["part"] == "limb"]
    torsos = [e for e in entries if e["part"] == "torso"]
    heads = [e for e in entries if e["part"] == "head"]
    composites = [e for e in entries if e["part"] == "composite_path"]
    issues: list[str] = []
    measured_limbs: list[dict[str, Any]] = []

    if len(limbs) != 4:
        issues.append(f"expected 4 measurable limbs; found {len(limbs)}")
    if len(torsos) != 1:
        issues.append(f"expected 1 measurable torso; found {len(torsos)}")
    if len(heads) != 1:
        issues.append(f"expected 1 head; found {len(heads)}")
    if composites:
        lengths = ", ".join(f"{float(e['length']):.1f}" for e in composites)
        issues.append(f"contains {len(composites)} unclassified composite body path(s): {lengths}")

    for index, entry in enumerate(limbs, 1):
        length = float(entry["length"])
        segments = [float(v) for v in entry["segments"]]
        arm_error = abs(pct(length, baseline["arm_total"]))
        leg_error = abs(pct(length, baseline["leg_total"]))
        kind = "arm" if arm_error <= leg_error else "leg"
        target_total = baseline[f"{kind}_total"]
        deviation = pct(length, target_total)
        item: dict[str, Any] = {
            "index": index,
            "classification": kind,
            "length": round(length, 2),
            "segments": rounded(segments),
            "deviation_percent": round(deviation, 2),
        }
        measured_limbs.append(item)

        if outside(length, target_total):
            issues.append(
                f"limb {index} ({kind}) total {length:.1f} is {deviation:+.1f}% from {target_total:.1f}"
            )
        if len(segments) != 2:
            issues.append(f"limb {index} has {len(segments)} skeletal segments; expected upper/lower pair")
        else:
            targets = (
                (baseline["upper_arm"], baseline["forearm"])
                if kind == "arm"
                else (baseline["thigh"], baseline["calf"])
            )
            names = ("upper arm", "forearm") if kind == "arm" else ("thigh", "calf")
            for segment, target, name in zip(segments, targets, names):
                if outside(segment, target):
                    issues.append(
                        f"limb {index} {name} {segment:.1f} is {pct(segment, target):+.1f}% from {target:.1f}"
                    )

    torso_values = [float(e["length"]) for e in torsos]
    for value in torso_values:
        if outside(value, baseline["torso"]):
            issues.append(
                f"torso {value:.1f} is {pct(value, baseline['torso']):+.1f}% from {baseline['torso']:.1f}"
            )
    head_values = [float(e["diameter"]) for e in heads]
    for value in head_values:
        if outside(value, baseline["head"]):
            issues.append(
                f"head {value:.1f} is {pct(value, baseline['head']):+.1f}% from {baseline['head']:.1f}"
            )

    # A person has two arms and two legs. Classification is based on the
    # nearest baseline and then checked against the strict threshold.
    arm_count = sum(e["classification"] == "arm" for e in measured_limbs)
    leg_count = sum(e["classification"] == "leg" for e in measured_limbs)
    if len(limbs) == 4 and (arm_count != 2 or leg_count != 2):
        issues.append(f"nearest-baseline classification gives {arm_count} arm(s) and {leg_count} leg(s)")

    return {
        "letter": letter,
        "status": "PASS" if not issues else "FAIL",
        "limbs": measured_limbs,
        "torso_lengths": rounded(torso_values),
        "head_diameters": rounded(head_values),
        "composite_path_lengths": rounded([float(e["length"]) for e in composites]),
        "issues": issues,
    }


def markdown_report(baseline: dict[str, float], results: list[dict[str, Any]]) -> str:
    passed = sum(r["status"] == "PASS" for r in results)
    failed = len(results) - passed
    lines = [
        "# Posture Master — Anatomical Consistency Audit",
        "",
        f"**Tolerance:** ±{TOLERANCE * 100:.0f}%  ",
        "**Baseline:** revised A forward-fold pose  ",
        f"**Result:** {passed} passed; {failed} flagged  ",
        "**Policy:** diagnostic only; exact 1782 pose construction takes priority where the two goals conflict.",
        "",
        "## Baseline measurements",
        "",
        "| Element | Baseline units |",
        "|---|---:|",
        f"| Thigh | {baseline['thigh']:.1f} |",
        f"| Calf | {baseline['calf']:.1f} |",
        f"| Whole leg | {baseline['leg_total']:.1f} |",
        f"| Upper arm | {baseline['upper_arm']:.1f} |",
        f"| Forearm | {baseline['forearm']:.1f} |",
        f"| Whole arm | {baseline['arm_total']:.1f} |",
        f"| Pelvis-to-shoulder torso/spine | {baseline['torso']:.1f} |",
        f"| Head diameter | {baseline['head']:.1f} |",
        "",
        "Measurements use source centerlines, not outline bounding boxes. No hidden foreshortening exemptions are applied.",
        "",
        "## A–Z summary",
        "",
        "| Glyph | Status | Limb totals | Torso | Head | Primary finding |",
        "|---|---|---|---:|---:|---|",
    ]
    for result in results:
        limb_text = ", ".join(
            f"{e['classification'][0].upper()} {e['length']:.1f}" for e in result["limbs"]
        ) or "—"
        torso = ", ".join(f"{v:.1f}" for v in result["torso_lengths"]) or "—"
        head = ", ".join(f"{v:.1f}" for v in result["head_diameters"]) or "—"
        finding = result["issues"][0] if result["issues"] else "Within tolerance"
        lines.append(
            f"| {result['letter']} | **{result['status']}** | {limb_text} | {torso} | {head} | {finding} |"
        )
    lines.extend(["", "## Detailed flags", ""])
    for result in results:
        if not result["issues"]:
            continue
        lines.append(f"### {result['letter']}")
        lines.extend(f"- {issue}" for issue in result["issues"])
        lines.append("")
    lines.extend(
        [
            "## Enforcement note",
            "",
            "For diagnostic CI, `python validate_anatomy.py --strict` exits non-zero while any glyph is outside tolerance. It is not the release gate for the historically faithful build: composite surreal constructions are intentionally not auto-exempted or normalized.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit 1 if any glyph fails")
    args = parser.parse_args()
    baseline = establish_baseline()
    results = [audit_letter(letter, baseline) for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    payload = {
        "tolerance_percent": TOLERANCE * 100,
        "baseline_glyph": "A",
        "baseline": {k: round(v, 3) for k, v in baseline.items()},
        "results": results,
    }
    (ROOT / "anatomy-validation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ROOT / "anatomy-validation.md").write_text(markdown_report(baseline, results), encoding="utf-8")
    passed = sum(r["status"] == "PASS" for r in results)
    print(f"Anatomy audit: {passed}/26 pass; {26 - passed}/26 flagged")
    print("Wrote anatomy-validation.md and anatomy-validation.json")
    if args.strict and passed != 26:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
