---
title: "[P3-S2] Calibrator.transform(): accuracy and rounding"
labels: ["phase-3", "core", "tdd"]
milestone: "Phase 3 — Calibration"
---

## Summary
Verify and harden `transform()` rounding behaviour and test it against a realistic calibration scenario (different image size vs screen resolution).

## Motivation
Sub-pixel rounding errors in the transform cause the mouse to land in the wrong place. This story ensures integer output is correctly rounded.

## Acceptance Criteria
- [ ] Output is always a tuple of two Python `int` values (not float)
- [ ] Rounding is `round()` (nearest), not `int()` (truncate)
- [ ] A realistic scenario (1920×1080 screen, 4096×4096 reference map) transforms correctly
- [ ] Points near map edges do not produce negative screen coordinates for a sensible calibration

## Tasks
- [ ] Write test: transform returns `(int, int)` tuple
- [ ] Write test: rounding is nearest-integer (0.6 → 1, not 0)
- [ ] Write test: realistic scale-down scenario (large map → 1080p screen)
- [ ] Harden implementation if any tests fail

## Dependencies
P3-S1

## Notes
Keep this story small — it is a hardening pass on P3-S1, not a new feature.
