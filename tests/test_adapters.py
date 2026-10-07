import pytest

from medsystem1 import ClinicalState
from medsystem1.adapters import OpenMedExtractionProvider, StrandsDecisionProvider


def test_openmed_adapter_normalizes_entities():
    provider = OpenMedExtractionProvider(
        lambda text: [{"label": "laterality", "text": "左眼", "score": 0.98}]
    )
    state = provider.extract("患者左眼视物模糊")
    assert state.facts[0].name == "laterality"
    assert state.facts[0].evidence == "左眼"
    assert state.facts[0].provenance == "openmed"


def test_openmed_adapter_rejects_non_text():
    provider = OpenMedExtractionProvider(lambda _: [])
    with pytest.raises(TypeError):
        provider.extract({"text": "x"})


def test_strands_adapter_reads_confidence():
    provider = StrandsDecisionProvider(
        lambda **_: {"confidence": 0.91, "choice": "yes"}
    )
    confidence, metadata = provider.decide(task="urgent", state=ClinicalState())
    assert confidence == 0.91
    assert metadata["choice"] == "yes"


def test_strands_adapter_rejects_missing_confidence():
    provider = StrandsDecisionProvider(lambda **_: {"choice": "yes"})
    with pytest.raises(ValueError):
        provider.decide(task="urgent", state=ClinicalState())


@pytest.mark.parametrize("score", [True, False, float("nan"), float("inf"), -0.1, 1.1, "nan", "bad"])
def test_openmed_rejects_malformed_confidence(score):
    provider = OpenMedExtractionProvider(lambda _: [{"text": "左眼", "score": score}])
    with pytest.raises(ValueError):
        provider.extract("左眼")


@pytest.mark.parametrize("score", [True, False, float("nan"), float("inf"), -0.1, 1.1, "nan", "bad"])
def test_strands_rejects_malformed_confidence(score):
    provider = StrandsDecisionProvider(lambda **_: {"confidence": score})
    with pytest.raises(ValueError):
        provider.decide(task="extract_iop", state=ClinicalState())


def test_adapters_accept_numeric_strings_without_losing_evidence():
    state = OpenMedExtractionProvider(
        lambda _: [{"text": "左眼", "score": "0.95"}]
    ).extract("左眼")
    assert state.facts[0].confidence == 0.95
    assert state.facts[0].evidence == "左眼"
    score, _ = StrandsDecisionProvider(lambda **_: ("0.91", {})).decide(
        task="extract_laterality", state=state,
    )
    assert score == 0.91


def test_openmed_missing_score_stays_unknown():
    fact = OpenMedExtractionProvider(lambda _: [{"text": "左眼"}]).extract("左眼").facts[0]
    assert fact.confidence is None
