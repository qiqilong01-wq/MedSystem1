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
