---
title: "[P2-S2] RoadSampler: skeletonize road mask to centerlines"
labels: ["phase-2", "core", "tdd"]
milestone: "Phase 2 — Road Sampler"
---

## Summary
Implement `RoadSampler._skeletonize()` which thins the road mask to single-pixel centerlines using ximgproc thinning with a morphological fallback.

## Motivation
Sampling a wide road mask directly produces duplicate points. The skeleton gives us one clean path per road to sample along.

## Acceptance Criteria
- [ ] A filled rectangle input produces a skeleton that is thinner than the input
- [ ] A single-pixel line input is unchanged by thinning
- [ ] The morphological fallback is tested when ximgproc is monkey-patched out
- [ ] Output is a single-channel uint8 ndarray

## Tasks
- [ ] Write failing tests: thick line → skeleton is thinner (max width ≤ 1px row)
- [ ] Write fallback test: patch `cv2.ximgproc` to raise AttributeError, confirm fallback runs
- [ ] Implement `_skeletonize()` with ximgproc primary and `_morph_skeleton()` fallback
- [ ] Ensure both paths return equivalent results on the same input

## Dependencies
P2-S1

## Notes
Use `unittest.mock.patch` to simulate missing ximgproc for the fallback test.
