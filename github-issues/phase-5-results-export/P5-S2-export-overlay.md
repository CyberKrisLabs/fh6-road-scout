---
title: "[P5-S2] export_overlay(): annotated PNG export"
labels: ["phase-5", "core", "tdd"]
milestone: "Phase 5 — Results & Export"
---

## Summary
Implement `export_overlay()` which writes a blended PNG of the reference map annotated with green/red scan result dots.

## Motivation
Users need a shareable result image to use as a reference while playing the game (e.g. on a second screen or phone).

## Acceptance Criteria
- [ ] Output image has same dimensions as reference image
- [ ] DISCOVERED points appear as green circles at correct coordinates
- [ ] UNDISCOVERED points appear as red/orange circles at correct coordinates
- [ ] UNKNOWN points are not rendered in the export
- [ ] Output file is written to the specified path
- [ ] `FileNotFoundError` raised if reference image cannot be read
- [ ] Tested with a synthetic reference image and known point list

## Tasks
- [ ] Write `tests/core/test_exporter.py` with failing tests first
- [ ] Test: output dimensions match input
- [ ] Test: a known red pixel exists at an UNDISCOVERED point location
- [ ] Test: a known green pixel exists at a DISCOVERED point location
- [ ] Test: FileNotFoundError on bad reference path
- [ ] Implement `export_overlay()` until tests pass

## Dependencies
P1-S2

## Notes
Sample pixel colour in tests with `cv2.imread` on the output file. Allow ±20 colour tolerance for the blended result.
