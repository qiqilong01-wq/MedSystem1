from __future__ import annotations

from typing import Any

from .._validation import provider_confidence
from ..models import ClinicalFact, ClinicalState


class OpenMedExtractionProvider:
    """Thin optional adapter around an injected OpenMed-compatible analyzer.

    The analyzer is injected instead of imported by core. This avoids coupling
    MedSystem1 to a specific OpenMed version or bundling third-party model assets.
    """

    def __init__(self, analyzer: Any):
        self.analyzer = analyzer

    def extract(self, payload: Any) -> ClinicalState:
        if not isinstance(payload, str):
            raise TypeError("OpenMedExtractionProvider expects text input")

        results = self.analyzer(payload)
        facts: list[ClinicalFact] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            facts.append(
                ClinicalFact(
                    name=str(item.get("label") or item.get("type") or "entity"),
                    value=item.get("text", item.get("value")),
                    confidence=_optional_float(item.get("score", item.get("confidence"))),
                    evidence=item.get("text"),
                    provenance="openmed",
                )
            )
        return ClinicalState(tuple(facts))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return provider_confidence(value)
