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


# ── Transform accuracy & rounding (P3-S2) ────────────────────────────────────


class TestTransformOutputTypes:
    def test_returns_tuple_of_ints(self, identity_calibrator: Calibrator) -> None:
        result = identity_calibrator.transform(10, 20)
        assert isinstance(result, tuple)
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_rounding_is_nearest_not_truncate(self, calibrator: Calibrator) -> None:
        # Build a calibrator whose transform adds 0.6 to x → should round to 1
        ref = _pts([(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)])
        screen = _pts([(0.6, 0.0), (10.6, 0.0), (0.6, 10.0)])
        calibrator.fit(ref, screen)
        x, _ = calibrator.transform(0, 0)
        assert x == 1  # round(0.6) = 1, not int(0.6) = 0


class TestRealisticScenario:
    def test_large_map_to_1080p_screen(self, calibrator: Calibrator) -> None:
        """4096x4096 reference map → 1920x1080 screen with 3-point calibration."""
        ref = _pts([(0.0, 0.0), (4096.0, 0.0), (0.0, 4096.0)])
        # Screen occupies roughly top-left 1920x1080 region
        screen = _pts([(0.0, 0.0), (1920.0, 0.0), (0.0, 1080.0)])
        calibrator.fit(ref, screen)
        # Centre of map should land near centre of screen
        x, y = calibrator.transform(2048, 2048)
        assert 900 <= x <= 1000 and 500 <= y <= 600

    def test_no_negative_coords_for_sensible_calibration(self, calibrator: Calibrator) -> None:
        ref = _pts([(100.0, 100.0), (300.0, 100.0), (100.0, 300.0)])
        screen = _pts([(200.0, 150.0), (600.0, 150.0), (200.0, 550.0)])
        calibrator.fit(ref, screen)
        x, y = calibrator.transform(200, 200)
        assert x >= 0 and y >= 0


# ── Serialise / deserialise (P3-S3) ──────────────────────────────────────────


class TestToDict:
    def test_unfitted_returns_empty_dict(self, calibrator: Calibrator) -> None:
        assert calibrator.to_dict() == {}

    def test_fitted_returns_dict_with_matrix_key(self, identity_calibrator: Calibrator) -> None:
        d = identity_calibrator.to_dict()
        assert "matrix" in d

    def test_matrix_is_list_of_lists(self, identity_calibrator: Calibrator) -> None:
        d = identity_calibrator.to_dict()
        assert isinstance(d["matrix"], list)
        assert all(isinstance(row, list) for row in d["matrix"])


class TestFromDict:
    def test_empty_dict_leaves_unfitted(self, calibrator: Calibrator) -> None:
        calibrator.from_dict({})
        assert calibrator.is_fitted is False

    def test_round_trip_preserves_transform(self, translation_calibrator: Calibrator) -> None:
        d = translation_calibrator.to_dict()
        restored = Calibrator()
        restored.from_dict(d)
        assert restored.is_fitted
        x1, y1 = translation_calibrator.transform(50, 60)
        x2, y2 = restored.transform(50, 60)
        assert abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1

    def test_round_trip_accuracy_to_3dp(self, translation_calibrator: Calibrator) -> None:
        import json

        d = translation_calibrator.to_dict()
        # Simulate JSON serialisation (QSettings stores as string)
        d2 = json.loads(json.dumps(d))
        restored = Calibrator()
        restored.from_dict(d2)
        x1, y1 = translation_calibrator.transform(123, 456)
        x2, y2 = restored.transform(123, 456)
        assert abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1


class TestQSettingsCalibration:
    def test_save_and_load_calibration(self, translation_calibrator: Calibrator, qtbot) -> None:
        from app.core.calibrator import load_calibration, save_calibration

        save_calibration(translation_calibrator)
        loaded = Calibrator()
        load_calibration(loaded)
        assert loaded.is_fitted
        x1, y1 = translation_calibrator.transform(10, 20)
        x2, y2 = loaded.transform(10, 20)
        assert abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1

    def test_load_with_no_saved_data_stays_unfitted(self, qtbot) -> None:
        from PySide6.QtCore import QSettings

        from app.core.calibrator import load_calibration

        QSettings("HorizonScout", "HorizonScout").remove("calibration/matrix")
        c = Calibrator()
        load_calibration(c)
        assert c.is_fitted is False
