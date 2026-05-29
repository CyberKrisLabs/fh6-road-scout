"""Tests for Detector: template loading, template matching, color heuristic."""

import numpy as np
import pytest

from app.core.detector import Detector

# ── Synthetic image fixtures ──────────────────────────────────────────────────


@pytest.fixture
def template_bgr() -> np.ndarray:
    """80x30 template: bright cyan stripe on dark background (has clear variance)."""
    img = np.zeros((30, 80, 3), dtype=np.uint8)
    img[8:22, 10:70] = (200, 200, 50)  # bright inner rectangle — gives variance
    return img


@pytest.fixture
def roi_with_template(template_bgr: np.ndarray) -> np.ndarray:
    """220x90 dark ROI with the template embedded at (10, 10)."""
    roi = np.zeros((90, 220, 3), dtype=np.uint8)
    th, tw = template_bgr.shape[:2]
    roi[10 : 10 + th, 10 : 10 + tw] = template_bgr
    return roi


@pytest.fixture
def roi_without_template() -> np.ndarray:
    """220x90 ROI filled with noise — no template pattern present."""
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 60, size=(90, 220, 3), dtype=np.uint8)


@pytest.fixture
def detector_with_template(template_bgr: np.ndarray, tmp_path) -> Detector:
    import cv2

    path = str(tmp_path / "template.png")
    cv2.imwrite(path, template_bgr)
    d = Detector()
    d.load_template(path)
    return d


# ── load_template ─────────────────────────────────────────────────────────────


class TestLoadTemplate:
    def test_valid_path_sets_template(self, detector_with_template: Detector) -> None:
        assert detector_with_template._template is not None

    def test_invalid_path_leaves_template_none(self) -> None:
        d = Detector()
        d.load_template("nonexistent.png")
        assert d._template is None

    def test_template_none_by_default(self) -> None:
        assert Detector()._template is None

    def test_constructor_path_loads_template(self, template_bgr: np.ndarray, tmp_path) -> None:
        import cv2

        path = str(tmp_path / "t.png")
        cv2.imwrite(path, template_bgr)
        d = Detector(template_path=path)
        assert d._template is not None


# ── _template_match ───────────────────────────────────────────────────────────


class TestTemplateMatch:
    def test_no_template_returns_zero(self, roi_with_template: np.ndarray) -> None:
        d = Detector()
        assert d._template_match(roi_with_template) == 0.0

    def test_matching_roi_returns_high_score(
        self, detector_with_template: Detector, roi_with_template: np.ndarray
    ) -> None:
        score = detector_with_template._template_match(roi_with_template)
        assert score >= 0.72

    def test_non_matching_roi_returns_low_score(
        self, detector_with_template: Detector, roi_without_template: np.ndarray
    ) -> None:
        score = detector_with_template._template_match(roi_without_template)
        assert score < 0.3

    def test_template_larger_than_roi_does_not_crash(self, template_bgr: np.ndarray) -> None:
        import cv2

        big_template = cv2.resize(template_bgr, (500, 200))
        small_roi = np.zeros((50, 100, 3), dtype=np.uint8)
        d = Detector()
        d._template = big_template
        score = d._template_match(small_roi)
        assert isinstance(score, float)

    def test_returns_float(
        self, detector_with_template: Detector, roi_with_template: np.ndarray
    ) -> None:
        assert isinstance(detector_with_template._template_match(roi_with_template), float)


# ── Color heuristic fixtures ──────────────────────────────────────────────────


@pytest.fixture
def teal_roi() -> np.ndarray:
    """ROI with a block of teal pixels (hue ~92, high sat/val in HSV)."""
    import cv2

    roi = np.zeros((90, 220, 3), dtype=np.uint8)
    # BGR teal: (180, 200, 30) → HSV ~(92, 230, 200) — inside hue 82-105 range
    roi[20:60, 50:170] = (180, 200, 30)
    return cv2.cvtColor(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV), cv2.COLOR_HSV2BGR)


@pytest.fixture
def no_teal_roi() -> np.ndarray:
    """ROI with only red pixels — no teal."""
    roi = np.zeros((90, 220, 3), dtype=np.uint8)
    roi[:, :] = (0, 0, 200)  # pure red
    return roi


# ── _color_heuristic ──────────────────────────────────────────────────────────


class TestColorHeuristic:
    def test_teal_roi_returns_score_above_threshold(self, teal_roi: np.ndarray) -> None:
        score = Detector()._color_heuristic(teal_roi)
        assert score > 0.02

    def test_no_teal_roi_returns_score_at_or_below_threshold(self, no_teal_roi: np.ndarray) -> None:
        score = Detector()._color_heuristic(no_teal_roi)
        assert score <= 0.02

    def test_returns_float(self, teal_roi: np.ndarray) -> None:
        assert isinstance(Detector()._color_heuristic(teal_roi), float)

    def test_empty_teal_roi_returns_zero(self) -> None:
        blank = np.zeros((90, 220, 3), dtype=np.uint8)
        assert Detector()._color_heuristic(blank) == 0.0


# ── is_fast_travel_visible ────────────────────────────────────────────────────


class TestIsFastTravelVisible:
    def _full_screen(self, roi: np.ndarray) -> np.ndarray:
        """Embed the ROI in a 1920x1080 screenshot at a known position."""
        screen = np.zeros((1080, 1920, 3), dtype=np.uint8)
        screen[0 : roi.shape[0], 0 : roi.shape[1]] = roi
        return screen

    def test_returns_true_when_template_matches(
        self,
        detector_with_template: Detector,
        roi_with_template: np.ndarray,
    ) -> None:
        screen = self._full_screen(roi_with_template)
        # Position cursor so the ROI region is captured
        detected, conf = detector_with_template.is_fast_travel_visible(screen, 110, 145)
        assert detected is True
        assert conf > 0.0

    def test_returns_true_when_teal_present(self, teal_roi: np.ndarray) -> None:
        screen = self._full_screen(teal_roi)
        detected, _conf = Detector().is_fast_travel_visible(screen, 110, 145)
        assert detected is True

    def test_returns_false_when_neither_passes(self, roi_without_template: np.ndarray) -> None:
        screen = self._full_screen(roi_without_template)
        detected, _ = Detector().is_fast_travel_visible(screen, 110, 145)
        assert detected is False

    def test_returns_tuple_of_bool_and_float(self, roi_without_template: np.ndarray) -> None:
        screen = self._full_screen(roi_without_template)
        result = Detector().is_fast_travel_visible(screen, 110, 145)
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)

    def test_roi_outside_screen_returns_false(self) -> None:
        tiny_screen = np.zeros((10, 10, 3), dtype=np.uint8)
        detected, conf = Detector().is_fast_travel_visible(tiny_screen, 5, 5)
        assert detected is False
        assert conf == 0.0
