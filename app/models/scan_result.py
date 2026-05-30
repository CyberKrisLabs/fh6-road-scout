"""Core data models for scan points and sessions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DiscoveryState(Enum):
    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    UNDISCOVERED = "undiscovered"


class RoadType(Enum):
    ASPHALT  = "asphalt"   # white solid line
    TUNNEL   = "tunnel"    # white solid line with subtle black centre dots
    DIRT     = "dirt"      # orange solid line
    OFFROAD  = "offroad"   # orange dashed line
    ALLEYWAY = "alleyway"  # cyan thin dashed line


@dataclass
class ScanPoint:
    ref_x: int
    ref_y: int
    state: DiscoveryState = DiscoveryState.UNKNOWN
    confidence: float = 0.0
    road_type: RoadType = RoadType.ASPHALT


@dataclass
class ScanSession:
    points: list[ScanPoint] = field(default_factory=list)
    reference_map_path: str = ""
    calibration_data: dict[str, Any] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.points)

    @property
    def scanned(self) -> int:
        return sum(1 for p in self.points if p.state != DiscoveryState.UNKNOWN)

    @property
    def discovered(self) -> int:
        return sum(1 for p in self.points if p.state == DiscoveryState.DISCOVERED)

    @property
    def undiscovered(self) -> int:
        return sum(1 for p in self.points if p.state == DiscoveryState.UNDISCOVERED)
