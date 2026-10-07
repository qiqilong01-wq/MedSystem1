from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .._validation import provider_confidence
from ..errors import ProviderContractError, ProviderExecutionError
from ..models import ClinicalFact, ClinicalState
from ..validation import validate_clinical_state


class OpenMedExtractionProvider:
    """Thin optional adapter around an injected OpenMed-compatible analyzer.

    The analyzer is injected instead of imported by core. This avoids coupling
    MedSystem1 to a specific OpenMed version or bundling third-party model assets.
    """

    def __init__(self, analyzer: Any):
        if not callable(analyzer):
            raise TypeError("analyzer must be callable")
        self.analyzer = analyzer

    def extract(self, payload: Any) -> ClinicalState:
        if not isinstance(payload, str):
            raise TypeError("OpenMedExtractionProvider expects text input")

        try:
            results = self.analyzer(payload)
        except Exception as exc:
            raise ProviderExecutionError("extraction provider execution failed") from exc
        if isinstance(results, (str, bytes, Mapping)) or not isinstance(results, Iterable):
            raise ProviderContractError("extraction provider must return an iterable of mappings")
        facts: list[ClinicalFact] = []
        try:
            for item in results:
                if not isinstance(item, Mapping):
                    raise ProviderContractError("extraction items must be mappings")
                facts.append(
                    ClinicalFact(
                        name=item.get("label", item.get("type", "entity")),
                        value=item.get("value", item.get("text")),
                        confidence=_optional_float(item.get("score", item.get("confidence"))),
                        evidence=item.get("text"),
                        provenance="openmed",
                    )
                )
        except ProviderContractError:
            raise
        except Exception as exc:
            raise ProviderExecutionError("extraction provider iteration failed") from exc
        return validate_clinical_state(ClinicalState(tuple(facts)), source_text=payload)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return provider_confidence(value)
    except ValueError as exc:
        raise ProviderContractError("extraction confidence is invalid") from exc
