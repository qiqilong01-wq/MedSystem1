import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from medsystem1.core.config import load_bundle
from medsystem1.core.normalize import normalize
from medsystem1.core.rules_engine import evaluate_rules, metadata_event
from medsystem1.wire_models import RequestModel, ResponseModel

ROOT=Path(__file__).resolve().parents[1]


def request(text, tasks=None, facts=None):
    data=json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
    data['patient_state']['sources'][0]['text']=text
    data['patient_state']['facts']=facts or []
    if tasks is not None:
        data['tasks']=tasks
    return data


class RuleEngineTests(unittest.TestCase):
    def values(self,response):
        return {r['task_id']:r['value'] for r in response['results']}

    def test_all_seed_cases_match_gold_without_model(self):
        for line in (ROOT/'benchmarks/smoke.jsonl').read_text(encoding='utf-8').splitlines():
            case=json.loads(line)
            with self.subTest(case=case['case_id']):
                response=evaluate_rules(case['request'],ROOT)
                self.assertEqual(self.values(response),case['expected_values'])
                self.assertEqual(response['review_required'],case['expected_review_required'])

    def test_low_risk_single_task_returns_structured_rules_only(self):
        response=evaluate_rules(request('患者右眼模糊三个月，否认闪光感和飞蚊。',['laterality']),ROOT)
        self.assertEqual(response['route'],'rules')
        self.assertFalse(response['review_required'])
        self.assertEqual(self.values(response),{'laterality':'right'})
        self.assertIsNone(response['results'][0]['confidence']['native_score'])

    def test_whole_input_scanned_for_subset(self):
        response=evaluate_rules(request('患者右眼模糊三个月，有闪光感。',['laterality']),ROOT)
        self.assertEqual(response['route'],'human_review')
        self.assertEqual(response['risk'],'high')

    def test_unsupported_tail_cannot_be_truncated_or_ignored(self):
        text='患者右眼模糊三个月，否认闪光和飞蚊。'+'注释。'*1000+'患者突然看不见。'
        response=evaluate_rules(request(text,['laterality']),ROOT)
        self.assertTrue(response['review_required'])
        self.assertIn('risk_requires_review',response['reason_codes'])

    def test_unknown_subject_and_empty_content_require_review(self):
        for text in ('右眼模糊三个月。','   ','家属左眼有闪光。'):
            response=evaluate_rules(request(text,['laterality']),ROOT)
            self.assertTrue(response['review_required'])
            self.assertEqual(self.values(response)['laterality'],'unknown')

    def test_unsupported_negation_never_means_absent(self):
        for text in ('患者并非没有闪光感。','患者不能否认飞蚊。','患者否认无闪光感。'):
            response=evaluate_rules(request(text),ROOT)
            self.assertTrue(response['review_required'])
            self.assertEqual(self.values(response)['photopsia'],'unknown')
            self.assertEqual(self.values(response)['floaters'],'unknown')

    def test_uncertain_symptom_is_unknown_and_reviewed(self):
        response=evaluate_rules(request('患者可能有闪光感。'),ROOT)
        self.assertEqual(self.values(response)['photopsia'],'unknown')
        self.assertTrue(response['review_required'])

    def test_historical_and_other_subjects_not_current_patient_symptoms(self):
        response=evaluate_rules(request('患者曾有飞蚊，现在否认飞蚊和闪光感。'),ROOT)
        self.assertEqual(self.values(response)['floaters'],'absent')
        response=evaluate_rules(request('家属左眼有闪光，患者右眼模糊两周，患者否认闪光和飞蚊。'),ROOT)
        self.assertEqual(self.values(response)['laterality'],'right')
        self.assertEqual(self.values(response)['photopsia'],'absent')

    def test_separate_sources_do_not_inherit_subject(self):
        req=request('患者右眼模糊两周。',['laterality'])
        req['patient_state']['sources'].append({'source_id':'s2','kind':'note','text':'有闪光感。'})
        response=evaluate_rules(req,ROOT)
        self.assertTrue(response['review_required'])

    def test_current_conflicts_and_multi_eye_clauses_review(self):
        for text in ('患者有闪光感，否认闪光感。', '患者右眼模糊三天，左眼有飞蚊。'):
            response=evaluate_rules(request(text),ROOT)
            self.assertTrue(response['review_required'])
            self.assertIn('input_conflict',response['reason_codes'])

    def test_duration_boundary_and_chinese_number(self):
        for duration, expected in (('七天','recent'),('八天','longstanding'),
                                   ('一周','recent'),('两周','longstanding'),('十二天','longstanding'),
                                   ('半个月','longstanding'),('3小时','recent')):
            response=evaluate_rules(request('患者右眼模糊'+duration+'。',['temporal_classification']),ROOT)
            self.assertEqual(self.values(response)['temporal_classification'],expected)
        response=evaluate_rules(request('患者右眼模糊0天。',['temporal_classification']),ROOT)
        self.assertEqual(self.values(response)['temporal_classification'],'unknown')
        self.assertTrue(response['review_required'])

    def test_duration_overflow_is_unknown(self):
        response=evaluate_rules(request('患者右眼模糊'+'9'*1000+'年。',['temporal_classification']),ROOT)
        self.assertEqual(self.values(response)['temporal_classification'],'unknown')
        self.assertTrue(response['review_required'])

    def test_decimal_acuity_and_documentation_presence(self):
        response=evaluate_rules(request('患者右眼模糊三天，视力0.8，眼底检查已记录。',['missing_fields']),ROOT)
        self.assertEqual(self.values(response)['missing_fields'],[])
        self.assertFalse(response['review_required'])
        response=evaluate_rules(request('患者视力0.8，视力0.7。',['missing_fields']),ROOT)
        self.assertIn('visual_acuity',self.values(response)['missing_fields'])
        self.assertTrue(response['review_required'])

    def test_fact_cannot_override_source_or_spoof_risk(self):
        text='患者右眼模糊三个月'
        fact={'field':'laterality','value':'left','assertion':'affirmed','temporality':'current',
              'subject':'patient','evidence':[{'source_id':'s1','start':0,'end':len(text)}]}
        response=evaluate_rules(request(text,['laterality'],[fact]),ROOT)
        self.assertEqual(self.values(response)['laterality'],'conflicting')
        self.assertTrue(response['review_required'])
        fact['value']='right'
        response=evaluate_rules(request(text,['laterality'],[fact]),ROOT)
        self.assertEqual(response['route'],'rules')

    def test_cloud_requested_does_not_call_network(self):
        req=request('患者右眼有闪光感。')
        req['cloud_fallback_requested']=True
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            response=evaluate_rules(req,ROOT)
        self.assertTrue(response['review_required'])
        self.assertIn('cloud_disabled',response['reason_codes'])

    def test_input_snapshot_is_frozen_and_requests_do_not_leak(self):
        req=request('患者左眼模糊三天。',['laterality'])
        saved=copy.deepcopy(req)
        model=RequestModel.from_dict(req,ROOT/'schemas/v0.1')
        req['patient_state']['sources'][0]['text']='患者右眼模糊两周。'
        self.assertEqual(model.to_dict(),saved)
        state=normalize(model)
        with self.assertRaises(FrozenInstanceError):
            state.state.sources[0].text='modified'
        self.assertEqual(self.values(evaluate_rules(saved,ROOT))['laterality'],'left')
        self.assertEqual(self.values(evaluate_rules(req,ROOT))['laterality'],'right')
        self.assertEqual(model.to_dict(),saved)

    def test_metadata_and_reprs_exclude_patient_content_and_identifiers(self):
        req=request('患者右眼模糊三天。SECRET_PHI',['laterality'])
        req['patient_state']['encounter_id']='SECRET_ENCOUNTER'
        model=RequestModel.from_dict(req,ROOT/'schemas/v0.1')
        response=evaluate_rules(req,ROOT)
        encoded=json.dumps(metadata_event(response))
        for marker in ('SECRET_PHI','SECRET_ENCOUNTER','source_id','evidence','patient_state'):
            self.assertNotIn(marker,encoded)
        self.assertNotIn('SECRET',repr(model))
        self.assertNotIn('SECRET',repr(normalize(model)))

    def test_schema_models_have_exact_roundtrip_and_same_rejections(self):
        req=request('患者右眼模糊三天。')
        model=RequestModel.from_dict(req,ROOT/'schemas/v0.1')
        response=evaluate_rules(req,ROOT)
        self.assertEqual(ResponseModel.from_dict(response,model,ROOT/'schemas/v0.1').to_dict(),response)
        req['diagnosis']='forbidden'
        with self.assertRaises(Exception):
            RequestModel.from_dict(req,ROOT/'schemas/v0.1')

    def test_registry_labels_checked_against_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            path=Path(tmp)
            shutil.copytree(ROOT/'schemas',path/'schemas')
            shutil.copytree(ROOT/'configs',path/'configs')
            catalog=json.loads((path/'configs/v0.1/tasks.json').read_text(encoding='utf-8'))
            catalog['tasks']['urgency_to_review']['labels'].append('safe')
            (path/'configs/v0.1/tasks.json').write_text(json.dumps(catalog),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'catalog_labels_mismatch'):
                load_bundle(path)

    def test_cli_redacts_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'request.json'
            path.write_text('{"SECRET_PHI":',encoding='utf-8')
            result=subprocess.run([sys.executable,'-m','medsystem1','--project-root',str(ROOT),
                                   'decide','--input',str(path)],capture_output=True,text=True,
                                   env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')})
            self.assertEqual(result.returncode,2)
            self.assertNotIn('SECRET_PHI',result.stderr)
            self.assertNotIn('Traceback',result.stderr)
            self.assertEqual(result.stdout,'')


if __name__=='__main__':
    unittest.main()
