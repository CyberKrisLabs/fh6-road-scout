---
title: "[P6-S4] PyInstaller build: verified single-file .exe"
labels: ["phase-6", "packaging", "devops"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Verify and finalise the PyInstaller build spec to produce a working `HorizonScout.exe` that bundles all assets and runs without a Python installation.

## Motivation
End users are gamers, not Python developers. A single `.exe` is the only acceptable distribution format.

## Acceptance Criteria
- [ ] `pyinstaller horizon_scout.spec` completes without errors
- [ ] `dist/HorizonScout.exe` runs on a machine with no Python installed
- [ ] Assets (ft_indicator.png, etc.) are accessible via `sys._MEIPASS`
- [ ] No console window appears on launch (`--windowed`)
- [ ] File size is reasonable (target < 150MB)
- [ ] All app features work from the bundled exe

## Tasks
- [ ] Update `horizon_scout.spec` with correct `datas` entries for assets
- [ ] Add `sys._MEIPASS` fallback for asset path resolution in code
- [ ] Build and test exe on a clean Windows VM or user account
- [ ] Document build steps in CLAUDE.md
- [ ] Add `build/` and `dist/` to `.gitignore`

## Dependencies
All prior phases

## Notes
Asset path resolution: `base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))`. Add this to a `app/utils/paths.py` helper.
