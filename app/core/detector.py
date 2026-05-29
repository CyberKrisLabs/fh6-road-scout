"""Detect the fast-travel hover indicator in a screen ROI."""

import logging

import cv2
import numpy as np

log = logging.getLogger(__name__)

_MATCH_THRESHOLD = 0.72
_ROI_W = 220
_ROI_H = 90
_ROI_OFFSET_Y = -100  # pixels above cursor centre


class Detector:
    def __init__(self, template_path: str = "") -> None:
        self._template: np.ndarray | None = None
        if template_path:
            self.load_template(template_path)

    def load_template(self, path: str) -> None:
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None:
            self._template = img
            log.debug("Loaded FT template: %s", path)
        else:
            log.warning("Could not load template: %s", path)

    def is_fast_travel_visible(
        self, screenshot: np.ndarray, cursor_x: int, cursor_y: int
    ) -> tuple[bool, float]:
        """Return (discovered, confidence) for the given screen capture."""
        roi = self._extract_roi(screenshot, cursor_x, cursor_y)
        if roi is None or roi.size == 0:
            return False, 0.0

        template_score = 0.0
        if self._template is not None:
            template_score = self._template_match(roi)
            if template_score >= _MATCH_THRESHOLD:
                return True, template_score

        color_score = self._color_heuristic(roi)
        if color_score > 0.02:
            return True, max(template_score, color_score)

        return False, max(template_score, color_score)

    # ------------------------------------------------------------------

    def _extract_roi(self, screen: np.ndarray, cx: int, cy: int) -> np.ndarray | None:
        h, w = screen.shape[:2]
        x1 = max(0, cx - _ROI_W // 2)
        y1 = max(0, cy + _ROI_OFFSET_Y - _ROI_H // 2)
        x2 = min(w, x1 + _ROI_W)
        y2 = min(h, y1 + _ROI_H)
        if x2 <= x1 or y2 <= y1:
            return None
        return screen[y1:y2, x1:x2]

    def _template_match(self, roi: np.ndarray) -> float:
        tmpl = self._template
        if tmpl is None:
            return 0.0
        th, tw = tmpl.shape[:2]
        rh, rw = roi.shape[:2]
        if rh < th or rw < tw:
            scale = min(rh / th, rw / tw) * 0.9
            tmpl = cv2.resize(tmpl, None, fx=scale, fy=scale)
            th, tw = tmpl.shape[:2]
        if rh < th or rw < tw:
            return 0.0
        result = cv2.matchTemplate(roi, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return float(max_val)

    def _color_heuristic(self, roi: np.ndarray) -> float:
        """Fraction of pixels in the teal/cyan range typical of FT indicators."""
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower = np.array([82, 140, 160])
        upper = np.array([105, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        return float(cv2.countNonZero(mask)) / roi.size
