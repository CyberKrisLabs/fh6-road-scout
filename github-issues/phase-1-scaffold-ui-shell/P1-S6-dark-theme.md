---
title: "[P1-S6] Dark theme: Forza-inspired orange/black stylesheet"
labels: ["phase-1", "ui", "design"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Apply a consistent dark theme (near-black background, orange accent) to the entire application via a Qt stylesheet.

## Motivation
Visual consistency and the right "game companion" aesthetic. Should be applied globally so future widgets inherit it automatically.

## Acceptance Criteria
- [ ] App background is near-black (#12121A)
- [ ] Primary accent colour is orange (#FF6B1A)
- [ ] All buttons, labels, progress bar, and dialogs follow the theme
- [ ] Theme is defined in a single `app/ui/theme.py` `STYLESHEET` constant
- [ ] Applied once in `main.py` via `QApplication.setStyleSheet()`
- [ ] No hard-coded colours in widget code — only via property classes in the stylesheet

## Tasks
- [ ] Write a visual smoke test: load the app, assert `QApplication.styleSheet()` is non-empty
- [ ] Define all colour tokens in `theme.py`
- [ ] Verify all property classes used in widgets are defined in the stylesheet
- [ ] Manual review: launch app, confirm theme renders correctly

## Dependencies
P1-S3, P1-S4, P1-S5

## Notes
This story has minimal automated tests — the acceptance criteria are mostly visual. Manual review is the primary verification.
