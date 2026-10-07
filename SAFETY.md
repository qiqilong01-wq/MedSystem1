# Safety model

Current main 0.1.1.dev1: the original [SAFETY_BOUNDARIES.md](SAFETY_BOUNDARIES.md)
and six-task catalog are restored. Native confidence is advisory, model auto and
cloud calls are disabled, moderate/unknown/high risk and missing evidence lock
human review. No metadata assertion can grant calibration or export permission.

MedSystem1 separates **prediction confidence** from **permission to act**.

## Core invariants

1. High model confidence never grants clinical authority.
2. Invalid schemas or missing evidence cannot take the LOCAL path.
3. Explicit high-risk clinical capabilities require human review.
4. Unknown capabilities fail conservatively.
5. Escalation to a stronger model is not equivalent to authorization.
6. Clinical state should be structured, attributable, and auditable; conversational memory is not a clinical source of truth.

## Runtime input contract (unreleased main)

Confidence and thresholds must be finite numbers in [0, 1]; booleans are not
confidence values. Schema/evidence flags must be actual booleans, not strings
or integers. Malformed input raises `ValueError`. Callers must stop the
operation for repair/review; catching an exception must never fall through to
an authorized clinical action.

Explicit high-risk tasks and unknown risk levels keep HUMAN_REVIEW even when
evidence is missing. A stronger model cannot repair missing human authority.
The callable adapters allow finite numeric confidence strings from upstream
payloads but reject booleans and out-of-range/non-finite scores. An absent
extraction confidence remains unknown (`None`).

The default thresholds are retained API settings, not calibrated guarantees or
authorization; this slice never issues LOCAL or ESCALATE. See docs/API_MIGRATION.md.

## High-risk capability examples

The default policy bounds `final_diagnosis`, `prescribe_medication`, `change_treatment`, `submit_medical_record`, `perform_procedure`, and `autonomous_patient_instruction`.

Applications may add stricter rules. Clinical deployments should not silently weaken these defaults.

## Data

Examples and benchmark cases in this repository are synthetic unless explicitly stated otherwise. Do not commit identifiable patient data.

## Status

v0.1 is alpha research/developer infrastructure. It has not been clinically validated or cleared/approved as a medical device.

