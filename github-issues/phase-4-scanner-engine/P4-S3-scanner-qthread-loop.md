---
title: "[P4-S3] Scanner: QThread hover-capture-detect loop"
labels: ["phase-4", "core", "threading", "tdd"]
milestone: "Phase 4 — Scanner Engine"
---

## Summary
Implement the `Scanner` QThread that moves the mouse to each road point, captures the ROI, detects fast-travel presence, and emits results via signals.

## Motivation
The scan loop is the core of the application. Thread safety, signal emission, and correct UNKNOWN → DISCOVERED/UNDISCOVERED state transitions must all be tested.

## Acceptance Criteria
- [ ] `Scanner` is a `QObject` that can be moved to a `QThread`
- [ ] `point_scanned` signal is emitted for each point after detection
- [ ] `progress` signal is emitted every 10 points
- [ ] `finished` signal is emitted when all points are processed
- [ ] Points with non-UNKNOWN state are skipped (resume support)
- [ ] Mouse movements use `pyautogui.FAILSAFE = True`
- [ ] Scan can be stopped by calling `stop()` between points

## Tasks
- [ ] Write `tests/core/test_scanner.py` with failing tests first
- [ ] Mock `pyautogui.moveTo`, `mss.MSS`, and `Detector` to avoid hardware access in tests
- [ ] Test: all points are scanned and `point_scanned` emitted for each
- [ ] Test: `finished` signal emitted after all points
- [ ] Test: pre-scanned (non-UNKNOWN) points are skipped
- [ ] Test: `stop()` halts the loop before all points are processed
- [ ] Implement `Scanner.run()` until all tests pass

## Dependencies
P3-S1, P4-S2

## Notes
Use `qtbot.waitSignal(scanner.finished, timeout=5000)` for the thread test. Mock all hardware interaction — tests must run without a game or display.
