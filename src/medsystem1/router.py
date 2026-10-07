from __future__ import annotations

from ._validation import unit_interval
from .models import Action, RouteDecision, RouteRequest
from .policy import TaskCatalog

HIGH_RISK_CAPABILITIES = frozenset({
    "final_diagnosis", "prescribe_medication", "change_treatment",
    "submit_medical_record", "perform_procedure", "autonomous_patient_instruction",
})
LOW_RISK_CAPABILITIES = frozenset({
    "extract_structured_fact", "format_note", "classify_intent",
    "detect_missing_field", "read_only_summary",
})


class SafetyRouter:
    """Review-only until calibrated deployment eligibility is implemented.

    RouteRequest is a legacy library advisory input, not the clinical wire
    contract. It grants no execution permission. There are no network calls.
    """
    def __init__(self, local_threshold: float = 0.90, review_threshold: float = 0.65):
        local_threshold = unit_interval(local_threshold, name="local threshold")
        review_threshold = unit_interval(review_threshold, name="review threshold")
        if not 0 <= review_threshold <= local_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= review <= local <= 1")
        self.local_threshold = local_threshold
        self.review_threshold = review_threshold
        self.catalog = TaskCatalog()

    def route(self, request: RouteRequest) -> RouteDecision:
        unit_interval(request.confidence, name="confidence")
        if type(request.schema_valid) is not bool or type(request.evidence_present) is not bool:
            raise ValueError("schema_valid and evidence_present must be booleans")
        if not isinstance(request.capability, str) or not request.capability.strip():
            raise ValueError("capability must be a non-empty string")
        if not isinstance(request.task, str) or not request.task.strip():
            raise ValueError("task must be a non-empty string")

        def review(reason, risk):
            return RouteDecision(Action.HUMAN_REVIEW, (reason,), risk, request.confidence)

        if request.capability in HIGH_RISK_CAPABILITIES:
            return review("high-risk capability requires human authority", "high")
        task = self.catalog.get(request.task)
        if task is None:
            return review("task is outside the bounded v0.1 catalog", "unknown")
        if request.capability != task.capability:
            return review("capability does not match trusted task definition", "unknown")
        if not isinstance(request.risk, str) or request.risk not in {"auto", "low", "medium", "moderate", "high"}:
            return review("unrecognized risk level fails conservatively", "unknown")
        if request.risk == "high":
            return review("task risk is high", "high")
        if task.risk == "moderate" or request.risk in {"medium", "moderate"}:
            return review("moderate risk requires locked human review", "medium")
        if not request.schema_valid:
            return review("schema validation failed; human review locked", "low")
        if not request.evidence_present:
            return review("evidence is missing; human review locked", "low")
        # Thresholds and caller/provider metadata cannot create calibration proof.
        return review("model auto disabled; no validated domain calibration", "low")

