"""Independent post-validation: adapter output remains untrusted candidates."""
from dataclasses import fields
from math import isfinite

from ..bounded import BoundedAnswer, BoundedDescriptor, BoundedProviderError, BoundedResult
from ..contracts import parse_request_json


def _number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        return False


def _exact(value, cls):
    return type(value) is cls and set(vars(value)) == {f.name for f in fields(cls)}


def _snapshot(value, cls):
    if not _exact(value, cls):
        raise ValueError('candidate_shape')
    return cls(**vars(value).copy())


def validate_candidates(result, expected, tasks, catalog):
    """No evidence, calibration or risk authority is accepted from a provider.

    Canonical task labels come from the Schema-checked deployment catalog. The
    bounded candidate protocol is separate from the canonical clinical response.
    """
    try:
        result = _snapshot(result, BoundedResult)
        descriptor = _snapshot(result.descriptor, BoundedDescriptor)
        if type(result.answers) is not tuple:
            raise ValueError('candidate_batch')
        result = BoundedResult(tuple(_snapshot(a, BoundedAnswer) for a in result.answers),
                               descriptor, result.latency_ms)
        if (not _exact(result, BoundedResult) or not _exact(result.descriptor, BoundedDescriptor)
                or result.descriptor != expected or type(result.answers) is not tuple
                or not _number(result.latency_ms) or result.latency_ms < 0
                or len(result.answers) != len(tasks)):
            raise ValueError('candidate_envelope')
        for answer, task in zip(result.answers, tasks):
            if (not _exact(answer, BoundedAnswer) or answer.task_id != task
                    or type(answer._probabilities_json) is not str
                    or len(answer._probabilities_json) > 4096):
                raise ValueError('candidate_answer')
            probabilities = parse_request_json(answer._probabilities_json)
            labels = catalog['tasks'][task]['labels']
            if (not isinstance(probabilities, dict) or set(probabilities) != set(labels)
                    or not isinstance(answer.label, str) or answer.label not in probabilities
                    or not all(_number(p) and 0 <= p <= 1 for p in probabilities.values())
                    or abs(sum(probabilities.values())-1) > 1e-5
                    or probabilities[answer.label] != max(probabilities.values())
                    or not _number(answer.native_score) or not 0 <= answer.native_score <= 1):
                raise ValueError('candidate_probability')
            native = max(0, min(1, (len(labels)*max(probabilities.values())-1)/(len(labels)-1)))
            if abs(native-answer.native_score) > 1e-5:
                raise ValueError('candidate_confidence')
        return result
    except Exception:
        raise BoundedProviderError('invalid_provider_output') from None
