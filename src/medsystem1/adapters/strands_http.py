"""Opt-in v19 choice-only HTTP adapter. No SDK, downloads, cloud or auto routing."""
import http.client
import json
from math import isfinite
import socket
import threading
from time import monotonic
from urllib.parse import urlsplit
import weakref

from ..bounded import BoundedAnswer, BoundedDescriptor, BoundedProviderError, BoundedResult
from ..contracts import parse_request_json
from ..core.local_deployment import LocalDeployment

_LOCKS = weakref.WeakValueDictionary()
_LOCK_GUARD = threading.Lock()
_MAX_BODY = 128*1024
_MAX_RESPONSE = 1024*1024


def _finite(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        return False


def _deadline(timeout_ms):
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1 <= timeout_ms <= 120000:
        raise BoundedProviderError('out_of_domain')
    return monotonic()+timeout_ms/1000


def _remaining(deadline):
    result = deadline-monotonic()
    if result <= 0:
        raise BoundedProviderError('provider_timeout')
    return result


class StrandsHttpProvider:
    def __init__(self, deployment: LocalDeployment):
        if not isinstance(deployment, LocalDeployment):
            raise BoundedProviderError('capability_missing')
        cfg = deployment.settings
        if not cfg['enabled']:
            raise BoundedProviderError('capability_missing')
        self._cfg = cfg
        self._catalog = deployment.catalog['tasks']
        self.descriptor = BoundedDescriptor('strands', cfg['model_id'], cfg['code_revision'],
            cfg['model_revision'], cfg['base_revision'], tuple(cfg['tasks']))
        endpoint = cfg['endpoint']
        # Schema restricts the complete endpoint, including port, to IPv4 loopback.
        uri = urlsplit(endpoint)
        self._port = uri.port
        with _LOCK_GUARD:
            self._lock = _LOCKS.setdefault(endpoint, threading.Lock())

    def _http(self, path, deadline, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', self._port, timeout=_remaining(deadline))
        try:
            conn.request('POST' if body is not None else 'GET', path, body=body,
                         headers={'Content-Type': 'application/json', 'Connection': 'close'})
            if conn.sock:
                conn.sock.settimeout(_remaining(deadline))
            response = conn.getresponse()
            _remaining(deadline)
            # Never follow redirects, echo error bodies or retry.
            if response.status != 200:
                code = 'out_of_domain' if response.status == 422 else 'provider_error'
                raise BoundedProviderError(code)
            parts, size = [], 0
            while True:
                if conn.sock:
                    conn.sock.settimeout(_remaining(deadline))
                chunk = response.read1(min(65536, _MAX_RESPONSE+1-size))
                _remaining(deadline)
                if not chunk:
                    break
                parts.append(chunk)
                size += len(chunk)
                if size > _MAX_RESPONSE:
                    raise BoundedProviderError('invalid_provider_output')
            payload = parse_request_json(b''.join(parts).decode('utf-8'))
            if not isinstance(payload, dict):
                raise BoundedProviderError('invalid_provider_output')
            return payload
        except BoundedProviderError:
            raise
        except (TimeoutError, socket.timeout):
            raise BoundedProviderError('provider_timeout') from None
        except (ValueError, UnicodeError, RecursionError):
            raise BoundedProviderError('invalid_provider_output') from None
        except (OSError, http.client.HTTPException):
            raise BoundedProviderError('provider_error') from None
        finally:
            conn.close()

    def _health(self, deadline):
        health = self._http('/health', deadline)
        if (health.get('status') != 'ok' or health.get('model') != self._cfg['expected_model_name']
                or health.get('base_model') != self._cfg['base_id']
                or health.get('prefix_cache') is not False
                or type(health.get('max_length')) is not int or health['max_length'] < 1):
            raise BoundedProviderError('capability_missing')

    def health(self, *, timeout_ms=2000):
        deadline = _deadline(timeout_ms)
        try:
            if not self._lock.acquire(timeout=_remaining(deadline)):
                return False
            try:
                self._health(deadline)
                return True
            finally:
                self._lock.release()
        except BoundedProviderError:
            return False

    def decide(self, state, task_ids, *, timeout_ms):
        started = monotonic()
        deadline = _deadline(timeout_ms)
        if (not isinstance(state, str) or not state or not isinstance(task_ids, tuple)
                or not task_ids or len(task_ids) > 4
                or any(not isinstance(t, str) for t in task_ids)
                or len(set(task_ids)) != len(task_ids)):
            raise BoundedProviderError('out_of_domain')
        if not set(task_ids) <= set(self.descriptor.supported_tasks):
            raise BoundedProviderError('capability_missing')
        questions = {}
        for task in task_ids:
            definition = self._catalog[task]
            questions[task] = {'type': 'choice', 'instructions': definition['instructions'],
                               'criteria': dict.fromkeys(definition['labels'], None)}
        try:
            body = json.dumps({'state': state, 'questions': questions},
                              ensure_ascii=False, allow_nan=False).encode('utf-8')
        except (ValueError, UnicodeError):
            raise BoundedProviderError('out_of_domain') from None
        if len(body) > _MAX_BODY:
            raise BoundedProviderError('out_of_domain')
        if not self._lock.acquire(timeout=_remaining(deadline)):
            raise BoundedProviderError('provider_timeout')
        try:
            self._health(deadline)
            payload = self._http('/v1/systemone', deadline, body)
            result = self._parse(payload, task_ids, (monotonic()-started)*1000)
            _remaining(deadline)
            return result
        finally:
            self._lock.release()

    def _parse(self, payload, tasks, latency):
        if (set(payload) != {'model', 'answers', 'usage', 'latency_ms'}
                or payload['model'] != self._cfg['expected_model_name']
                or not isinstance(payload['answers'], dict) or set(payload['answers']) != set(tasks)
                or not _finite(payload['latency_ms']) or payload['latency_ms'] < 0):
            raise BoundedProviderError('invalid_provider_output')
        usage = payload['usage']
        if (not isinstance(usage, dict) or set(usage) != {'input_tokens', 'output_tokens'}
                or any(type(v) is not int or v < 0 for v in usage.values())):
            raise BoundedProviderError('invalid_provider_output')
        answers = []
        for task in tasks:
            answer = payload['answers'][task]
            if not isinstance(answer, dict) or set(answer) != {'type', 'choice', 'probabilities', 'confidence'}:
                raise BoundedProviderError('invalid_provider_output')
            probs = answer['probabilities']
            if (answer['type'] != 'choice' or not isinstance(probs, dict)
                    or set(probs) != set(self._catalog[task]['labels'])
                    or not isinstance(answer['choice'], str) or answer['choice'] not in probs
                    or not all(_finite(p) and 0 <= p <= 1 for p in probs.values())
                    or abs(sum(probs.values())-1) > 1e-5
                    or probs[answer['choice']] != max(probs.values())
                    or not _finite(answer['confidence']) or not 0 <= answer['confidence'] <= 1):
                raise BoundedProviderError('invalid_provider_output')
            native = max(0, min(1, (len(probs)*max(probs.values())-1)/(len(probs)-1)))
            if abs(native-answer['confidence']) > 1e-5:
                raise BoundedProviderError('invalid_provider_output')
            answers.append(BoundedAnswer(task, answer['choice'], answer['confidence'],
                                         json.dumps(probs, allow_nan=False)))
        return BoundedResult(tuple(answers), self.descriptor, latency)
