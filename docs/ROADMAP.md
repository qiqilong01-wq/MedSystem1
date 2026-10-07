# Bounded roadmap and handoff

This tracks the existing README roadmap. It does not change the Ophthalmology
Copilot v0.2 MVP, its Patient State contract, or its application milestones.

## Current baseline

- v0.1.0 is the published GitHub alpha tag; preserve its commit.
- Main uses 0.1.1.dev0 for routing/provider hardening; it is not a new release.
- Verify PyPI upload separately using [PUBLISHING.md](PUBLISHING.md).
- Core remains dependency-free; synthetic benchmark cases are not clinical validation.

## Work in order

1. **Routing contracts and calibration hooks.** Harden runtime confidence,
   thresholds, boolean safety signals, and high-risk precedence first. Reject
   malformed requests with `ValueError`; the caller must stop that operation
   and require repair/review, never treat exceptions as authorization. Default
   thresholds are engineering policy, not statistically calibrated safety
   guarantees. Calibration hooks require benchmark evidence before implementation.
2. **Optional providers.** OpenMed and Strands callable adapters have explicit
   contracts, normalized-state validation, and conformance coverage for
   missing/malformed state, absent evidence, output shapes, and provider failures.
   See [PROVIDERS.md](PROVIDERS.md). Real SDK/model integration remains
   unvalidated until tested with versioned synthetic fixtures. Do not add model
   dependencies/downloads to core.
3. **Ophthalmology benchmark.** A 30-case versioned synthetic routing regression
   now runs in CI and reports failures and coverage. Its scenario signals are
   supplied annotations, not extracted facts. A separate 24-case extraction
   evaluator scores recorded scalar facts and evidence; its gold-replay self-test
   is not a model result. See [EXTRACTION_EVALUATION.md](EXTRACTION_EVALUATION.md).
   Next compare a real injected provider only after its license, version,
   task prompts, normalization, and runtime are chosen.
   Do not equate policy regression success with extraction or clinical performance.
4. **Audit events and conformance.** Add minimal read-only decision/failure
   events when their schema and consumer are established; do not log raw clinical
   text by default. No distributed control plane or automatic repair.
5. **Integration validation.** Validate a text/mock integration against the
   application's authoritative Patient State schema and doctor-review boundary
   before considering broader workflows.

## Copilot boundary

MedSystem1 supplies bounded extraction/routing infrastructure. It does not
replace the application's Patient State, Evidence, State Merger, permission
layer, cost ledger, or doctor approval. A LOCAL decision authorizes only the
bounded task already permitted by the caller. ESCALATE grants no new capability.

No new ASR/OCR, diagnosis, prescribing, autonomous patient instructions,
medical-record submission, HIS/PACS, enterprise permissions, or multi-agent
runtime is required by this roadmap. Keep the v0.2 text/mock milestone and
existing recording-to-reviewed-note workflow as the product priority.
