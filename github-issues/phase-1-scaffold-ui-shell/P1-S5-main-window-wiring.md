---
title: "[P1-S5] MainWindow: wire panel + map view, load map flow"
labels: ["phase-1", "ui", "integration", "tdd"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Implement `MainWindow` that wires `ScanPanel` and `MapView` together. Loading a reference map samples road points and overlays them on the map.

## Motivation
Integration wiring is where signal/slot connections can silently break. Testing the load-map flow end-to-end catches issues early.

## Acceptance Criteria
- [ ] Window opens at 1280×820
- [ ] Loading a valid image updates the map view and enables calibrate/start
- [ ] Loading an invalid path shows an error and leaves controls disabled
- [ ] Session starts empty (0 points)
- [ ] Status label reflects current state (ready, loaded, scanning, etc.)
- [ ] Window close stops any running scanner thread cleanly

## Tasks
- [ ] Write `tests/ui/test_main_window.py` with failing tests first
- [ ] Test window title is "Horizon Scout"
- [ ] Test that after loading a valid map, `panel.btn_start` is enabled
- [ ] Test that loading an invalid path does not crash
- [ ] Test session point count is > 0 after loading a test road-map PNG
- [ ] Implement `app/ui/main_window.py` load-map flow until tests pass

## Dependencies
P1-S3, P1-S4

## Notes
Keep a small synthetic test map (white line on black, ~100x100px) in `tests/fixtures/` for deterministic testing.
