"""Canonical Schema validation plus repository-level cross-field invariants."""
import json
from functools import lru_cache
from math import isfinite
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


@lru_cache(maxsize=8)
def schema_registry(schema_dir: Path) -> tuple[dict, Registry]:
    # Public versioned Schemas only. Never cache requests, facts, or results.
    schemas = {}
    registry = Registry()
    for path in sorted(schema_dir.glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(doc)
        schemas[path.name] = doc
        registry = registry.with_resource(doc["$id"], Resource.from_contents(doc))
    return schemas, registry


def validate_schema(data: dict, name: str, schema_dir: Path) -> None:
    def finite(value):
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("non_finite_number")
        if isinstance(value, dict):
            for item in value.values():
                finite(item)
        if isinstance(value, list):
            for item in value:
                finite(item)
    finite(data)
    schemas, registry = schema_registry(schema_dir)
    Draft202012Validator(schemas[name], registry=registry).validate(data)


def _validate_evidence(items: list, state: dict) -> None:
    sources = {s["source_id"]: s["text"] for s in state["sources"]}
    for evidence in items:
        source = evidence["source_id"]
        if source not in sources:
            raise ValueError("evidence_source_not_in_state")
        if not 0 <= evidence["start"] < evidence["end"] <= len(sources[source]):
            raise ValueError("evidence_span_out_of_range")


def validate_request(data: dict, schema_dir: Path) -> None:
    validate_schema(data, "request.schema.json", schema_dir)
    state = data["patient_state"]
    ids = [s["source_id"] for s in state["sources"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_source_id")
    for fact in state["facts"]:
        _validate_evidence(fact["evidence"], state)


def validate_response(data: dict, request: dict, schema_dir: Path) -> None:
    """Does not prove evidence semantics, thresholds, capabilities or calibration."""
    validate_request(request, schema_dir)
    validate_schema(data, "response.schema.json", schema_dir)
    ids = [item["task_id"] for item in data["results"]]
    if ids != request["tasks"]:
        raise ValueError("result_task_coverage_or_order")
    ranks = {"low": 0, "moderate": 1, "high": 2, "unknown": 3}
    item_risk = max((i["risk"] for i in data["results"]), key=ranks.get)
    if ranks[data["risk"]] < ranks[item_risk]:
        raise ValueError("aggregate_risk_downgrade")
    statuses = [i["status"] for i in data["results"]]
    expected_status = next((s for s in ("blocked", "review_required", "abstained")
                            if s in statuses), "completed")
    # Aggregate safety guard may elevate a request above individually completed items.
    status_ranks = {"completed": 0, "abstained": 1, "review_required": 2, "blocked": 3}
    if status_ranks[data["status"]] < status_ranks[expected_status]:
        raise ValueError("aggregate_status_downgrade")
    for item in data["results"]:
        _validate_evidence(item["evidence"], request["patient_state"])
        if item["value"] is not None and item["task_id"] != "missing_fields" and not item["evidence"]:
            raise ValueError("ungrounded_value")
        if item["value"] is None and item["evidence"]:
            raise ValueError("evidence_without_value")
        if item["task_id"] == "missing_fields" and 'rule_missing_fields' not in item['reason_codes']:
            raise ValueError('missing_fields_requires_profile_reason')
        if item["route"] == "rules":
            conf = item["confidence"]
            if any(conf[k] is not None for k in ("native_score", "selected_probability", "calibrated_probability")):
                raise ValueError("rule_claims_model_probability")
        if item["task_id"] == "urgency_to_review" and item["status"] == "completed":
            raise ValueError("urgency_auto_forbidden")
