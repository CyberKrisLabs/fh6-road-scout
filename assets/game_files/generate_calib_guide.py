"""Generate assets/calib_guide.png — annotated road map showing calibration points.

Run from the repo root:
    python assets/game_files/generate_calib_guide.py
"""

import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.utils.map_coords import world_to_ref  # noqa: E402

ROAD_MAP = ROOT / "assets" / "road_map.png"
OUT = ROOT / "assets" / "calib_guide.png"

# Named landmarks extracted from route0.nt — car meet sites visible on the
# in-game map as distinctive icons.
LANDMARKS = [
    {
        "id": 1,
        "name": "Okuibuki Car Meet",
        "world_x": 1076.676390,
        "world_z": 6270.772400,
        "hint": "Car meet icon — mountain area, mid-right of map",
    },
    {
        "id": 2,
        "name": "Festival Car Meet",
        "world_x": -1982.071722,
        "world_z": -863.733710,
        "hint": "Main Festival site — centre-left of map",
    },
    {
        "id": 3,
        "name": "Daikoku Car Meet",
        "world_x": -409.082064,
        "world_z": -6541.234125,
        "hint": "Daikoku car meet — southern coastal area",
    },
]


def main() -> None:
    img = cv2.imread(str(ROAD_MAP))
    if img is None:
        print(f"ERROR: could not load {ROAD_MAP}")
        sys.exit(1)

    for lm in LANDMARKS:
        rx, ry = world_to_ref(lm["world_x"], lm["world_z"])
        lm["ref_x"] = rx
        lm["ref_y"] = ry
        print(
            f"  #{lm['id']} {lm['name']}: world ({lm['world_x']:.1f}, {lm['world_z']:.1f})"
            f" -> pixel ({rx}, {ry})"
        )

    # Draw markers
    for lm in LANDMARKS:
        rx, ry = lm["ref_x"], lm["ref_y"]
        # Outer white ring
        cv2.circle(img, (rx, ry), 22, (255, 255, 255), 3)
        # Coloured fill
        colours = [(0, 120, 255), (0, 200, 80), (0, 80, 255)]  # BGR
        cv2.circle(img, (rx, ry), 18, colours[lm["id"] - 1], -1)
        # Number
        cv2.putText(
            img,
            str(lm["id"]),
            (rx - 7, ry + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        # Label below marker
        cv2.putText(
            img,
            lm["name"],
            (rx - 60, ry + 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

    cv2.imwrite(str(OUT), img)
    print(f"\nSaved -> {OUT}")
    print("\nCalibration points to hardcode:")
    for lm in LANDMARKS:
        print(
            f"  {lm['id']}: world_x={lm['world_x']}, world_z={lm['world_z']}"
            f"  ref=({lm['ref_x']},{lm['ref_y']})  — {lm['hint']}"
        )


if __name__ == "__main__":
    main()
