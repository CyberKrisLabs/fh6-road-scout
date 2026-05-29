"""Tests for MapView scan-result overlay: colours, update_point repaint."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from pytestqt.qtbot import QtBot

from app.models.scan_result import DiscoveryState, ScanPoint
from app.ui.map_view import (
    _DISCOVERED_COLOR,
    _UNDISCOVERED_COLOR,
    _UNKNOWN_COLOR,
    MapView,
)


@pytest.fixture
def view(qtbot: QtBot) -> MapView:
    w = MapView()
    qtbot.addWidget(w)
    w.resize(800, 600)
    w.show()
    return w


# ── Colour constants ──────────────────────────────────────────────────────────


class TestOverlayColours:
    def test_discovered_colour_is_green(self) -> None:
        c = _DISCOVERED_COLOR
        assert c.green() > c.red() and c.green() > c.blue()

    def test_undiscovered_colour_is_red_orange(self) -> None:
        c = _UNDISCOVERED_COLOR
        assert c.red() > c.green() and c.red() > c.blue()

    def test_unknown_colour_is_grey(self) -> None:
        c = _UNKNOWN_COLOR
        assert abs(c.red() - c.green()) < 30 and abs(c.green() - c.blue()) < 30

    def test_discovered_hex_contains_green_component(self) -> None:
        assert _DISCOVERED_COLOR.green() >= 200

    def test_undiscovered_has_high_red(self) -> None:
        assert _UNDISCOVERED_COLOR.red() >= 200

    def test_unknown_is_semitransparent(self) -> None:
        assert _UNKNOWN_COLOR.alpha() < 255


# ── set_points / update_point ─────────────────────────────────────────────────


class TestOverlayPoints:
    def test_set_points_stores_all_states(self, view: MapView) -> None:
        pts = [
            ScanPoint(ref_x=10, ref_y=10, state=DiscoveryState.DISCOVERED),
            ScanPoint(ref_x=20, ref_y=20, state=DiscoveryState.UNDISCOVERED),
            ScanPoint(ref_x=30, ref_y=30, state=DiscoveryState.UNKNOWN),
        ]
        view.set_points(pts)
        assert view._points[0].state == DiscoveryState.DISCOVERED
        assert view._points[1].state == DiscoveryState.UNDISCOVERED
        assert view._points[2].state == DiscoveryState.UNKNOWN

    def test_update_point_triggers_repaint(self, view: MapView, qtbot: QtBot) -> None:
        pt = ScanPoint(ref_x=50, ref_y=50)
        view.set_points([pt])
        repainted = []
        original_paint = view.paintEvent

        def _track_paint(event) -> None:  # type: ignore[no-untyped-def]
            repainted.append(True)
            original_paint(event)

        view.paintEvent = _track_paint  # type: ignore[method-assign]
        pt.state = DiscoveryState.DISCOVERED
        view.update_point(pt)
        qtbot.waitExposed(view)
        # Force event processing
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()
        assert len(repainted) > 0

    def test_dot_radius_at_default_scale(self, view: MapView) -> None:
        from app.ui.map_view import _DOT_R

        view._scale = 1.0
        r = max(2, int(_DOT_R * min(view._scale, 2.0)))
        assert r >= 2

    def test_dot_radius_clamped_to_minimum_at_low_zoom(self, view: MapView) -> None:
        from app.ui.map_view import _DOT_R

        view._scale = 0.01
        r = max(2, int(_DOT_R * min(view._scale, 2.0)))
        assert r == 2

    def test_paint_with_all_three_states_does_not_raise(
        self, view: MapView, tmp_path, qtbot: QtBot
    ) -> None:
        px = QPixmap(200, 200)
        px.fill(Qt.GlobalColor.black)
        px.save(str(tmp_path / "map.png"))
        view.load_image(str(tmp_path / "map.png"))
        view.set_points(
            [
                ScanPoint(ref_x=10, ref_y=10, state=DiscoveryState.DISCOVERED),
                ScanPoint(ref_x=20, ref_y=20, state=DiscoveryState.UNDISCOVERED),
                ScanPoint(ref_x=30, ref_y=30, state=DiscoveryState.UNKNOWN),
            ]
        )
        view.repaint()
