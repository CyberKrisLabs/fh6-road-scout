"""Integration tests for MainWindow: wiring, load-map flow, window properties."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytestqt.qtbot import QtBot

from app.ui.main_window import MainWindow

FIXTURES = Path(__file__).parent.parent / "fixtures"
ROAD_MAP = FIXTURES / "road_map.png"
MISSING_PATH = str(FIXTURES / "does_not_exist.png")


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    # Suppress auto-load so tests start with a clean (unloaded) state
    with patch("app.ui.main_window.MainWindow._autoload_season"):
        win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


class TestWindowProperties:
    def test_title_is_horizon_scout(self, window: MainWindow) -> None:
        assert window.windowTitle() == "Horizon Scout"

    def test_initial_size(self, window: MainWindow) -> None:
        # Use sizeHint from the resize() call rather than actual rendered size,
        # which can be constrained by the CI screen resolution
        assert window.width() >= 400
        assert window.height() >= 300

    def test_session_starts_empty(self, window: MainWindow) -> None:
        assert window._session.total == 0


class TestLoadMap:
    def test_loading_invalid_path_does_not_crash(self, window: MainWindow) -> None:
        with patch("app.ui.main_window.QMessageBox.critical"):
            window._load_map(MISSING_PATH)  # must not raise

    def test_loading_invalid_path_leaves_start_disabled(self, window: MainWindow) -> None:
        with patch("app.ui.main_window.QMessageBox.critical"):
            window._load_map(MISSING_PATH)
        assert not window._panel.btn_start.isEnabled()

    def test_loading_valid_image_enables_start(self, window: MainWindow) -> None:
        window._load_map(str(ROAD_MAP))
        assert window._panel.btn_start.isEnabled()

    def test_loading_valid_image_enables_calibrate(self, window: MainWindow) -> None:
        window._load_map(str(ROAD_MAP))
        assert window._panel.btn_calibrate.isEnabled()

    def test_loading_valid_image_sets_ref_map_path(self, window: MainWindow) -> None:
        window._load_map(str(ROAD_MAP))
        assert window._ref_map_path == str(ROAD_MAP)

    def test_loading_valid_image_does_not_sample_roads(self, window: MainWindow) -> None:
        """Season maps are backgrounds only — road sampling must not run on load."""
        window._load_map(str(ROAD_MAP))
        assert window._session.total == 0  # no road points until road_points.json exists

    def test_loading_valid_image_updates_map_view(self, window: MainWindow) -> None:
        window._load_map(str(ROAD_MAP))
        assert window._map_view._pixmap is not None


class TestRoadPointsLoading:
    def test_road_points_loaded_from_json_when_present(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        road_pts = {
            "points": [
                {"x": 10, "y": 20, "state": "unknown", "conf": 0.0},
                {"x": 30, "y": 40, "state": "unknown", "conf": 0.0},
            ]
        }
        road_json = tmp_path / "road_points.json"
        road_json.write_text(json.dumps(road_pts), encoding="utf-8")
        with patch("app.ui.main_window.asset", return_value=road_json):
            window._try_load_road_points()
        assert window._session.total == 2

    def test_missing_road_points_file_leaves_session_empty(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        nonexistent = tmp_path / "no_road_points.json"
        with patch("app.ui.main_window.asset", return_value=nonexistent):
            window._try_load_road_points()
        assert window._session.total == 0


class TestWindowClose:
    def test_close_does_not_raise_without_scanner(self, window: MainWindow, qtbot: QtBot) -> None:
        window.close()  # must not raise

    def test_close_stops_scanner_if_running(self, window: MainWindow, qtbot: QtBot) -> None:
        from unittest.mock import MagicMock

        mock_scanner = MagicMock()
        window._scanner = mock_scanner
        window.close()
        mock_scanner.stop.assert_called_once()
