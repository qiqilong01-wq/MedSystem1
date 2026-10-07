"""Offline evaluation helpers; they never grant clinical authority."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite

from .errors import ProviderContractError
from .models import ClinicalFact, ClinicalState
from .validation import validate_clinical_state


@dataclass(frozen=True)
class ExtractionCase:
    case_id: str
    dimension: str
    text: str
    expected: tuple[ClinicalFact, ...]
    task: str = "extract_target_facts"


def _scalar(value: object) -> bool:
    return (
        isinstance(value, (str, bool, int))
        or isinstance(value, float) and isfinite(value)
    )


def _equal(left: object, right: object) -> bool:
    # False is not 0, and True is not 1. Numeric 16 and 16.0 are equivalent.
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return type(left) is type(right) and left == right or (
        isinstance(left, (int, float)) and isinstance(right, (int, float)) and left == right
    )


def _validate_case(case: ExtractionCase) -> None:
    if not isinstance(case, ExtractionCase):
        raise ValueError("gold cases must be ExtractionCase objects")
    for value in (case.case_id, case.dimension, case.text, case.task):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("case identifiers, dimensions, and text must be non-empty")
    validate_clinical_state(ClinicalState(case.expected), source_text=case.text)
    names = set()
    for fact in case.expected:
        if not _scalar(fact.value) or fact.evidence is None:
            raise ValueError("gold facts require JSON scalar values and literal evidence anchors")
        if fact.name in names:
            raise ValueError("gold fact names must be unique within a case")
        names.add(fact.name)


def _metrics(rows: list[dict]) -> dict:
    matched = sum(r["matched_facts"] for r in rows)
    supported = sum(r["supported_facts"] for r in rows)
    predicted = sum(r["predicted_facts"] for r in rows)
    expected = sum(r["expected_facts"] for r in rows)

    def rates(correct: int) -> dict:
        return {
            "precision": correct / predicted if predicted else None,
            "recall": correct / expected if expected else None,
            "f1": 2 * correct / (predicted + expected) if predicted + expected else None,
        }

    exact = sum(r["exact_match"] for r in rows)
    return {
        "total_cases": len(rows), "exact_cases": exact,
        "failed_cases": len(rows) - exact,
        "output_error_cases": sum("error" in r for r in rows),
        "case_exact_match_rate": exact / len(rows),
        "expected_facts": expected, "valid_predicted_facts": predicted,
        "matched_facts": matched, "supported_facts": supported,
        "fact_match": rates(matched), "supported_match": rates(supported),
    }


def evaluate_extraction(
    cases: Iterable[ExtractionCase], predictions: Mapping[str, ClinicalState], *,
    provider_label: str, mode: str = "recorded_provider_predictions",
) -> dict:
    """Score one-to-one scalar facts and gold-anchored source evidence.

    Outputs omit raw text, values, evidence, and upstream error messages. Invalid
    output is a failed case: it contributes zero valid predictions and all gold
    facts remain unmatched. Always inspect output-error counts with precision.
    """
    if mode not in {"recorded_provider_predictions", "fixture_replay_self_test"}:
        raise ValueError("unsupported evaluation mode")
    if not isinstance(provider_label, str) or not provider_label.strip():
        raise ValueError("provider_label must be non-empty text")
    cases = list(cases)
    if not cases or not isinstance(predictions, Mapping):
        raise ValueError("evaluation requires gold cases and a prediction mapping")
    ids = set()
    for case in cases:
        _validate_case(case)
        if case.case_id in ids:
            raise ValueError("duplicate gold case identifier")
        ids.add(case.case_id)
    if set(predictions) - ids:
        raise ValueError("predictions contain unknown case identifiers")

    rows = []
    for case in cases:
        row = {
            "id": case.case_id, "dimension": case.dimension, "task": case.task,
            "expected_facts": len(case.expected), "predicted_facts": 0,
            "matched_facts": 0, "supported_facts": 0, "exact_match": False,
        }
        if case.case_id not in predictions:
            row["error"] = "missing_prediction"
        else:
            try:
                state = validate_clinical_state(predictions[case.case_id], source_text=case.text)
                if any(not _scalar(f.value) for f in state.facts):
                    raise ProviderContractError("evaluation values must be JSON scalars")
            except ProviderContractError:
                row["error"] = "invalid_provider_output"
            else:
                row["predicted_facts"] = len(state.facts)
                available = list(range(len(state.facts)))
                for gold in case.expected:
                    matches = [i for i in available if state.facts[i].name == gold.name
                               and _equal(state.facts[i].value, gold.value)]
                    if not matches:
                        continue
                    supported = [i for i in matches if state.facts[i].evidence is not None
                                 and gold.evidence in state.facts[i].evidence]
                    chosen = supported[0] if supported else matches[0]
                    available.remove(chosen)
                    row["matched_facts"] += 1
                    row["supported_facts"] += bool(supported)
                row["unexpected_facts"] = len(available)
                row["missing_facts"] = len(case.expected) - row["matched_facts"]
                row["unsupported_matches"] = row["matched_facts"] - row["supported_facts"]
                row["exact_match"] = (
                    row["supported_facts"] == len(case.expected) and not available
                )
        rows.append(row)
    return {
        "scope": "synthetic_extraction_evaluation", "mode": mode,
        "provider_label": provider_label,
        "metrics": _metrics(rows),
        "coverage": {dimension: _metrics([r for r in rows if r["dimension"] == dimension])
                     for dimension in sorted({case.dimension for case in cases})},
        "results": rows,
    }
