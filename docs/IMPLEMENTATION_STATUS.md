# Unified implementation status — 2026-10-08

Spec consolidation 0.1.3; software 0.1.1.dev2; clinical wire Schema 0.1.0.
Baseline: GitHub main 3fdee119; v0.1.0 remains the immutable published alpha.

The original nine-document v0.1 plan is retained, including all M0–M6 milestones
and Product Definition of Done. This change restores requirements and implements
the safety and deterministic rules slices; it is not completion of the full plan.

| Milestone | Previous local work available to port | Current GitHub slice / next acceptance |
|---|---|---|
| M0: contracts/development baseline | Seven schemas, immutable wire models, cross-field validators, locked core/build install | Schemas, validators, immutable wire snapshots, fixtures and task-policy parity restored; canonical library/CLI integrated. Full deployment lock and HTTP remain pending |
| M1: deterministic rules/Patient State | Six-task finite Chinese grammar, whole-source preflight, evidence/subject/time/conflict checks | Ported and locally tested for the declared finite grammar. All source text is checked; facts cannot override evidence; request isolation and metadata redaction covered. General clinical NLP is not claimed |
| M2: real Strands | Loopback HTTP adapter, strict deployment manifest and fake-server tests | Existing GitHub callable adapter retained; wire adapter/manifest port, exact base revision, checksums and at least ten real synthetic smoke cases pending |
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
3. Port the verified Strands HTTP contract and complete real deployment acceptance.
4. Integrate routing/post-validation/CLI/API, then opt-in frontier gates.
5. Evaluate actual provider outputs using frozen grouped splits; calibration remains
   review-only until original quality/eligibility gates are met.
6. Complete Product DoD and packaging/license/release checks.

OpenMed, numeric IOP/acuity extraction and other optional experiments do not expand
the six-task release scope or the ophthalmic Copilot MVP. Existing extraction
scorer fixtures are preserved as historical engineering regression assets.
