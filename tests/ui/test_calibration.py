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
