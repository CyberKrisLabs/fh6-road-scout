"""Affine calibrator: maps reference-map pixels to game screen coordinates."""

import json
import logging
from typing import Any

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QSettings

log = logging.getLogger(__name__)

_SETTINGS_ORG = "HorizonScout"
_SETTINGS_APP = "HorizonScout"
_MATRIX_KEY = "calibration/matrix"


class Calibrator:
    def __init__(self) -> None:
        self._matrix: np.ndarray | None = None  # 2x3 affine float64

    @property
    def is_fitted(self) -> bool:
        return self._matrix is not None

    def fit(self, ref_pts: list[QPointF], screen_pts: list[QPointF]) -> None:
        if len(ref_pts) < 3 or len(screen_pts) < 3:
            raise ValueError("Need at least 3 point pairs for affine calibration.")
        src = np.array([[p.x(), p.y()] for p in ref_pts[:3]], dtype=np.float32)
        dst = np.array([[p.x(), p.y()] for p in screen_pts[:3]], dtype=np.float32)
        self._matrix = cv2.getAffineTransform(src, dst)
        log.debug("Calibrator fitted")

    def transform(self, ref_x: int, ref_y: int) -> tuple[int, int]:
        if self._matrix is None:
            raise RuntimeError("Calibrator has not been fitted.")
        pt = np.array([[[ref_x, ref_y]]], dtype=np.float32)
        result = cv2.transform(pt, self._matrix)
        x, y = result[0][0]
        return round(float(x)), round(float(y))

    def map_screen_region(self) -> tuple[int, int, int, int] | None:
        """
        Return the approximate screen region (x, y, w, h) covered by the calibrated map.
        Used by RoadMapper to set the raster scan bounds.
        Returns None when not fitted.
        """
        if self._matrix is None:
            return None
        # Derive bounding box by transforming the four corners of a unit square
        # scaled to a typical full-map extent.  The actual extents come from the
        # calibration points so this is a reasonable approximation.
        corners_ref = np.array([[[0, 0]], [[3840, 0]], [[3840, 4096]], [[0, 4096]]],
                               dtype=np.float32)
        corners_screen = cv2.transform(corners_ref, self._matrix.astype(np.float32))
        pts = corners_screen[:, 0, :]
        x1, y1 = int(pts[:, 0].min()), int(pts[:, 1].min())
        x2, y2 = int(pts[:, 0].max()), int(pts[:, 1].max())
        return (x1, y1, x2 - x1, y2 - y1)

    def to_dict(self) -> dict[str, Any]:
        if self._matrix is None:
            return {}
        return {"matrix": self._matrix.tolist()}

    def from_dict(self, data: dict[str, Any]) -> None:
        m = data.get("matrix")
        if m:
            self._matrix = np.array(m, dtype=np.float64)


def save_calibration(calibrator: "Calibrator") -> None:
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    s.setValue(_MATRIX_KEY, json.dumps(calibrator.to_dict()))


def load_calibration(calibrator: "Calibrator") -> None:
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    raw = s.value(_MATRIX_KEY)
    if raw:
        calibrator.from_dict(json.loads(str(raw)))
