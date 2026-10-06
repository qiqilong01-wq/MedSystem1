"""Synthetic ophthalmology routing examples. No patient data."""

from medsystem1 import MedSystem1, RouteRequest

system = MedSystem1()

cases = [
    RouteRequest(
        task="extract_iop",
        confidence=0.97,
        schema_valid=True,
        evidence_present=True,
        capability="extract_structured_fact",
        metadata={"text": "左眼眼压 28 mmHg"},
    ),
    RouteRequest(
        task="change_glaucoma_treatment",
        confidence=0.99,
        schema_valid=True,
        evidence_present=True,
        capability="change_treatment",
    ),
    RouteRequest(
        task="extract_laterality",
        confidence=0.52,
        schema_valid=True,
        evidence_present=True,
        capability="extract_structured_fact",
        metadata={"text": "患者诉左眼视物模糊半年"},
    ),
]

for case in cases:
    decision = system.route(case)
    print(case.task, "=>", decision.action.value, decision.reasons)
