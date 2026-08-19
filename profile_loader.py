"""Load shin outline and profile from extracted files."""
import re
from pathlib import Path

def load_outline_from_svg(svg_path):
    """Load 2D outline points from an SVG file."""
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
    
    return points

# Load shin-only outline from SVG file
ROOT = Path(__file__).resolve().parent
SHIN_OUTLINE_POINTS = load_outline_from_svg(ROOT / 'shin_only.svg')

# Load the top edge profile
# This file contains SHIN_PROFILE_TOP which is the normalized top edge
exec(open(ROOT / 'shin_profile_top_new.py').read())
