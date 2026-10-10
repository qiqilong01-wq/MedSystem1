# Local orchestration validation — 2026-10-09

Software 0.1.1.dev4; spec consolidation 0.1.5; clinical Schema 0.1.0.
Based on transport PR #9 / d8a3bce6. This is a conservative M3 library/CLI slice,
not real deployment acceptance or a completed release.

## Observed checks

- Python 3.12.14, pytest: **343 passed**. New cases cover rules/whole-source/urgency
  priority, task capabilities, version identity, independent candidate validation,
  nonfinite/duplicate probability JSON, no fabricated facts/evidence/calibration,
  late/error responses, redacted metadata, request isolation and aggregate route locks.
- unittest discover: **77 passed**, overlapping pytest coverage, not additional tests.
- Fake loopback server exercised the full manifest -> MedSystem1.decide -> candidate
  validation -> review response, plus CLI stdout response/stderr metadata. No actual
  model, cloud, downloads or external clinical export was involved.
- Ruff, package validator, thirty routing regression cases and twenty-four extraction
  scorer gold replay passed. The eight rules benchmark seeds and new synthetic
  candidate request were exercised without a model. Provider smoke fixtures remain
  unexecuted against any actual Strands model.
- sdist/wheel built; installed-wheel resources/default and explicit-disabled manifest
  checked outside checkout with sockets forbidden. No new runtime dependency.

Source checks use PYTHONPATH=src; installed-wheel checks run separately without that
setting. CI results belong to the associated PR; no real-provider/calibration metrics
are claimed by this report.

## Limits

Default is rules-only. Explicit verified administrator deployment may call only
authorized low-risk unknown tasks; every candidate stays review-required.
Native probability never enables auto. Matching unknown retains rule context, not
model-supplied evidence. Disagreement clears the value/evidence and raises uncertainty.

Timeouts reject late results; synchronous custom adapters must honor their budget.
No hard thread termination/watchdog is claimed. Real artifact/base/loader checks and
ten actual synthetic Strands requests, HTTP decide service, frontier/privacy gates,
formal evaluation/calibration and release Definition of Done remain open.
