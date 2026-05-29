"""Tests for CalibrationWizard: Phase 1 ref-map clicks, Phase 2 screen capture."""

import pytest
from PySide6.QtCore import QPointF, Qt
from pytestqt.qtbot import QtBot

from app.ui.calibration import CalibrationWizard
from app.ui.map_view import MapView


@pytest.fixture
def map_view(qtbot: QtBot) -> MapView:
    w = MapView()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def wizard(qtbot: QtBot, map_view: MapView) -> CalibrationWizard:
    dlg = CalibrationWizard(map_view)
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg


# ── Phase 1 — reference map clicks ───────────────────────────────────────────


class TestPhase1InitialState:
    def test_next_disabled_initially(self, wizard: CalibrationWizard) -> None:
        assert not wizard.btn_next.isEnabled()

    def test_count_label_shows_zero(self, wizard: CalibrationWizard) -> None:
        assert "0 / 3" in wizard.lbl_count.text()

    def test_back_disabled_initially(self, wizard: CalibrationWizard) -> None:
        assert not wizard.btn_back.isEnabled()

    def test_map_view_in_calibration_mode(
        self, wizard: CalibrationWizard, map_view: MapView
    ) -> None:
        assert map_view._calib_mode is True


class TestPhase1Clicks:
    def _click(self, map_view: MapView, x: float, y: float) -> None:
        map_view.calibration_click.emit(QPointF(x, y))

    def test_one_click_updates_count(self, wizard: CalibrationWizard, map_view: MapView) -> None:
        self._click(map_view, 10.0, 20.0)
        assert "1 / 3" in wizard.lbl_count.text()

    def test_two_clicks_still_disables_next(
        self, wizard: CalibrationWizard, map_view: MapView
    ) -> None:
        self._click(map_view, 10.0, 10.0)
        self._click(map_view, 20.0, 20.0)
        assert not wizard.btn_next.isEnabled()

    def test_three_clicks_enables_next(self, wizard: CalibrationWizard, map_view: MapView) -> None:
        for i in range(3):
            self._click(map_view, float(i * 10), float(i * 10))
        assert wizard.btn_next.isEnabled()

    def test_three_clicks_count_label(self, wizard: CalibrationWizard, map_view: MapView) -> None:
        for i in range(3):
            self._click(map_view, float(i * 10), float(i * 10))
        assert "3 / 3" in wizard.lbl_count.text()

    def test_extra_clicks_ignored_after_3(
        self, wizard: CalibrationWizard, map_view: MapView
    ) -> None:
        for i in range(5):
            self._click(map_view, float(i * 10), float(i * 10))
        assert len(wizard._ref_points) == 3


class TestPhase1Back:
    def test_back_resets_ref_points(self, wizard: CalibrationWizard, map_view: MapView) -> None:
        map_view.calibration_click.emit(QPointF(5.0, 5.0))
        map_view.calibration_click.emit(QPointF(15.0, 15.0))
        map_view.calibration_click.emit(QPointF(25.0, 25.0))
        wizard.btn_next.click()  # advance to phase 2
        wizard.btn_back.click()  # go back
        assert len(wizard._ref_points) == 0

    def test_back_disables_next(self, wizard: CalibrationWizard, map_view: MapView) -> None:
        for i in range(3):
            map_view.calibration_click.emit(QPointF(float(i * 10), 0.0))
        wizard.btn_next.click()
        wizard.btn_back.click()
        assert not wizard.btn_next.isEnabled()


class TestPhase1Cancel:
    def test_cancel_disables_map_calibration_mode(
        self, wizard: CalibrationWizard, map_view: MapView, qtbot: QtBot
    ) -> None:
        qtbot.mouseClick(wizard.btn_cancel, Qt.MouseButton.LeftButton)
        assert map_view._calib_mode is False


# ── Phase 2 — screen point capture (P3-S5) ───────────────────────────────────


@pytest.fixture
def wizard_phase2(qtbot: QtBot, map_view: MapView) -> CalibrationWizard:
    """Wizard already advanced to Phase 2."""
    dlg = CalibrationWizard(map_view)
    qtbot.addWidget(dlg)
    dlg.show()
    for i in range(3):
        map_view.calibration_click.emit(QPointF(float(i * 10), 0.0))
    dlg.btn_next.click()
    return dlg


class TestPhase2InitialState:
    def test_finish_disabled_initially(self, wizard_phase2: CalibrationWizard) -> None:
        assert not wizard_phase2.btn_next.isEnabled()

    def test_count_label_shows_zero(self, wizard_phase2: CalibrationWizard) -> None:
        assert "0 / 3" in wizard_phase2.lbl_count.text()

    def test_back_is_enabled(self, wizard_phase2: CalibrationWizard) -> None:
        assert wizard_phase2.btn_back.isEnabled()


class TestPhase2Captures:
    def test_capture_increments_count(self, wizard_phase2: CalibrationWizard) -> None:
        wizard_phase2._on_screen_capture()
        assert "1 / 3" in wizard_phase2.lbl_count.text()

    def test_three_captures_enable_finish(self, wizard_phase2: CalibrationWizard) -> None:
        for _ in range(3):
            wizard_phase2._on_screen_capture()
        assert wizard_phase2.btn_next.isEnabled()

    def test_extra_captures_ignored(self, wizard_phase2: CalibrationWizard) -> None:
        for _ in range(5):
            wizard_phase2._on_screen_capture()
        assert len(wizard_phase2._screen_points) == 3


class TestPhase2Finish:
    def test_calibration_done_signal_emitted(
        self, wizard_phase2: CalibrationWizard, qtbot: QtBot
    ) -> None:
        for _ in range(3):
            wizard_phase2._on_screen_capture()
        with qtbot.waitSignal(wizard_phase2.calibration_done, timeout=500) as blocker:
            wizard_phase2.btn_next.click()
        ref_pts, screen_pts = blocker.args
        assert len(ref_pts) == 3
        assert len(screen_pts) == 3

    def test_signal_carries_correct_ref_points(
        self, wizard_phase2: CalibrationWizard, qtbot: QtBot, map_view: MapView
    ) -> None:
        for _ in range(3):
            wizard_phase2._on_screen_capture()
        with qtbot.waitSignal(wizard_phase2.calibration_done, timeout=500) as blocker:
            wizard_phase2.btn_next.click()
        ref_pts = blocker.args[0]
        assert ref_pts[0].x() == pytest.approx(0.0)
        assert ref_pts[1].x() == pytest.approx(10.0)
        assert ref_pts[2].x() == pytest.approx(20.0)


class TestFallbackButton:
    def test_fallback_button_shown_when_keyboard_missing(
        self, wizard_phase2: CalibrationWizard
    ) -> None:
        from unittest.mock import patch

        with patch.dict("sys.modules", {"keyboard": None}):
            wizard_phase2._install_hotkey()
        assert hasattr(wizard_phase2, "btn_capture")
