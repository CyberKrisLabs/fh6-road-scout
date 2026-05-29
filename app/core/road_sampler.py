"""Extract road centerline sample points from a reference map image."""

import logging

import cv2
import numpy as np
from PySide6.QtCore import QSettings

from app.models.scan_result import DiscoveryState, ScanPoint

log = logging.getLogger(__name__)

_SETTINGS_ORG = "HorizonScout"
_SETTINGS_APP = "HorizonScout"
_INTERVAL_KEY = "sampler/interval"

_DEFAULT_INTERVAL = 15
_MIN_ROAD_BRIGHTNESS = 180  # HSV Value threshold (0-255)
_MAX_ROAD_SATURATION = 60  # keep near-grey/white pixels only


class RoadSampler:
    def __init__(self, interval: int = _DEFAULT_INTERVAL) -> None:
        self.interval = max(5, min(50, interval))

    def sample(self, image_path: str) -> list[ScanPoint]:
        """Return evenly-spaced ScanPoints along road centrelines."""
        img = cv2.imread(image_path)
        if img is None:
            log.warning("Cannot read image: %s", image_path)
            return []
        mask = self._road_mask(img)
        skeleton = self._skeletonize(mask)
        return self._sample_skeleton(skeleton)

    # ------------------------------------------------------------------

    def _road_mask(self, bgr: np.ndarray) -> np.ndarray:
        """Binary mask: 255 where bright low-saturation (road-like) pixels are."""
        hsv: np.ndarray = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 0, _MIN_ROAD_BRIGHTNESS])
        upper = np.array([180, _MAX_ROAD_SATURATION, 255])
        mask: np.ndarray = cv2.inRange(hsv, lower, upper)
        kernel: np.ndarray = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened: np.ndarray = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        closed: np.ndarray = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
        return closed

    def _skeletonize(self, mask: np.ndarray) -> np.ndarray:
        """Thin the road mask to a single-pixel skeleton."""
        ximgproc = getattr(cv2, "ximgproc", None)
        thinned: np.ndarray
        if ximgproc is not None:
            thinned = ximgproc.thinning(mask, thinningType=ximgproc.THINNING_ZHANGSUEN)
            return thinned
        return _morph_skeleton(mask)

    def _sample_skeleton(self, skeleton: np.ndarray) -> list[ScanPoint]:
        """Sample points at least `interval` pixels apart along the skeleton."""
        ys, xs = np.where(skeleton > 0)
        if len(xs) == 0:
            return []

        coords = np.stack([xs, ys], axis=1)
        order = np.lexsort((coords[:, 0], coords[:, 1]))
        coords = coords[order]

        points: list[ScanPoint] = []
        last_pt = np.array([-9999, -9999])
        for coord in coords:
            if np.linalg.norm(coord.astype(float) - last_pt.astype(float)) >= self.interval:
                points.append(
                    ScanPoint(
                        ref_x=int(coord[0]),
                        ref_y=int(coord[1]),
                        state=DiscoveryState.UNKNOWN,
                    )
                )
                last_pt = coord

        return points


def save_interval(interval: int) -> None:
    """Persist the sample interval to QSettings."""
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    s.setValue(_INTERVAL_KEY, max(5, min(50, interval)))


def load_interval() -> int:
    """Load the sample interval from QSettings (default 15)."""
    s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
    return int(str(s.value(_INTERVAL_KEY, _DEFAULT_INTERVAL)))


def _morph_skeleton(img: np.ndarray) -> np.ndarray:
    """Pure-OpenCV iterative morphological thinning (no ximgproc required)."""
    img = img.copy()
    skel: np.ndarray = np.zeros_like(img)
    kernel: np.ndarray = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    for _ in range(100):
        eroded: np.ndarray = cv2.erode(img, kernel)
        opened: np.ndarray = cv2.dilate(eroded, kernel)
        diff: np.ndarray = cv2.subtract(img, opened)
        merged: np.ndarray = cv2.bitwise_or(skel, diff)
        skel = merged
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break
    return skel
