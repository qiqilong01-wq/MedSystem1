# Changelog

## 0.1.0 - Release candidate

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
