from types import MappingProxyType, SimpleNamespace

import pytest

from medsystem1 import (
    Action, ClinicalFact, ClinicalState, MedSystem1, ProviderContractError,
    ProviderExecutionError, RouteRequest, validate_clinical_state,
)
from medsystem1.adapters import OpenMedExtractionProvider, StrandsDecisionProvider


@pytest.mark.parametrize("state", [None, {}, [], ClinicalState([]), ClinicalState(({},))])
def test_normalized_state_shape_is_enforced(state):
    with pytest.raises(ProviderContractError):
        validate_clinical_state(state)


@pytest.mark.parametrize("fact", [
    ClinicalFact("", "left"), ClinicalFact(123, "left"), ClinicalFact("iop", None),
    ClinicalFact("iop", 16, confidence="0.99"), ClinicalFact("iop", 16, confidence=True),
    ClinicalFact("iop", 16, evidence=" "), ClinicalFact("iop", 16, evidence=16),
    ClinicalFact("iop", 16, provenance=""),
])
def test_malformed_fact_fields_are_rejected(fact):
    with pytest.raises(ProviderContractError):
        validate_clinical_state(ClinicalState((fact,)))


def test_zero_and_negation_values_are_not_missing():
    state = ClinicalState((ClinicalFact("eye_pain", False), ClinicalFact("count", 0)))
    assert validate_clinical_state(state) is state


def test_empty_state_is_valid_but_not_evidence():
    assert validate_clinical_state(ClinicalState()).facts == ()


def test_evidence_must_occur_in_supplied_source_without_echoing_data():
    state = ClinicalState((ClinicalFact("laterality", "right", evidence="右眼"),))
    with pytest.raises(ProviderContractError) as error:
        validate_clinical_state(state, source_text="左眼视物模糊")
    assert "左眼" not in str(error.value)
    assert "右眼" not in str(error.value)


@pytest.mark.parametrize("output", [None, "左眼", b"entity", {"text": "左眼"}, [None], ["左眼"]])
def test_extraction_output_shape_rejected(output):
    provider = OpenMedExtractionProvider(lambda _: output)
    with pytest.raises(ProviderContractError):
        provider.extract("左眼")


@pytest.mark.parametrize("item", [{}, {"label": None, "text": "左眼"}, {"text": ""}, {"value": None}])
def test_missing_or_malformed_entities_are_not_success(item):
    with pytest.raises(ProviderContractError):
        OpenMedExtractionProvider(lambda _: [item]).extract("左眼")


def test_mixed_valid_and_invalid_entities_do_not_return_partial_state():
    provider = OpenMedExtractionProvider(lambda _: [{"text": "左眼"}, "malformed"])
    with pytest.raises(ProviderContractError):
        provider.extract("左眼")


def test_extraction_preserves_normalized_value_and_literal_evidence():
    provider = OpenMedExtractionProvider(lambda _: (
        MappingProxyType({"type": "laterality", "text": "左眼", "value": "left"}),
    ))
    fact = provider.extract("患者左眼视物模糊").facts[0]
    assert fact.value == "left"
    assert fact.evidence == "左眼"
    assert fact.provenance == "openmed"


def test_missing_evidence_is_never_fabricated():
    fact = OpenMedExtractionProvider(
        lambda _: [{"label": "iop", "value": 16, "score": 0.99}]
    ).extract("左眼眼压16").facts[0]
    assert fact.value == 16
    assert fact.evidence is None


def test_generator_failure_is_not_partial_success():
    def analyzer(_):
        yield {"text": "左眼"}
        raise RuntimeError("upstream failure")

    with pytest.raises(ProviderExecutionError):
        OpenMedExtractionProvider(analyzer).extract("左眼")


@pytest.mark.parametrize("adapter", [OpenMedExtractionProvider, StrandsDecisionProvider])
def test_non_callable_configuration_is_rejected(adapter):
    with pytest.raises(TypeError):
        adapter(None)


def test_provider_failures_are_typed_and_do_not_echo_payload():
    def fail(*args, **kwargs):
        raise RuntimeError("private clinical detail")

    for operation in (
        lambda: OpenMedExtractionProvider(fail).extract("左眼"),
        lambda: StrandsDecisionProvider(fail).decide(task="extract_iop", state=ClinicalState()),
    ):
        with pytest.raises(ProviderExecutionError) as error:
            operation()
        assert "private clinical detail" not in str(error.value)


@pytest.mark.parametrize("result", [
    {"confidence": 0.95, "choice": "local"},
    (0.95, {"choice": "local"}),
    SimpleNamespace(confidence=0.95, metadata={"choice": "local"}),
])
def test_decision_result_shapes_conform(result):
    confidence, metadata = StrandsDecisionProvider(lambda **_: result).decide(
        task="extract_iop", state=ClinicalState(),
    )
    assert confidence == 0.95
    assert metadata["choice"] == "local"
    assert "raw_result" not in metadata


@pytest.mark.parametrize("result", [
    (0.95, None), (0.95, []), (0.95, [("choice", "local")]), (0.95, {1: "local"}),
    SimpleNamespace(confidence=0.95, metadata="bad"), (0.95,), [0.95, {}],
])
def test_malformed_decision_results_rejected(result):
    with pytest.raises(ProviderContractError):
        StrandsDecisionProvider(lambda **_: result).decide(task="extract_iop", state=ClinicalState())


def test_opaque_result_is_not_kept_in_metadata():
    result = SimpleNamespace(confidence=0.99, private_payload="clinical data")
    _, metadata = StrandsDecisionProvider(lambda **_: result).decide(
        task="extract_iop", state=ClinicalState(),
    )
    assert metadata == {}


@pytest.mark.parametrize("task,state", [("", ClinicalState()), (None, ClinicalState()), ("x", {})])
def test_invalid_decision_input_stops_before_calling_provider(task, state):
    def must_not_run(**_):
        pytest.fail("invalid input reached upstream")

    with pytest.raises(ProviderContractError):
        StrandsDecisionProvider(must_not_run).decide(task=task, state=state)


@pytest.mark.parametrize("capability,evidence,expected", [
    ("change_treatment", True, Action.HUMAN_REVIEW),
    ("submit_medical_record", True, Action.HUMAN_REVIEW),
    ("unknown_tool", True, Action.HUMAN_REVIEW),
    ("extract_structured_fact", False, Action.HUMAN_REVIEW),
    ("extract_structured_fact", True, Action.HUMAN_REVIEW),
])
def test_provider_suggested_local_never_overrides_router(capability, evidence, expected):
    state = ClinicalState((ClinicalFact("iop", 16, evidence="眼压16" if evidence else None),))
    score, metadata = StrandsDecisionProvider(
        lambda **_: {"confidence": 1.0, "action": "LOCAL", "capability": "extract_structured_fact"}
    ).decide(task="laterality", state=state)
    decision = MedSystem1().route(RouteRequest(
        task="laterality", confidence=score, schema_valid=True,
        evidence_present=bool(state.facts) and all(f.evidence is not None for f in state.facts),
        capability=capability, metadata=metadata,
    ))
    assert decision.action is expected

