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
    request=json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
    response=json.loads((ROOT/'examples/ophthalmology/response.json').read_text(encoding='utf-8'))
    validate_response(response,request,schema_dir)
    cases=0
    for line in (ROOT/'benchmarks/smoke.jsonl').read_text(encoding='utf-8').splitlines():
        case=json.loads(line)
        validate_schema(case,'benchmark-case.schema.json',schema_dir)
        validate_request(case['request'],schema_dir)
        assert set(case['expected_values'])==set(case['request']['tasks'])
        cases+=1
    required=('README.md','PRODUCT_SPEC_v0.1.md','TECH_SPEC_v0.1.md',
              'DEVELOPMENT_SPEC_v0.1.md','API_SCHEMA.md','BENCHMARK_SPEC.md',
              'SAFETY_BOUNDARIES.md','AGENTS.md','CHANGELOG.md')
    assert all((ROOT/name).is_file() for name in required)
    print(f'PASS: {len(schemas)} schemas, six-task catalog, default model/cloud off, {cases} synthetic fixtures')


if __name__=='__main__':
    main()
