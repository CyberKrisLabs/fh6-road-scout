# Horizon Scout

A desktop companion app for **Forza Horizon 6** that scans the in-game world map to find roads you haven't explored yet.

It works by moving your mouse over every road point on a reference map image, capturing the screen, and detecting whether the fast-travel hover indicator is visible — meaning you have already discovered that road. Roads without the indicator are flagged as undiscovered.

---

## How It Works

1. You take a screenshot of the FH6 world map and load it as a reference image.
2. Horizon Scout samples road centrelines from the image using HSV thresholding and morphological thinning.
3. You calibrate the app by clicking 3 matching landmarks on both the reference map and the live game screen.
4. The scanner moves the mouse over every sampled road point, captures a screen region, and checks for the fast-travel indicator (template match + teal colour heuristic).
5. Results are shown as a green/red dot overlay on the map. You can export the annotated image, save the session, and resume later.

---

## Requirements

- Windows 10 or 11 (64-bit)
- Python 3.12+ (3.11 works for development, 3.12 recommended)
- Forza Horizon 6 running in **windowed** or **borderless windowed** mode

---

## Setup

```powershell
# Clone the repo
git clone https://github.com/CyberKrisLabs/fh6-road-scout.git
cd fh6-road-scout

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements-dev.txt
```

---

## Running the App

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

---

## Usage

### 1. Prepare a Reference Map

- In FH6, open the World Map and take a full screenshot.
- Load it in Horizon Scout via **Load Reference Map**.
- The app will sample road points automatically and overlay grey dots on all detected roads.

### 2. Capture the Fast-Travel Template

Before scanning you need a crop of the fast-travel hover indicator:

1. In FH6, hover over a road you **have already explored** on the map.
2. Screenshot the tooltip/icon that appears (`Win+Shift+S`).
3. Crop it to just the indicator element (~100–200 px wide).
4. Save as `assets/ft_indicator.png` in the project folder.

### 3. Calibrate

Click **Calibrate** and follow the two-phase wizard:

- **Phase 1** — Click 3 recognisable landmarks (road junctions, coastline bends, town centres) on the reference map inside the app.
- **Phase 2** — The app minimises. Move your mouse to each matching landmark in the live game and press **F9** to capture the screen coordinate.

Calibration is saved automatically and survives app restarts.

### 4. Scan

Click **Start**. The scanner will:

- Move the mouse to each road point (don't touch the mouse during the scan).
- Capture a small ROI around the cursor.
- Detect the fast-travel indicator.
- Update the map overlay in real time — green = discovered, red = undiscovered.

Use **Pause** / **Resume** to interrupt and continue. Use **Stop** to end early (progress is kept).

### 5. Review Results

- **Next Gap** — cycles through undiscovered road clusters so you can navigate to each one in the game.
- **Export PNG** — saves an annotated map image you can use as a reference while playing.
- **Save** — saves the full session to JSON so you can resume later.
- **Load** — restores a previously saved session.

---

## Development

```powershell
# Lint and auto-fix
ruff check . --fix

# Format
ruff format .

# Type check
mypy app/

# Run tests with coverage
pytest --cov=app --cov-report=term-missing tests/

# Build standalone .exe
pyinstaller horizon_scout.spec
```

Tests use synthetic images (no game assets needed) and mock all hardware interaction (mouse, screen capture). The full suite runs in under 5 seconds for core/model tests; UI tests using `pytest-qt` take a little longer on first run due to PySide6 initialisation.

---

## Project Structure

```
fh6-road-scout/
├── app/
│   ├── core/          # Business logic
│   │   ├── calibrator.py      # Affine transform from 3 point pairs
│   │   ├── detector.py        # Template match + colour heuristic
│   │   ├── exporter.py        # Annotated PNG export
│   │   ├── road_sampler.py    # HSV mask + skeleton + sample points
│   │   ├── scanner.py         # QThread hover-capture-detect loop
│   │   └── session_store.py   # JSON save/load
│   ├── models/
│   │   └── scan_result.py     # ScanPoint, ScanSession, DiscoveryState
│   ├── ui/
│   │   ├── calibration.py     # Two-phase calibration wizard
│   │   ├── main_window.py     # Top-level window, wires everything
│   │   ├── map_view.py        # Zoomable/pannable map canvas
│   │   ├── scan_panel.py      # Left-side control panel
│   │   └── theme.py           # Dark orange/black stylesheet
│   └── utils/
│       ├── logging_setup.py   # Console (dev) or rotating file (exe)
│       └── paths.py           # Asset path resolution (dev + PyInstaller)
├── tests/                     # Mirrors app/ structure
├── assets/                    # ft_indicator.png goes here
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── horizon_scout.spec         # PyInstaller build config
```

---

## Building a Standalone Executable

```powershell
pyinstaller horizon_scout.spec
```

The output is `dist/HorizonScout.exe` — a single file with no Python installation required. Logs are written to `%APPDATA%\HorizonScout\logs\horizon_scout.log`.

---

## Tips

- A **larger hover delay** (`scanner/hover_delay` in QSettings, default 0.12 s) helps on slower machines or with slower tooltip rendering.
- A **smaller sample interval** (`sampler/interval`, default 15 px) catches more short road segments but makes the scan take longer.
- If the scanner misclassifies roads, re-capture a cleaner `ft_indicator.png` crop with more contrast.
- The morphological skeleton fallback is used automatically if `opencv-contrib-python` is not installed. Installing it (`pip install opencv-contrib-python`) improves skeleton quality.

---

## License

MIT
