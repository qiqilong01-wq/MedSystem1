# Unified implementation status — 2026-10-07

Spec consolidation 0.1.2; software 0.1.1.dev1; clinical wire Schema 0.1.0.
Baseline: GitHub main 3fdee119; v0.1.0 remains the immutable published alpha.

The original nine-document v0.1 plan is retained, including all M0–M6 milestones
and Product Definition of Done. This change restores requirements and implements
the first safety slice; it is not completion of the full plan.

| Milestone | Previous local work available to port | Current GitHub slice / next acceptance |
|---|---|---|
| M0: contracts/development baseline | Seven schemas, immutable wire models, cross-field validators, locked core/build install | Schemas, validators, fixtures and task-policy parity restored. Legacy dataclasses remain; wire models/API integration and complete lock still pending |
| M1: deterministic rules/Patient State | Six-task finite Chinese grammar, whole-source preflight, evidence/subject/time/conflict checks | Not yet ported. Preserve these tests and behavior; do not substitute caller flags for extraction |
| M2: real Strands | Loopback HTTP adapter, strict deployment manifest and fake-server tests | Existing GitHub callable adapter retained; wire adapter/manifest port, exact base revision, checksums and at least ten real synthetic smoke cases pending |
| M3: routing/orchestration | Rules-only CLI/API and conservative dev2 unknown-task orchestration | Six-task scope and task-owned risk/capability now enforced; native scores cannot auto-complete; moderate/evidence/scope locks restored. Full wire orchestration/API, calibration eligibility and rule route pending |
| M4: optional frontier | Dev2 bounded gateway and request-bound synthetic export grants, mock tests | Still pending port and acceptance. No cloud calls exist in this slice; ESCALATE grants no export permission |
| M5: evaluation/calibration | Eight smoke cases; unfinished runner and review-only histogram candidates | GitHub's 30 routing and 24 extraction-scorer cases retained. New routing fixture 0.3 reflects review-only defaults. Actual provider predictions, formal grouped splits, independent annotation, ECE/Brier/latency and unsafe gates pending |
| M6: packaging/release | Original specs/license records, partial source/wheel work | Specs and Coding Agent entry restored; wheel catalog/schema resources included. Full DoD, dependency/model locks, installation evidence and public stable release still pending |

## Default behavior

The legacy model-routing entry currently returns HUMAN_REVIEW for all valid
requests. Model auto coverage is 0. Unknown/out-of-scope task, moderate/high/unknown
risk, capability mismatch, invalid schema or missing evidence cannot bypass review.
Native confidence and metadata cannot create calibration or deployment authority.
No rules/provider orchestrator has yet been ported into this facade.

## Work order

1. Complete this restoration/safety slice and its conformance tests.
2. Port original immutable Patient State/models and finite rules, preserving provenance;
   expose the canonical request/response independently of legacy RouteRequest.
3. Port the verified Strands HTTP contract and complete real deployment acceptance.
4. Integrate routing/post-validation/CLI/API, then opt-in frontier gates.
5. Evaluate actual provider outputs using frozen grouped splits; calibration remains
   review-only until original quality/eligibility gates are met.
6. Complete Product DoD and packaging/license/release checks.

OpenMed, numeric IOP/acuity extraction and other optional experiments do not expand
the six-task release scope or the ophthalmic Copilot MVP. Existing extraction
scorer fixtures are preserved as historical engineering regression assets.
