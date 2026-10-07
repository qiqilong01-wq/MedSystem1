from dataclasses import FrozenInstanceError

import pytest

from medsystem1 import Action, MedSystem1, RouteRequest, SafetyRouter
from medsystem1.policy import TaskCatalog


def request(task='laterality', **changes):
    data=dict(task=task, confidence=1.0, schema_valid=True, evidence_present=True,
              capability='extract_structured_fact')
    data.update(changes)
    return RouteRequest(**data)


@pytest.mark.parametrize('task', ['change_glaucoma_treatment', 'extract_iop', 'diagnose', 'arbitrary'])
def test_low_capability_cannot_disguise_out_of_scope_task(task):
    result=MedSystem1().route(request(task))
    assert result.action is Action.HUMAN_REVIEW
    assert result.effective_risk=='unknown'


@pytest.mark.parametrize('risk', ['medium','moderate','high','unknown'])
@pytest.mark.parametrize('confidence', [0.0,0.649,0.95,1.0])
def test_review_lock_cannot_be_downgraded_by_threshold_or_confidence(risk,confidence):
    assert MedSystem1().route(request(risk=risk,confidence=confidence)).action is Action.HUMAN_REVIEW


@pytest.mark.parametrize('risk', ['auto','low','medium','high'])
def test_urgency_catalog_risk_cannot_be_lowered_by_caller(risk):
    result=MedSystem1().route(request('urgency_to_review',capability='classify_intent',risk=risk))
    assert result.action is Action.HUMAN_REVIEW
    assert result.effective_risk in ('medium','high')


def test_catalog_matches_six_canonical_tasks_and_is_immutable():
    catalog=TaskCatalog()
    assert set(catalog.tasks)=={'laterality','temporal_classification','photopsia','floaters',
                                'missing_fields','urgency_to_review'}
    with pytest.raises(TypeError):
        catalog.tasks['diagnose']=catalog.get('laterality')
    with pytest.raises(FrozenInstanceError):
        catalog.get('urgency_to_review').risk='low'


def test_metadata_cannot_enable_model_auto_calibration_or_cloud():
    result=SafetyRouter(local_threshold=0,review_threshold=0).route(request(metadata={
        'model_auto_enabled':True,'calibration_valid':True,'calibrated_probability':1,
        'cloud_enabled':True,'synthetic':True,'risk':'low'}))
    assert result.action is Action.HUMAN_REVIEW
    assert 'model auto disabled' in result.reasons[0]


def test_task_capability_mismatch_and_missing_evidence_are_not_permission_repair():
    for req in (request(capability='read_only_summary'),request(evidence_present=False),
                request(schema_valid=False)):
        assert MedSystem1().route(req).action is Action.HUMAN_REVIEW


@pytest.mark.parametrize('task', ['', ' ', None, [], {}])
def test_malformed_task_rejected(task):
    with pytest.raises(ValueError):
        MedSystem1().route(request(task))
