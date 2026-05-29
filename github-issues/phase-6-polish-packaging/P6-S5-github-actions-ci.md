---
title: "[P6-S5] GitHub Actions CI: lint + test on push/PR"
labels: ["phase-6", "devops", "ci"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Activate and verify the `.github/workflows/ci.yml` CI pipeline that runs ruff, mypy, and pytest on every push and pull request.

## Motivation
CI catches regressions automatically and signals to contributors that the project has quality gates.

## Acceptance Criteria
- [ ] CI runs on push to `main` and `develop` and on all PRs
- [ ] Lint job fails if ruff reports any violations
- [ ] Type check job fails if mypy reports any errors
- [ ] Test job fails if any test fails or coverage drops below 80%
- [ ] Green CI badge visible on README

## Tasks
- [ ] Push repo to GitHub (once account is ready)
- [ ] Trigger CI with a passing commit and verify all 3 jobs go green
- [ ] Trigger CI with an intentional ruff violation and verify lint job fails
- [ ] Add coverage badge to README
- [ ] Confirm Windows runner resolves PySide6 Qt platform plugin correctly

## Dependencies
P6-S4

## Notes
PySide6 on headless Windows CI may need `QT_QPA_PLATFORM=offscreen` env var. Add to the test job env block.
