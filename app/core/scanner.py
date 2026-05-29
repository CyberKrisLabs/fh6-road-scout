"""Scanner: QThread-based hover-capture-detect loop over road points."""

import logging
import time

import mss
import numpy as np
import pyautogui
from PySide6.QtCore import QObject, QSettings, Signal

from app.core.calibrator import Calibrator
from app.core.detector import Detector
from app.models.scan_result import DiscoveryState, ScanPoint

log = logging.getLogger(__name__)

_DEFAULT_HOVER_DELAY = 0.12
_BATCH_SIGNAL = 10
_SETTINGS_ORG = "HorizonScout"
_SETTINGS_APP = "HorizonScout"
_DELAY_KEY = "scanner/hover_delay"
_DELAY_MIN = 0.05
_DELAY_MAX = 1.0


class Scanner(QObject):
    point_scanned = Signal(ScanPoint)
    progress = Signal(int)
    finished = Signal()

    def __init__(
        self,
        points: list[ScanPoint],
        calibrator: Calibrator,
        ft_template_path: str = "",
        hover_delay: float = _DEFAULT_HOVER_DELAY,
    ) -> None:
        super().__init__()
        self._points = points
        self._calibrator = calibrator
        self._detector = Detector(ft_template_path)
        self._hover_delay = max(0.05, min(1.0, hover_delay))
        self._running = False
        self._paused = False

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._running = False
        self._paused = False

    # ------------------------------------------------------------------
    # Main loop (runs in QThread)
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._running = True
        pyautogui.FAILSAFE = True

        with mss.mss() as sct:
            monitor = sct.monitors[1]

            for i, point in enumerate(self._points):
                if not self._running:
                    break

                while self._paused and self._running:
                    time.sleep(0.05)

                if not self._running:
                    break

                if point.state != DiscoveryState.UNKNOWN:
                    if (i + 1) % _BATCH_SIGNAL == 0:
                        self.progress.emit(i + 1)
                    continue

                try:
                    sx, sy = self._calibrator.transform(point.ref_x, point.ref_y)
                except RuntimeError:
                    break

                pyautogui.moveTo(sx, sy, duration=0.0)
                time.sleep(self._hover_delay)

                raw = sct.grab(monitor)
                screen = np.frombuffer(raw.bgra, dtype=np.uint8).reshape(raw.height, raw.width, 4)
                screen_bgr = screen[:, :, :3]

                discovered, confidence = self._detector.is_fast_travel_visible(screen_bgr, sx, sy)
                point.state = (
                    DiscoveryState.DISCOVERED if discovered else DiscoveryState.UNDISCOVERED
                )
                point.confidence = confidence

                self.point_scanned.emit(point)
                if (i + 1) % _BATCH_SIGNAL == 0:
                    self.progress.emit(i + 1)

        total_scanned = sum(1 for p in self._points if p.state != DiscoveryState.UNKNOWN)
        self.progress.emit(total_scanned)
        self.finished.emit()


def save_hover_delay(delay: float) -> None:
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    s.setValue(_DELAY_KEY, max(_DELAY_MIN, min(_DELAY_MAX, delay)))


def load_hover_delay() -> float:
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    return float(str(s.value(_DELAY_KEY, _DEFAULT_HOVER_DELAY)))
