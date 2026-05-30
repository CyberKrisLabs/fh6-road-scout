"""Tests for RoadCursorDetector — find two-ring road cursor in a screenshot."""

import numpy as np
import pytest

from app.core.road_cursor_detector import RoadCursorDetector


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_screenshot(
    size: tuple[int, int] = (640, 480),
    center: tuple[int, int] = (320, 240),
    outer_r: int = 28,
    inner_r: int = 17,
    bg: tuple[int, int, int] = (40, 80, 40),
) -> np.ndarray:
    """
    Synthetic game-map screenshot with a two-ring road cursor.

    Structure:  inner filled white circle  |  gap  |  outer white ring
    """
    import cv2  # local to keep module-level imports clean

    h, w = size[1], size[0]
    img = np.full((h, w, 3), bg, dtype=np.uint8)
    cx, cy = center
    cv2.circle(img, (cx, cy), outer_r, (255, 255, 255), thickness=4)
    cv2.circle(img, (cx, cy), inner_r, (255, 255, 255), thickness=-1)
    return img


def _make_blank(size: tuple[int, int] = (640, 480)) -> np.ndarray:
    return np.full((size[1], size[0], 3), (40, 80, 40), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Basic detection
# ---------------------------------------------------------------------------

class TestDetectPresence:
    def test_finds_cursor_on_dark_background(self) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(bg=(30, 30, 30))
        assert det.detect(img) is not None

    def test_finds_cursor_on_green_terrain(self) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(bg=(40, 90, 40))
        assert det.detect(img) is not None

    def test_finds_cursor_on_blue_water(self) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(bg=(100, 80, 30))
        assert det.detect(img) is not None

    def test_returns_none_on_blank_image(self) -> None:
        det = RoadCursorDetector()
        assert det.detect(_make_blank()) is None

    def test_returns_none_on_solid_white_image(self) -> None:
        det = RoadCursorDetector()
        img = np.full((480, 640, 3), 255, dtype=np.uint8)
        assert det.detect(img) is None


# ---------------------------------------------------------------------------
# Position accuracy
# ---------------------------------------------------------------------------

class TestDetectPosition:
    @pytest.mark.parametrize("cx,cy", [
        (320, 240),
        (100, 100),
        (550, 400),
        (50, 50),
    ])
    def test_returns_centre_within_tolerance(self, cx: int, cy: int) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(center=(cx, cy))
        result = det.detect(img)
        assert result is not None
        rx, ry = result
        assert abs(rx - cx) <= 10, f"x off by {abs(rx - cx)}"
        assert abs(ry - cy) <= 10, f"y off by {abs(ry - cy)}"

    def test_returns_tuple_of_ints(self) -> None:
        det = RoadCursorDetector()
        result = det.detect(_make_screenshot())
        assert result is not None
        x, y = result
        assert isinstance(x, int)
        assert isinstance(y, int)


# ---------------------------------------------------------------------------
# Search region
# ---------------------------------------------------------------------------

class TestSearchRegion:
    def test_finds_cursor_inside_region(self) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(center=(100, 100))
        result = det.detect(img, search_region=(50, 50, 120, 120))
        assert result is not None

    def test_misses_cursor_outside_region(self) -> None:
        det = RoadCursorDetector()
        img = _make_screenshot(center=(500, 400))
        # Search region excludes the cursor
        result = det.detect(img, search_region=(0, 0, 200, 200))
        assert result is None

    def test_coordinates_returned_in_full_image_space(self) -> None:
        """detect() always returns coords in full-screenshot space even with region."""
        det = RoadCursorDetector()
        img = _make_screenshot(center=(300, 300))
        result = det.detect(img, search_region=(200, 200, 200, 200))
        assert result is not None
        x, y = result
        # Should be near (300, 300) in full-image coords, not region-local
        assert abs(x - 300) <= 10
        assert abs(y - 300) <= 10


# ---------------------------------------------------------------------------
# Real sample images
# ---------------------------------------------------------------------------

class TestRealSamples:
    """Smoke tests against the actual game cursor crops."""

    SAMPLES = [
        "assets/cursor_samples/road_cursor_01_asphalt.png",
        "assets/cursor_samples/road_cursor_02_terrain.png",
        "assets/cursor_samples/road_cursor_03_dirt_road.png",
        "assets/cursor_samples/road_cursor_05_white_road.png",
        "assets/cursor_samples/road_cursor_06_dark_terrain.png",
    ]

    @pytest.mark.parametrize("path", SAMPLES)
    def test_detects_cursor_in_sample(self, path: str) -> None:
        import cv2

        img = cv2.imread(path)
        assert img is not None, f"Could not load {path}"
        det = RoadCursorDetector()
        result = det.detect(img)
        # Cursor should be roughly centred in each 60×60 crop
        assert result is not None, f"No cursor detected in {path}"
        x, y = result
        assert 15 <= x <= 45, f"x={x} not near centre in {path}"
        assert 15 <= y <= 45, f"y={y} not near centre in {path}"
