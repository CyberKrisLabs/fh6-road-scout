---
title: "[P2-S3] RoadSampler: sample skeleton into ScanPoint list"
labels: ["phase-2", "core", "tdd"]
milestone: "Phase 2 — Road Sampler"
---

## Summary
Implement `RoadSampler._sample_skeleton()` and the top-level `sample()` method that returns a list of `ScanPoint` objects spaced at least `interval` pixels apart.

## Motivation
The sample list drives the entire scan loop. Spacing must be configurable and the output must be deterministic.

## Acceptance Criteria
- [ ] Points are spaced at least `interval` pixels apart (default 15)
- [ ] No two returned points are closer than `interval` pixels
- [ ] An all-black skeleton returns an empty list
- [ ] `sample(path)` returns empty list for an unreadable image path
- [ ] All returned points have `state == DiscoveryState.UNKNOWN`

## Tasks
- [ ] Write failing tests for spacing guarantee and empty-image cases
- [ ] Test that every pair of consecutive points has distance ≥ interval
- [ ] Test `sample()` with a valid synthetic road image returns > 0 points
- [ ] Test `sample()` with invalid path returns empty list (no exception)
- [ ] Implement `_sample_skeleton()` and `sample()` until tests pass

## Dependencies
P2-S1, P2-S2

## Notes
The spacing check should use Euclidean distance, not Manhattan.
