"""Fast Travel template capture wizard — guides the user to save ft_indicator.png."""

import logging

import cv2
import mss
import numpy as np
import pyautogui
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.paths import asset

log = logging.getLogger(__name__)

# Size of capture region around mouse (px)
_CAPTURE_W = 300
_CAPTURE_H = 100


class FTWizard(QDialog):
    """
    Guided workflow to capture the Fast Travel indicator template.

    Steps:
      1. User opens the in-game map and hovers over a discovered road.
      2. User presses F9 while this dialog is open.
      3. App captures a region around the cursor and saves it to assets/ft_indicator.png.
      4. User confirms the preview looks correct.
    """

    _COUNTDOWN_SECS = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Capture Fast Travel Template")
        self.setMinimumWidth(420)
        self._captured_img: np.ndarray | None = None
        self._out_path = str(asset("ft_indicator.png"))
        self._countdown_remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build_ui()
        self._setup_hotkey()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        instruction = QLabel(
            "<b>Step 1:</b> Switch to the game and open the world map.<br>"
            "<b>Step 2:</b> Hover the cursor over a road you have already discovered<br>"
            "   so the <i>Fast Travel</i> button is visible.<br>"
            "<b>Step 3:</b> Click <b>Start Capture</b> below, then switch to the game.<br>"
            "   The screenshot is taken automatically when the countdown ends.<br><br>"
            "The preview below will show what was captured."
        )
        instruction.setWordWrap(True)
        instruction.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(instruction)

        self._preview_label = QLabel("No capture yet.")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumHeight(80)
        self._preview_label.setStyleSheet("border: 1px solid grey; background: #1a1a1f;")
        layout.addWidget(self._preview_label)

        self._status_label = QLabel("Click 'Start Capture' when ready.")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        self._capture_btn = QPushButton("Start Capture (8s countdown)")
        self._capture_btn.clicked.connect(self._start_countdown)
        layout.addWidget(self._capture_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        buttons.accepted.connect(self._on_confirm)
        buttons.rejected.connect(self.reject)
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        layout.addWidget(buttons)

    def _setup_hotkey(self) -> None:
        pass  # no hotkey needed — countdown does the capture

    # ------------------------------------------------------------------
    # Countdown + capture
    # ------------------------------------------------------------------

    def _start_countdown(self) -> None:
        self._countdown_remaining = self._COUNTDOWN_SECS
        self._capture_btn.setEnabled(False)
        self._status_label.setText(
            f"Switch to the game NOW — capturing in {self._countdown_remaining}s…"
        )
        self._timer.start()

    def _tick(self) -> None:
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._status_label.setText(
                f"Switch to the game NOW — capturing in {self._countdown_remaining}s…"
            )
        else:
            self._timer.stop()
            self._capture()

    def _capture(self) -> None:
        mx, my = pyautogui.position()
        with mss.mss() as sct:
            region = {
                "left": max(0, mx - _CAPTURE_W // 2),
                "top":  max(0, my - _CAPTURE_H // 2),
                "width": _CAPTURE_W,
                "height": _CAPTURE_H,
            }
            shot = sct.grab(region)
        bgr: np.ndarray = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
        self._captured_img = bgr
        self._show_preview(bgr)
        self._status_label.setText("Captured! Check the preview looks correct, then click OK.")
        self._ok_btn.setEnabled(True)
        self._capture_btn.setEnabled(True)
        self._capture_btn.setText("Re-capture (8s countdown)")
        log.debug("FT template captured: %dx%d", bgr.shape[1], bgr.shape[0])

    def _show_preview(self, bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        from PySide6.QtGui import QImage  # avoid module-level import issue in tests
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(qimg).scaledToWidth(380, Qt.TransformationMode.SmoothTransformation)
        self._preview_label.setPixmap(px)

    def _on_confirm(self) -> None:
        if self._captured_img is None:
            return
        cv2.imwrite(self._out_path, self._captured_img)
        log.info("FT template saved to %s", self._out_path)
        self.accept()
