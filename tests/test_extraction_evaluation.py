from dataclasses import replace

import pytest

from medsystem1 import ClinicalFact, ClinicalState
from medsystem1.evaluation import ExtractionCase, evaluate_extraction


def case(*facts):
    return ExtractionCase("one", "numeric", "左眼眼压16，右眼眼压28，无眼痛。", tuple(facts))


def score(gold, *facts):
    return evaluate_extraction([gold], {"one": ClinicalState(tuple(facts))}, provider_label="test")


LEFT = ClinicalFact("left_iop_mmHg", 16, evidence="左眼眼压16")
RIGHT = ClinicalFact("right_iop_mmHg", 28, evidence="右眼眼压28")


def test_correct_values_and_evidence_pass_in_any_order():
    report = score(case(LEFT, RIGHT), RIGHT, replace(LEFT, value=16.0))
    assert report["metrics"]["fact_match"]["f1"] == 1.0
    assert report["metrics"]["supported_match"]["f1"] == 1.0
    assert report["metrics"]["exact_cases"] == 1


def test_eye_swap_is_wrong_even_with_valid_source_quotes():
    report = score(case(LEFT, RIGHT), replace(LEFT, value=28), replace(RIGHT, value=16))
    assert report["metrics"]["matched_facts"] == 0
    assert report["results"][0]["missing_facts"] == 2
    assert report["results"][0]["unexpected_facts"] == 2


@pytest.mark.parametrize("evidence", [None, "右眼眼压28", "16"])
def test_correct_value_with_missing_or_wrong_anchor_cannot_pass(evidence):
    report = score(case(LEFT), replace(LEFT, evidence=evidence))
    assert report["metrics"]["fact_match"]["f1"] == 1.0
    assert report["metrics"]["supported_match"]["f1"] == 0.0
    assert report["metrics"]["failed_cases"] == 1


def test_fabricated_evidence_invalidates_whole_output():
    report = score(case(LEFT), replace(LEFT, evidence="眼压100"))
    assert report["results"][0]["error"] == "invalid_provider_output"
    assert report["metrics"]["output_error_cases"] == 1


def test_duplicate_fact_counts_as_extra_not_another_success():
    report = score(case(LEFT), LEFT, LEFT)
    assert report["metrics"]["matched_facts"] == 1
    assert report["metrics"]["fact_match"]["precision"] == 0.5
    assert report["metrics"]["failed_cases"] == 1


def test_matching_prefers_supported_duplicate_but_still_penalizes_extra():
    report = score(case(LEFT), replace(LEFT, evidence=None), LEFT)
    assert report["metrics"]["supported_facts"] == 1
    assert report["results"][0]["unexpected_facts"] == 1


def test_false_is_not_numeric_zero():
    gold = ClinicalFact("eye_pain", False, evidence="无眼痛")
    report = score(case(gold), replace(gold, value=0))
    assert report["metrics"]["matched_facts"] == 0


def test_numeric_strings_are_not_numeric_measurements():
    assert score(case(LEFT), replace(LEFT, value="16"))["metrics"]["matched_facts"] == 0


def test_missing_prediction_is_visible_and_lowers_recall():
    cases = [case(LEFT), replace(case(RIGHT), case_id="two")]
    report = evaluate_extraction(cases, {"one": ClinicalState((LEFT,))}, provider_label="test")
    assert report["metrics"]["fact_match"]["recall"] == 0.5
    assert report["metrics"]["output_error_cases"] == 1
    assert report["results"][1]["error"] == "missing_prediction"


@pytest.mark.parametrize("state", [None, {}, ClinicalState((replace(LEFT, value={"number": 16}),))])
def test_malformed_output_is_case_failure(state):
    report = evaluate_extraction([case(LEFT)], {"one": state}, provider_label="test")
    assert report["metrics"]["exact_cases"] == 0
    assert report["results"][0]["error"] == "invalid_provider_output"


def test_empty_gold_rewards_abstention_and_penalizes_hallucination():
    assert score(case())["metrics"]["exact_cases"] == 1
    assert score(case())["metrics"]["fact_match"]["f1"] is None
    assert score(case(), LEFT)["metrics"]["failed_cases"] == 1


@pytest.mark.parametrize("gold", [
    case(replace(LEFT, evidence=None)), case(LEFT, LEFT), case(replace(LEFT, evidence="not in source")),
])
def test_invalid_gold_rejected(gold):
    with pytest.raises(ValueError):
        evaluate_extraction([gold], {}, provider_label="test")


def test_unknown_prediction_id_and_duplicate_gold_cannot_inflate_score():
    with pytest.raises(ValueError):
        evaluate_extraction([case(LEFT)], {"other": ClinicalState()}, provider_label="test")
    with pytest.raises(ValueError):
        evaluate_extraction([case(LEFT), case(LEFT)], {}, provider_label="test")


def test_report_omits_clinical_text_values_and_evidence():
    report = score(case(LEFT), LEFT)
    assert "左眼" not in str(report)
    assert "evidence" not in report["results"][0]
    assert "value" not in report["results"][0]


def test_coverage_includes_invalid_and_missing_outputs():
    other = replace(case(RIGHT), case_id="two", dimension="correction")
    report = evaluate_extraction([case(LEFT), other], {"one": ClinicalState((LEFT,))}, provider_label="test")
    assert report["coverage"]["correction"]["failed_cases"] == 1
    assert report["coverage"]["numeric"]["exact_cases"] == 1
