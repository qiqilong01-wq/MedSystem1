"""Pure routing kernel; contexts MUST be built by a trusted orchestrator.

This function does not validate clinical evidence, privacy, calibration artifacts,
or deployment capabilities. It is not an HTTP request handler or clinical system.
"""
from dataclasses import dataclass
from enum import Enum
from math import isfinite


class Risk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


class Route(str, Enum):
    RULES = "rules"
    LOCAL_AUTO = "local_auto"
    FRONTIER_FALLBACK = "frontier_fallback"
    HUMAN_REVIEW = "human_review"
    ABSTAIN = "abstain"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RouteContext:
    risk: Risk = Risk.UNKNOWN
    scope_allowed: bool = True
    review_lock: bool = False
    output_valid: bool = True
    evidence_valid: bool = False
    out_of_domain: bool = False
    task_capability: bool = False
    deterministic_result: bool = False
    auto_enabled: bool = False
    calibration_valid: bool = False
    calibrated_probability: float | None = None
    threshold: float = 0.95
    frontier_enabled: bool = False
    frontier_requested: bool = False
    export_capability: bool = False
    privacy_cleared: bool = False
    sanitized_payload_valid: bool = False
    frontier_healthy: bool = False
    any_result: bool = True


def decide_route(c: RouteContext) -> Route:
    """Select one route; no side effects. Native confidence is never an input."""
    if not c.scope_allowed:
        return Route.BLOCKED
    if c.risk != Risk.LOW or c.review_lock:
        return Route.HUMAN_REVIEW
    if not c.output_valid or c.out_of_domain:
        return Route.HUMAN_REVIEW
    if not isfinite(c.threshold) or not 0 <= c.threshold <= 1:
        return Route.HUMAN_REVIEW
    p = c.calibrated_probability
    if p is not None and (not isfinite(p) or not 0 <= p <= 1):
        return Route.HUMAN_REVIEW
    if c.task_capability and c.deterministic_result and c.evidence_valid:
        return Route.RULES
    if (c.task_capability and c.evidence_valid and c.auto_enabled
            and c.calibration_valid and p is not None and p >= c.threshold):
        return Route.LOCAL_AUTO
    # Invalid / unsupported evidence cannot be repaired by permission escalation.
    if c.any_result and not c.evidence_valid:
        return Route.HUMAN_REVIEW
    if all((c.frontier_enabled, c.frontier_requested, c.export_capability,
            c.privacy_cleared, c.sanitized_payload_valid, c.frontier_healthy)):
        return Route.FRONTIER_FALLBACK
    return Route.HUMAN_REVIEW if c.any_result else Route.ABSTAIN
