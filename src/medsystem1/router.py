from __future__ import annotations

from ._validation import unit_interval
from .models import Action, RouteDecision, RouteRequest


HIGH_RISK_CAPABILITIES = frozenset({
    "final_diagnosis",
    "prescribe_medication",
    "change_treatment",
    "submit_medical_record",
    "perform_procedure",
    "autonomous_patient_instruction",
})

LOW_RISK_CAPABILITIES = frozenset({
    "extract_structured_fact",
    "format_note",
    "classify_intent",
    "detect_missing_field",
    "read_only_summary",
})


class SafetyRouter:
    def __init__(self, local_threshold: float = 0.90, review_threshold: float = 0.65):
        local_threshold = unit_interval(local_threshold, name="local threshold")
        review_threshold = unit_interval(review_threshold, name="review threshold")
        if not 0 <= review_threshold <= local_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= review <= local <= 1")
        self.local_threshold = local_threshold
        self.review_threshold = review_threshold

    def route(self, request: RouteRequest) -> RouteDecision:
        unit_interval(request.confidence, name="confidence")
        if type(request.schema_valid) is not bool or type(request.evidence_present) is not bool:
            raise ValueError("schema_valid and evidence_present must be booleans")
        if not isinstance(request.capability, str) or not request.capability.strip():
            raise ValueError("capability must be a non-empty string")

        if request.capability in HIGH_RISK_CAPABILITIES:
            return RouteDecision(
                Action.HUMAN_REVIEW,
                ("high-risk capability requires human authority",),
                "high",
                request.confidence,
            )

        if request.capability not in LOW_RISK_CAPABILITIES:
            return RouteDecision(
                Action.HUMAN_REVIEW,
                ("unknown capability fails conservatively",),
                "unknown",
                request.confidence,
            )

        risk = "low" if request.risk == "auto" else request.risk
        if not isinstance(risk, str) or risk not in {"low", "medium", "high"}:
            return RouteDecision(
                Action.HUMAN_REVIEW,
                ("unrecognized risk level fails conservatively",),
                "unknown",
                request.confidence,
            )
        if risk == "high":
            return RouteDecision(
                Action.HUMAN_REVIEW, ("task risk is high",), risk, request.confidence
            )

        evidence_failures = []
        if not request.schema_valid:
            evidence_failures.append("schema validation failed")
        if not request.evidence_present:
            evidence_failures.append("evidence is missing")
        if evidence_failures:
            return RouteDecision(
                Action.ESCALATE, tuple(evidence_failures), "medium", request.confidence
            )

        if request.confidence >= self.local_threshold and risk == "low":
            return RouteDecision(
                Action.LOCAL,
                ("bounded low-risk task passed local threshold",),
                risk,
                request.confidence,
            )

        if request.confidence >= self.review_threshold:
            return RouteDecision(
                Action.HUMAN_REVIEW,
                ("confidence/risk requires human review",),
                risk,
                request.confidence,
            )

        return RouteDecision(
            Action.ESCALATE,
            ("confidence below review threshold",),
            risk,
            request.confidence,
        )
