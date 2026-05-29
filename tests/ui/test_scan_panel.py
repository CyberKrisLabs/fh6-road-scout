"""Tests for ScanPanel: buttons, signals, enabled states, progress."""

import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from app.ui.scan_panel import ScanPanel


@pytest.fixture
def panel(qtbot: QtBot) -> ScanPanel:
    widget = ScanPanel()
    qtbot.addWidget(widget)
    widget.show()
    return widget


class TestInitialState:
    def test_width_is_fixed_at_210(self, panel: ScanPanel) -> None:
        assert panel.width() == 210

    def test_calibrate_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_calibrate.isEnabled()

    def test_start_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_start.isEnabled()

    def test_pause_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_pause.isEnabled()

    def test_stop_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_stop.isEnabled()

    def test_jump_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_jump.isEnabled()

    def test_export_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_export.isEnabled()

    def test_save_disabled_initially(self, panel: ScanPanel) -> None:
        assert not panel.btn_save.isEnabled()

    def test_load_enabled_initially(self, panel: ScanPanel) -> None:
        assert panel.btn_load.isEnabled()

    def test_load_session_enabled_initially(self, panel: ScanPanel) -> None:
        assert panel.btn_load_session.isEnabled()


class TestSetMapLoaded:
    def test_true_enables_calibrate(self, panel: ScanPanel) -> None:
        panel.set_map_loaded(True)
        assert panel.btn_calibrate.isEnabled()

    def test_true_enables_start(self, panel: ScanPanel) -> None:
        panel.set_map_loaded(True)
        assert panel.btn_start.isEnabled()

    def test_false_disables_calibrate(self, panel: ScanPanel) -> None:
        panel.set_map_loaded(True)
        panel.set_map_loaded(False)
        assert not panel.btn_calibrate.isEnabled()

    def test_false_disables_start(self, panel: ScanPanel) -> None:
        panel.set_map_loaded(True)
        panel.set_map_loaded(False)
        assert not panel.btn_start.isEnabled()


class TestSetScanRunning:
    def test_running_true_disables_load(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        assert not panel.btn_load.isEnabled()

    def test_running_true_disables_calibrate(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        assert not panel.btn_calibrate.isEnabled()

    def test_running_true_disables_start(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        assert not panel.btn_start.isEnabled()

    def test_running_true_enables_pause(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        assert panel.btn_pause.isEnabled()

    def test_running_true_enables_stop(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        assert panel.btn_stop.isEnabled()

    def test_running_false_re_enables_load(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        panel.set_scan_running(False)
        assert panel.btn_load.isEnabled()

    def test_running_false_disables_pause(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        panel.set_scan_running(False)
        assert not panel.btn_pause.isEnabled()

    def test_running_false_disables_stop(self, panel: ScanPanel) -> None:
        panel.set_scan_running(True)
        panel.set_scan_running(False)
        assert not panel.btn_stop.isEnabled()

    def test_paused_keeps_stop_enabled(self, panel: ScanPanel) -> None:
        panel.set_scan_running(False, paused=True)
        assert panel.btn_stop.isEnabled()


class TestUpdateProgress:
    def test_sets_bar_percentage(self, panel: ScanPanel) -> None:
        panel.update_progress(50, 100, 30, 20)
        assert panel.progress_bar.value() == 50

    def test_zero_total_gives_zero_percent(self, panel: ScanPanel) -> None:
        panel.update_progress(0, 0, 0, 0)
        assert panel.progress_bar.value() == 0

    def test_progress_label_text(self, panel: ScanPanel) -> None:
        panel.update_progress(3, 10, 2, 1)
        assert panel.lbl_progress.text() == "3 / 10 points"

    def test_discovered_label(self, panel: ScanPanel) -> None:
        panel.update_progress(5, 10, 4, 1)
        assert panel.lbl_discovered.text() == "4"

    def test_undiscovered_label(self, panel: ScanPanel) -> None:
        panel.update_progress(5, 10, 4, 1)
        assert panel.lbl_undiscovered.text() == "1"

    def test_total_label(self, panel: ScanPanel) -> None:
        panel.update_progress(5, 10, 4, 1)
        assert panel.lbl_total.text() == "10"

    def test_jump_enabled_when_undiscovered(self, panel: ScanPanel) -> None:
        panel.update_progress(5, 10, 4, 1)
        assert panel.btn_jump.isEnabled()

    def test_jump_disabled_when_no_undiscovered(self, panel: ScanPanel) -> None:
        panel.update_progress(5, 5, 5, 0)
        assert not panel.btn_jump.isEnabled()

    def test_export_enabled_when_scanned(self, panel: ScanPanel) -> None:
        panel.update_progress(1, 10, 1, 0)
        assert panel.btn_export.isEnabled()

    def test_save_enabled_when_scanned(self, panel: ScanPanel) -> None:
        panel.update_progress(1, 10, 1, 0)
        assert panel.btn_save.isEnabled()


class TestSetStatus:
    def test_sets_label_text(self, panel: ScanPanel) -> None:
        panel.set_status("Scanning...")
        assert panel.lbl_status.text() == "Scanning..."


class TestSignals:
    def test_load_map_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.load_map_requested, timeout=500):
            qtbot.mouseClick(panel.btn_load, Qt.MouseButton.LeftButton)

    def test_calibrate_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        panel.set_map_loaded(True)
        with qtbot.waitSignal(panel.calibrate_requested, timeout=500):
            qtbot.mouseClick(panel.btn_calibrate, Qt.MouseButton.LeftButton)

    def test_scan_start_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        panel.set_map_loaded(True)
        with qtbot.waitSignal(panel.scan_start_requested, timeout=500):
            qtbot.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    def test_scan_pause_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        panel.set_scan_running(True)
        with qtbot.waitSignal(panel.scan_pause_requested, timeout=500):
            qtbot.mouseClick(panel.btn_pause, Qt.MouseButton.LeftButton)

    def test_scan_stop_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        panel.set_scan_running(True)
        with qtbot.waitSignal(panel.scan_stop_requested, timeout=500):
            qtbot.mouseClick(panel.btn_stop, Qt.MouseButton.LeftButton)

    def test_load_session_signal(self, panel: ScanPanel, qtbot: QtBot) -> None:
        with qtbot.waitSignal(panel.load_session_requested, timeout=500):
            qtbot.mouseClick(panel.btn_load_session, Qt.MouseButton.LeftButton)
