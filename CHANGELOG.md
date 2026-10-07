# Changelog

## 0.1.1 - Unreleased

### Fixed
- Reject boolean/non-numeric confidence, invalid thresholds, and non-boolean schema/evidence signals.
- Keep explicit high/unknown task risk on HUMAN_REVIEW before checking evidence.
- Reject non-finite, out-of-range, or boolean adapter confidence.

### Development
- Verify distribution metadata and run CI tests against the installed wheel.
- Document first PyPI publication and recovery without moving the v0.1.0 tag.
- Main uses 0.1.1.dev0; no new release is implied by these changes.

## 0.1.0 - 2026-10-06 (Alpha)

### Added
- Dependency-light medical AI safety router.
- LOCAL / HUMAN_REVIEW / ESCALATE routing contract.
- Explicit high-risk capability boundary.
- ExtractionProvider and DecisionProvider protocols.
- Synthetic Chinese ophthalmology examples and benchmark scaffold.
- Python 3.10-3.12 CI and core safety tests.

### Safety
- Model confidence is never treated as clinical authority.
- Unknown capabilities fail conservatively.
- High-risk clinical capabilities require human review.
