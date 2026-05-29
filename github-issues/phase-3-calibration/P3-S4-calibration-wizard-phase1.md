---
title: "[P3-S4] CalibrationWizard: Phase 1 — click reference map points"
labels: ["phase-3", "ui", "tdd"]
milestone: "Phase 3 — Calibration"
---

## Summary
Implement the first phase of the calibration wizard: user clicks 3 landmarks on the reference map, markers are shown, and Next is enabled after 3 clicks.

## Motivation
The calibration UX must be clear and hard to mis-use. Phase 1 is purely within the app so it is fully automatable with pytest-qt.

## Acceptance Criteria
- [ ] Dialog opens in ref-map mode with instructions and count "0 / 3 selected"
- [ ] Each `calibration_click` signal click adds a marker to the map view
- [ ] Count label updates after each click
- [ ] "Next" button is disabled until exactly 3 points are selected
- [ ] Clicking "Back" clears all ref points and resets to 0/3
- [ ] Clicking "Cancel" disables calibration mode on the map view

## Tasks
- [ ] Write `tests/ui/test_calibration.py` with failing tests first
- [ ] Test initial state: next is disabled, count is "0 / 3 selected"
- [ ] Simulate 3 `calibration_click` signals, assert next becomes enabled
- [ ] Test back button resets points and disables next
- [ ] Test cancel disables map view calibration mode
- [ ] Implement Phase 1 wizard logic until tests pass

## Dependencies
P3-S1, P1-S3

## Notes
Emit `calibration_click` directly in tests via `map_view.calibration_click.emit(QPointF(x, y))` — no mouse simulation needed.
