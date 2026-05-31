# Horizon Scout — Project Rules

## Project Overview
Desktop app that helps Forza Horizon 6 players find unexplored roads by scanning
the in-game world map using mouse-hover detection of the fast-travel indicator.

**App name:** Horizon Scout
**GitHub repo:** https://github.com/CyberKrisLabs/fh6-road-scout
**Target platform:** Windows 10/11 (64-bit)
**Stack:** Python 3.12+, PySide6, OpenCV, PyAutoGUI, mss, PyInstaller
**Total roads in FH6:** 671

---

## Road Types

| Type | In-game map colour | Line style | `RoadType` value |
|---|---|---|---|
| Asphalt | White | Solid | `asphalt` |
| Tunnel | White | Solid (with subtle black centre dots) | `tunnel` |
| Dirt road | Orange | Solid | `dirt` |
| Offroad track | Orange | Dashed | `offroad` |
| Alleyway | Cyan (thin) | Dashed | `alleyway` |

---

## In-Game Map Mechanics

### Cursor (two-part)

The in-game map cursor has two distinct parts that move independently:

**Primary cursor** — follows the actual mouse position (can be anywhere: terrain, sea, road):
- Large white circle with black outer border
- Four small circular pins extending N, E, W, S from the circle

**Road cursor** — always snaps to the nearest road regardless of where the primary cursor is:
- Two concentric white circles (larger outer ring, smaller inner circle)
- Never appears on terrain or sea — always locked to the closest road
- Moves smoothly along the road as the primary cursor moves nearby
- This is the element we track to detect road positions

### Fast Travel Indicator

Appears overlaid on the road cursor when it is positioned on a **discovered** road:

- **Button graphic:** keyboard-style "X" button — black text, white background, black border
- **Label:** "Fast Travel" text to the right of the button
- **Container:** transparent background with padding; no visible border (background shows through)
- Indicator is absent on undiscovered roads even when the road cursor is on them

### Auto-targeting behaviour

The road cursor snaps to the closest road even when the primary cursor is far away
(e.g. in the ocean). This means moving the mouse across any area of the map will
cause the road cursor to track along nearby roads.

---

## Scanning Architecture (Revised)

The app operates in two distinct modes:

### Mode A — Road Database (pre-built from game files — replaces cursor scan)

Road positions are extracted directly from the game's binary AI-track files instead
of runtime cursor detection.  The source data lives in:

```
D:\SteamLibrary\steamapps\common\ForzaHorizon6\media\OpenWorld\Brio\AITracks\
```

167 `Route*.owt` files use the **FTWO binary format** (56-byte records):
- Bytes 0–11: `float32 X, Y, Z` — game world position
- Bytes 12–55: tangent vectors, accumulated distance, flags

Extraction script: `assets/game_files/parse_owt.py`
Build script:      `assets/game_files/build_world_road_points.py`

Result: **`assets/world_road_points.json`** — 48,476 unique road points on a 15 m
dedup grid, in game-world (X, Z) coordinates.

> **Coordinate system:** game world units (metres).  X ≈ −8,053 … +11,022,
> Z ≈ −9,492 … +20,163.  Calibration (Phase 3) maps (world_x, world_z) to
> (ref_x, ref_y) pixel coordinates on the reference map.

The cursor-based `RoadMapper` class (and `road_points.json`) is superseded by this
approach and will eventually be removed.

### Mode B — Discovery Scan (repeated by each player)
For each road point in `world_road_points.json`:
1. Apply calibration to convert world (X, Z) → in-game map screen position
2. Move the mouse to that screen position
3. Capture the screen and detect whether the fast travel indicator is present
4. Record the road as discovered or undiscovered

Result: a list of undiscovered road points, highlighted on the reference map.

### Why game-file extraction beats cursor tracking
- Zero false positives — positions are authoritative, not inferred from vision
- No scrolling, no settle delays, no cursor detection failures
- Works offline (no game running during data extraction)
- One-time extraction; all players share the same `world_road_points.json`

---

## Development Methodology

### TDD — Tests First, Always
- Write the failing test **before** writing the implementation.
- A PR that adds implementation without a corresponding test will not be merged.
- Tests live in `tests/` mirroring the `app/` structure:
  - `tests/core/test_road_sampler.py` for `app/core/road_sampler.py`
  - `tests/ui/test_map_view.py` for `app/ui/map_view.py`
  - etc.

### Story / Issue Structure
- Each **Phase** corresponds to a GitHub Milestone.
- Each **Story** within a phase corresponds to one GitHub Issue.
- One story = one PR = one merged branch.
- Commit messages reference the issue: `feat(scan): implement hover delay #12`.

### Branch Naming
```
feature/P1-S2-data-models
feature/P3-S4-calibration-wizard-phase1
fix/P4-S3-scanner-signal-leak
```
Format: `feature/<STORY-ID>-<short-description>` or `fix/<STORY-ID>-<short-description>`.

---

## Code Standards

### Type Hints
- All public functions, methods, and class attributes **must** have type hints.
- `mypy` runs in strict mode — no bare `Any` without a `# type: ignore[...]` comment explaining why.

### Style
- **Ruff** is the single source of truth for formatting and linting.
- Line length: 100 characters.
- No `print()` statements — use `logging` (logger per module: `log = logging.getLogger(__name__)`).
- No bare `except:` — always catch a specific exception type.
- No unused imports — ruff will catch these.

### Logging
- Every module gets its own logger: `log = logging.getLogger(__name__)`
- Logging is configured once at startup via `app/utils/logging_setup.py`:
  - **Dev (no frozen exe):** logs to console at `DEBUG` level
  - **Packaged exe:** logs to rotating file at `INFO` level
    - Path: `%APPDATA%\HorizonScout\logs\horizon_scout.log`
    - Max size: 1 MB, 3 backups kept
- Never configure logging inside modules — only in `logging_setup.py` and `main.py`.

### Qt / PySide6
- Prefer `QSettings` over ad-hoc JSON for persisting user preferences and window state.
- All background work runs in a `QThread` — never block the main/GUI thread.
- Signals and slots must be typed: `Signal(int)`, `Signal(str)`, etc.
- Test Qt widgets with `pytest-qt`'s `qtbot` fixture — never instantiate `QApplication` manually in tests.

---

## Commands

```bash
# Lint and auto-fix
ruff check . --fix

# Format
ruff format .

# Type check
mypy app/

# Run tests with coverage
pytest --cov=app --cov-report=term-missing tests/

# Build .exe
pyinstaller horizon_scout.spec
```

---

## Project Structure

```
fh6-road-scout/
├── app/
│   ├── ui/            # PySide6 windows, widgets, dialogs
│   ├── core/          # Business logic (scanner, detector, calibrator, sampler)
│   ├── models/        # Data classes
│   └── utils/
│       ├── paths.py         # asset path resolution (dev vs PyInstaller _MEIPASS)
│       └── logging_setup.py # configure console + rotating file logging
├── tests/
│   ├── ui/
│   ├── core/
│   └── fixtures/      # synthetic test images (generated, not committed as binaries)
├── assets/            # ft_indicator.png template, icons
├── github-issues/     # issue .md files + create-issues.ps1 script
├── .github/
│   └── workflows/
│       ├── ci.yml         # lint + test on push/PR
│       └── release.yml    # build .exe on vX.Y.Z tag
├── CLAUDE.md
├── pyproject.toml         # ruff, mypy, pytest config
├── .pre-commit-config.yaml
├── .gitignore
├── horizon_scout.spec     # PyInstaller spec
├── main.py
├── requirements.txt
└── requirements-dev.txt
```

---

## Packaging

- **PyInstaller** with `--onefile --windowed` produces a single `HorizonScout.exe`.
- `horizon_scout.spec` is checked into the repo so builds are reproducible.
- The `assets/` folder is bundled via `datas` in the spec file.
- GitHub release workflow triggers on a `vX.Y.Z` tag, attaches the `.exe` as a release asset.

---

## Phase & Story Breakdown

### Phase 1 — Project Scaffold & UI Shell
| Story | Description |
|---|---|
| P1-S1 | Dev tooling: pyproject.toml, ruff, mypy, pytest, pre-commit |
| P1-S2 | `ScanPoint` / `ScanSession` data models + unit tests |
| P1-S3 | `MapView` widget: load image, zoom, pan + tests |
| P1-S4 | `ScanPanel` layout, signals, enabled/disabled states + tests |
| P1-S5 | `MainWindow` wiring: load map triggers road sampling overlay |
| P1-S6 | Dark theme (orange/black) applied globally |

### Phase 2 — Road Database (from game files — replaces cursor mapping)
| Story | Description |
|---|---|
| P2-S1 | ~~`RoadCursorDetector`~~ — **superseded**; road positions come from game files |
| P2-S2 | ~~`RasterScanner`~~ — still used in discovery scan; road mapping raster not needed |
| P2-S3 | ~~`RoadMapper`~~ — **superseded**; `assets/world_road_points.json` is the source |
| P2-S4 | ~~`RoadType` from cursor heuristic~~ — road type TBD (all default to `asphalt` for now) |
| P2-S5 | Load `world_road_points.json` at startup; expose world coords to calibrator + scanner |

### Phase 3 — Calibration
| Story | Description |
|---|---|
| P3-S1 | `Calibrator.fit()`: affine transform from 3 point pairs + tests |
| P3-S2 | `Calibrator.transform()`: **world (X, Z) → ref map (px, py)** + tests |
| P3-S3 | `Calibrator` serialise/deserialise (QSettings) + tests |
| P3-S4 | `CalibrationWizard` dialog: click 3 known world landmarks on in-game map + tests |
| P3-S5 | `CalibrationWizard` dialog: capture corresponding ref map clicks (F9 hotkey) |

### Phase 4 — Fast Travel Detector & Discovery Scan
| Story | Description |
|---|---|
| P4-S1 | `FastTravelDetector.load_template()` + `_template_match()` + tests |
| P4-S2 | `FastTravelDetector._color_heuristic()` + combined `is_visible()` + tests |
| P4-S3 | `DiscoveryScanner` QThread: raster scan → road cursor pos + FT detection loop |
| P4-S4 | Mark road points discovered/undiscovered based on FT presence; pause/resume/stop |
| P4-S5 | Configurable hover delay and raster step size in settings |

### Phase 5 — Results & Export
| Story | Description |
|---|---|
| P5-S1 | Map overlay: green/red dots per scan state |
| P5-S2 | `export_overlay()`: annotated PNG + tests |
| P5-S3 | "Next Gap" navigation: cluster undiscovered points, jump to nearest |
| P5-S4 | Save / load session (QSettings + JSON) + tests |

### Phase 6 — Polish & Packaging
| Story | Description |
|---|---|
| P6-S1 | Settings dialog: hover delay, threshold, sample interval, **monitor selector** |
| P6-S2 | FT template capture workflow (guided in-app) |
| P6-S3 | Onboarding / first-run guide dialog |
| P6-S4 | `horizon_scout.spec` + PyInstaller build verified |
| P6-S5 | GitHub Actions CI workflow (lint + test) |
| P6-S6 | GitHub Actions release workflow (build .exe on tag) |

---

## Resolved Design Decisions

| Topic | Decision |
|---|---|
| Logging (dev) | Console, DEBUG level |
| Logging (packaged exe) | Rotating file in `%APPDATA%\HorizonScout\logs\`, INFO level |
| Multi-monitor | Monitor selector dropdown added to Settings dialog (P6-S1) |
| Branch naming | `feature/P1-S2-short-description` / `fix/P4-S3-short-description` |
| Asset paths | `app/utils/paths.py` — single helper used everywhere, handles `sys._MEIPASS` |
| Road database | `assets/world_road_points.json` (game-file extraction, FTWO parser); replaces cursor-based road mapping |
| Road coordinates | Game world (X, Z) in metres; calibration maps to ref-map pixel coords at runtime |
| Road type | All points default to `asphalt` until type classification is implemented |
