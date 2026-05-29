"""Tests for Calibrator: fit, transform, error cases."""

import pytest
from PySide6.QtCore import QPointF

from app.core.calibrator import Calibrator


def _pts(pairs: list[tuple[float, float]]) -> list[QPointF]:
    return [QPointF(x, y) for x, y in pairs]


@pytest.fixture
def calibrator() -> Calibrator:
    return Calibrator()


@pytest.fixture
def identity_calibrator() -> Calibrator:
    c = Calibrator()
    pts = _pts([(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)])
    c.fit(pts, pts)
    return c


@pytest.fixture
def translation_calibrator() -> Calibrator:
    """Screen = ref + (100, 50)."""
    c = Calibrator()
    ref = _pts([(0.0, 0.0), (200.0, 0.0), (0.0, 200.0)])
    screen = _pts([(100.0, 50.0), (300.0, 50.0), (100.0, 250.0)])
    c.fit(ref, screen)
    return c


class TestFit:
    def test_is_fitted_false_before_fit(self, calibrator: Calibrator) -> None:
        assert calibrator.is_fitted is False

    def test_is_fitted_true_after_fit(self, identity_calibrator: Calibrator) -> None:
        assert identity_calibrator.is_fitted is True

    def test_fewer_than_3_ref_points_raises(self, calibrator: Calibrator) -> None:
        with pytest.raises(ValueError):
            calibrator.fit(_pts([(0.0, 0.0), (1.0, 0.0)]), _pts([(0.0, 0.0), (1.0, 0.0)]))

    def test_fewer_than_3_screen_points_raises(self, calibrator: Calibrator) -> None:
        with pytest.raises(ValueError):
            calibrator.fit(
                _pts([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]),
                _pts([(0.0, 0.0), (1.0, 0.0)]),
            )

    def test_only_first_3_points_used(self, calibrator: Calibrator) -> None:
        many = _pts([(0.0, 0.0), (100.0, 0.0), (0.0, 100.0), (50.0, 50.0)])
        calibrator.fit(many, many)
        assert calibrator.is_fitted


class TestTransformErrors:
    def test_transform_before_fit_raises(self, calibrator: Calibrator) -> None:
        with pytest.raises(RuntimeError):
            calibrator.transform(10, 10)


class TestIdentityTransform:
    def test_origin_maps_to_origin(self, identity_calibrator: Calibrator) -> None:
        x, y = identity_calibrator.transform(0, 0)
        assert abs(x) <= 1 and abs(y) <= 1

    def test_arbitrary_point_maps_to_itself(self, identity_calibrator: Calibrator) -> None:
        x, y = identity_calibrator.transform(50, 70)
        assert abs(x - 50) <= 1 and abs(y - 70) <= 1


class TestTranslationTransform:
    def test_origin_maps_to_offset(self, translation_calibrator: Calibrator) -> None:
        x, y = translation_calibrator.transform(0, 0)
        assert abs(x - 100) <= 1 and abs(y - 50) <= 1

    def test_arbitrary_point_is_translated(self, translation_calibrator: Calibrator) -> None:
        x, y = translation_calibrator.transform(50, 60)
        assert abs(x - 150) <= 1 and abs(y - 110) <= 1


class TestScalingTransform:
    def test_double_scale_transform(self, calibrator: Calibrator) -> None:
        ref = _pts([(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)])
        screen = _pts([(0.0, 0.0), (200.0, 0.0), (0.0, 200.0)])
        calibrator.fit(ref, screen)
        x, y = calibrator.transform(50, 50)
        assert abs(x - 100) <= 1 and abs(y - 100) <= 1
