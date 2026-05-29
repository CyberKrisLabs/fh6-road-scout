---
title: "[P3-S1] Calibrator.fit(): affine transform from 3 point pairs"
labels: ["phase-3", "core", "tdd"]
milestone: "Phase 3 — Calibration"
---

## Summary
Implement `Calibrator.fit()` which computes a 2×3 affine transform matrix from 3 reference-map / screen-coordinate point pairs.

## Motivation
The calibrator is the bridge between reference map pixels and game screen pixels. Accuracy here directly determines scan accuracy.

## Acceptance Criteria
- [ ] `fit()` with 3 valid point pairs sets `is_fitted = True`
- [ ] `fit()` with fewer than 3 pairs raises `ValueError`
- [ ] After fitting with identity-mapped points, `transform()` returns the input unchanged
- [ ] After fitting with a known translation, `transform()` returns the translated coords
- [ ] `transform()` raises `RuntimeError` when called before `fit()`

## Tasks
- [ ] Write `tests/core/test_calibrator.py` with failing tests first
- [ ] Test identity transform: ref points == screen points → transform is identity
- [ ] Test translation: screen = ref + (100, 50) → transform outputs ref + (100, 50)
- [ ] Test scaling: screen = ref * 2 → transform doubles coordinates
- [ ] Test error cases: < 3 points, unfitted transform call
- [ ] Implement `Calibrator.fit()` and `Calibrator.transform()` until tests pass

## Dependencies
P1-S1

## Notes
Use `QPointF` in the API to stay consistent with the UI, but convert to numpy float32 internally for `cv2.getAffineTransform`.
