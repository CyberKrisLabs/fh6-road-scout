"""Extract road centerline sample points from a reference map image."""

import logging

import cv2
import numpy as np

from app.models.scan_result import DiscoveryState, ScanPoint

log = logging.getLogger(__name__)

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
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 0, _MIN_ROAD_BRIGHTNESS])
        upper = np.array([180, _MAX_ROAD_SATURATION, 255])
        mask = cv2.inRange(hsv, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return mask

    def _skeletonize(self, mask: np.ndarray) -> np.ndarray:
        """Thin the road mask to a single-pixel skeleton."""
        try:
            skeleton = cv2.ximgproc.thinning(  # type: ignore[attr-defined]
                mask,
                thinningType=cv2.ximgproc.THINNING_ZHANGSUEN,  # type: ignore[attr-defined]
            )
        except AttributeError:
            skeleton = _morph_skeleton(mask)
        return skeleton  # type: ignore[no-any-return]

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


def _morph_skeleton(img: np.ndarray) -> np.ndarray:
    """Pure-OpenCV iterative morphological thinning (no ximgproc required)."""
    img = img.copy()
    skel = np.zeros_like(img)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    for _ in range(100):
        eroded = cv2.erode(img, kernel)
        opened = cv2.dilate(eroded, kernel)
        diff = cv2.subtract(img, opened)
        skel = cv2.bitwise_or(skel, diff)
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break
    return skel
