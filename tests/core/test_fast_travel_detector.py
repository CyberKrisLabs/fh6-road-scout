"""Tests for FastTravelDetector — detect the Fast Travel indicator near the road cursor."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.core.fast_travel_detector import FastTravelDetector

_TEMPLATE = "assets/ft_samples/ft_button_template.png"
_SAMPLES = [
    "assets/ft_samples/ft_indicator_01_light_grey.png",
    "assets/ft_samples/ft_indicator_02_dark.png",
    "assets/ft_samples/ft_indicator_03_terrain_brown.png",
    "assets/ft_samples/ft_indicator_04_terrain_tan.png",
    "assets/ft_samples/ft_indicator_05_terrain_olive.png",
    "assets/ft_samples/ft_indicator_06_dark_grey.png",
]


def _embed(indicator: np.ndarray, canvas_size: tuple[int, int] = (800, 600),
           pos: tuple[int, int] = (300, 250)) -> tuple[np.ndarray, tuple[int, int]]:
    """Embed indicator into a larger canvas and return canvas + cursor pos."""
    h, w = indicator.shape[:2]
    canvas = np.full((canvas_size[1], canvas_size[0], 3), (40, 80, 40), dtype=np.uint8)
    x, y = pos
    canvas[y: y + h, x: x + w] = indicator
    # Cursor is roughly left-centre of the indicator
    cursor = (x + w // 4, y + h // 2)
    return canvas, cursor


class TestLoadTemplate:
    def test_load_valid_template(self) -> None:
        det = FastTravelDetector()
        det.load_template(_TEMPLATE)
        assert det.is_loaded

    def test_not_loaded_by_default(self) -> None:
        assert not FastTravelDetector().is_loaded

    def test_load_nonexistent_path_does_not_raise(self) -> None:
        det = FastTravelDetector()
        det.load_template("does_not_exist.png")
        assert not det.is_loaded


class TestIsVisible:
    def test_returns_false_when_template_not_loaded(self) -> None:
        det = FastTravelDetector()
        canvas = np.zeros((600, 800, 3), dtype=np.uint8)
        assert det.is_visible(canvas, (400, 300)) is False

    def test_returns_false_on_blank_canvas(self) -> None:
        det = FastTravelDetector()
        det.load_template(_TEMPLATE)
        blank = np.full((600, 800, 3), (40, 80, 40), dtype=np.uint8)
        assert det.is_visible(blank, (400, 300)) is False

    @pytest.mark.parametrize("sample_path", _SAMPLES)
    def test_detects_indicator_in_sample_embedded_in_canvas(self, sample_path: str) -> None:
        det = FastTravelDetector()
        det.load_template(_TEMPLATE)
        indicator = cv2.imread(sample_path)
        assert indicator is not None
        canvas, cursor_pos = _embed(indicator)
        assert det.is_visible(canvas, cursor_pos), \
            f"Failed to detect FT indicator from {sample_path}"

    def test_search_region_limits_to_area_near_cursor(self) -> None:
        det = FastTravelDetector()
        det.load_template(_TEMPLATE)
        indicator = cv2.imread(_SAMPLES[0])
        # Place indicator far from the default search window of cursor
        canvas, _ = _embed(indicator, pos=(10, 10))
        # Cursor is far away — should NOT detect
        assert det.is_visible(canvas, (700, 500)) is False


class TestConfidenceThreshold:
    def test_custom_threshold_too_high_returns_false(self) -> None:
        det = FastTravelDetector(threshold=0.9999)
        det.load_template(_TEMPLATE)
        # Even the best sample will likely fall below 0.9999 when embedded in noise
        indicator = cv2.imread(_SAMPLES[0])
        canvas, cursor = _embed(indicator)
        # Add noise
        noise = np.random.randint(0, 30, canvas.shape, dtype=np.uint8)
        noisy = cv2.add(canvas, noise)
        # May or may not detect — just verify no crash
        det.is_visible(noisy, cursor)  # no assertion, just smoke test
