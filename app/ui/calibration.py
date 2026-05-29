"""CalibrationWizard: two-phase dialog to collect ref-map and screen points."""

import logging
from typing import Protocol

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)

NUM_POINTS = 3


class MapViewProtocol(Protocol):
    """Structural type for the map view dependency."""

    def set_calibration_mode(self, active: bool) -> None: ...
    def set_calibration_points(self, points: list[QPointF]) -> None: ...

    calibration_click: object  # Signal(QPointF)


class CalibrationWizard(QDialog):
    """Two-phase wizard: pick ref-map points then capture screen points."""

    calibration_done = Signal(list, list)  # ref_points, screen_points

    def __init__(self, map_view: "MapViewProtocol", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibration")
        self.setModal(True)
        self.setFixedWidth(420)
        self._map_view = map_view

        self._ref_points: list[QPointF] = []
        self._screen_points: list[QPointF] = []
        self._phase: str = "ref"
        self._keyboard_installed: bool = False

        self._build_ui()
        self._enter_ref_phase()

        self._map_view.calibration_click.connect(self._on_ref_click)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.lbl_phase = QLabel()
        self.lbl_phase.setProperty("class", "section-label")
        layout.addWidget(self.lbl_phase)

        self.lbl_instruction = QLabel()
        self.lbl_instruction.setWordWrap(True)
        layout.addWidget(self.lbl_instruction)

        self.lbl_count = QLabel()
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_count.setProperty("class", "stat-value")
        layout.addWidget(self.lbl_count)

        frame = QFrame()
        frame.setProperty("class", "stat-card")
        fl = QVBoxLayout(frame)
        self.lbl_points = QLabel()
        self.lbl_points.setProperty("class", "small-label")
        self.lbl_points.setWordWrap(True)
        fl.addWidget(self.lbl_points)
        layout.addWidget(frame)

        btn_row = QHBoxLayout()
        self.btn_back = QPushButton("Back")
        self.btn_back.clicked.connect(self._go_back)
        self.btn_next = QPushButton("Next")
        self.btn_next.setProperty("class", "primary-btn")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._go_next)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_next)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Phase management
    # ------------------------------------------------------------------

    def _enter_ref_phase(self) -> None:
        self._phase = "ref"
        self._ref_points = []
        self.lbl_phase.setText("Phase 1 of 2 — Reference Map Points")
        self.lbl_instruction.setText(
            f"Click {NUM_POINTS} recognizable landmarks on the map in the left panel "
            "(e.g. road intersections, town centres, coastline bends). "
            "These must match points you can find exactly in the game."
        )
        self._map_view.set_calibration_mode(True)
        self._map_view.set_calibration_points([])
        self._update_ui()
        self.btn_back.setEnabled(False)
        self.btn_next.setText("Next: Mark in-game points")

    def _enter_screen_phase(self) -> None:
        self._phase = "screen"
        self._screen_points = []
        self.lbl_phase.setText("Phase 2 of 2 — In-Game Screen Points")
        self.lbl_instruction.setText(
            f"The app will minimise in {NUM_POINTS} seconds. "
            "Move your mouse to each landmark in the same order and press F9."
        )
        self._map_view.set_calibration_mode(False)
        self._update_ui()
        self.btn_back.setEnabled(True)
        self.btn_next.setText("Finish")
        self.btn_next.setEnabled(False)
        QTimer.singleShot(3000, self._start_screen_capture)

    def _start_screen_capture(self) -> None:
        win = QApplication.activeWindow()
        if win:
            win.showMinimized()
        self._install_hotkey()

    def _install_hotkey(self) -> None:
        try:
            import keyboard

            keyboard.add_hotkey("F9", self._on_screen_capture)
            self._keyboard_installed = True
        except ImportError:
            self.lbl_instruction.setText(
                "Move your mouse to each landmark in order and click 'Capture Point'."
            )
            self.btn_capture = QPushButton("Capture Point (F9 fallback)")
            self.btn_capture.setProperty("class", "primary-btn")
            self.btn_capture.clicked.connect(self._on_screen_capture)
            layout = self.layout()
            if isinstance(layout, QVBoxLayout):
                layout.insertWidget(3, self.btn_capture)
            self._keyboard_installed = False
            win = QApplication.activeWindow()
            if win:
                win.showNormal()

    def _on_screen_capture(self) -> None:
        if len(self._screen_points) >= NUM_POINTS:
            return
        pos = QCursor.pos()
        self._screen_points.append(QPointF(pos))
        self._update_ui()
        if len(self._screen_points) == NUM_POINTS:
            if self._keyboard_installed:
                try:
                    import keyboard

                    keyboard.remove_hotkey("F9")
                except Exception:
                    pass
            win = QApplication.activeWindow()
            if win:
                win.showNormal()
            self.raise_()
            self.activateWindow()

    def _on_ref_click(self, img_pt: QPointF) -> None:
        if self._phase != "ref" or len(self._ref_points) >= NUM_POINTS:
            return
        self._ref_points.append(img_pt)
        self._map_view.set_calibration_points(self._ref_points)
        self._update_ui()

    def _update_ui(self) -> None:
        if self._phase == "ref":
            n = len(self._ref_points)
            self.lbl_count.setText(f"{n} / {NUM_POINTS} selected")
            pts_text = (
                "\n".join(
                    f"  Point {i + 1}: ({p.x():.0f}, {p.y():.0f})"
                    for i, p in enumerate(self._ref_points)
                )
                or "  None yet"
            )
            self.lbl_points.setText("Reference points:\n" + pts_text)
            self.btn_next.setEnabled(n == NUM_POINTS)
        else:
            n = len(self._screen_points)
            self.lbl_count.setText(f"{n} / {NUM_POINTS} captured")
            pts_text = (
                "\n".join(
                    f"  Point {i + 1}: ({p.x():.0f}, {p.y():.0f})"
                    for i, p in enumerate(self._screen_points)
                )
                or "  None yet"
            )
            self.lbl_points.setText("Screen points:\n" + pts_text)
            self.btn_next.setEnabled(n == NUM_POINTS)

    def _go_next(self) -> None:
        if self._phase == "ref":
            self._enter_screen_phase()
        else:
            self._map_view.set_calibration_mode(False)
            self.calibration_done.emit(self._ref_points, self._screen_points)
            self.accept()

    def _go_back(self) -> None:
        self._enter_ref_phase()

    def reject(self) -> None:
        self._map_view.set_calibration_mode(False)
        super().reject()
