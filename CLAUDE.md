# Horizon Scout — Project Rules

## Project Overview
Desktop app that helps Forza Horizon 6 players find unexplored roads by scanning
the in-game world map using mouse-hover detection of the fast-travel indicator.

**App name:** Horizon Scout
**GitHub repo:** https://github.com/CyberKrisLabs/fh6-road-scout
**Target platform:** Windows 10/11 (64-bit)
**Stack:** Python 3.12+, PySide6, OpenCV, PyAutoGUI, mss, PyInstaller

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

### Phase 2 — Road Sampler
| Story | Description |
|---|---|
| P2-S1 | `RoadSampler.road_mask()`: HSV threshold + morphology + tests |
| P2-S2 | `RoadSampler.skeletonize()`: thinning + fallback + tests |
| P2-S3 | `RoadSampler.sample()`: skeleton → ScanPoint list + tests |
| P2-S4 | Configurable sample interval exposed in settings |

### Phase 3 — Calibration
| Story | Description |
|---|---|
| P3-S1 | `Calibrator.fit()`: affine transform from 3 point pairs + tests |
| P3-S2 | `Calibrator.transform()`: ref → screen coordinate + tests |
| P3-S3 | `Calibrator` serialise/deserialise (QSettings) + tests |
| P3-S4 | `CalibrationWizard` dialog: phase 1 ref clicks + tests |
| P3-S5 | `CalibrationWizard` dialog: phase 2 screen capture (F9 hotkey) |

### Phase 4 — Scanner Engine
| Story | Description |
|---|---|
| P4-S1 | `Detector.load_template()` + `_template_match()` + tests |
| P4-S2 | `Detector._color_heuristic()` + combined `is_fast_travel_visible()` + tests |
| P4-S3 | `Scanner` QThread: hover → capture → detect loop |
| P4-S4 | Pause / resume / stop controls wired end-to-end |
| P4-S5 | Configurable hover delay in settings |

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
| Prototype code | Deleted — rebuilt TDD-first phase by phase |
| Logging (dev) | Console, DEBUG level |
| Logging (packaged exe) | Rotating file in `%APPDATA%\HorizonScout\logs\`, INFO level |
| Multi-monitor | Monitor selector dropdown added to Settings dialog (P6-S1) |
| Branch naming | `feature/P1-S2-short-description` / `fix/P4-S3-short-description` |
| Asset paths | `app/utils/paths.py` — single helper used everywhere, handles `sys._MEIPASS` |
