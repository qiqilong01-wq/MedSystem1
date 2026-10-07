import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "run_extraction.py"
GOLD = ROOT / "benchmarks" / "extraction_ophthalmology_zh_v0.1.jsonl"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_self_test_is_explicitly_not_a_model_result():
    result = run("--self-test")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "fixture_replay_self_test"
    assert report["provider_label"] == "gold_fixture_replay_no_model"
    assert report["metrics"]["exact_cases"] == 24
    assert len(report["fixture_sha256"]) == 64


def predictions(tmp_path, rows):
    path = tmp_path / "predictions.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return str(path)


def test_recorded_prediction_requires_identity_and_fails_for_missing_cases(tmp_path):
    row = json.loads(GOLD.read_text(encoding="utf-8").splitlines()[0])
    path = predictions(tmp_path, [{"id": row["id"], "facts": row["expected"]}])
    assert run("--predictions", path).returncode == 2
    result = run("--predictions", path, "--provider-label", "fake-provider@1")
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["mode"] == "recorded_provider_predictions"
    assert report["metrics"]["exact_cases"] == 1
    assert report["metrics"]["output_error_cases"] == 23


def test_malformed_case_output_is_failed_not_skipped(tmp_path):
    path = predictions(tmp_path, [{"id": "extract-oph-001", "facts": "wrong shape"}])
    result = run("--predictions", path, "--provider-label", "test")
    assert result.returncode == 1
    assert json.loads(result.stdout)["results"][0]["error"] == "invalid_provider_output"


def test_unknown_or_duplicate_prediction_ids_reject_file(tmp_path):
    for rows in (
        [{"id": "unknown", "facts": []}],
        [{"id": "extract-oph-001", "facts": []}] * 2,
    ):
        result = run("--predictions", predictions(tmp_path, rows), "--provider-label", "test")
        assert result.returncode == 2
        assert result.stdout == ""


@pytest.mark.parametrize("content", ["", "not-json", "{}", '{"value": NaN}'])
def test_invalid_gold_cannot_pass_self_test(tmp_path, content):
    path = tmp_path / "bad-gold.jsonl"
    path.write_text(content, encoding="utf-8")
    result = run("--cases", str(path), "--self-test")
    assert result.returncode == 2
    assert result.stdout == ""


def test_missing_reference_evidence_is_rejected(tmp_path):
    row = json.loads(GOLD.read_text(encoding="utf-8").splitlines()[0])
    row["expected"][0].pop("evidence")
    path = tmp_path / "unsupported-gold.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    assert run("--cases", str(path), "--self-test").returncode == 2


def test_duplicate_json_fields_are_not_silently_overwritten(tmp_path):
    path = tmp_path / "duplicate-fields.jsonl"
    path.write_text('{"id":"extract-oph-001","facts":[],"facts":[]}', encoding="utf-8")
    result = run("--predictions", str(path), "--provider-label", "test")
    assert result.returncode == 2
    assert result.stdout == ""

