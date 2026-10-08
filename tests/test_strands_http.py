"""Loopback fake-server conformance. No weights, SDK or external network."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from medsystem1 import MedSystem1  # noqa: E402
from medsystem1.adapters.strands_http import StrandsHttpProvider  # noqa: E402
from medsystem1.bounded import BoundedProviderError  # noqa: E402
from medsystem1.core.local_deployment import load_local_deployment  # noqa: E402

MARKER = 'PRIVATE_FIXTURE_MARKER'


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.calls.append(('GET', self.path))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(self.server.health_payload).encode())

    def do_POST(self):
        self.server.calls.append(('POST', self.path))
        self.server.request_payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.server.delay:
            time.sleep(self.server.delay)
        try:
            self.send_response(self.server.status)
            if self.server.status == 302:
                self.send_header('Location', 'https://example.invalid/'+MARKER)
            self.end_headers()
            raw = self.server.raw
            self.wfile.write(raw if raw is not None else json.dumps(self.server.payload).encode())
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def enabled_config(port):
    cfg = json.loads((ROOT/'configs/v0.1/local-deployment.disabled.json').read_text())
    cfg.update(enabled=True, verified=True, endpoint=f'http://127.0.0.1:{port}',
               code_revision='a'*40, model_revision='b'*40, base_revision='c'*40,
               tasks=['laterality', 'temporal_classification', 'photopsia', 'floaters'],
               attestation={'artifact_sha256': {'code': '1'*64, 'model': '2'*64, 'base': '3'*64},
                            'runtime_versions': {'synthetic-fake-server': '1'}, 'launch_verified': True})
    return cfg


class StrandsHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'configs', self.root/'configs')
        shutil.copytree(ROOT/'schemas', self.root/'schemas')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.calls = []
        self.server.status = 200
        self.server.delay = 0
        self.server.raw = None
        self.server.health_payload = {'status': 'ok', 'model': 'strands-decider-2B-hobson-v19',
            'base_model': 'Qwen/Qwen3.5-2B-Base', 'prefix_cache': False, 'max_length': 4096}
        self.server.payload = {'model': 'strands-decider-2B-hobson-v19', 'answers': {
            'laterality': {'type': 'choice', 'choice': 'right',
                'probabilities': {'left': .05, 'right': .83, 'bilateral': .04, 'unknown': .04, 'conflicting': .04},
                'confidence': .7875}}, 'usage': {'input_tokens': 0, 'output_tokens': 0}, 'latency_ms': 0}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cfg = enabled_config(self.server.server_port)
        registry_path = self.root/'configs/v0.1/providers.json'
        registry = json.loads(registry_path.read_text())
        registry['strands'].update(code_revision='a'*40, verified_model_release_revision='b'*40,
                                   base_revision='c'*40)
        registry_path.write_text(json.dumps(registry))
        self.path = self.root/'deployment.json'
        self.write_config()
        self.provider = StrandsHttpProvider(load_local_deployment(self.root, self.path))

    def write_config(self):
        self.path.write_text(json.dumps(self.cfg))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def call(self, **kwargs):
        return self.provider.decide(MARKER, ('laterality',), timeout_ms=kwargs.get('timeout_ms', 2000))

    def assert_rejected(self, code, action=None):
        with self.assertRaises(BoundedProviderError) as caught:
            (action or self.call)()
        self.assertEqual(caught.exception.code, code)
        self.assertNotIn(MARKER, str(caught.exception))

    def test_native_score_probability_and_candidate_authority(self):
        result = self.call()
        answer = result.answers[0]
        self.assertEqual(answer.native_score, .7875)
        self.assertEqual(answer.selected_probability, .83)
        self.assertEqual(answer.label, 'right')
        probabilities = answer.probabilities
        probabilities['right'] = 0
        self.assertEqual(answer.selected_probability, .83)
        self.assertFalse(hasattr(result, 'route'))
        self.assertFalse(hasattr(result, 'evidence'))
        self.assertFalse(hasattr(result, 'calibrated_probability'))
        self.assertNotIn(MARKER, repr(result))
        wire = self.server.request_payload
        self.assertEqual(set(wire), {'state', 'questions'})
        self.assertEqual(wire['state'], MARKER)
        self.assertNotIn(MARKER, wire['questions']['laterality']['instructions'])
        self.assertEqual(list(wire['questions']['laterality']['criteria']),
                         ['left', 'right', 'bilateral', 'unknown', 'conflicting'])
        self.assertTrue(all(v is None for v in wire['questions']['laterality']['criteria'].values()))

    def test_multiple_tasks_exact_coverage_and_catalog_labels(self):
        self.server.payload['answers']['photopsia'] = {'type': 'choice', 'choice': 'unknown',
            'probabilities': {'present': .05, 'absent': .05, 'unknown': .85, 'conflicting': .05},
            'confidence': .8}
        result = self.provider.decide(MARKER, ('photopsia', 'laterality'), timeout_ms=2000)
        self.assertEqual([a.task_id for a in result.answers], ['photopsia', 'laterality'])

    def test_loader_disabled_and_frozen_without_network(self):
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            disabled = load_local_deployment(ROOT)
            self.assert_rejected('capability_missing', lambda: StrandsHttpProvider(disabled))
            deployment = load_local_deployment(self.root, self.path)
            cfg = deployment.settings
            cfg['tasks'].append('diagnosis')
            self.assertNotIn('diagnosis', deployment.settings['tasks'])
            catalog = deployment.catalog
            catalog['tasks']['laterality']['labels'].append('diagnosis')
            self.assertNotIn('diagnosis', deployment.catalog['tasks']['laterality']['labels'])

    def test_deployment_revisions_settings_and_task_scope(self):
        original = copy.deepcopy(self.cfg)
        changes = [('code_revision', 'd'*40), ('model_revision', 'd'*40), ('base_revision', 'd'*40),
            ('code_revision', 'main'), ('strict_window', False), ('prefix_cache', True),
            ('verified', False), ('tasks', ['missing_fields']), ('tasks', ['urgency_to_review']),
            ('tasks', ['laterality', 'laterality']), ('attestation', None),
            ('endpoint', 'http://127.0.0.1:0'), ('endpoint', 'http://127.0.0.1:65536'),
            ('endpoint', 'http://localhost:8099'), ('endpoint', 'https://example.com'),
            ('endpoint', 'http://127.0.0.1:8099/path'), ('endpoint', 'http://user@127.0.0.1:8099')]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                self.cfg = copy.deepcopy(original)
                self.cfg[key] = value
                self.write_config()
                self.assert_rejected('capability_missing', lambda: load_local_deployment(self.root, self.path))
        self.assertEqual(self.server.calls, [])

    def test_unresolved_base_cannot_enable_by_claiming_verified(self):
        registry_path = self.root/'configs/v0.1/providers.json'
        registry = json.loads(registry_path.read_text())
        registry['strands']['base_revision'] = None
        registry_path.write_text(json.dumps(registry))
        self.assert_rejected('capability_missing', lambda: load_local_deployment(self.root, self.path))
        self.assertEqual(self.server.calls, [])

    def test_duplicate_keys_and_unknown_manifest_fields(self):
        for raw in ('{"enabled":false,"enabled":true}', json.dumps({**self.cfg, 'diagnosis': MARKER})):
            self.path.write_text(raw)
            self.assert_rejected('capability_missing', lambda: load_local_deployment(self.root, self.path))

    def test_invalid_input_or_unsupported_task_never_calls_health(self):
        cases = [('', ('laterality',), 100), (MARKER, ('diagnosis',), 100),
            (MARKER, ('urgency_to_review',), 100), (MARKER, ('missing_fields',), 100),
            (MARKER, ('laterality', 'laterality'), 100), (MARKER, ['laterality'], 100),
            (MARKER, ([1],), 100), (MARKER, (), 100), (MARKER, ('laterality',), True),
            (MARKER, ('laterality',), float('nan')), (MARKER, ('laterality',), 0),
            (MARKER, ('laterality',), 120001), ('x'*131073, ('laterality',), 100),
            ('\ud800', ('laterality',), 100)]
        for state, tasks, timeout in cases:
            with self.subTest(tasks=tasks, timeout=timeout):
                with self.assertRaises(BoundedProviderError):
                    self.provider.decide(state, tasks, timeout_ms=timeout)
        self.assertEqual(self.server.calls, [])

    def test_wrong_health_or_cache_enabled_stops_before_post(self):
        original = copy.deepcopy(self.server.health_payload)
        for key, value in [('model', MARKER), ('base_model', MARKER), ('prefix_cache', True),
                           ('status', 'bad'), ('max_length', True), ('max_length', 0)]:
            self.server.health_payload = {**original, key: value}
            self.assert_rejected('capability_missing')
        self.assertTrue(all(method == 'GET' for method, _ in self.server.calls))

    def test_invalid_envelope_and_incomplete_answers(self):
        original = copy.deepcopy(self.server.payload)
        for key, value in [('model', MARKER), ('answers', {}), ('answers', []),
                           ('usage', {'input_tokens': True, 'output_tokens': 0}),
                           ('usage', {'input_tokens': 1}), ('latency_ms', -1), ('latency_ms', float('nan')),
                           ('latency_ms', 10**400),
                           ('diagnosis', MARKER), ('truncated', True)]:
            self.server.payload = {**copy.deepcopy(original), key: value}
            self.assert_rejected('invalid_provider_output')

    def test_invalid_probabilities_choice_and_confidence(self):
        original = copy.deepcopy(self.server.payload)
        changes = [('confidence', .99), ('confidence', True), ('confidence', float('inf')),
                   ('choice', 'left'), ('choice', MARKER), ('choice', []), ('type', 'score'),
                   ('probabilities', {}), ('diagnosis', MARKER)]
        for key, value in changes:
            self.server.payload = copy.deepcopy(original)
            self.server.payload['answers']['laterality'][key] = value
            self.assert_rejected('invalid_provider_output')
        for value in [float('nan'), -.1, True, .2]:
            self.server.payload = copy.deepcopy(original)
            self.server.payload['answers']['laterality']['probabilities']['right'] = value
            self.assert_rejected('invalid_provider_output')

    def test_duplicate_malformed_large_and_non_utf8_wire(self):
        for raw in [b'{"model":"a","model":"b"}', b'NaN', b'{broken', b'\xff', b'x'*1048577]:
            self.server.raw = raw
            self.assert_rejected('invalid_provider_output')

    def test_redirect_422_and_failure_bodies_are_redacted_no_retry(self):
        self.server.raw = MARKER.encode()
        for status, code in [(302, 'provider_error'), (422, 'out_of_domain'), (500, 'provider_error')]:
            self.server.status = status
            count = len(self.server.calls)
            self.assert_rejected(code)
            self.assertEqual(len(self.server.calls)-count, 2)

    def test_timeout_and_lock_budget_no_retry(self):
        self.provider._lock.acquire()
        try:
            self.assert_rejected('provider_timeout', lambda: self.call(timeout_ms=10))
            self.assertEqual(self.server.calls, [])
        finally:
            self.provider._lock.release()
        self.server.delay = .1
        self.assert_rejected('provider_timeout', lambda: self.call(timeout_ms=30))
        self.assertEqual(len(self.server.calls), 2)

    def test_clients_share_endpoint_lock_and_failed_health_releases_it(self):
        other = StrandsHttpProvider(load_local_deployment(self.root, self.path))
        self.assertIs(other._lock, self.provider._lock)
        self.server.health_payload['model'] = MARKER
        self.assertFalse(self.provider.health())
        self.server.health_payload['model'] = 'strands-decider-2B-hobson-v19'
        self.assertTrue(other.health())

    def test_environment_proxy_cannot_redirect_loopback_request(self):
        with patch.dict('os.environ', {'HTTP_PROXY': 'http://example.invalid:8000',
                                      'http_proxy': 'http://example.invalid:8000', 'NO_PROXY': ''}):
            result = self.call()
        self.assertEqual(result.answers[0].label, 'right')
        self.assertEqual(self.server.calls, [('GET', '/health'), ('POST', '/v1/systemone')])

    def test_connection_error_is_redacted_and_health_false(self):
        with patch('medsystem1.adapters.strands_http.http.client.HTTPConnection') as connection:
            connection.return_value.request.side_effect = OSError(MARKER)
            self.assert_rejected('provider_error')
            self.assertFalse(self.provider.health())
        self.assertEqual(self.server.calls, [])

    def test_canonical_decide_still_has_no_provider_side_effect(self):
        request = json.loads((ROOT/'examples/ophthalmology/request.json').read_text(encoding='utf-8'))
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            result = MedSystem1().decide(request)
        self.assertTrue(result['review_required'])
        self.assertEqual(self.server.calls, [])


if __name__ == '__main__':
    unittest.main()
