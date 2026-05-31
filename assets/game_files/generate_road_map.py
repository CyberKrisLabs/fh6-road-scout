"""Generate assets/road_map.png from assets/world_road_points.json.

Uses the same coordinate constants as app/utils/map_coords.py so that dots
placed at world_to_ref(x, z) land exactly on the drawn roads.

Run from the repo root:
    python assets/game_files/generate_road_map.py
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.utils.map_coords import (  # noqa: E402
    MAP_HEIGHT,
    MAP_WIDTH,
    WORLD_X_MAX,
    WORLD_X_MIN,
    WORLD_Z_MAX,
    WORLD_Z_MIN,
    world_to_ref,
)

WORLD_POINTS = ROOT / "assets" / "world_road_points.json"
OUT_PNG = ROOT / "assets" / "road_map.png"


def main() -> None:
    print(f"Loading {WORLD_POINTS} ...")
    with WORLD_POINTS.open() as f:
        data = json.load(f)

    points = data["points"]
    print(f"  {len(points):,} road points")
    print(f"  World X {WORLD_X_MIN} .. {WORLD_X_MAX}  Z {WORLD_Z_MIN} .. {WORLD_Z_MAX}")
    print(f"  Canvas {MAP_WIDTH} x {MAP_HEIGHT} px")

    # Dark background
    img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)
    img[:] = (18, 18, 24)  # near-black, slight blue tint

    # Draw each road point as a small bright dot
    dot_color = (255, 165, 30)  # orange (BGR)
    for pt in points:
        rx, ry = world_to_ref(pt["world_x"], pt["world_z"])
        if 0 <= rx < MAP_WIDTH and 0 <= ry < MAP_HEIGHT:
            cv2.circle(img, (rx, ry), 2, dot_color, -1)

    cv2.imwrite(str(OUT_PNG), img)
    size_kb = OUT_PNG.stat().st_size / 1024
    print(f"Saved -> {OUT_PNG}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
