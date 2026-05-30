"""Scan road points and mark each as discovered or undiscovered."""

import logging
import threading
import time

import cv2
import mss
import numpy as np
import pyautogui
from PySide6.QtCore import QObject, Signal

from app.core.fast_travel_detector import FastTravelDetector
from app.core.road_cursor_detector import RoadCursorDetector
from app.models.scan_result import DiscoveryState, ScanPoint

log = logging.getLogger(__name__)

_CAPTURE_RADIUS = 300  # wider region so FT indicator is always in frame


class DiscoveryScanner(QObject):
    """
    Moves the mouse to each road point's screen position, captures a screenshot,
    and determines whether the Fast Travel indicator is visible.

    - FT visible  → DiscoveryState.DISCOVERED
    - FT absent   → DiscoveryState.UNDISCOVERED

    Points already in DISCOVERED or UNDISCOVERED state are skipped (resume support).

    Run inside a QThread:

        thread = QThread()
        scanner.moveToThread(thread)
        thread.started.connect(scanner.run)
        thread.start()
    """

    point_scanned = Signal(object)  # ScanPoint with updated state
    progress = Signal(int, int)      # (scanned, total)
    finished = Signal()

    def __init__(
        self,
        points: list[ScanPoint],
        cursor_detector: RoadCursorDetector,
        ft_detector: FastTravelDetector,
        dwell_ms: int = 80,
    ) -> None:
        super().__init__()
        self._points = points
        self._cursor_det = cursor_detector
        self._ft_det = ft_detector
        self._dwell = dwell_ms / 1000.0
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._pause_flag.set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def pause(self) -> None:
        self._pause_flag.clear()

    def resume(self) -> None:
        self._pause_flag.set()

    def stop(self) -> None:
        self._stop_flag.set()
        self._pause_flag.set()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        pending = [p for p in self._points if p.state == DiscoveryState.UNKNOWN]
        total = len(pending)
        done = 0

        for pt in pending:
            if self._stop_flag.is_set():
                break

            self._pause_flag.wait()
            if self._stop_flag.is_set():
                break

            pyautogui.moveTo(pt.ref_x, pt.ref_y)
            if self._dwell > 0:
                time.sleep(self._dwell)

            screenshot = self._capture(pt.ref_x, pt.ref_y)

            # Check fast travel indicator near the cursor position
            # For now use the target screen position as the cursor reference
            if self._ft_det.is_visible(screenshot, (pt.ref_x, pt.ref_y)):
                pt.state = DiscoveryState.DISCOVERED
            else:
                pt.state = DiscoveryState.UNDISCOVERED

            done += 1
            self.point_scanned.emit(pt)
            self.progress.emit(done, total)
            log.debug("Scanned (%d,%d) → %s", pt.ref_x, pt.ref_y, pt.state.value)

        log.info("Discovery scan complete: %d/%d points scanned", done, total)
        self.finished.emit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _capture(self, mx: int, my: int) -> np.ndarray:
        """Capture a wide region around (mx, my) so the FT indicator is in frame."""
        with mss.mss() as sct:
            region = {
                "left":   max(0, mx - _CAPTURE_RADIUS),
                "top":    max(0, my - _CAPTURE_RADIUS),
                "width":  _CAPTURE_RADIUS * 2,
                "height": _CAPTURE_RADIUS * 2,
            }
            shot = sct.grab(region)
            bgr: np.ndarray = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
            return bgr
