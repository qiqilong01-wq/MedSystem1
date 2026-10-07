from __future__ import annotations

from typing import Any, Callable

from .._validation import provider_confidence
from ..models import ClinicalState


class StrandsDecisionProvider:
    """Adapter for an injected Strands-Decider-compatible callable.

    No clinical authority is delegated to this provider. Its confidence is only
    one signal consumed by the MedSystem1 safety router.
    """

    def __init__(self, decider: Callable[..., Any]):
        self.decider = decider

    def decide(self, *, task: str, state: ClinicalState) -> tuple[float, dict[str, Any]]:
        result = self.decider(task=task, state=state)
        if isinstance(result, tuple) and len(result) == 2:
            confidence, metadata = result
        elif isinstance(result, dict):
            confidence = result.get("confidence")
            metadata = result
        else:
            confidence = getattr(result, "confidence", None)
            metadata = {"raw_result": result}

        if confidence is None:
            raise ValueError("decision provider did not return confidence")
        confidence = provider_confidence(confidence)
        return confidence, dict(metadata)
