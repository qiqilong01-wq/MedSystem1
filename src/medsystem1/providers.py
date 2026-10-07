from __future__ import annotations

from typing import Any, Protocol

from .models import ClinicalState


class ExtractionProvider(Protocol):
    """Return attributable state; validate it before merging into Patient State.

    Errors stop the operation. Empty state is valid shape, not evidence.
    """

    def extract(self, payload: Any) -> ClinicalState:
        ...


class DecisionProvider(Protocol):
    """Return finite confidence and advisory metadata, never clinical authority.

    The caller owns task risk, capabilities, and the final SafetyRouter request.
    """

    def decide(self, *, task: str, state: ClinicalState) -> tuple[float, dict[str, Any]]:
        ...
