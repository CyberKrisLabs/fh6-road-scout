"""Script to generate synthetic test fixture images (run once, not a test)."""

from pathlib import Path

import cv2
import numpy as np


def make_road_map(path: Path) -> None:
    """100x100 image: white horizontal road on black background."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.line(img, (5, 50), (94, 50), (255, 255, 255), 3)
    cv2.imwrite(str(path), img)


if __name__ == "__main__":
    out = Path(__file__).parent
    make_road_map(out / "road_map.png")
    print("Generated fixtures/road_map.png")
