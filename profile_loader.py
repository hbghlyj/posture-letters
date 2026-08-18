"""Load foot and shin profiles from SVG files."""
import re
from pathlib import Path

def load_profile_from_svg(svg_path):
    """Load normalized profile points from an SVG file."""
    with open(svg_path) as f:
        svg = f.read()
    
    # Extract path d attribute
    match = re.search(r'd="([^"]+)"', svg)
    if not match:
        raise ValueError(f"No path found in {svg_path}")
    
    d = match.group(1)
    
    # Parse path commands
    points = []
    tokens = re.findall(r'[MLZ]|[-+]?\d*\.?\d+', d)
    i = 0
    while i < len(tokens):
        if tokens[i] == 'M' or tokens[i] == 'L':
            x = float(tokens[i+1])
            y = float(tokens[i+2])
            points.append((x, y))
            i += 3
        elif tokens[i] == 'Z':
            i += 1
        else:
            # Bare coordinate pair (continuation)
            x = float(tokens[i])
            y = float(tokens[i+1])
            points.append((x, y))
            i += 2
    
    # Normalize to 0-1 range
    xs = [x for x, y in points]
    ys = [y for x, y in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    normalized = []
    for x, y in points:
        nx = (x - x_min) / x_range
        ny = 1.0 - (y - y_min) / y_range  # Invert Y
        normalized.append((nx, ny))
    
    return normalized

# Load profiles from SVG files
ROOT = Path(__file__).resolve().parent
FOOT_PROFILE = load_profile_from_svg(ROOT / 'foot_outline.svg')
SHIN_PROFILE = load_profile_from_svg(ROOT / 'shin_outline.svg')

# Reorder to start at heel/knee
foot_heel_candidates = [(i, frac, height) for i, (frac, height) in enumerate(FOOT_PROFILE) 
                        if frac < 0.05 and height < 0.2]
if foot_heel_candidates:
    foot_heel_idx = min(foot_heel_candidates, key=lambda x: x[1] + x[2])[0]
    FOOT_PROFILE = FOOT_PROFILE[foot_heel_idx:] + FOOT_PROFILE[:foot_heel_idx]

shin_knee_candidates = [(i, frac, height) for i, (frac, height) in enumerate(SHIN_PROFILE) 
                        if frac < 0.15 and height < 0.15]
if shin_knee_candidates:
    shin_knee_idx = min(shin_knee_candidates, key=lambda x: x[1] + x[2])[0]
    SHIN_PROFILE = SHIN_PROFILE[shin_knee_idx:] + SHIN_PROFILE[:shin_knee_idx]
