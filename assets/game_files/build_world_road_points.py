"""
Build assets/world_road_points.json from all Route*.owt AI track files.

Output schema
-------------
{
  "format": "world_road_points_v1",
  "coordinate_system": "fh6_world_xz",
  "note": "Calibrate (world_x, world_z) -> (ref_x, ref_y) before use in app",
  "world_bounds": {"x_min": ..., "x_max": ..., "z_min": ..., "z_max": ...},
  "point_count": <int>,
  "points": [
    {"world_x": <float>, "world_z": <float>},
    ...
  ]
}

Subsampling: one grid cell per GRID_M metres (avoids duplicating heavily-travelled roads).
The dedup grid uses only (world_x, world_z) - elevation is discarded for 2-D map use.
"""

import json
import struct
import sys
from pathlib import Path

AI_TRACKS  = Path(r"D:\SteamLibrary\steamapps\common\ForzaHorizon6\media\OpenWorld\Brio\AITracks")
OUT_JSON   = Path(__file__).parent.parent / "world_road_points.json"   # assets/
OUT_PNG    = Path(__file__).parent / "world_road_points_preview.png"

MAGIC      = b"FTWO"
HDR_SIZE   = 0x60
STRIDE     = 56
COUNT_OFF  = 0x24

GRID_M     = 15   # deduplicate within 15-metre grid cells


# ---------------------------------------------------------------------------
# FTWO parser (same logic as parse_owt.py)
# ---------------------------------------------------------------------------

def parse_owt(path: Path) -> list[tuple[float, float, float]]:
    data = path.read_bytes()
    if data[:4] != MAGIC:
        return []
    count = struct.unpack_from("<I", data, COUNT_OFF)[0]
    if HDR_SIZE + count * STRIDE > len(data) + 64:
        count2 = struct.unpack_from("<I", data, 0x50)[0]
        if HDR_SIZE + count2 * STRIDE <= len(data) + 64:
            count = count2
    points: list[tuple[float, float, float]] = []
    offset = HDR_SIZE
    for _ in range(count):
        if offset + 12 > len(data):
            break
        x, y, z = struct.unpack_from("<fff", data, offset)
        if abs(x) < 50_000 and abs(z) < 50_000 and -500 < y < 5_000:
            points.append((x, y, z))
        offset += STRIDE
    return points


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    owt_files = sorted(AI_TRACKS.glob("*.owt"))
    if not owt_files:
        print(f"ERROR: no .owt files found in {AI_TRACKS}", file=sys.stderr)
        sys.exit(1)
    print(f"Parsing {len(owt_files)} .owt files ...")

    # Dedup grid: keep one point per GRID_M x GRID_M cell
    seen: set[tuple[int, int]] = set()
    kept: list[dict[str, float]] = []

    for owt in owt_files:
        for x, _y, z in parse_owt(owt):
            cell = (int(x / GRID_M), int(z / GRID_M))
            if cell not in seen:
                seen.add(cell)
                kept.append({"world_x": round(x, 2), "world_z": round(z, 2)})

    if not kept:
        print("ERROR: no points extracted", file=sys.stderr)
        sys.exit(1)

    all_x = [p["world_x"] for p in kept]
    all_z = [p["world_z"] for p in kept]
    bounds = {
        "x_min": round(min(all_x), 1),
        "x_max": round(max(all_x), 1),
        "z_min": round(min(all_z), 1),
        "z_max": round(max(all_z), 1),
    }

    out = {
        "format": "world_road_points_v1",
        "coordinate_system": "fh6_world_xz",
        "note": (
            "Calibrate (world_x, world_z) -> (ref_x, ref_y) with CalibrationWizard "
            "before use in the scanner."
        ),
        "grid_resolution_m": GRID_M,
        "source_routes": len(owt_files),
        "world_bounds": bounds,
        "point_count": len(kept),
        "points": kept,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w") as f:
        json.dump(out, f, separators=(",", ":"))

    size_kb = OUT_JSON.stat().st_size / 1024
    print(f"Written {len(kept):,} unique points ({size_kb:.0f} KB) -> {OUT_JSON}")
    print(f"World bounds: X {bounds['x_min']} .. {bounds['x_max']}  "
          f"Z {bounds['z_min']} .. {bounds['z_max']}")

    # Preview PNG
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = [p["world_x"] for p in kept]
        zs = [p["world_z"] for p in kept]

        _fig, ax = plt.subplots(figsize=(14, 14), facecolor="black")
        ax.set_facecolor("black")
        ax.scatter(xs, zs, s=0.3, c="#ff6600", alpha=0.6, linewidths=0)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(
            f"FH6 World Road Points — {len(kept):,} pts  (grid {GRID_M}m)",
            color="white", fontsize=13, pad=8,
        )
        plt.tight_layout()
        plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="black")
        print(f"Preview -> {OUT_PNG}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
