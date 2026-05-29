---
title: "[P6-S6] GitHub Actions Release: build .exe on vX.Y.Z tag"
labels: ["phase-6", "devops", "release"]
milestone: "Phase 6 — Polish & Packaging"
---

## Summary
Activate and verify the `.github/workflows/release.yml` workflow that builds `HorizonScout.exe` and attaches it to a GitHub Release on every version tag.

## Motivation
Manual release builds are error-prone and slow. Automated releases ensure users always get a freshly-built binary from a tagged commit.

## Acceptance Criteria
- [ ] Pushing `v0.1.0` tag triggers the release workflow
- [ ] Workflow builds `HorizonScout.exe` on `windows-latest`
- [ ] Exe is attached as a release asset on the GitHub Release
- [ ] Release notes are auto-generated from commit messages
- [ ] Workflow fails fast if PyInstaller build fails

## Tasks
- [ ] Push first release tag `v0.1.0` after P6-S4 is verified
- [ ] Confirm workflow runs and attaches the exe
- [ ] Verify the downloaded exe works on a clean machine
- [ ] Document the release process in CLAUDE.md

## Dependencies
P6-S5

## Notes
Uses `softprops/action-gh-release@v2`. Ensure `GITHUB_TOKEN` has write permissions for releases.
