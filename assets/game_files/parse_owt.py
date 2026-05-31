"""
Parse all Route*.owt files (FTWO binary format) to extract road waypoints.

FTWO record layout (56 bytes each, starting at offset 0x60):
  offset  0: float32 X  — world X coordinate
  offset  4: float32 Y  — elevation (ignored for 2-D map use)
  offset  8: float32 Z  — world Z coordinate
  offset 12: float32[3]  — tangent/direction vector
  offset 24: float32[3]  — secondary vector
  offset 36: float32     — accumulated distance along route
  offset 40: uint8[4]    — flags
  offset 44: uint32      — padding / secondary data
  offset 48: float32[2]  — curve data
  (total: 56 bytes)

The header (0x60 = 96 bytes) contains:
  offset 0x00: "FTWO" magic
  offset 0x24: uint32  waypoint count
"""

import json
import struct
from pathlib import Path

AI_TRACKS = Path(r"D:\SteamLibrary\steamapps\common\ForzaHorizon6\media\OpenWorld\Brio\AITracks")
OUT_JSON  = Path(__file__).parent / "owt_waypoints.json"
OUT_PNG   = Path(__file__).parent / "owt_preview.png"

MAGIC     = b"FTWO"
HDR_SIZE  = 0x60   # 96 bytes
STRIDE    = 56
COUNT_OFF = 0x24   # uint32 little-endian


def parse_owt(path: Path) -> list[tuple[float, float, float]]:
    """Return list of (X, Y, Z) tuples from a .owt file."""
    data = path.read_bytes()
    if data[:4] != MAGIC:
        return []

    count = struct.unpack_from("<I", data, COUNT_OFF)[0]
    # Validate: data must be large enough
    expected_end = HDR_SIZE + count * STRIDE
    if expected_end > len(data) + 64:  # allow small fuzz
        # Try alternative count at 0x50
        count2 = struct.unpack_from("<I", data, 0x50)[0]
        if HDR_SIZE + count2 * STRIDE <= len(data) + 64:
            count = count2

    points: list[tuple[float, float, float]] = []
    offset = HDR_SIZE
    for _ in range(count):
        if offset + 12 > len(data):
            break
        x, y, z = struct.unpack_from("<fff", data, offset)
        # Sanity check: skip obviously bogus coordinates
        if abs(x) < 50_000 and abs(z) < 50_000 and -500 < y < 5000:
            points.append((x, y, z))
        offset += STRIDE

    return points


def main() -> None:
    owt_files = sorted(AI_TRACKS.glob("*.owt"))
    print(f"Found {len(owt_files)} .owt files in {AI_TRACKS}")

    all_routes: dict[str, list[list[float]]] = {}
    total_pts = 0

    for owt in owt_files:
        pts = parse_owt(owt)
        if pts:
            all_routes[owt.stem] = [[x, y, z] for x, y, z in pts]
            total_pts += len(pts)

    print(f"Extracted {total_pts:,} waypoints from {len(all_routes)} routes")

    # Coordinate bounds
    all_x = [p[0] for pts in all_routes.values() for p in pts]
    all_z = [p[2] for pts in all_routes.values() for p in pts]
    if all_x:
        print(f"World X: {min(all_x):.0f} ... {max(all_x):.0f}")
        print(f"World Z: {min(all_z):.0f} ... {max(all_z):.0f}")

    with OUT_JSON.open("w") as f:
        json.dump({
            "source": "AITracks/*.owt  (FTWO format)",
            "route_count": len(all_routes),
            "total_waypoints": total_pts,
            "routes": all_routes,
        }, f, separators=(",", ":"))

    print(f"Saved -> {OUT_JSON}")

    # Generate preview PNG
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.collections as mc
        import matplotlib.pyplot as plt

        lines: list[list[tuple[float, float]]] = []
        for pts in all_routes.values():
            seg = [(p[0], p[2]) for p in pts]
            if len(seg) >= 2:
                lines.append(seg)

        _fig, ax = plt.subplots(figsize=(16, 16), facecolor="black")
        ax.set_facecolor("black")
        lc = mc.LineCollection(lines, colors="#00ccff", linewidths=0.6, alpha=0.9)
        ax.add_collection(lc)
        ax.autoscale()
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"FH6 AI Route Waypoints — {len(lines)} routes ({total_pts:,} pts)",
                     color="white", fontsize=13, pad=8)
        plt.tight_layout()
        plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="black")
        print(f"Preview -> {OUT_PNG}")
    except ImportError:
        print("matplotlib not available, skipping preview")


if __name__ == "__main__":
    main()
