---
title: "[P1-S2] ScanPoint & ScanSession data models"
labels: ["phase-1", "models", "tdd"]
milestone: "Phase 1 — Project Scaffold & UI Shell"
---

## Summary
Implement the core data models (`ScanPoint`, `ScanSession`, `DiscoveryState`) with full unit test coverage.

## Motivation
All other modules depend on these types. Getting them right and tested first means downstream code can rely on a stable contract.

## Acceptance Criteria
- [ ] `ScanPoint` stores `ref_x`, `ref_y`, `state: DiscoveryState`, `confidence: float`
- [ ] `ScanSession` computes `total`, `scanned`, `discovered`, `undiscovered` correctly
- [ ] `DiscoveryState` has UNKNOWN, DISCOVERED, UNDISCOVERED variants
- [ ] All properties tested with edge cases (empty list, all unknown, mixed)
- [ ] 100% line coverage on `app/models/`

## Tasks
- [ ] Write `tests/models/test_scan_result.py` with failing tests first
- [ ] Test `ScanSession.total` returns `len(points)`
- [ ] Test `ScanSession.scanned` excludes UNKNOWN points
- [ ] Test `ScanSession.discovered` / `undiscovered` counts
- [ ] Test edge cases: empty session, all same state
- [ ] Implement `app/models/scan_result.py` until all tests pass

## Dependencies
P1-S1 (tooling must be in place)

## Notes
Use `@dataclass` with `field(default_factory=list)`. Keep models pure Python — no Qt imports.
