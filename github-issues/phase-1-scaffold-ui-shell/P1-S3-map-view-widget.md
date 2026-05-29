---
title: "[P1-S3] MapView widget: load image, zoom, pan"
labels: ["phase-1", "ui", "tdd"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Implement the `MapView` widget that displays a reference map image with smooth zoom (mouse wheel) and pan (drag), plus a scan-point overlay.

## Motivation
The map view is the central UI element. Users need to clearly see their reference map and the overlay of discovered/undiscovered points.

## Acceptance Criteria
- [ ] `load_image(path)` returns True for a valid image, False for invalid
- [ ] Mouse wheel zooms toward cursor position
- [ ] Left-drag pans the map
- [ ] Scale is clamped to [0.05, 50.0]
- [ ] `set_points()` renders UNKNOWN/DISCOVERED/UNDISCOVERED dots in correct colours
- [ ] `jump_to_point()` re-centres the view on the given point
- [ ] Widget shows placeholder text when no image is loaded
- [ ] Tests use `pytest-qt` `qtbot` — no manual QApplication

## Tasks
- [ ] Write `tests/ui/test_map_view.py` with failing tests first
- [ ] Test `load_image` returns False for a missing path
- [ ] Test `load_image` returns True for a valid PNG
- [ ] Test `_widget_to_img` / `_img_to_widget` round-trip transforms
- [ ] Test `set_points` stores points (verify via internal state)
- [ ] Test calibration mode: `calibration_click` signal emitted on left-click
- [ ] Implement `app/ui/map_view.py` until all tests pass

## Dependencies
P1-S2 (needs ScanPoint model)

## Notes
Use `qtbot.addWidget(view)` in tests. For transform tests, set a known scale/offset before asserting.
