"""World-to-reference-map coordinate transform.

Road positions from assets/world_road_points.json are in game-world (X, Z).
This module converts them to pixel coordinates on assets/road_map.png using a
fixed linear transform.  The same constants are used when generating road_map.png
so dots always land exactly on the roads.
"""

# World bounds — padded slightly beyond the data range for visual breathing room
WORLD_X_MIN: float = -8100.0
WORLD_X_MAX: float = 11100.0
WORLD_Z_MIN: float = -9600.0
WORLD_Z_MAX: float = 20300.0

# Road map PNG canvas size in pixels
MAP_WIDTH: int = 1500
MAP_HEIGHT: int = 2336  # keeps the correct world aspect ratio


def world_to_ref(world_x: float, world_z: float) -> tuple[int, int]:
    """Convert game-world (X, Z) to road_map.png pixel (ref_x, ref_y)."""
    ref_x = int((world_x - WORLD_X_MIN) / (WORLD_X_MAX - WORLD_X_MIN) * MAP_WIDTH)
    ref_y = int((world_z - WORLD_Z_MIN) / (WORLD_Z_MAX - WORLD_Z_MIN) * MAP_HEIGHT)
    return ref_x, ref_y


def ref_to_world(ref_x: int, ref_y: int) -> tuple[float, float]:
    """Convert road_map.png pixel (ref_x, ref_y) to game-world (X, Z)."""
    world_x = ref_x / MAP_WIDTH * (WORLD_X_MAX - WORLD_X_MIN) + WORLD_X_MIN
    world_z = ref_y / MAP_HEIGHT * (WORLD_Z_MAX - WORLD_Z_MIN) + WORLD_Z_MIN
    return world_x, world_z
