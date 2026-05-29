"""Tests for MapView widget: image loading, transforms, points, calibration."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPixmap
from pytestqt.qtbot import QtBot

from app.models.scan_result import DiscoveryState, ScanPoint
from app.ui.map_view import MapView


@pytest.fixture
def view(qtbot: QtBot) -> MapView:
    widget = MapView()
    qtbot.addWidget(widget)
    widget.resize(800, 600)
    widget.show()
    return widget


class TestLoadImage:
    def test_returns_false_for_missing_path(self, view: MapView) -> None:
        assert view.load_image("nonexistent_file.png") is False

    def test_returns_false_for_empty_path(self, view: MapView) -> None:
        assert view.load_image("") is False

    def test_returns_true_for_valid_pixmap(self, view: MapView, tmp_path) -> None:
        img_path = tmp_path / "test.png"
        px = QPixmap(100, 100)
        px.fill(Qt.GlobalColor.white)
        px.save(str(img_path))
        assert view.load_image(str(img_path)) is True

    def test_pixmap_stored_after_load(self, view: MapView, tmp_path) -> None:
        img_path = tmp_path / "test.png"
        px = QPixmap(100, 100)
        px.fill(Qt.GlobalColor.white)
        px.save(str(img_path))
        view.load_image(str(img_path))
        assert view._pixmap is not None
        assert not view._pixmap.isNull()

    def test_no_image_initially(self, view: MapView) -> None:
        assert view._pixmap is None


class TestTransforms:
    def test_img_to_widget_round_trips_via_widget_to_img(self, view: MapView) -> None:
        view._scale = 2.0
        view._offset = QPointF(100.0, 50.0)
        img_pt = QPointF(30.0, 40.0)
        widget_pt = view._img_to_widget(img_pt)
        recovered = view._widget_to_img(widget_pt)
        assert abs(recovered.x() - img_pt.x()) < 1e-9
        assert abs(recovered.y() - img_pt.y()) < 1e-9

    def test_img_to_widget_applies_scale_and_offset(self, view: MapView) -> None:
        view._scale = 2.0
        view._offset = QPointF(10.0, 20.0)
        result = view._img_to_widget(QPointF(5.0, 5.0))
        assert result.x() == pytest.approx(20.0)
        assert result.y() == pytest.approx(30.0)

    def test_widget_to_img_inverts_transform(self, view: MapView) -> None:
        view._scale = 0.5
        view._offset = QPointF(0.0, 0.0)
        result = view._widget_to_img(QPointF(10.0, 20.0))
        assert result.x() == pytest.approx(20.0)
        assert result.y() == pytest.approx(40.0)


class TestSetPoints:
    def test_stores_points(self, view: MapView) -> None:
        pts = [ScanPoint(ref_x=i, ref_y=0) for i in range(3)]
        view.set_points(pts)
        assert view._points == pts

    def test_replaces_previous_points(self, view: MapView) -> None:
        view.set_points([ScanPoint(ref_x=0, ref_y=0)])
        new_pts = [ScanPoint(ref_x=1, ref_y=1), ScanPoint(ref_x=2, ref_y=2)]
        view.set_points(new_pts)
        assert len(view._points) == 2


class TestCalibrationMode:
    def test_calibration_mode_off_by_default(self, view: MapView) -> None:
        assert view._calib_mode is False

    def test_set_calibration_mode_on(self, view: MapView) -> None:
        view.set_calibration_mode(True)
        assert view._calib_mode is True

    def test_set_calibration_mode_off(self, view: MapView) -> None:
        view.set_calibration_mode(True)
        view.set_calibration_mode(False)
        assert view._calib_mode is False

    def test_calibration_click_signal_emitted(self, view: MapView, qtbot: QtBot) -> None:
        view.set_calibration_mode(True)
        view._scale = 1.0
        view._offset = QPointF(0.0, 0.0)
        with qtbot.waitSignal(view.calibration_click, timeout=1000) as blocker:
            qtbot.mouseClick(view, Qt.MouseButton.LeftButton)
        assert blocker.signal_triggered

    def test_calibration_click_not_emitted_outside_calib_mode(
        self, view: MapView, qtbot: QtBot
    ) -> None:
        view.set_calibration_mode(False)
        with qtbot.assertNotEmitted(view.calibration_click):
            qtbot.mouseClick(view, Qt.MouseButton.LeftButton)


class TestJumpToPoint:
    def test_jump_does_nothing_without_image(self, view: MapView) -> None:
        initial_offset = QPointF(view._offset)
        view.jump_to_point(ScanPoint(ref_x=100, ref_y=100))
        assert view._offset == initial_offset

    def test_jump_changes_offset_with_image(self, view: MapView, tmp_path) -> None:
        img_path = tmp_path / "test.png"
        px = QPixmap(400, 400)
        px.fill(Qt.GlobalColor.white)
        px.save(str(img_path))
        view.load_image(str(img_path))
        offset_before = QPointF(view._offset)
        # Jump to a corner — far from the current centre — so offset must change
        view.jump_to_point(ScanPoint(ref_x=0, ref_y=0))
        assert view._offset != offset_before


class TestZoom:
    def _wheel(self, view: MapView, delta_y: int) -> None:
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QWheelEvent

        pos = QPointF(400.0, 300.0)
        event = QWheelEvent(
            pos,
            view.mapToGlobal(QPoint(400, 300)),
            QPoint(0, 0),
            QPoint(0, delta_y),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        view.wheelEvent(event)

    def test_scale_increases_on_scroll_up(self, view: MapView) -> None:
        initial_scale = view._scale
        self._wheel(view, 120)
        assert view._scale > initial_scale

    def test_scale_decreases_on_scroll_down(self, view: MapView) -> None:
        view._scale = 2.0
        self._wheel(view, -120)
        assert view._scale < 2.0

    def test_scale_clamped_at_max(self, view: MapView) -> None:
        view._scale = 49.9
        for _ in range(20):
            self._wheel(view, 120)
        assert view._scale <= 50.0

    def test_scale_clamped_at_min(self, view: MapView) -> None:
        view._scale = 0.06
        for _ in range(20):
            self._wheel(view, -120)
        assert view._scale >= 0.05


class TestCalibrationPoints:
    def test_stores_calibration_points(self, view: MapView) -> None:
        pts = [QPointF(10.0, 20.0), QPointF(30.0, 40.0)]
        view.set_calibration_points(pts)
        assert view._calib_points == pts

    def test_replaces_previous_calibration_points(self, view: MapView) -> None:
        view.set_calibration_points([QPointF(1.0, 1.0)])
        view.set_calibration_points([QPointF(2.0, 2.0), QPointF(3.0, 3.0)])
        assert len(view._calib_points) == 2


class TestPaint:
    def test_paint_does_not_raise_without_image(self, view: MapView) -> None:
        view.repaint()  # should not raise

    def test_paint_does_not_raise_with_points(self, view: MapView, tmp_path) -> None:
        img_path = tmp_path / "test.png"
        px = QPixmap(100, 100)
        px.fill(Qt.GlobalColor.white)
        px.save(str(img_path))
        view.load_image(str(img_path))
        view.set_points(
            [
                ScanPoint(ref_x=10, ref_y=10, state=DiscoveryState.UNKNOWN),
                ScanPoint(ref_x=20, ref_y=20, state=DiscoveryState.DISCOVERED),
                ScanPoint(ref_x=30, ref_y=30, state=DiscoveryState.UNDISCOVERED),
            ]
        )
        view.set_calibration_points([QPointF(50.0, 50.0)])
        view.repaint()  # should not raise
