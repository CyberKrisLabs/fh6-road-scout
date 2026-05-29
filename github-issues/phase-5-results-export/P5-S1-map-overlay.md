---
title: "[P5-S1] MapView: live scan results overlay"
labels: ["phase-5", "ui", "tdd"]
milestone: "Phase 5 — Results & Export"
---

## Summary
Render discovered (green) and undiscovered (red/orange) scan points as coloured dots on the MapView, updating in real time as the scanner emits results.

## Motivation
Seeing the scan progress live is the core user experience. Colour accuracy and rendering performance matter here.

## Acceptance Criteria
- [ ] DISCOVERED points render as green dots (#50DC64)
- [ ] UNDISCOVERED points render as red/orange dots (#FF5032)
- [ ] UNKNOWN points render as grey dots (#B4B4B4) at reduced opacity
- [ ] Dot radius scales with zoom level (clamped to min 2px)
- [ ] New points render within one paint cycle of `update_point()` being called
- [ ] 10,000 points render without noticeable lag on a 1080p display

## Tasks
- [ ] Write `tests/ui/test_map_view_overlay.py` with failing tests
- [ ] Test: after `set_points()`, internal list matches input
- [ ] Test: `update_point()` triggers a repaint (use `qtbot.waitExposed`)
- [ ] Manual visual test: load a synthetic map, set 100 mixed points, verify colours
- [ ] Implement/update overlay rendering in `map_view.py`

## Dependencies
P1-S3, P4-S3

## Notes
Performance test with 10k points is a manual benchmark, not automated. Render using a single `QPainter.drawEllipse` call per point.
