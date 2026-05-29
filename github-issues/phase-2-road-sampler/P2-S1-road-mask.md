---
title: "[P2-S1] RoadSampler: HSV threshold road mask"
labels: ["phase-2", "core", "tdd"]
milestone: "Phase 2 — Road Sampler"
---

## Summary
Implement `RoadSampler._road_mask()` which converts a BGR image to a binary mask isolating bright, low-saturation road pixels.

## Motivation
Road detection is the foundation of the sampler. A solid mask means clean road centerlines and accurate scan point placement.

## Acceptance Criteria
- [ ] A white line on a dark background produces a mask covering the line pixels
- [ ] Bright-coloured (high-saturation) pixels are excluded from the mask
- [ ] Morphological open/close removes isolated noise pixels
- [ ] Returns a single-channel uint8 ndarray with 0/255 values
- [ ] Tested with synthetic images (no FH6 game assets required)

## Tasks
- [ ] Create `tests/fixtures/` with synthetic test images: white_line.png, no_roads.png
- [ ] Write `tests/core/test_road_sampler.py` with failing mask tests first
- [ ] Test white line on black → mask is non-zero along the line
- [ ] Test black image → mask is all zero
- [ ] Test coloured pixels (high saturation) are excluded
- [ ] Implement `_road_mask()` until tests pass

## Dependencies
P1-S1

## Notes
Generate synthetic test images programmatically in a pytest fixture using numpy/cv2 — avoids committing binary test assets.
