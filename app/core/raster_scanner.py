"""Move the mouse in a grid pattern across a screen region."""

import logging
import threading
import time

import pyautogui
from PySide6.QtCore import QObject, Signal

log = logging.getLogger(__name__)


class RasterScanner(QObject):
    """
    Moves the mouse in a raster (column-by-column, top-to-bottom) pattern
    across a defined screen region and emits a signal after each dwell.

    Designed to run inside a QThread:

        thread = QThread()
        scanner.moveToThread(thread)
        thread.started.connect(scanner.run)
        thread.start()
    """

    position_ready = Signal(int, int)   # (x, y) screen coordinates after dwell
    progress = Signal(int, int)          # (positions_done, total_positions)
    finished = Signal()

    def __init__(
        self,
        region: tuple[int, int, int, int],
        step_px: int = 20,
        dwell_ms: int = 50,
    ) -> None:
        super().__init__()
        self._region = region
        self._step = max(1, step_px)
        self._dwell = dwell_ms / 1000.0
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._pause_flag.set()  # set = not paused; cleared = paused

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def total_positions(self) -> int:
        """Total number of grid positions in this scan."""
        _, _, rw, rh = self._region
        cols = rw // self._step + 1
        rows = rh // self._step + 1
        return cols * rows

    def run(self) -> None:
        """Execute the raster scan.  Call this via QThread.started."""
        rx, ry, rw, rh = self._region
        total = self.total_positions
        current = 0

        x = rx
        while x <= rx + rw:
            y = ry
            while y <= ry + rh:
                if self._stop_flag.is_set():
                    log.debug("RasterScanner stopped at (%d, %d)", x, y)
                    self.finished.emit()
                    return

                # Block here while paused (does not busy-wait)
                self._pause_flag.wait()

                if self._stop_flag.is_set():
                    self.finished.emit()
                    return

                pyautogui.moveTo(x, y)
                if self._dwell > 0:
                    time.sleep(self._dwell)

                current += 1
                self.position_ready.emit(x, y)
                self.progress.emit(current, total)

                y += self._step
            x += self._step

        log.info("RasterScanner finished: %d positions scanned", total)
        self.finished.emit()

    def pause(self) -> None:
        """Pause after the current position."""
        self._pause_flag.clear()
        log.debug("RasterScanner paused")

    def resume(self) -> None:
        """Resume a paused scan."""
        self._pause_flag.set()
        log.debug("RasterScanner resumed")

    def stop(self) -> None:
        """Stop the scan.  Safe to call from any thread."""
        self._stop_flag.set()
        self._pause_flag.set()  # unblock a paused scan so it can exit
        log.debug("RasterScanner stop requested")
