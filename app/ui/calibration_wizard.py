"""CalibrationWizard: 3-point click calibration using known car-meet landmarks.

Flow
----
1. Dialog shows the annotated calib_guide.png alongside step-by-step instructions.
2. For each landmark the user clicks "Start countdown" (5 s).
3. During the countdown they switch to the game, filter the map to Car Meets,
   and hover their mouse over the highlighted landmark icon.
4. When the countdown hits 0 the app captures pyautogui.position().
5. After all 3 captures the "Apply Calibration" button fits the affine transform.
"""

import logging
from typing import ClassVar

import pyautogui
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.calibration_landmarks import LANDMARKS, CalibrationLandmark
from app.core.calibrator import Calibrator
from app.utils.paths import asset

log = logging.getLogger(__name__)

_COUNTDOWN_SECS = 5


class CalibrationWizard(QDialog):
    """Step-by-step calibration wizard using 3 car-meet landmarks."""

    def __init__(self, calibrator: Calibrator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibrate — Car Meet Landmarks")
        self.resize(900, 580)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)

        self._calibrator = calibrator
        self._step = 0  # 0-based index into LANDMARKS
        self._screen_pts: list[QPointF] = []  # captured screen coords
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._countdown = 0

        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # Left: guide image
        guide_path = asset("calib_guide.png")
        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._img_label.setFixedWidth(340)
        if guide_path.exists():
            px = QPixmap(str(guide_path)).scaledToWidth(
                330, Qt.TransformationMode.SmoothTransformation
            )
            self._img_label.setPixmap(px)
        else:
            self._img_label.setText("calib_guide.png not found")
        root.addWidget(self._img_label)

        # Right: instructions + controls
        right = QVBoxLayout()
        right.setSpacing(12)

        # Title
        title = QLabel("Calibrate the map — 3 car-meet clicks")
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        title.setFont(f)
        right.addWidget(title)

        # Instructions
        instr = QLabel(
            "1. Open the in-game map in Forza Horizon 6.\n"
            "2. Use the map filter to show <b>Car Meets only</b>.\n"
            "3. For each step below, hover your mouse over the named icon\n"
            "   in the game, then click <b>Start countdown</b>.\n"
            "4. Switch to the game before the timer reaches 0."
        )
        instr.setTextFormat(Qt.TextFormat.RichText)
        instr.setWordWrap(True)
        right.addWidget(instr)

        right.addWidget(_hr())

        # Step cards
        self._cards: list[_StepCard] = []
        for lm in LANDMARKS:
            card = _StepCard(lm)
            self._cards.append(card)
            right.addWidget(card)

        right.addStretch()

        # Countdown display (hidden until active)
        self._countdown_label = QLabel("")
        f2 = QFont()
        f2.setPointSize(40)
        f2.setBold(True)
        self._countdown_label.setFont(f2)
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_label.setStyleSheet("color: #ff6600;")
        self._countdown_label.hide()
        right.addWidget(self._countdown_label)

        # Capture button
        self._btn_capture = QPushButton("Start 5-second countdown")
        self._btn_capture.setMinimumHeight(38)
        self._btn_capture.setStyleSheet("font-weight:bold; font-size:13px;")
        self._btn_capture.clicked.connect(self._start_countdown)
        right.addWidget(self._btn_capture)

        # Dialog buttons
        self._btn_box = QDialogButtonBox()
        self._btn_apply = self._btn_box.addButton(
            "Apply Calibration", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._btn_apply.setEnabled(False)
        self._btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self._btn_box.accepted.connect(self._apply)
        self._btn_box.rejected.connect(self.reject)
        right.addWidget(self._btn_box)

        root.addLayout(right)

    # ------------------------------------------------------------------
    # Step management
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        done = len(self._screen_pts)
        for i, card in enumerate(self._cards):
            if i < done:
                card.set_state("done")
            elif i == self._step:
                card.set_state("active")
            else:
                card.set_state("pending")

        all_done = done == len(LANDMARKS)
        self._btn_capture.setVisible(not all_done)
        self._btn_apply.setEnabled(all_done)
        if all_done:
            self._btn_capture.hide()
            self._countdown_label.hide()
        else:
            lm = LANDMARKS[self._step]
            self._btn_capture.setText(f"Start countdown — then hover over: {lm.name}")

    # ------------------------------------------------------------------
    # Countdown
    # ------------------------------------------------------------------

    def _start_countdown(self) -> None:
        self._countdown = _COUNTDOWN_SECS
        self._btn_capture.setEnabled(False)
        self._countdown_label.show()
        self._countdown_label.setText(str(self._countdown))
        self._timer.start()

    def _tick(self) -> None:
        self._countdown -= 1
        if self._countdown > 0:
            self._countdown_label.setText(str(self._countdown))
            return
        self._timer.stop()
        self._countdown_label.hide()
        self._capture_position()

    def _capture_position(self) -> None:
        sx, sy = pyautogui.position()
        lm = LANDMARKS[self._step]
        self._screen_pts.append(QPointF(sx, sy))
        self._cards[self._step].set_captured(sx, sy)
        log.info(
            "Calibration point %d captured: landmark=%s screen=(%d,%d) ref=(%d,%d)",
            self._step + 1,
            lm.name,
            sx,
            sy,
            lm.ref_x,
            lm.ref_y,
        )
        self._step += 1
        self._btn_capture.setEnabled(True)
        self._refresh()

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _apply(self) -> None:
        ref_pts = [QPointF(lm.ref_x, lm.ref_y) for lm in LANDMARKS]
        self._calibrator.fit(ref_pts, self._screen_pts)
        log.info("Calibration applied with %d point pairs", len(ref_pts))
        self.accept()


# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------


class _StepCard(QFrame):
    """Displays one calibration step — pending / active / done."""

    _COLORS: ClassVar[dict[str, tuple[str, str]]] = {
        "pending": ("#555", "#888"),
        "active": ("#ff6600", "#fff"),
        "done": ("#3c3", "#fff"),
    }

    def __init__(self, lm: CalibrationLandmark, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._lm = lm
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        self._badge = QLabel(str(lm.id))
        self._badge.setFixedSize(28, 28)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setBold(True)
        self._badge.setFont(f)
        layout.addWidget(self._badge)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        self._name_lbl = QLabel(f"<b>{lm.name}</b>")
        self._name_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._hint_lbl = QLabel(lm.hint)
        self._hint_lbl.setStyleSheet("font-size:10px; color:#aaa;")
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._hint_lbl)
        layout.addLayout(text_col)

        layout.addStretch()
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#3c3; font-size:10px;")
        layout.addWidget(self._status_lbl)

        self.set_state("pending")

    def set_state(self, state: str) -> None:
        border_color, badge_fg = self._COLORS[state]
        self.setStyleSheet(f"QFrame {{ border: 1px solid {border_color}; border-radius:4px; }}")
        self._badge.setStyleSheet(
            f"background:{border_color}; color:{badge_fg}; border-radius:14px;"
        )

    def set_captured(self, sx: int, sy: int) -> None:
        self._status_lbl.setText(f"screen ({sx}, {sy})")
        self.set_state("done")


def _hr() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("color:#555;")
    return line
