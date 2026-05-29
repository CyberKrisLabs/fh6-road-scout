---
title: "[P1-S1] Dev tooling setup: ruff, mypy, pytest, pre-commit"
labels: ["phase-1", "tooling", "dx"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Set up the full developer toolchain so every contributor has consistent linting, type checking, testing, and git hooks from day one.

## Motivation
Without enforced tooling from the start, code quality drifts and ruff/mypy violations accumulate. This story installs and verifies everything before any feature code is written.

## Acceptance Criteria
- [ ] `ruff check .` and `ruff format --check .` both pass with zero violations
- [ ] `mypy app/` reports no errors
- [ ] `pytest tests/` runs and exits 0 (even with an empty test suite)
- [ ] `pre-commit install` hooks run on `git commit`
- [ ] `requirements-dev.txt` installs cleanly on a fresh Python 3.12 venv

## Tasks
- [ ] Install requirements-dev.txt in a clean venv and verify no conflicts
- [ ] Run `pre-commit install` and verify hooks fire on a test commit
- [ ] Add a `tests/__init__.py` and `tests/core/__init__.py` so pytest discovers correctly
- [ ] Write a trivial smoke test (`test_imports.py`) confirming all app modules import
- [ ] Verify `ruff check .` passes on the existing scaffold
- [ ] Verify `mypy app/` passes (fix any annotation gaps)

## Dependencies
None — this is the first story.

## Notes
P1-S1 is the only story with no failing test to write first — its own test IS the toolchain verification smoke test.
