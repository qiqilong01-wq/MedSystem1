from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Action(str, Enum):
    LOCAL = "LOCAL"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class ClinicalFact:
    name: str
    value: Any
    confidence: float | None = None
    evidence: str | None = None
    provenance: str | None = None


@dataclass(frozen=True)
class ClinicalState:
    facts: tuple[ClinicalFact, ...] = ()


@dataclass(frozen=True)
class RouteRequest:
    task: str
    confidence: float
    schema_valid: bool
    evidence_present: bool
    capability: str
    risk: str = "auto"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    action: Action
    reasons: tuple[str, ...]
    effective_risk: str
    confidence: float
