---
title: "[P5-S3] "Next Gap" navigation: jump to nearest undiscovered cluster"
labels: ["phase-5", "ui", "ux", "tdd"]
milestone: "Phase 5 — Results & Export"
---

## Summary
Implement "Next Gap" which cycles through clusters of UNDISCOVERED points and re-centres the MapView on each in turn.

## Motivation
When a scan finds 10 undiscovered road segments scattered across the map, users need to step through them one by one efficiently.

## Acceptance Criteria
- [ ] Each click of "Next Gap" jumps to the next UNDISCOVERED point
- [ ] Cycling is circular: after the last undiscovered point, wraps back to the first
- [ ] Button is disabled when no UNDISCOVERED points exist
- [ ] View re-centres on the selected point
- [ ] If new UNDISCOVERED points are added during a scan, they are included in the cycle

## Tasks
- [ ] Write `tests/ui/test_main_window_nav.py` with failing tests
- [ ] Test: cycling through 3 undiscovered points visits all 3 in order
- [ ] Test: wrap-around returns to first point after last
- [ ] Test: button disabled when undiscovered count is 0
- [ ] Implement `_on_jump_next()` in MainWindow
- [ ] Verify `map_view.jump_to_point()` is called with the correct point

## Dependencies
P1-S5, P5-S1

## Notes
Index the undiscovered list lazily on each button press (regenerate from session). No need for a maintained sorted data structure.
