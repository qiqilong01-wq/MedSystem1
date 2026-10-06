import pytest

from medsystem1 import Action, MedSystem1, RouteRequest, SafetyRouter


def req(**overrides):
    values = dict(
        task="extract_iop",
        confidence=0.95,
        schema_valid=True,
        evidence_present=True,
        capability="extract_structured_fact",
    )
    values.update(overrides)
    return RouteRequest(**values)


def test_low_risk_high_confidence_can_stay_local():
    assert MedSystem1().route(req()).action is Action.LOCAL


def test_high_risk_never_becomes_local_from_confidence():
    assert MedSystem1().route(
        req(capability="change_treatment", confidence=1.0)
    ).action is Action.HUMAN_REVIEW


def test_missing_evidence_escalates():
    assert MedSystem1().route(req(evidence_present=False)).action is Action.ESCALATE


def test_invalid_schema_escalates():
    assert MedSystem1().route(req(schema_valid=False)).action is Action.ESCALATE


def test_unknown_capability_fails_conservatively():
    assert MedSystem1().route(req(capability="unknown_tool")).action is Action.HUMAN_REVIEW


def test_medium_confidence_requires_review():
    assert MedSystem1().route(req(confidence=0.80)).action is Action.HUMAN_REVIEW


def test_low_confidence_escalates():
    assert MedSystem1().route(req(confidence=0.40)).action is Action.ESCALATE


def test_bad_confidence_rejected():
    with pytest.raises(ValueError):
        MedSystem1().route(req(confidence=1.1))


def test_threshold_validation():
    with pytest.raises(ValueError):
        SafetyRouter(local_threshold=0.5, review_threshold=0.8)
