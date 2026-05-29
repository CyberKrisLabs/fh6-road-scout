---
title: "[P4-S5] Scanner: configurable hover delay via QSettings"
labels: ["phase-4", "core", "settings", "tdd"]
milestone: "Phase 4 — Scanner Engine"
---

## Summary
Make the hover delay (time between mouse move and screenshot) configurable, persisted in QSettings, and validated to a safe range.

## Motivation
A delay too short misses slow-loading hover tooltips; too long makes the 7-minute scan unbearably slow. Users need to tune this.

## Acceptance Criteria
- [ ] `Scanner(hover_delay=0.05)` uses 50ms delay
- [ ] Valid range: 0.05–1.0 seconds (clamped)
- [ ] Delay is read from QSettings on scanner construction
- [ ] A settings field (P6-S1 stub) allows editing and persisting the value

## Tasks
- [ ] Write test: `hover_delay` parameter is passed to `time.sleep` in the loop
- [ ] Write test: delay is clamped to [0.05, 1.0]
- [ ] Implement delay parameter and QSettings persistence
- [ ] Add to settings dialog stub (even if dialog not yet fully implemented)

## Dependencies
P4-S3

## Notes
QSettings key: `scanner/hover_delay`, default 0.12.
