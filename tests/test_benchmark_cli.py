import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "run_routing.py"
FIXTURES = ROOT / "benchmarks" / "routing_ophthalmology_zh_v0.2.jsonl"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_versioned_routing_regression_runs_all_cases():
    result = run()
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["scope"] == "synthetic_routing_regression"
    assert report["total"] == 30
    assert report["passed"] == 30
    assert report["failed"] == 0
    assert sum(d["total"] for d in report["coverage"].values()) == 30
    assert all("text" not in case and "request" not in case for case in report["results"])


def test_wrong_expectation_exits_nonzero_and_reports_case(tmp_path):
    case = json.loads(FIXTURES.read_text().splitlines()[0])
    case["expected_action"] = "HUMAN_REVIEW"
    path = tmp_path / "wrong.jsonl"
    path.write_text(json.dumps(case), encoding="utf-8")
    result = run("--cases", str(path))
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["failed"] == 1
    assert report["results"][0]["actual_action"] == "LOCAL"


@pytest.mark.parametrize("content", ["", "not-json", "{}", '{"synthetic": false}', '{"score": NaN}'])
def test_invalid_fixture_cannot_report_success(tmp_path, content):
    path = tmp_path / "bad.jsonl"
    path.write_text(content, encoding="utf-8")
    result = run("--cases", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "not-json" not in result.stderr


def test_duplicate_case_id_is_not_double_counted(tmp_path):
    line = FIXTURES.read_text().splitlines()[0]
    path = tmp_path / "duplicate.jsonl"
    path.write_text(line + "\n" + line, encoding="utf-8")
    assert run("--cases", str(path)).returncode == 2


def test_malformed_route_request_is_a_failed_case(tmp_path):
    case = json.loads(FIXTURES.read_text().splitlines()[0])
    case["request"]["evidence_present"] = "true"
    path = tmp_path / "bad-request.jsonl"
    path.write_text(json.dumps(case), encoding="utf-8")
    result = run("--cases", str(path))
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["results"][0]["error"] == "ValueError"
