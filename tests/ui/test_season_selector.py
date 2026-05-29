"""Tests for season map selector: ScanPanel buttons, MainWindow auto-load, QSettings."""

from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings, Qt
from pytestqt.qtbot import QtBot

from app.ui.main_window import MainWindow
from app.ui.scan_panel import ScanPanel

SEASONS = ["spring", "summer", "autumn", "winter"]


@pytest.fixture
def panel(qtbot: QtBot) -> ScanPanel:
    w = ScanPanel()
    qtbot.addWidget(w)
    w.show()
    return w


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


# ── ScanPanel season buttons ──────────────────────────────────────────────────


class TestSeasonButtons:
    def test_has_season_selected_signal(self, panel: ScanPanel) -> None:
        assert hasattr(panel, "season_selected")

    def test_has_all_four_season_buttons(self, panel: ScanPanel) -> None:
        assert hasattr(panel, "btn_spring")
        assert hasattr(panel, "btn_summer")
        assert hasattr(panel, "btn_autumn")
        assert hasattr(panel, "btn_winter")

    def test_spring_button_emits_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.season_selected, timeout=500) as blocker:
            qtbot.mouseClick(panel.btn_spring, Qt.MouseButton.LeftButton)
        assert blocker.args == ["spring"]

    def test_summer_button_emits_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.season_selected, timeout=500) as blocker:
            qtbot.mouseClick(panel.btn_summer, Qt.MouseButton.LeftButton)
        assert blocker.args == ["summer"]

    def test_autumn_button_emits_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.season_selected, timeout=500) as blocker:
            qtbot.mouseClick(panel.btn_autumn, Qt.MouseButton.LeftButton)
        assert blocker.args == ["autumn"]

    def test_winter_button_emits_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.season_selected, timeout=500) as blocker:
            qtbot.mouseClick(panel.btn_winter, Qt.MouseButton.LeftButton)
        assert blocker.args == ["winter"]


# ── MainWindow season loading ─────────────────────────────────────────────────


class TestMainWindowSeasonLoad:
    def test_on_season_selected_loads_map(self, window: MainWindow, tmp_path) -> None:
        from PySide6.QtCore import Qt as QtCore_Qt
        from PySide6.QtGui import QPixmap

        # Create a small fake season map
        px = QPixmap(100, 100)
        px.fill(QtCore_Qt.GlobalColor.darkGreen)
        fake_map = str(tmp_path / "spring.jpg")
        px.save(fake_map)

        with patch("app.ui.main_window.MainWindow._season_map_path", return_value=fake_map):
            window._on_season_selected("spring")

        assert window._map_view._pixmap is not None

    def test_on_season_selected_persists_to_qsettings(
        self, window: MainWindow, tmp_path, qtbot
    ) -> None:
        from PySide6.QtCore import Qt as QtCore_Qt
        from PySide6.QtGui import QPixmap

        px = QPixmap(100, 100)
        px.fill(QtCore_Qt.GlobalColor.darkGreen)
        fake_map = str(tmp_path / "summer.jpg")
        px.save(fake_map)

        with patch("app.ui.main_window.MainWindow._season_map_path", return_value=fake_map):
            window._on_season_selected("summer")

        s = QSettings("HorizonScout", "HorizonScout")
        assert s.value("map/selected_season") == "summer"

    def test_qsettings_season_round_trip(self, window: MainWindow, qtbot) -> None:
        from app.ui.main_window import load_selected_season, save_selected_season

        save_selected_season("autumn")
        assert load_selected_season() == "autumn"

    def test_load_selected_season_default(self, qtbot) -> None:
        from app.ui.main_window import load_selected_season

        QSettings("HorizonScout", "HorizonScout").remove("map/selected_season")
        assert load_selected_season() == "spring"
