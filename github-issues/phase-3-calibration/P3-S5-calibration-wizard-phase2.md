---
title: "[P3-S5] CalibrationWizard: Phase 2 — capture screen points (F9)"
labels: ["phase-3", "ui", "integration"]
milestone: "Phase 3 — Calibration"
---

## Summary
Implement the second phase of the calibration wizard: app minimises, user positions mouse at each landmark in-game and presses F9 to capture screen coordinates.

## Motivation
This phase requires real mouse position capture. Automated testing is limited here — integration testing with a mock hotkey is used.

## Acceptance Criteria
- [ ] Phase 2 instructions are shown after clicking Next from Phase 1
- [ ] App minimises after 3s countdown when entering Phase 2
- [ ] Each F9 press captures current cursor position
- [ ] Count updates after each capture
- [ ] "Finish" is enabled only after 3 captures
- [ ] If `keyboard` library is not installed, a manual "Capture Point" button is shown instead
- [ ] `calibration_done` signal emits both lists when Finish is clicked

## Tasks
- [ ] Write test: `calibration_done` signal emits correct ref + screen point lists
- [ ] Write test: fallback button appears when keyboard library is absent (mock import)
- [ ] Write test: finish is disabled until 3 screen points captured
- [ ] Implement `_on_screen_capture()` and fallback button logic
- [ ] Implement `calibration_done` signal emission on finish

## Dependencies
P3-S4

## Notes
Mock the `keyboard` import in tests using `unittest.mock.patch`. The minimise-on-countdown behaviour is not unit tested — it is manual only.
