"""Detect the Fast Travel indicator (X button + 'Fast Travel' text) in a screenshot."""

import logging
from pathlib import Path

import cv2
import numpy as np

log = logging.getLogger(__name__)

# Search window around the road cursor position (px in each direction)
_SEARCH_HALF_W = 250
_SEARCH_HALF_H = 120


class FastTravelDetector:
    """
    Detects whether the Fast Travel indicator is visible near the road cursor.

    The indicator is a keyboard-style X button followed by 'Fast Travel' text,
    appearing on a semi-transparent background.  Detection uses template matching
    against a pre-captured X button crop.

    Usage::

        det = FastTravelDetector()
        det.load_template("assets/ft_indicator.png")
        if det.is_visible(screenshot, road_cursor_pos):
            ...  # road is discovered
    """

    def __init__(self, threshold: float = 0.82) -> None:
        self._threshold = threshold
        self._template: np.ndarray | None = None

    @property
    def is_loaded(self) -> bool:
        return self._template is not None

    def load_template(self, path: str) -> None:
        """Load the X button template.  Safe to call even if path does not exist."""
        p = Path(path)
        if not p.exists():
            log.warning("FastTravelDetector: template not found at %s", path)
            return
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is None:
            log.warning("FastTravelDetector: could not read template %s", path)
            return
        self._template = img
        log.info("FastTravelDetector: template loaded (%dx%d)", img.shape[1], img.shape[0])

    def is_visible(
        self,
        screenshot: np.ndarray,
        cursor_pos: tuple[int, int],
    ) -> bool:
        """
        Return True if the Fast Travel indicator appears near the road cursor.

        Args:
            screenshot:  BGR full-screen capture.
            cursor_pos:  (x, y) screen position of the road cursor.

        Returns:
            True if confidence ≥ threshold, False otherwise or when not loaded.
        """
        if self._template is None:
            return False

        cx, cy = cursor_pos
        h, w = screenshot.shape[:2]

        x1 = max(0, cx - _SEARCH_HALF_W)
        y1 = max(0, cy - _SEARCH_HALF_H)
        x2 = min(w, cx + _SEARCH_HALF_W)
        y2 = min(h, cy + _SEARCH_HALF_H)
        roi = screenshot[y1:y2, x1:x2]

        if roi.size == 0:
            return False

        gray: np.ndarray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if roi.ndim == 3 else roi
        th, tw = self._template.shape[:2]

        if gray.shape[0] < th or gray.shape[1] < tw:
            return False

        result: np.ndarray = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
        _, best, _, _ = cv2.minMaxLoc(result)

        log.debug("FastTravelDetector: best match=%.3f (threshold=%.3f)", best, self._threshold)
        return float(best) >= self._threshold
