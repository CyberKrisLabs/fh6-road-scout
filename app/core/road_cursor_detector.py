"""Detect the road-snapping cursor (two concentric white circles) in a screenshot."""

import logging

import cv2
import numpy as np

log = logging.getLogger(__name__)

# Hough circle detection parameters
_HOUGH_DP = 1
_HOUGH_MIN_DIST = 4      # minimum distance between detected circle centres
_HOUGH_PARAM1 = 40       # Canny high threshold
_HOUGH_PARAM2 = 16       # accumulator threshold — lower = more circles


class RoadCursorDetector:
    """
    Locates the road-snapping cursor in a screenshot.

    The road cursor consists of two concentric white circles:
      - Outer ring  (~28px radius at 1080p)
      - Inner filled circle (~17px radius)

    The background colour visible in the gap varies with map terrain, so detection
    is done purely from the circular white-ring structure using Hough circles.
    """

    def __init__(
        self,
        outer_radius_range: tuple[int, int] = (14, 42),
        inner_outer_ratio: float = 0.62,
        ratio_tolerance: float = 0.20,
        centre_tolerance: int = 10,
    ) -> None:
        self._outer_min, self._outer_max = outer_radius_range
        self._ratio = inner_outer_ratio
        self._ratio_tol = ratio_tolerance
        self._centre_tol = centre_tolerance

    def detect(
        self,
        screenshot: np.ndarray,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> tuple[int, int] | None:
        """
        Find the road cursor centre in the screenshot.

        Args:
            screenshot:    BGR (or grayscale) image — full screen or any crop.
            search_region: Optional (x, y, w, h) in full-image coordinates.
                           Restricts detection to that region.  Returned
                           coordinates are always in full-image space.

        Returns:
            (x, y) pixel centre of the road cursor, or None if not found.
        """
        if search_region is not None:
            rx, ry, rw, rh = search_region
            roi = screenshot[ry : ry + rh, rx : rx + rw]
            result = self._detect_in(roi)
            if result is None:
                return None
            return (result[0] + rx, result[1] + ry)
        return self._detect_in(screenshot)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _detect_in(self, img: np.ndarray) -> tuple[int, int] | None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        blurred: np.ndarray = cv2.GaussianBlur(gray, (3, 3), 1.0)

        raw = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=_HOUGH_DP,
            minDist=_HOUGH_MIN_DIST,
            param1=_HOUGH_PARAM1,
            param2=_HOUGH_PARAM2,
            minRadius=self._outer_min // 2,
            maxRadius=self._outer_max,
        )

        if raw is None:
            return None

        circles = np.round(raw[0]).astype(int)
        return self._best_concentric_pair(circles)

    def _best_concentric_pair(
        self, circles: np.ndarray
    ) -> tuple[int, int] | None:
        """
        Find the best pair of concentric circles matching the cursor geometry.

        Searches for one larger (outer ring) and one smaller (inner circle) with:
          - centres within self._centre_tol pixels of each other
          - radius ratio within self._ratio_tol of self._ratio
          - outer radius in self._outer_radius_range
        Returns the centre of the best-scoring outer circle.
        """
        best_score: float = -1.0
        best_centre: tuple[int, int] | None = None

        # Sort descending by radius so we check large circles first
        by_radius = sorted(circles, key=lambda c: -c[2])

        for a in by_radius:
            ax, ay, ar = int(a[0]), int(a[1]), int(a[2])
            if not (self._outer_min <= ar <= self._outer_max):
                continue
            for b in circles:
                bx, by_, br = int(b[0]), int(b[1]), int(b[2])
                if br >= ar:
                    continue
                dist = float(np.hypot(ax - bx, ay - by_))
                if dist > self._centre_tol:
                    continue
                ratio = br / ar
                ratio_err = abs(ratio - self._ratio)
                if ratio_err > self._ratio_tol:
                    continue
                # Score: larger outer radius is preferred; penalise centre offset
                score = float(ar) - dist * 0.5
                if score > best_score:
                    best_score = score
                    best_centre = (ax, ay)

        if best_centre is not None:
            log.debug("Road cursor detected at %s (score=%.1f)", best_centre, best_score)
        return best_centre
