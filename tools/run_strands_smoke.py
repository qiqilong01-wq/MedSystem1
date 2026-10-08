"""Explicit opt-in, shipped synthetic cases only. Never downloads or starts a model."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from medsystem1 import __version__  # noqa: E402
from medsystem1.adapters.strands_http import StrandsHttpProvider  # noqa: E402
from medsystem1.bounded import BoundedProviderError  # noqa: E402
from medsystem1.contracts import parse_request_json  # noqa: E402
from medsystem1.core.local_deployment import load_local_deployment  # noqa: E402


def run_smoke(deployment_path, *, allow_real_provider=False):
    if allow_real_provider is not True:
        raise BoundedProviderError('capability_missing')
    deployment = load_local_deployment(ROOT, deployment_path)
    provider = StrandsHttpProvider(deployment)
    raw = ROOT.joinpath('examples/ophthalmology/strands-smoke.synthetic.json').read_bytes()
    fixture = parse_request_json(raw)
    cases = fixture['cases']
    if (fixture['fixture_version'] != 'strands-smoke-0.1.0' or len(cases) != 10
            or len({c['case_id'] for c in cases}) != 10):
        raise BoundedProviderError('out_of_domain')
    results = []
    for case in cases:
        try:
            response = provider.decide(case['state'], (case['task_id'],), timeout_ms=30000)
            answer = response.answers[0]
            results.append({'case_id': case['case_id'], 'task_id': case['task_id'],
                'contract_valid': True, 'label': answer.label,
                'expected_label_match': answer.label == case['expected_label'],
                'native_score': answer.native_score, 'selected_probability': answer.selected_probability,
                'latency_ms': response.latency_ms})
        except BoundedProviderError as error:
            results.append({'case_id': case['case_id'], 'task_id': case['task_id'],
                            'contract_valid': False, 'error_code': error.code})
    return {'validation_kind': 'opt_in_local_provider_synthetic_smoke',
        'software_version': __version__, 'python_version': platform.python_version(),
        'fixture_sha256': hashlib.sha256(raw).hexdigest(), 'deployment_sha256': deployment.config_sha256,
        'descriptor': asdict(provider.descriptor), 'cases': results,
        'attempted': len(results), 'contract_valid': sum(c['contract_valid'] for c in results),
        'expected_label_matches': sum(c.get('expected_label_match', False) for c in results),
        'clinical_validation': False, 'calibration_validated': False, 'auto_enabled': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deployment', type=Path, required=True)
    parser.add_argument('--allow-real-provider', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = run_smoke(args.deployment, allow_real_provider=args.allow_real_provider)
    except BoundedProviderError as error:
        print(json.dumps({'error_code': error.code, 'provider_calls_started': False}))
        return 2
    except Exception:
        print(json.dumps({'error_code': 'service_unavailable'}))
        return 2
    # Metadata only: do not serialize source text, raw HTTP body or deployment paths.
    print(json.dumps(report, allow_nan=False))
    return 0 if report['contract_valid'] == 10 else 1


if __name__ == '__main__':
    raise SystemExit(main())
