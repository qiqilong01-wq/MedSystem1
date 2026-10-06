# Safety model

MedSystem1 separates **prediction confidence** from **permission to act**.

## Core invariants

1. High model confidence never grants clinical authority.
2. Invalid schemas or missing evidence cannot take the LOCAL path.
3. Explicit high-risk clinical capabilities require human review.
4. Unknown capabilities fail conservatively.
5. Escalation to a stronger model is not equivalent to authorization.
6. Clinical state should be structured, attributable, and auditable; conversational memory is not a clinical source of truth.

## High-risk capability examples

The default policy bounds `final_diagnosis`, `prescribe_medication`, `change_treatment`, `submit_medical_record`, `perform_procedure`, and `autonomous_patient_instruction`.

Applications may add stricter rules. Clinical deployments should not silently weaken these defaults.

## Data

Examples and benchmark cases in this repository are synthetic unless explicitly stated otherwise. Do not commit identifiable patient data.

## Status

v0.1 is alpha research/developer infrastructure. It has not been clinically validated or cleared/approved as a medical device.
