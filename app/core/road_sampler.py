"""Road centerline sampler — stub; full implementation in P2-S1."""

import logging

from app.models.scan_result import ScanPoint

log = logging.getLogger(__name__)


class RoadSampler:
    def __init__(self, interval: int = 15) -> None:
        self.interval = interval

    def sample(self, image_path: str) -> list[ScanPoint]:
        """Return road sample points from a reference map image."""
        return []
