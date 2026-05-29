"""Tests for RoadSampler: road_mask, skeletonize, sample."""

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
