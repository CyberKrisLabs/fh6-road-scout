"""Affine calibrator: maps reference-map pixels to game screen coordinates."""

import logging

import cv2
import numpy as np
from PySide6.QtCore import QPointF

log = logging.getLogger(__name__)


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
