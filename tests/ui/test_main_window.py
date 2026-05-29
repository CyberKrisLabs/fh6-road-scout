"""Integration tests for MainWindow: wiring, load-map flow, window properties."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pytestqt.qtbot import QtBot

from app.ui.main_window import MainWindow

FIXTURES = Path(__file__).parent.parent / "fixtures"
ROAD_MAP = FIXTURES / "road_map.png"
MISSING_PATH = str(FIXTURES / "does_not_exist.png")


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


class TestWindowProperties:
    def test_title_is_horizon_scout(self, window: MainWindow) -> None:
        assert window.windowTitle() == "Horizon Scout"

    def test_initial_size(self, window: MainWindow) -> None:
        assert window.width() == 1280
        assert window.height() == 820

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

    def test_loading_valid_image_populates_session(self, window: MainWindow) -> None:
        from unittest.mock import patch

        from app.models.scan_result import ScanPoint

        fake_points = [ScanPoint(ref_x=i, ref_y=50) for i in range(5)]
        with patch("app.ui.main_window.RoadSampler.sample", return_value=fake_points):
            window._load_map(str(ROAD_MAP))
        assert window._session.total == 5

    def test_loading_valid_image_updates_map_view(self, window: MainWindow) -> None:
        window._load_map(str(ROAD_MAP))
        assert window._map_view._pixmap is not None


class TestWindowClose:
    def test_close_does_not_raise_without_scanner(self, window: MainWindow, qtbot: QtBot) -> None:
        window.close()  # must not raise

    def test_close_stops_scanner_if_running(self, window: MainWindow, qtbot: QtBot) -> None:
        from unittest.mock import MagicMock

        mock_scanner = MagicMock()
        window._scanner = mock_scanner
        window.close()
        mock_scanner.stop.assert_called_once()
