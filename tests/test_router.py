import pytest

from medsystem1 import Action, MedSystem1, RouteRequest, SafetyRouter


def req(**overrides):
    values = dict(
        task="laterality",
        confidence=0.95,
        schema_valid=True,
        evidence_present=True,
        capability="extract_structured_fact",
    )
    values.update(overrides)
    return RouteRequest(**values)


def test_high_native_confidence_stays_review_without_calibration():
    assert MedSystem1().route(req()).action is Action.HUMAN_REVIEW


def test_high_risk_never_becomes_local_from_confidence():
    assert MedSystem1().route(
        req(capability="change_treatment", confidence=1.0)
    ).action is Action.HUMAN_REVIEW


def test_missing_evidence_locks_review():
    assert MedSystem1().route(req(evidence_present=False)).action is Action.HUMAN_REVIEW


def test_invalid_schema_locks_review():
    assert MedSystem1().route(req(schema_valid=False)).action is Action.HUMAN_REVIEW


def test_unknown_capability_fails_conservatively():
    assert MedSystem1().route(req(capability="unknown_tool")).action is Action.HUMAN_REVIEW


def test_medium_confidence_requires_review():
    assert MedSystem1().route(req(confidence=0.80)).action is Action.HUMAN_REVIEW


def test_low_confidence_has_no_implicit_export_permission():
    assert MedSystem1().route(req(confidence=0.40)).action is Action.HUMAN_REVIEW


def test_bad_confidence_rejected():
    with pytest.raises(ValueError):
        MedSystem1().route(req(confidence=1.1))


def test_threshold_validation():
    with pytest.raises(ValueError):
        SafetyRouter(local_threshold=0.5, review_threshold=0.8)


@pytest.mark.parametrize("confidence", [True, False, "0.99", None, float("nan"), float("inf"), -0.1, 1.1])
def test_malformed_confidence_cannot_authorize_local(confidence):
    with pytest.raises(ValueError):
        MedSystem1().route(req(confidence=confidence))


@pytest.mark.parametrize("field", ["schema_valid", "evidence_present"])
@pytest.mark.parametrize("value", ["false", "true", 0, 1, None, [], {}])
def test_safety_signals_require_actual_booleans(field, value):
    with pytest.raises(ValueError):
        MedSystem1().route(req(**{field: value}))


@pytest.mark.parametrize("capability", ["", "  ", None, [], {}])
def test_malformed_capability_rejected(capability):
    with pytest.raises(ValueError):
        MedSystem1().route(req(capability=capability))


@pytest.mark.parametrize("field", ["local_threshold", "review_threshold"])
@pytest.mark.parametrize("value", [True, "0.9", None, float("nan"), float("inf"), -0.1, 1.1])
def test_malformed_thresholds_rejected(field, value):
    with pytest.raises(ValueError):
        SafetyRouter(**{field: value})


@pytest.mark.parametrize("schema_valid", [False, True])
@pytest.mark.parametrize("evidence_present", [False, True])
@pytest.mark.parametrize("risk", ["high", "unknown", None, []])
def test_high_or_unknown_risk_keeps_human_review(schema_valid, evidence_present, risk):
    decision = MedSystem1().route(req(
        risk=risk, schema_valid=schema_valid, evidence_present=evidence_present,
    ))
    assert decision.action is Action.HUMAN_REVIEW


@pytest.mark.parametrize("capability", [
    "final_diagnosis", "prescribe_medication", "change_treatment", "submit_medical_record",
    "perform_procedure", "autonomous_patient_instruction", "unknown_tool",
])
@pytest.mark.parametrize("confidence", [0.0, 0.65, 0.90, 1.0])
def test_authority_boundary_survives_evidence_failure_and_risk_override(capability, confidence):
    decision = MedSystem1().route(req(
        capability=capability, confidence=confidence, risk="low",
        schema_valid=False, evidence_present=False,
    ))
    assert decision.action is Action.HUMAN_REVIEW


@pytest.mark.parametrize("confidence, expected", [
    (0.0, Action.HUMAN_REVIEW), (0.649, Action.HUMAN_REVIEW), (0.65, Action.HUMAN_REVIEW),
    (0.899, Action.HUMAN_REVIEW), (0.90, Action.HUMAN_REVIEW), (1, Action.HUMAN_REVIEW),
])
def test_default_threshold_edges(confidence, expected):
    assert MedSystem1().route(req(confidence=confidence)).action is expected


def test_medium_risk_never_uses_local_even_at_full_confidence():
    assert MedSystem1().route(req(risk="medium", confidence=1.0)).action is Action.HUMAN_REVIEW

