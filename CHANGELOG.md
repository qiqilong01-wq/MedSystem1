# Changelog

## 0.1.1.dev4 — 2026-10-09 (unreleased)

- Bind explicit administrator local deployment to canonical decide/CLI; keep default
  rules-only, no model auto or cloud calls. Known facts and all review locks skip
  inference; only authorized low-risk unknown tasks reach one bounded local call.
- Independently snapshot/validate candidate shape, exact pinned descriptor, task
  coverage/order, finite probabilities and native confidence consistency.
- Reject late/invalid/failing provider output into review with fixed redacted codes.
  Matching unknown labels retain only rule context; disagreements clear value
  and evidence, raise uncertainty and never add Patient State facts.
- Include trusted deployment digest in configuration identity and measure local
  time in core. Strengthen aggregate route validation to forbid review downgrades.
- Add mock orchestration/CLI-loopback tests and an original synthetic candidate
  request. Real Strands, HTTP decide API, frontier/calibration/release remain open.

## 0.1.1.dev3 — 2026-10-08 (unreleased)

- Add separate canonical bounded-provider protocol and pinned v19 loopback HTTP
  adapter, retaining the legacy callable adapter. Trusted catalog owns questions.
- Add immutable administrator deployment manifest/schema, exact revision checks,
  required launch/checksum attestations and default-disabled packaged config.
- Reject redirects, duplicate JSON, invalid probabilities/envelopes, wrong health
  identity/cache settings, oversized input/output, retries and unsupported tasks.
- Serialize same-endpoint calls within this process; include queue/health/inference
  in the deadline. Return candidates without evidence, calibrated scores or grants.
- Add ten original synthetic smoke fixtures and an explicit opt-in runner;
  installation/ordinary tests never load models or invoke that runner against a model.
- Recheck pinned code/model license sources; record inferred upstream base SHA
  separately from verified deployment state. Real M2 acceptance remains pending.

## 0.1.1.dev2 — 2026-10-08 (unreleased)

- Port original immutable Schema-backed wire models and request-scoped Patient State;
  snapshot JSON before validation and redact clinical identifiers from debug repr.
- Port the finite six-task Chinese rules, whole-source preflight and evidence
  checking, preserving historical/other-subject/negation/unknown/conflict behavior.
- Add MedSystem1.decide for canonical requests alongside legacy advisory route,
  plus local demo/decide CLI with strict JSON and fixed redacted errors.
- Preserve model auto/cloud disabled. Low-risk deterministic structure can complete;
  risk, unknown grammar, conflicts and urgency retain mandatory review.
- Reuse original rules/kernel tests and add facade isolation, provenance and transport
  safety tests. Real providers, HTTP, calibration and formal benchmark remain pending.

## 0.1.1.dev1 — 2026-10-07 (unreleased)

- Restore the complete original v0.1 specification set, seven canonical schemas,
  versioned task/policy/provider configs, fixtures and shared AGENTS/CLAUDE entry.
- Enforce the trusted six-task catalog and task-owned risk/capability; unknown or
  clinical-action tasks cannot obtain LOCAL by claiming a low-risk capability.
- Default model routing to HUMAN_REVIEW regardless of native confidence. Moderate
  risk, invalid schema and missing evidence now lock review rather than ESCALATE.
- Preserve legacy Python input shape and released v0.1.0 tag; document intentionally
  tightened behavior and unfinished canonical wire/orchestrator integration.
- Add regression fixture v0.3 without rewriting v0.2 or extraction gold truth.
  Current model auto coverage is 0; gold replay remains a scorer self-test.
- Package schemas/catalog in wheels; add canonical validation and scope tests.
  Full M0–M6 acceptance, real Strands, calibration and release benchmark remain pending.

## 0.1.1 - Unreleased

### Fixed
- Reject boolean/non-numeric confidence, invalid thresholds, and non-boolean schema/evidence signals.
- Keep explicit high/unknown task risk on HUMAN_REVIEW before checking evidence.
- Reject non-finite, out-of-range, or boolean adapter confidence.
- Reject malformed extraction batches and unmatched literal evidence instead of returning partial success.
- Validate normalized provider state and decision metadata; remove opaque raw-result metadata.

### Added
- ProviderContractError / ProviderExecutionError and public normalized-state validation.
- Provider conformance tests including authority boundaries and execution failures.
- Versioned 30-case synthetic ophthalmology routing-policy regression runner with failure exit codes.
- Evidence-aware offline extraction evaluator, 24 synthetic gold cases, and a recorded-prediction CLI.
- Separate factual/source-supported scores, output-error counts, and an explicitly labeled gold-replay self-test.

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

