# Unified implementation status — 2026-10-08

Spec consolidation 0.1.4; software 0.1.1.dev3; clinical wire Schema 0.1.0.
Original GitHub baseline: 3fdee119; rules slice: PR #8 / 3b75f12c; v0.1.0 remains the immutable published alpha.

The original nine-document v0.1 plan is retained, including all M0–M6 milestones
and Product Definition of Done. This change restores requirements and implements
the safety and deterministic rules slices; it is not completion of the full plan.

| Milestone | Previous local work available to port | Current GitHub slice / next acceptance |
|---|---|---|
| M0: contracts/development baseline | Seven schemas, immutable wire models, cross-field validators, locked core/build install | Schemas, validators, immutable wire snapshots, fixtures and task-policy parity restored; canonical library/CLI integrated. Full deployment lock and HTTP remain pending |
| M1: deterministic rules/Patient State | Six-task finite Chinese grammar, whole-source preflight, evidence/subject/time/conflict checks | Ported and locally tested for the declared finite grammar. All source text is checked; facts cannot override evidence; request isolation and metadata redaction covered. General clinical NLP is not claimed |
| M2: real Strands | Loopback HTTP adapter, strict deployment manifest and fake-server tests | Legacy callable retained; pinned v19 loopback adapter, frozen administrator manifest, fake-server conformance and ten-case opt-in runner implemented. Base artifact verification/checksums, runtime lock and ten REAL synthetic smoke executions pending |
| M3: routing/orchestration | Rules-only CLI/API and conservative dev2 unknown-task orchestration | Legacy model gates retained; canonical rules/review facade and CLI implemented. Full provider orchestration, HTTP API and calibrated model eligibility pending |
| M4: optional frontier | Dev2 bounded gateway and request-bound synthetic export grants, mock tests | Still pending port and acceptance. No cloud calls exist in this slice; ESCALATE grants no export permission |
| M5: evaluation/calibration | Eight smoke cases; unfinished runner and review-only histogram candidates | GitHub's 30 routing and 24 extraction-scorer cases retained. New routing fixture 0.3 reflects review-only defaults. Actual provider predictions, formal grouped splits, independent annotation, ECE/Brier/latency and unsafe gates pending |
| M6: packaging/release | Original specs/license records, partial source/wheel work | Specs and Coding Agent entry restored; wheel catalog/schema resources included. Full DoD, dependency/model locks, installation evidence and public stable release still pending |

## Default behavior

The legacy model-routing entry currently returns HUMAN_REVIEW for all valid
requests. Model auto coverage is 0. Unknown/out-of-scope task, moderate/high/unknown
risk, capability mismatch, invalid schema or missing evidence cannot bypass review.
Native confidence and metadata cannot create calibration or deployment authority.
MedSystem1.decide uses the canonical wire contract and finite rules; low-risk
supported structure may complete via rules with null model probabilities.
All-source risk/unknown/conflict locks and urgency tasks require review. This
changes deterministic coverage, not model auto coverage. There is no model/cloud
provider orchestration or HTTP service in this slice.

## Work order

1. Restoration/safety and immutable Patient State/finite rules are implemented;
   retain conformance/installed-wheel tests and the declared grammar limits.
2. Complete real Strands deployment acceptance; wire adapter and mock conformance exist.
3. Integrate routing/post-validation/CLI/API, then opt-in frontier gates.
4. Evaluate actual provider outputs using frozen grouped splits; calibration remains
   review-only until original quality/eligibility gates are met.
5. Complete Product DoD and packaging/license/release checks.

OpenMed, numeric IOP/acuity extraction and other optional experiments do not expand
the six-task release scope or the ophthalmic Copilot MVP. Existing extraction
scorer fixtures are preserved as historical engineering regression assets.

The standalone StrandsHttpProvider is opt-in infrastructure, not called by
MedSystem1.decide/CLI. It returns immutable bounded candidates, no evidence spans,
calibration eligibility or action authority. Base provenance reports an inferred
SHA; the trusted verified base_revision remains null. See STRANDS_DEPLOYMENT.md.
