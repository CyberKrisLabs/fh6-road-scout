---
title: "[P1-S4] ScanPanel: controls layout, signals, enabled states"
labels: ["phase-1", "ui", "tdd"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Implement the left-side `ScanPanel` widget with all buttons, progress bar, stats, and correct enabled/disabled state transitions.

## Motivation
The panel is the user's primary control surface. State management (what's enabled when) must be correct from the start to avoid confusing UX.

## Acceptance Criteria
- [ ] All buttons present: Load Map, Calibrate, Start, Pause, Stop, Next Gap, Export, Save, Load
- [ ] `set_map_loaded(False)` disables Calibrate and Start
- [ ] `set_map_loaded(True)` enables Calibrate and Start
- [ ] `set_scan_running(True)` disables Load, Calibrate, Start; enables Pause, Stop
- [ ] `set_scan_running(False)` reverses the above
- [ ] `update_progress()` updates bar percentage and stat labels correctly
- [ ] Each button emits its corresponding signal when clicked
- [ ] Panel width is fixed at 210px

## Tasks
- [ ] Write `tests/ui/test_scan_panel.py` with failing tests first
- [ ] Test initial state: Calibrate and Start are disabled
- [ ] Test `set_map_loaded(True)` enables correct buttons
- [ ] Test `set_scan_running(True/False)` transitions
- [ ] Test `update_progress` sets correct label text and bar value
- [ ] Test each signal is emitted when its button is clicked (use `qtbot.waitSignal`)
- [ ] Implement `app/ui/scan_panel.py` until all tests pass

## Dependencies
P1-S2

## Notes
Use `qtbot.waitSignal(panel.load_map_requested)` pattern for signal emission tests.
