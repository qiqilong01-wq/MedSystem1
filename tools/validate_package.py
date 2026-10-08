"""Check canonical assets and default gates without providers, downloads or egress."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0,str(ROOT/'src'))
    from medsystem1.contracts import schema_registry, validate_request, validate_response, validate_schema
    from medsystem1.policy import TaskCatalog
    schema_dir=ROOT/'schemas/v0.1'
    schemas,_=schema_registry(schema_dir)
    catalog=TaskCatalog()
    policy=json.loads((ROOT/'configs/v0.1/policy.json').read_text(encoding='utf-8'))
    validate_schema(policy,'policy.schema.json',schema_dir)
    assert set(policy['tasks'])==set(catalog.tasks)
    assert not policy['frontier']['enabled']
    assert all(not item['auto_enabled'] for item in policy['tasks'].values())
    from medsystem1.core.local_deployment import load_local_deployment
    deployment=load_local_deployment(ROOT)
    assert not deployment.settings['enabled']
    assert deployment.settings['tasks']==[]
    deployment_schemas,_=schema_registry(ROOT/'schemas/deployment/v0.1')
    provider_cases=json.loads((ROOT/'examples/ophthalmology/strands-smoke.synthetic.json').read_text(encoding='utf-8'))['cases']
    assert len(provider_cases)==10 and len({c['case_id'] for c in provider_cases})==10
    for case in provider_cases:
        task=case['task_id']
        assert task in ('laterality','temporal_classification','photopsia','floaters')
        assert case['expected_label'] in catalog.tasks[task].labels
        assert isinstance(case['state'],str) and case['state']
    request=json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
    response=json.loads((ROOT/'examples/ophthalmology/response.json').read_text(encoding='utf-8'))
    validate_response(response,request,schema_dir)
    from medsystem1 import MedSystem1
    executed=MedSystem1().decide(request)
    validate_response(executed,request,schema_dir)
    assert executed['review_required']
    cases=0
    for line in (ROOT/'benchmarks/smoke.jsonl').read_text(encoding='utf-8').splitlines():
        case=json.loads(line)
        validate_schema(case,'benchmark-case.schema.json',schema_dir)
        validate_request(case['request'],schema_dir)
        assert set(case['expected_values'])==set(case['request']['tasks'])
        result=MedSystem1().decide(case['request'])
        assert {r['task_id']:r['value'] for r in result['results']}==case['expected_values']
        assert result['review_required']==case['expected_review_required']
        cases+=1
    required=('README.md','PRODUCT_SPEC_v0.1.md','TECH_SPEC_v0.1.md',
              'DEVELOPMENT_SPEC_v0.1.md','API_SCHEMA.md','BENCHMARK_SPEC.md',
              'SAFETY_BOUNDARIES.md','AGENTS.md','CHANGELOG.md')
    assert all((ROOT/name).is_file() for name in required)
    print(f'PASS: {len(schemas)} clinical + {len(deployment_schemas)} deployment schemas, six-task catalog, default model/cloud off, {cases} executed rules fixtures, 10 unexecuted provider fixtures')


if __name__=='__main__':
    main()
