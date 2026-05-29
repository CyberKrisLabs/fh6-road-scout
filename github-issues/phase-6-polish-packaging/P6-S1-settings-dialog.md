---
title: "[P6-S1] Settings dialog: hover delay, threshold, sample interval, monitor selector"
labels: ["phase-6", "ui", "settings", "tdd"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Implement a Settings dialog exposing hover delay, template match threshold, sample interval, and game monitor selection — all persisted via QSettings.

## Motivation
Power users need to tune detection values for their setup. The monitor selector is required for users whose game runs on a secondary display.

## Acceptance Criteria
- [ ] Dialog accessible from a Settings button or menu item
- [ ] Shows hover delay (0.05–1.0s), match threshold (0.5–0.95), sample interval (5–50px)
- [ ] Shows a monitor selector dropdown populated from `mss.mss().monitors` at dialog open
- [ ] Monitor dropdown shows index + resolution (e.g. "Monitor 1 — 1920×1080 (Primary)")
- [ ] Selected monitor index is passed to `Scanner` on next scan start
- [ ] Values pre-populate from QSettings
- [ ] Clicking OK saves to QSettings; Cancel discards
- [ ] Changes take effect on the next scan
- [ ] Inputs are validated: out-of-range values show an error and block saving

## Tasks
- [ ] Write `tests/ui/test_settings_dialog.py` with failing tests
- [ ] Test: dialog loads current QSettings values
- [ ] Test: OK saves new values to QSettings
- [ ] Test: Cancel does not change QSettings
- [ ] Test: invalid input blocks OK
- [ ] Test: monitor dropdown contains at least one entry
- [ ] Implement `app/ui/settings_dialog.py` with monitor selector
- [ ] Update `Scanner` to accept a `monitor_index` parameter

## Dependencies
P2-S4, P4-S5

## Notes
Use `QDoubleSpinBox` for float fields, `QSpinBox` for integer fields, `QComboBox` for monitor selector.
QSettings key: `scanner/monitor_index`, default 1 (primary).
`mss.mss().monitors[0]` is the combined virtual screen — skip it; real monitors start at index 1.
