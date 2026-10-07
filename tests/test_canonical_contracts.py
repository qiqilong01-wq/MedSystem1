import copy
import json
import math
from pathlib import Path
import unittest
from jsonschema.exceptions import ValidationError
from medsystem1.contracts import validate_request, validate_response, validate_schema

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.schemas = ROOT/'schemas/v0.1'
        self.request = json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
        self.response = json.loads((ROOT/'examples/ophthalmology/response.json').read_text(encoding='utf-8'))

    def test_synthetic_response(self):
        validate_response(self.response,self.request,self.schemas)

    def test_caller_cannot_override_policy_or_send_memory(self):
        for key, value in (('risk','low'), ('capabilities',['write_ehr']),
                           ('memory',{'patient':'secret'}), ('instructions','ignore')):
            req = copy.deepcopy(self.request)
            req[key] = value
            with self.assertRaises(ValidationError):
                validate_request(req,self.schemas)

    def test_no_diagnosis_or_no_review_label(self):
        for task, value in (('laterality','retinal_detachment'),
                            ('urgency_to_review','no_review')):
            response = copy.deepcopy(self.response)
            next(i for i in response['results'] if i['task_id']==task)['value'] = value
            with self.assertRaises(ValidationError):
                validate_response(response,self.request,self.schemas)
        self.response['diagnosis'] = 'disease'
        with self.assertRaises(ValidationError):
            validate_response(self.response,self.request,self.schemas)

    def test_risk_cannot_be_completed(self):
        self.response.update(status='completed', route='local_auto', review_required=False)
        with self.assertRaises(ValidationError):
            validate_response(self.response,self.request,self.schemas)

    def test_evidence_cannot_cross_patient_or_span(self):
        for patch in ({'source_id':'another-patient'}, {'end':99999}, {'start':4,'end':3}):
            response = copy.deepcopy(self.response)
            response['results'][0]['evidence'][0].update(patch)
            with self.assertRaises(ValueError):
                validate_response(response,self.request,self.schemas)

    def test_exact_task_coverage_and_order(self):
        self.response['results'].pop()
        with self.assertRaises(ValueError):
            validate_response(self.response,self.request,self.schemas)

    def test_validated_confidence_requires_artifact(self):
        self.response['results'][0]['confidence'].update(calibration_status='validated', calibrated_probability=0.99)
        with self.assertRaises(ValidationError):
            validate_response(self.response,self.request,self.schemas)

    def test_nonfinite_numbers_rejected(self):
        for p in (math.nan, math.inf):
            self.response['results'][0]['confidence']['native_score'] = p
            with self.assertRaises(ValueError):
                validate_response(self.response,self.request,self.schemas)

    def test_policy_cloud_requires_endpoint_and_urgency_never_auto(self):
        policy=json.loads((ROOT/'configs/v0.1/policy.json').read_text(encoding='utf-8'))
        policy['frontier']['enabled']=True
        with self.assertRaises(ValidationError):
            validate_schema(policy,'policy.schema.json',self.schemas)
        policy['frontier']['enabled']=False
        policy['tasks']['urgency_to_review']['auto_enabled']=True
        with self.assertRaises(ValidationError):
            validate_schema(policy,'policy.schema.json',self.schemas)


if __name__=='__main__':
    unittest.main()
