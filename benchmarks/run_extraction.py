"""Score recorded extraction predictions or run an explicitly labeled self-test."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from medsystem1 import ClinicalFact, ClinicalState, __version__
from medsystem1.evaluation import ExtractionCase, evaluate_extraction


def reject_constant(_: str) -> None:
    raise ValueError("non-finite JSON number")


def unique_fields(pairs: list[tuple]) -> dict:
    row = {}
    for key, value in pairs:
        if key in row:
            raise ValueError("duplicate JSON field")
        row[key] = value
    return row


def records(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line, parse_constant=reject_constant, object_pairs_hook=unique_fields)
            if not isinstance(row, dict):
                raise ValueError("each JSONL row must be a mapping")
            rows.append(row)
    if not rows:
        raise ValueError("empty dataset")
    return rows


def gold_cases(path: Path) -> list[ExtractionCase]:
    cases = []
    for row in records(path):
        if row.get("schema_version") != "0.1" or row.get("synthetic") is not True:
            raise ValueError("gold fixture version or provenance mismatch")
        if not isinstance(row["expected"], list):
            raise ValueError("expected facts must be a list")
        facts = tuple(ClinicalFact(**fact) for fact in row["expected"])
        cases.append(ExtractionCase(row["id"], row["dimension"], row["text"], facts, row["task"]))
    return cases


def recorded_predictions(path: Path) -> dict:
    predictions = {}
    for row in records(path):
        case_id = row["id"]
        if not isinstance(case_id, str) or case_id in predictions:
            raise ValueError("prediction identifiers must be unique text")
        # Retain invalid per-case output for explicit failure in the evaluator.
        try:
            facts = row["facts"]
            if not isinstance(facts, list):
                raise ValueError("facts must be a list")
            state = ClinicalState(tuple(ClinicalFact(**fact) for fact in facts))
        except (KeyError, TypeError, ValueError):
            state = None
        predictions[case_id] = state
    return predictions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name(
        "extraction_ophthalmology_zh_v0.1.jsonl"))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--predictions", type=Path)
    group.add_argument("--self-test", action="store_true")
    parser.add_argument("--provider-label")
    args = parser.parse_args()
    if args.predictions and not args.provider_label:
        parser.error("--predictions requires --provider-label (provider/version/run identifier)")
    try:
        cases = gold_cases(args.cases)
        if args.self_test:
            mode = "fixture_replay_self_test"
            predictions = {case.case_id: ClinicalState(case.expected) for case in cases}
            label = "gold_fixture_replay_no_model"
        else:
            mode = "recorded_provider_predictions"
            predictions = recorded_predictions(args.predictions)
            label = args.provider_label
        report = evaluate_extraction(cases, predictions, provider_label=label, mode=mode)
        report.update(
            package_version=__version__, fixture_schema_version="0.1",
            fixture_sha256=hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        )
        if args.predictions:
            report["predictions_sha256"] = hashlib.sha256(args.predictions.read_bytes()).hexdigest()
    except (OSError, KeyError, TypeError, ValueError):
        print("Invalid or unreadable extraction evaluation data; check the documented schema.", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if report["metrics"]["failed_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
