---
title: "[P6-S2] FT template capture: guided in-app workflow"
labels: ["phase-6", "ui", "ux"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Implement an in-app guided workflow for capturing the fast-travel indicator template, replacing the manual file-drop instruction.

## Motivation
The template is required for detection but the current README-based capture process is too technical for most users.

## Acceptance Criteria
- [ ] Wizard triggered from a "Capture FT Template" button
- [ ] Instructions explain: open FH6 map, hover over an explored road
- [ ] User presses F9 to capture a screen region around the cursor
- [ ] Preview of the captured region is shown for confirmation
- [ ] Confirmed capture is saved to `assets/ft_indicator.png`
- [ ] Detector is reloaded after saving

## Tasks
- [ ] Design wizard dialog (2 steps: instructions → preview/confirm)
- [ ] Implement F9 capture using mss ROI around cursor
- [ ] Implement preview widget showing captured image
- [ ] Save confirmed image and reload Detector
- [ ] Add a manual re-capture option accessible from Settings

## Dependencies
P4-S1, P6-S1

## Notes
This story has limited automated tests — the F9 capture is hardware-dependent. Focus tests on the preview/confirm step.
