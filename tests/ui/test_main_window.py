"""Integration tests for MainWindow: wiring, startup, window properties."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytestqt.qtbot import QtBot

from app.ui.main_window import MainWindow

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    # Suppress startup so tests begin with a clean, empty state
    with patch("app.ui.main_window.MainWindow._startup"):
        win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


class TestWindowProperties:
    def test_title_is_horizon_scout(self, window: MainWindow) -> None:
        assert window.windowTitle() == "Horizon Scout"

    def test_initial_size(self, window: MainWindow) -> None:
        assert window.width() >= 400
        assert window.height() >= 300

    def test_session_starts_empty(self, window: MainWindow) -> None:
        assert window._session.total == 0


class TestWorldRoadPointsLoading:
    def _make_world_json(self, tmp_path: Path, n: int = 3) -> Path:
        data = {
            "format": "world_road_points_v1",
            "points": [{"world_x": float(i * 100), "world_z": float(i * 200)} for i in range(n)],
        }
        p = tmp_path / "world_road_points.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_loads_points_into_session(self, window: MainWindow, tmp_path: Path) -> None:
        p = self._make_world_json(tmp_path, n=5)
        with patch("app.ui.main_window.asset", return_value=p):
            window._load_world_road_points()
        assert window._session.total == 5

    def test_points_have_ref_coords(self, window: MainWindow, tmp_path: Path) -> None:
        p = self._make_world_json(tmp_path, n=1)
        with patch("app.ui.main_window.asset", return_value=p):
            window._load_world_road_points()
        pt = window._session.points[0]
        assert isinstance(pt.ref_x, int)
        assert isinstance(pt.ref_y, int)

    def test_missing_file_leaves_session_empty(self, window: MainWindow, tmp_path: Path) -> None:
        nonexistent = tmp_path / "no_file.json"
        with patch("app.ui.main_window.asset", return_value=nonexistent):
            window._load_world_road_points()
        assert window._session.total == 0

    def test_successful_load_enables_start(self, window: MainWindow, tmp_path: Path) -> None:
        p = self._make_world_json(tmp_path, n=2)
        with patch("app.ui.main_window.asset", return_value=p):
            window._load_world_road_points()
        assert window._panel.btn_start.isEnabled()


class TestWindowClose:
    def test_close_does_not_raise_without_scanner(self, window: MainWindow, qtbot: QtBot) -> None:
        window.close()

    def test_close_stops_scanner_if_running(self, window: MainWindow, qtbot: QtBot) -> None:
        mock_scanner = MagicMock()
        window._scanner = mock_scanner
        window.close()
        mock_scanner.stop.assert_called_once()
