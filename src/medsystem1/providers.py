from __future__ import annotations

from typing import Any, Protocol

from .models import ClinicalState


class ExtractionProvider(Protocol):
    """Turn input into normalized clinical state."""

    def extract(self, payload: Any) -> ClinicalState:
        ...


class DecisionProvider(Protocol):
    """Optional bounded decision provider. It never grants clinical authority."""

    def decide(self, *, task: str, state: ClinicalState) -> tuple[float, dict[str, Any]]:
        ...
