"""Run synthetic routing-policy regressions; this does not evaluate a model."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from medsystem1 import Action, MedSystem1, RouteRequest, __version__


def reject_constant(_: str) -> None:
    raise ValueError("non-finite JSON number")


def load_cases(path: Path) -> list[dict]:
    cases = []
    seen = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line, parse_constant=reject_constant)
                if not isinstance(case, dict) or case.get("schema_version") != "0.3":
                    raise ValueError("fixture schema mismatch")
                if case.get("synthetic") is not True:
                    raise ValueError("fixture must be explicitly synthetic")
                for field in ("id", "dimension", "text"):
                    if not isinstance(case.get(field), str) or not case[field].strip():
                        raise ValueError("missing fixture field")
                if case["id"] in seen:
                    raise ValueError("duplicate fixture id")
                if not isinstance(case.get("request"), dict):
                    raise ValueError("missing route request")
                Action(case["expected_action"])
                RouteRequest(**case["request"])
            except (KeyError, TypeError, ValueError) as exc:
                # Do not echo a malformed line, source text, or exception payload.
                raise ValueError(f"invalid fixture at line {line_number}") from exc
            seen.add(case["id"])
            cases.append(case)
    if not cases:
        raise ValueError("fixture file must contain at least one case")
    return cases


def evaluate(cases: list[dict]) -> dict:
    system = MedSystem1()
    results = []
    for case in cases:
        result = {
            "id": case["id"], "dimension": case["dimension"],
            "expected_action": case["expected_action"],
        }
        try:
            decision = system.route(RouteRequest(**case["request"]))
            result.update(
                actual_action=decision.action.value, reasons=list(decision.reasons),
                passed=decision.action.value == case["expected_action"],
            )
        except (TypeError, ValueError) as exc:
            result.update(actual_action=None, passed=False, error=type(exc).__name__)
        results.append(result)
    passed = sum(result["passed"] for result in results)
    coverage = {}
    for dimension, total in sorted(Counter(case["dimension"] for case in cases).items()):
        successes = sum(r["passed"] for r in results if r["dimension"] == dimension)
        coverage[dimension] = {"total": total, "passed": successes, "failed": total - successes}
    return {
        "scope": "synthetic_routing_regression", "fixture_schema_version": "0.3",
        "package_version": __version__, "total": len(results), "passed": passed,
        "failed": len(results) - passed, "coverage": coverage, "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path,
        default=Path(__file__).with_name("routing_ophthalmology_zh_v0.3.jsonl"),
    )
    args = parser.parse_args()
    try:
        report = evaluate(load_cases(args.cases))
    except (OSError, ValueError):
        print("Invalid or unreadable synthetic fixture file; check its schema and line structure.", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

