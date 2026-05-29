---
title: "[P4-S4] Scanner: pause, resume, and stop controls"
labels: ["phase-4", "core", "ux", "tdd"]
milestone: "Phase 4 — Scanner Engine"
---

## Summary
Implement and test the pause/resume/stop control flow in the scanner, and wire the ScanPanel buttons to the Scanner instance in MainWindow.

## Motivation
Users need to interrupt a scan (e.g. to interact with the game) without losing progress. Pause/resume must leave the session state intact.

## Acceptance Criteria
- [ ] `pause()` suspends the loop between points without losing state
- [ ] `resume()` continues from the next unscanned point
- [ ] `stop()` exits the loop and triggers `finished`
- [ ] Paused points retain their UNKNOWN state
- [ ] Panel buttons correctly reflect running/paused/stopped states
- [ ] Stopping a paused scanner works correctly

## Tasks
- [ ] Write failing tests: pause mid-scan, verify state after pause, resume, verify completion
- [ ] Write test: stop from paused state emits `finished`
- [ ] Implement `pause()`, `resume()`, `stop()` in Scanner
- [ ] Wire Pause/Stop buttons in MainWindow to Scanner instance
- [ ] Test panel state transitions via MainWindow integration test

## Dependencies
P4-S3

## Notes
Use a threading.Event or a simple flag with `while self._paused: time.sleep(0.05)`. Keep the pause check inside the loop, not between threads.
