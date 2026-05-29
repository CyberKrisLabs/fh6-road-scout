---
title: "[P6-S3] First-run onboarding guide dialog"
labels: ["phase-6", "ui", "ux"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Show a first-run onboarding dialog that walks new users through the 4-step workflow: load map → capture template → calibrate → scan.

## Motivation
The app has a non-trivial setup sequence. A guided onboarding reduces support burden and improves first-use success rate.

## Acceptance Criteria
- [ ] Dialog shown automatically on first launch (checked via QSettings flag)
- [ ] Not shown on subsequent launches unless user resets via Settings
- [ ] 4 steps shown with icons, description, and a Next/Back flow
- [ ] "Skip" option available at any point
- [ ] Step 2 links to the FT template capture workflow (P6-S2)
- [ ] Step 3 links to the calibration wizard (P3-S4)

## Tasks
- [ ] Write test: dialog shown when QSettings has no `onboarding/completed` key
- [ ] Write test: dialog not shown when `onboarding/completed` is True
- [ ] Implement `OnboardingDialog` with step carousel
- [ ] Set `onboarding/completed = True` on dialog close/skip

## Dependencies
P6-S2, P3-S4

## Notes
Keep onboarding content in a static list of dicts (step title, description, icon path) to make it easy to edit.
