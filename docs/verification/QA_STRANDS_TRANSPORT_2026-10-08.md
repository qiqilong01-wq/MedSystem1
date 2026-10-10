# Strands transport validation — 2026-10-08

Software 0.1.1.dev3; based on rules PR #8, commit 3b75f12c. M2 transport slice,
not real deployment acceptance, calibration or a completed v0.1 release.

## Observed local checks

- Python 3.12.14; pytest: **322 passed**. Includes fake loopback HTTP conformance,
  trusted manifest/registry mismatch, redacted failures, same-endpoint locks,
  timeouts, invalid/duplicate JSON, probability checks, native/selected separation,
  environment proxy denial and mock-only opt-in smoke runner behavior.
- unittest discover: **56 passed**, a subset of the pytest total, not additional
  independent coverage. Temporary files redirected to workspace tmp on Windows.
- Ruff and package validator passed: seven clinical plus one administrator Schema,
  all six task definitions, default model/cloud/local-provider disabled, eight
  executed rules smoke cases, ten validated but **unexecuted real-provider** fixtures.
- Existing thirty-case routing regression and twenty-four-case extraction scorer
  gold replay passed. Gold replay validates scoring code, not a model's performance.
- sdist/wheel built; installed-wheel check outside checkout confirmed the disabled
  deployment resources and canonical rules path with socket creation forbidden.

Source checks select this checkout explicitly through PYTHONPATH=src; installed
wheel checks run in a separate process outside checkout without that setting.
No new runtime dependency, SDK, model download, external patient export or service
startup occurred. CI results are recorded on the associated PR, not fabricated here.

## Remaining evidence

No actual Strands inference was run. The base SHA reported by upstream is inferred
at training time and remains separate from verified local deployment state.
Artifact checksums in an enabled administrator manifest are administrator assertions;
this library does not hash a serving environment or remotely attest its launch.
M2 needs actual local artifacts/loader/strict-window verification, runtime versions
and notices, plus at least ten actual synthetic requests. M3 orchestration/HTTP API,
M4 frontier, M5 calibration/formal evaluation and M6 release remain open.
