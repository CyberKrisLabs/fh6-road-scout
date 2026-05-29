---
title: "[P4-S1] Detector: template matching for fast-travel indicator"
labels: ["phase-4", "core", "tdd"]
milestone: "Phase 4 — Scanner Engine"
---

## Summary
Implement `Detector.load_template()` and `_template_match()` to detect the presence of the FT indicator via OpenCV template matching.

## Motivation
Template matching is the primary detection method. Its accuracy directly determines how many roads are correctly classified.

## Acceptance Criteria
- [ ] `load_template()` with a valid path sets internal template; invalid path leaves it None
- [ ] `_template_match()` returns a score ≥ 0.72 when the ROI contains the template
- [ ] `_template_match()` returns a score < 0.3 when the ROI does not contain the template
- [ ] Template is auto-scaled down if it is larger than the ROI
- [ ] Returns 0.0 if no template is loaded

## Tasks
- [ ] Write `tests/core/test_detector.py` with failing tests first
- [ ] Create a synthetic template (coloured rectangle) and a matching ROI for tests
- [ ] Test: ROI containing template → score ≥ 0.72
- [ ] Test: ROI without template → score < 0.3
- [ ] Test: no template loaded → score is 0.0
- [ ] Test: template larger than ROI → auto-scaled, no crash
- [ ] Implement `load_template()` and `_template_match()` until tests pass

## Dependencies
P1-S1

## Notes
Create synthetic test fixtures with numpy (no game screenshots needed). A bright-coloured 80×30 block on a dark background works well.
