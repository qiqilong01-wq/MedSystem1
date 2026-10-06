from __future__ import annotations

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
        if not 0 <= review_threshold <= local_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= review <= local <= 1")
        self.local_threshold = local_threshold
        self.review_threshold = review_threshold

    def route(self, request: RouteRequest) -> RouteDecision:
        if not 0 <= request.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

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

        evidence_failures = []
        if not request.schema_valid:
            evidence_failures.append("schema validation failed")
        if not request.evidence_present:
            evidence_failures.append("evidence is missing")
        if evidence_failures:
            return RouteDecision(
                Action.ESCALATE, tuple(evidence_failures), "medium", request.confidence
            )

        risk = "low" if request.risk == "auto" else request.risk
        if risk not in {"low", "medium", "high"}:
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
