"""Tests for RoadSampler: road_mask, skeletonize, sample."""

import itertools
from unittest.mock import patch

import numpy as np
import pytest

from app.core.road_sampler import RoadSampler, _morph_skeleton

# ── Synthetic image fixtures ─────────────────────────────────────────────────


@pytest.fixture
def black_image() -> np.ndarray:
    """100x100 all-black BGR image — no road pixels."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def white_line_image() -> np.ndarray:
    """100x100 BGR image with a 3-pixel white horizontal line at y=50."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[48:51, 10:90] = 255  # white road strip
    return img


@pytest.fixture
def colored_image() -> np.ndarray:
    """100x100 BGR image with fully-saturated red pixels — should be excluded."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = (0, 0, 255)  # pure red (high saturation in HSV)
    return img


@pytest.fixture
def sampler() -> RoadSampler:
    return RoadSampler()


# ── _road_mask ────────────────────────────────────────────────────────────────


class TestRoadMask:
    def test_returns_single_channel_uint8(
        self, sampler: RoadSampler, white_line_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(white_line_image)
        assert mask.ndim == 2
        assert mask.dtype == np.uint8

    def test_white_line_produces_nonzero_mask(
        self, sampler: RoadSampler, white_line_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(white_line_image)
        assert np.any(mask > 0)

    def test_white_line_mask_covers_line_region(
        self, sampler: RoadSampler, white_line_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(white_line_image)
        # Centre of the white strip should be non-zero
        assert mask[50, 50] > 0

    def test_black_image_gives_zero_mask(
        self, sampler: RoadSampler, black_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(black_image)
        assert np.all(mask == 0)

    def test_high_saturation_pixels_excluded(
        self, sampler: RoadSampler, colored_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(colored_image)
        assert np.all(mask == 0)

    def test_mask_values_are_only_0_or_255(
        self, sampler: RoadSampler, white_line_image: np.ndarray
    ) -> None:
        mask = sampler._road_mask(white_line_image)
        unique = np.unique(mask)
        assert set(unique.tolist()).issubset({0, 255})


# ── Synthetic skeleton fixtures ───────────────────────────────────────────────


@pytest.fixture
def thick_road_mask() -> np.ndarray:
    """100x100 mask with a 10-pixel wide horizontal white band."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[45:55, 10:90] = 255
    return mask


@pytest.fixture
def thin_road_mask() -> np.ndarray:
    """100x100 mask with a 1-pixel wide horizontal line (already a skeleton)."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[50, 10:90] = 255
    return mask


# ── _skeletonize ──────────────────────────────────────────────────────────────


class TestSkeletonize:
    def test_returns_single_channel_uint8(
        self, sampler: RoadSampler, thick_road_mask: np.ndarray
    ) -> None:
        skel = sampler._skeletonize(thick_road_mask)
        assert skel.ndim == 2
        assert skel.dtype == np.uint8

    def test_thick_band_becomes_thinner(
        self, sampler: RoadSampler, thick_road_mask: np.ndarray
    ) -> None:
        skel = sampler._skeletonize(thick_road_mask)
        # Input band is 10px tall; skeleton must be much thinner (allow <= 3 for morph fallback)
        mid_col = skel[:, 50]
        assert np.sum(mid_col > 0) <= 3

    def test_skeleton_is_non_zero_for_road_input(
        self, sampler: RoadSampler, thick_road_mask: np.ndarray
    ) -> None:
        skel = sampler._skeletonize(thick_road_mask)
        assert np.any(skel > 0)

    def test_empty_mask_gives_empty_skeleton(self, sampler: RoadSampler) -> None:
        empty = np.zeros((100, 100), dtype=np.uint8)
        skel = sampler._skeletonize(empty)
        assert np.all(skel == 0)

    def test_fallback_runs_when_ximgproc_missing(
        self, sampler: RoadSampler, thick_road_mask: np.ndarray
    ) -> None:
        import cv2

        with patch.object(cv2, "ximgproc", None, create=True):
            skel = sampler._skeletonize(thick_road_mask)
        assert np.any(skel > 0)

    def test_morph_skeleton_helper_matches_shape(self, thick_road_mask: np.ndarray) -> None:
        result = _morph_skeleton(thick_road_mask)
        assert result.shape == thick_road_mask.shape
        assert result.dtype == np.uint8


# ── _sample_skeleton & sample() ───────────────────────────────────────────────


@pytest.fixture
def line_skeleton() -> np.ndarray:
    """Single-pixel horizontal line skeleton at y=50, x=0..99."""
    skel = np.zeros((100, 100), dtype=np.uint8)
    skel[50, :] = 255
    return skel


class TestSampleSkeleton:
    def test_empty_skeleton_returns_empty_list(self, sampler: RoadSampler) -> None:
        empty = np.zeros((100, 100), dtype=np.uint8)
        assert sampler._sample_skeleton(empty) == []

    def test_returns_scan_points(self, sampler: RoadSampler, line_skeleton: np.ndarray) -> None:
        from app.models.scan_result import ScanPoint

        pts = sampler._sample_skeleton(line_skeleton)
        assert len(pts) > 0
        assert all(isinstance(p, ScanPoint) for p in pts)

    def test_points_are_at_least_interval_apart(
        self, sampler: RoadSampler, line_skeleton: np.ndarray
    ) -> None:
        pts = sampler._sample_skeleton(line_skeleton)
        for a, b in itertools.pairwise(pts):
            dist = ((a.ref_x - b.ref_x) ** 2 + (a.ref_y - b.ref_y) ** 2) ** 0.5
            assert dist >= sampler.interval - 0.5  # small float tolerance

    def test_all_points_state_is_unknown(
        self, sampler: RoadSampler, line_skeleton: np.ndarray
    ) -> None:
        from app.models.scan_result import DiscoveryState

        pts = sampler._sample_skeleton(line_skeleton)
        assert all(p.state == DiscoveryState.UNKNOWN for p in pts)


class TestSampleMethod:
    def test_invalid_path_returns_empty_list(self, sampler: RoadSampler) -> None:
        assert sampler.sample("nonexistent_image.png") == []

    def test_valid_road_image_returns_points(self, sampler: RoadSampler, tmp_path) -> None:
        import cv2

        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[48:52, 5:95] = 255
        path = str(tmp_path / "road.png")
        cv2.imwrite(path, img)
        pts = sampler.sample(path)
        assert len(pts) > 0

    def test_black_image_returns_empty_list(self, sampler: RoadSampler, tmp_path) -> None:
        import cv2

        img = np.zeros((100, 100, 3), dtype=np.uint8)
        path = str(tmp_path / "black.png")
        cv2.imwrite(path, img)
        assert sampler.sample(path) == []


# ── Configurable interval ─────────────────────────────────────────────────────


class TestInterval:
    def test_default_interval_is_15(self) -> None:
        assert RoadSampler().interval == 15

    def test_custom_interval_is_stored(self) -> None:
        assert RoadSampler(interval=20).interval == 20

    def test_interval_clamped_below_minimum(self) -> None:
        assert RoadSampler(interval=1).interval == 5

    def test_interval_clamped_above_maximum(self) -> None:
        assert RoadSampler(interval=999).interval == 50

    def test_interval_at_minimum_boundary(self) -> None:
        assert RoadSampler(interval=5).interval == 5

    def test_interval_at_maximum_boundary(self) -> None:
        assert RoadSampler(interval=50).interval == 50

    def test_smaller_interval_produces_more_points(self, line_skeleton: np.ndarray) -> None:
        dense = RoadSampler(interval=5)
        sparse = RoadSampler(interval=30)
        assert len(dense._sample_skeleton(line_skeleton)) > len(
            sparse._sample_skeleton(line_skeleton)
        )


class TestQSettingsInterval:
    def test_save_and_load_interval(self, qtbot) -> None:
        from app.core.road_sampler import load_interval, save_interval

        save_interval(25)
        assert load_interval() == 25

    def test_load_returns_default_when_unset(self, qtbot) -> None:
        from PySide6.QtCore import QSettings

        from app.core.road_sampler import load_interval

        QSettings("HorizonScout", "HorizonScout").remove("sampler/interval")
        assert load_interval() == 15
