"""Hardcoded calibration landmarks extracted from route0.nt.

Each landmark is a named car-meet site visible on the FH6 in-game map.
The player can filter the map to show only Car Meet icons, making these
easy to click precisely.

ref_x / ref_y are computed at import time from the live map_coords constants
so they stay in sync if the canvas size is ever changed.
"""

from dataclasses import dataclass

from app.utils.map_coords import world_to_ref


@dataclass(frozen=True)
class CalibrationLandmark:
    id: int
    name: str
    hint: str
    world_x: float
    world_z: float
    ref_x: int
    ref_y: int


def _make(id: int, name: str, hint: str, world_x: float, world_z: float) -> CalibrationLandmark:
    rx, ry = world_to_ref(world_x, world_z)
    return CalibrationLandmark(
        id=id,
        name=name,
        hint=hint,
        world_x=world_x,
        world_z=world_z,
        ref_x=rx,
        ref_y=ry,
    )


LANDMARKS: list[CalibrationLandmark] = [
    _make(
        id=1,
        name="Okuibuki Car Meet",
        hint="Filter map to Car Meets — click the Okuibuki icon (upper area)",
        world_x=1076.676390,
        world_z=6270.772400,
    ),
    _make(
        id=2,
        name="Festival Car Meet",
        hint="Filter map to Car Meets — click the Festival icon (centre-left)",
        world_x=-1982.071722,
        world_z=-863.733710,
    ),
    _make(
        id=3,
        name="Daikoku Car Meet",
        hint="Filter map to Car Meets — click the Daikoku icon (southern coast)",
        world_x=-409.082064,
        world_z=-6541.234125,
    ),
]
