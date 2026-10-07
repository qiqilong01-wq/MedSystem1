from __future__ import annotations

from ._validation import unit_interval
from .errors import ProviderContractError
from .models import ClinicalFact, ClinicalState


def validate_clinical_state(
    state: object, *, source_text: str | None = None,
) -> ClinicalState:
    """Check normalized shape and literal evidence, not clinical correctness.

    Missing confidence/evidence stays unknown. This validator is separate from
    the consuming application's authoritative Patient State schema.
    """
    if source_text is not None and not isinstance(source_text, str):
        raise ProviderContractError("source_text must be text when supplied")
    if not isinstance(state, ClinicalState) or not isinstance(state.facts, tuple):
        raise ProviderContractError("provider must return ClinicalState with a facts tuple")
    for index, fact in enumerate(state.facts):
        prefix = f"fact {index}"
        if not isinstance(fact, ClinicalFact):
            raise ProviderContractError(f"{prefix} must be ClinicalFact")
        if not isinstance(fact.name, str) or not fact.name.strip():
            raise ProviderContractError(f"{prefix} name must be non-empty text")
        if fact.value is None:
            raise ProviderContractError(f"{prefix} must have a non-null value")
        if fact.confidence is not None:
            try:
                unit_interval(fact.confidence, name="fact confidence")
            except ValueError as exc:
                raise ProviderContractError(f"{prefix} confidence is invalid") from exc
        for field_name in ("evidence", "provenance"):
            value = getattr(fact, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ProviderContractError(f"{prefix} {field_name} must be non-empty text or None")
        if source_text is not None and fact.evidence is not None and fact.evidence not in source_text:
            raise ProviderContractError(f"{prefix} evidence is not present in source text")
    return state
