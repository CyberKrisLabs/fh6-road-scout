"""Orchestrate a raster scan to build road_points.json from the in-game map cursor."""

import logging

import cv2
import mss
import numpy as np
from PySide6.QtCore import QObject, Signal

from app.core.road_cursor_detector import RoadCursorDetector
from app.core.raster_scanner import RasterScanner
from app.core.session_store import SessionStore
from app.models.scan_result import DiscoveryState, RoadType, ScanPoint, ScanSession

log = logging.getLogger(__name__)

_CAPTURE_RADIUS = 80  # px around mouse to grab for detection


class RoadMapper(QObject):
    """
    Drives RasterScanner, detects the road cursor at each position, and accumulates
    road points.  Writes road_points.json when the scan finishes.

    Run inside a QThread:

        thread = QThread()
        mapper.moveToThread(thread)
        thread.started.connect(mapper.run)
        thread.start()
    """

    point_found = Signal(object)   # ScanPoint
    progress = Signal(int, int)     # (positions_done, total_positions)
    finished = Signal(int)          # total road points found

    def __init__(
        self,
        scanner: RasterScanner,
        detector: RoadCursorDetector,
        output_path: str,
        map_size: tuple[int, int] = (3840, 4096),
        dedup_radius: int = 15,
    ) -> None:
        super().__init__()
        self._scanner = scanner
        self._detector = detector
        self._output_path = output_path
        self._map_size = map_size
        self._dedup_radius = dedup_radius
        self._points: list[ScanPoint] = []
        self._done = False

    # ------------------------------------------------------------------
    # Public API (mirrors RasterScanner for pause/stop)
    # ------------------------------------------------------------------

    def pause(self) -> None:
        self._scanner.pause()

    def resume(self) -> None:
        self._scanner.resume()

    def stop(self) -> None:
        self._scanner.stop()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the mapping scan.  Call via QThread.started."""
        self._points = []
        self._scanner.position_ready.connect(self._on_position)
        self._scanner.progress.connect(self.progress)
        self._scanner.finished.connect(self._on_scan_done)
        self._scanner.run()

    # ------------------------------------------------------------------
    # Slots (called synchronously since scanner runs in same thread)
    # ------------------------------------------------------------------

    def _on_position(self, mx: int, my: int) -> None:
        screenshot = self._capture(mx, my)
        local_pos = self._detector.detect(screenshot)
        if local_pos is None:
            return

        # Convert local screenshot coordinates → screen coordinates → map coordinates
        screen_x = (mx - _CAPTURE_RADIUS) + local_pos[0]
        screen_y = (my - _CAPTURE_RADIUS) + local_pos[1]
        ref_x, ref_y = self._to_map_coords(screen_x, screen_y)

        if not self._is_new(ref_x, ref_y):
            return

        pt = ScanPoint(ref_x=ref_x, ref_y=ref_y, state=DiscoveryState.UNKNOWN,
                       road_type=RoadType.ASPHALT)
        self._points.append(pt)
        self.point_found.emit(pt)
        log.debug("Road point found: (%d, %d) — total %d", ref_x, ref_y, len(self._points))

    def _on_scan_done(self) -> None:
        self._save()
        total = len(self._points)
        log.info("Road mapping complete: %d points → %s", total, self._output_path)
        self.finished.emit(total)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _capture(self, mx: int, my: int) -> np.ndarray:
        """Capture a square region centred on (mx, my)."""
        with mss.mss() as sct:
            region = {
                "left":   mx - _CAPTURE_RADIUS,
                "top":    my - _CAPTURE_RADIUS,
                "width":  _CAPTURE_RADIUS * 2,
                "height": _CAPTURE_RADIUS * 2,
            }
            shot = sct.grab(region)
            bgr: np.ndarray = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
            return bgr

    def _to_map_coords(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        rx, ry, rw, rh = self._scanner._region
        map_w, map_h = self._map_size
        ref_x = int((screen_x - rx) / rw * map_w) if rw > 0 else screen_x
        ref_y = int((screen_y - ry) / rh * map_h) if rh > 0 else screen_y
        return ref_x, ref_y

    def _is_new(self, ref_x: int, ref_y: int) -> bool:
        for pt in self._points:
            if np.hypot(pt.ref_x - ref_x, pt.ref_y - ref_y) < self._dedup_radius:
                return False
        return True

    def _save(self) -> None:
        session = ScanSession(points=self._points)
        SessionStore.save(session, self._output_path)
