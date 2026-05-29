"""Export scan results as an annotated PNG overlay."""

import logging

import cv2

from app.models.scan_result import DiscoveryState, ScanPoint

log = logging.getLogger(__name__)

_DISC_COLOR = (80, 220, 100)  # BGR green
_UNDISC_COLOR = (50, 80, 255)  # BGR red-orange
_DOT_RADIUS = 6
_ALPHA_MAP = 0.4
_ALPHA_DOTS = 0.6


def export_overlay(ref_image_path: str, points: list[ScanPoint], output_path: str) -> None:
    """Write an annotated PNG blending the reference map with coloured dots."""
    img = cv2.imread(ref_image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read reference image: {ref_image_path}")

    overlay = img.copy()
    for pt in points:
        if pt.state == DiscoveryState.UNKNOWN:
            continue
        color = _DISC_COLOR if pt.state == DiscoveryState.DISCOVERED else _UNDISC_COLOR
        cv2.circle(overlay, (pt.ref_x, pt.ref_y), _DOT_RADIUS, color, -1)

    result = cv2.addWeighted(img, _ALPHA_MAP, overlay, _ALPHA_DOTS, 0)
    cv2.imwrite(output_path, result)
    log.info("Exported overlay to %s (%d points)", output_path, len(points))
