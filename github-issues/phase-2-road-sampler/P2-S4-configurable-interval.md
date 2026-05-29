---
title: "[P2-S4] RoadSampler: configurable sample interval"
labels: ["phase-2", "core", "settings", "tdd"]
milestone: "Phase 2 — Road Sampler"
---

## Summary
Expose the sample interval as a configurable parameter stored in `QSettings`, and surface it in the UI so users can trade scan speed for accuracy.

## Motivation
A larger interval = fewer points = faster scan but may miss short road segments. Users should control this trade-off.

## Acceptance Criteria
- [ ] `RoadSampler(interval=N)` uses N as the spacing threshold
- [ ] Interval is persisted to and loaded from `QSettings`
- [ ] Changing the interval in settings and reloading the map re-samples at the new spacing
- [ ] Valid range: 5–50 pixels (validated, clamped)

## Tasks
- [ ] Write test: `RoadSampler(interval=5)` produces more points than `interval=30` on the same image
- [ ] Write test: interval is clamped to [5, 50]
- [ ] Add QSettings persistence for interval
- [ ] Expose interval field in Settings dialog (P6-S1 dependency — stub for now)

## Dependencies
P2-S3

## Notes
QSettings key: `sampler/interval`, default 15.
