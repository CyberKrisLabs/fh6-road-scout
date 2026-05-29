---
title: "[P5-S4] Save and load scan session (JSON + QSettings)"
labels: ["phase-5", "core", "persistence", "tdd"]
milestone: "Phase 5 — Results & Export"
---

## Summary
Implement save/load of a complete scan session (points, states, calibration) to JSON, with the last-used path remembered via QSettings.

## Motivation
A 7-minute scan should never need to be repeated. Saving means users can close the app and resume later.

## Acceptance Criteria
- [ ] Saved JSON contains all points with their x, y, state, confidence, and calibration matrix
- [ ] Loaded session restores all point states correctly
- [ ] Loading a session with a missing reference image path shows a warning but does not crash
- [ ] QSettings remembers the last save/load directory
- [ ] Round-trip test: save then load produces identical `ScanSession` object

## Tasks
- [ ] Write `tests/core/test_session_persistence.py` with failing tests
- [ ] Test round-trip: save to tmp file, load, compare all fields
- [ ] Test: loading with missing reference image path logs a warning
- [ ] Test: corrupt/invalid JSON raises a descriptive error
- [ ] Implement save/load in MainWindow (or extract to a `SessionStore` helper)

## Dependencies
P1-S2, P3-S3

## Notes
Use `tmp_path` pytest fixture for file I/O tests — no permanent files created.
