---
title: "[P3-S3] Calibrator: serialise/deserialise via QSettings"
labels: ["phase-3", "core", "persistence", "tdd"]
milestone: "Phase 3 — Calibration"
---

## Summary
Implement `Calibrator.to_dict()` / `from_dict()` and persist calibration data in `QSettings` so it survives app restarts.

## Motivation
Re-calibrating on every launch is tedious. Persisting calibration means users only calibrate once per session/setup.

## Acceptance Criteria
- [ ] `to_dict()` on an unfitted calibrator returns `{}`
- [ ] `from_dict({})` leaves `is_fitted = False`
- [ ] Round-trip: `from_dict(to_dict())` produces the same `transform()` output
- [ ] Calibration is saved to QSettings on `fit()` and auto-loaded on app start

## Tasks
- [ ] Write failing tests for `to_dict` / `from_dict` round-trip
- [ ] Test empty dict → is_fitted remains False
- [ ] Test full round-trip preserves transform accuracy to 3 decimal places
- [ ] Implement serialisation methods
- [ ] Wire QSettings save/load into MainWindow

## Dependencies
P3-S1

## Notes
QSettings key: `calibration/matrix`. Store as a JSON string (list of lists).
