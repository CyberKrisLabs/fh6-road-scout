---
title: "[P4-S2] Detector: teal color heuristic fallback"
labels: ["phase-4", "core", "tdd"]
milestone: "Phase 4 — Scanner Engine"
---

## Summary
Implement `Detector._color_heuristic()` which detects the FT indicator by looking for the distinctive teal/cyan colour in the ROI, used as a fallback when template matching is inconclusive.

## Motivation
Template matching degrades with UI scaling or game updates. The colour heuristic provides a robust secondary signal.

## Acceptance Criteria
- [ ] An ROI with teal pixels (HSV hue 82–105, high sat/val) returns score > 0.02
- [ ] An ROI with no teal pixels returns score ≤ 0.02
- [ ] `is_fast_travel_visible()` returns True when either template match OR colour passes
- [ ] `is_fast_travel_visible()` returns False when both fail
- [ ] Confidence returned is the higher of the two scores

## Tasks
- [ ] Write failing tests for teal-positive and teal-negative ROIs
- [ ] Write integration tests for `is_fast_travel_visible()` combining both strategies
- [ ] Implement `_color_heuristic()` using `cv2.inRange` on HSV
- [ ] Implement combined `is_fast_travel_visible()` logic

## Dependencies
P4-S1

## Notes
HSV teal range for FH6: hue 82–105, sat 140–255, val 160–255. Adjust thresholds once real game screenshots are available.
