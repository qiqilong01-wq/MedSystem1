from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .._validation import provider_confidence
from ..errors import ProviderContractError, ProviderExecutionError
from ..models import ClinicalState
from ..validation import validate_clinical_state


class StrandsDecisionProvider:
    """Adapter for an injected Strands-Decider-compatible callable.

    No clinical authority is delegated to this provider. Its confidence is only
    one signal consumed by the MedSystem1 safety router.
    """

    def __init__(self, decider: Callable[..., Any]):
        if not callable(decider):
            raise TypeError("decider must be callable")
        self.decider = decider

    def decide(self, *, task: str, state: ClinicalState) -> tuple[float, dict[str, Any]]:
        if not isinstance(task, str) or not task.strip():
            raise ProviderContractError("decision task must be non-empty text")
        validate_clinical_state(state)
        try:
            result = self.decider(task=task, state=state)
        except Exception as exc:
            raise ProviderExecutionError("decision provider execution failed") from exc
        if isinstance(result, tuple) and len(result) == 2:
            confidence, metadata = result
        elif isinstance(result, Mapping):
            confidence = result.get("confidence")
            metadata = result
        else:
            confidence = getattr(result, "confidence", None)
            metadata = getattr(result, "metadata", {})

        if confidence is None:
            raise ProviderContractError("decision provider did not return confidence")
        if not isinstance(metadata, Mapping) or any(not isinstance(key, str) for key in metadata):
            raise ProviderContractError("decision metadata must be a mapping with text keys")
        try:
            confidence = provider_confidence(confidence)
        except ValueError as exc:
            raise ProviderContractError("decision confidence is invalid") from exc
        return confidence, dict(metadata)
