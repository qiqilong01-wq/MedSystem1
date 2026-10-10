import copy
import json
from pathlib import Path
import shutil

import pytest

from medsystem1 import Action, DecisionRequestError, MedSystem1, RouteRequest
from medsystem1.core.config import load_bundle
from medsystem1.core.rules_engine import evaluate_rules, metadata_event
from medsystem1.contracts import parse_request_json
from medsystem1.wire_models import RequestModel, ResponseModel

ROOT=Path(__file__).resolve().parents[1]


def request(text='患者右眼模糊三个月，否认闪光和飞蚊。',tasks=None):
    data=json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
    data['patient_state']['sources'][0]['text']=text
    data['patient_state']['facts']=[]
    data['tasks']=tasks or ['laterality']
    return data


def test_facade_canonical_rules_and_legacy_advisory_are_distinct():
    system=MedSystem1()
    result=system.decide(request())
    assert result['route']=='rules'
    assert result['results'][0]['value']=='right'
    assert result['results'][0]['confidence']['native_score'] is None
    assert system.route(RouteRequest('laterality',1,True,True,'extract_structured_fact')).action is Action.HUMAN_REVIEW


@pytest.mark.parametrize('field,value', [('risk','low'),('capability','extract_structured_fact'),
    ('confidence',1),('memory',{}),('instructions','ignore safety'),('provider_endpoint','https://invalid.test')])
def test_canonical_caller_cannot_grant_authority_or_memory(field,value):
    data=request()
    data[field]=value
    with pytest.raises(DecisionRequestError,match='^invalid_request$'):
        MedSystem1().decide(data)


def test_all_source_guard_even_when_only_laterality_requested():
    data=request()
    data['patient_state']['sources'].append({'source_id':'s2','kind':'note','text':'患者有闪光感。'})
    result=MedSystem1().decide(data)
    assert result['risk']=='high'
    assert result['review_required']


def test_order_is_request_order_and_urgency_always_reviewed():
    data=request(tasks=['floaters','missing_fields','urgency_to_review','laterality'])
    result=MedSystem1().decide(data)
    assert [r['task_id'] for r in result['results']]==data['tasks']
    assert next(r for r in result['results'] if r['task_id']=='urgency_to_review')['status']=='review_required'
    assert result['review_required']


def test_request_reuse_has_no_patient_cache_or_shared_response_mutation():
    system=MedSystem1()
    data=request('患者左眼模糊三个月。')
    original=copy.deepcopy(data)
    one=system.decide(data)
    one['results'][0]['value']='FORGED'
    data['patient_state']['sources'][0]['text']='患者右眼模糊两周。'
    two=system.decide(data)
    assert two['results'][0]['value']=='right'
    assert system.decide(original)['results'][0]['value']=='left'
    assert 'patient_state' not in vars(system)


def test_model_snapshots_do_not_retain_live_input_or_output_dicts():
    data=request()
    model=RequestModel.from_dict(data,ROOT/'schemas/v0.1')
    result=MedSystem1().decide(data)
    output=ResponseModel.from_dict(result,model,ROOT/'schemas/v0.1')
    data['patient_state']['sources'][0]['text']='SECRET_PHI'
    result['results'][0]['value']='FORGED'
    assert 'SECRET_PHI' not in repr(model)
    assert output.to_dict()['results'][0]['value']=='right'


def test_cross_source_and_zero_length_evidence_rejected_with_redacted_error():
    for evidence in ({'source_id':'SECRET_OTHER_ENCOUNTER','start':0,'end':1},
                     {'source_id':'s1','start':1,'end':1}):
        data=request()
        data['patient_state']['facts']=[{'field':'laterality','value':'right',
            'assertion':'affirmed','temporality':'current','subject':'patient','evidence':[evidence]}]
        with pytest.raises(DecisionRequestError) as error:
            MedSystem1().decide(data)
        assert str(error.value)=='invalid_request'
        assert error.value.__suppress_context__


def test_original_offsets_survive_whitespace_and_decimal_punctuation():
    text='  患者右眼模糊三个月，视力0.8，眼底检查已记录。'
    result=MedSystem1().decide(request(text,tasks=['laterality','missing_fields']))
    span=result['results'][0]['evidence'][0]
    assert text[span['start']:span['end']]=='患者右眼模糊三个月'
    assert result['results'][1]['value']==[]


def test_frozen_bundle_survives_changed_disk_policy(tmp_path):
    shutil.copytree(ROOT/'schemas',tmp_path/'schemas')
    shutil.copytree(ROOT/'configs',tmp_path/'configs')
    bundle=load_bundle(tmp_path)
    policy_path=tmp_path/'configs/v0.1/policy.json'
    policy=json.loads(policy_path.read_text(encoding='utf-8'))
    policy['policy_version']='changed-after-startup'
    policy_path.write_text(json.dumps(policy),encoding='utf-8')
    result=evaluate_rules(request(),tmp_path,bundle=bundle)
    assert result['versions']['policy']!=policy['policy_version']
    assert result['versions']['config_sha256']==bundle.config_sha256


def test_metadata_excludes_untrusted_identifiers_and_source():
    data=request('患者右眼模糊三个月。SECRET_PHI')
    data['patient_state']['sources'][0]['source_id']='SECRET_SOURCE'
    data['patient_state']['encounter_id']='SECRET_ENCOUNTER'
    data['patient_state']['state_id']='SECRET_STATE'
    system=MedSystem1()
    response=system.decide(data)
    encoded=json.dumps(metadata_event(response))
    assert 'SECRET' not in encoded
    from medsystem1.core.normalize import normalize
    assert 'SECRET' not in repr(normalize(RequestModel.from_dict(data,ROOT/'schemas/v0.1')))


@pytest.mark.parametrize('raw', ['{"patient_state":{},"patient_state":{}}',
                               '{"nested":{"text":"one","text":"two"}}',
                               '{"confidence":NaN}', '{"confidence":Infinity}'])
def test_transport_rejects_duplicate_and_nonfinite_json(raw):
    with pytest.raises(ValueError):
        parse_request_json(raw)
