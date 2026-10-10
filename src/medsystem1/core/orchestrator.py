"""Rules first; optional trusted local candidates; review locks only rise."""
from dataclasses import dataclass, field
import hashlib
import json
from time import monotonic

from ..bounded import BoundedDescriptor, BoundedProviderError, LocalDecisionProvider
from ..wire_models import RequestModel, ResponseModel
from .local_deployment import load_local_deployment
from .provider_validation import validate_candidates
from .rules_engine import evaluate_rules


@dataclass(frozen=True)
class LocalRuntime:
    # Administrator-owned only. Neither this object nor its fields are request data.
    provider: LocalDecisionProvider | None = field(default=None, repr=False)
    expected: BoundedDescriptor | None = None
    task_capabilities: frozenset[str] = frozenset()
    deployment_sha256: str | None = None


def bind_local_runtime(provider, deployment):
    """Bind an explicitly administered provider to its independent pinned identity."""
    cfg = deployment.settings
    if not cfg['enabled']:
        return LocalRuntime(deployment_sha256=deployment.config_sha256)
    expected = BoundedDescriptor('strands', cfg['model_id'], cfg['code_revision'],
        cfg['model_revision'], cfg['base_revision'], tuple(cfg['tasks']))
    return LocalRuntime(provider, expected, frozenset(cfg['tasks']), deployment.config_sha256)


def build_local_runtime(root, deployment_path, *, bundle=None):
    deployment = load_local_deployment(root, deployment_path, bundle=bundle)
    if not deployment.settings['enabled']:
        return bind_local_runtime(None, deployment)
    from ..adapters.strands_http import StrandsHttpProvider
    return bind_local_runtime(StrandsHttpProvider(deployment), deployment)


def _review(item, reason):
    item['status'], item['route'] = 'review_required', 'human_review'
    item['reason_codes'] = list(dict.fromkeys([c for c in item['reason_codes']
                                             if c != 'deterministic_match']+[reason]))


def _call(runtime, state, tasks, budget_ms, bundle):
    if budget_ms <= 0:
        raise BoundedProviderError('provider_timeout')
    try:
        if len(state.encode('utf-8')) > 128*1024:
            raise BoundedProviderError('out_of_domain')
        provider, expected = runtime.provider, runtime.expected
        if (provider is None or expected is None or expected.locality != 'local'
                or expected.provider_id != 'strands' or provider.descriptor != expected
                or not set(tasks) <= set(expected.supported_tasks)):
            raise BoundedProviderError('capability_missing')
        started = monotonic()
        result = provider.decide(state, tasks, timeout_ms=budget_ms)
        # The pinned HTTP adapter bounds I/O; no unbounded thread or retry is started.
        # A synchronous custom adapter must honor its timeout. Reject any late result.
        if (monotonic()-started)*1000 >= budget_ms:
            raise BoundedProviderError('provider_timeout')
        validated = validate_candidates(result, expected, tasks, bundle.catalog)
        if (monotonic()-started)*1000 >= budget_ms:
            raise BoundedProviderError('provider_timeout')
        return validated
    except BoundedProviderError as error:
        code = error.code if type(error.code) is str and error.code in ('provider_timeout', 'provider_error',
                    'invalid_provider_output', 'capability_missing', 'out_of_domain') else 'provider_error'
        raise BoundedProviderError(code) from None
    except Exception:
        raise BoundedProviderError('invalid_provider_output') from None


def evaluate(data, project_root, *, bundle, runtime=None):
    started = monotonic()
    runtime = runtime or LocalRuntime()
    model = RequestModel.from_dict(data, bundle.schema_dir)
    request = model.to_dict()  # private snapshot; never passed as mutable state to provider
    response = evaluate_rules(request, project_root, bundle=bundle)
    if runtime.deployment_sha256:
        response['versions']['config_sha256'] = hashlib.sha256(
            (bundle.config_sha256+'\x00'+runtime.deployment_sha256).encode()).hexdigest()
    # Whole-input/urgency locks stop inference before even a health probe.
    if response['review_required']:
        response['timing_ms']['total'] = (monotonic()-started)*1000
        return response
    items = {item['task_id']: item for item in response['results']}
    tasks = tuple(task for task in request['tasks']
        if task in ('laterality', 'temporal_classification', 'photopsia', 'floaters')
        and items[task]['value'] == 'unknown' and task in runtime.task_capabilities)
    if not tasks:
        response['timing_ms']['total'] = (monotonic()-started)*1000
        return response
    policy = bundle.policy
    remaining_ms = max(0, int(policy['total_timeout_ms']-(monotonic()-started)*1000))
    budget_ms = min(policy['local']['timeout_ms'], remaining_ms, 120000)
    # Carry the original source sequence without dropping tail text. No encounter,
    # state IDs, caller facts, memory, prompts or deployment settings are exported.
    state = json.dumps([{'kind': s['kind'], 'text': s['text']}
                       for s in request['patient_state']['sources']],
                      ensure_ascii=False, separators=(',', ':'))
    local_started = monotonic()
    failure = None
    try:
        result = _call(runtime, state, tasks, budget_ms, bundle)
    except BoundedProviderError as error:
        failure = error.code
    response['timing_ms']['local'] = (monotonic()-local_started)*1000
    if failure:
        for task in tasks:
            _review(items[task], failure)
    else:
        # Record only the pinned identity after independently validated output.
        descriptor = runtime.expected
        response['versions'].update(provider=descriptor.provider_id, model=descriptor.model_id,
            model_revision=descriptor.model_revision, base_revision=descriptor.base_revision)
        for answer in result.answers:
            item = items[answer.task_id]
            _review(item, 'uncalibrated')
            item['confidence']['native_score'] = answer.native_score
            item['confidence']['selected_probability'] = answer.selected_probability
            if answer.label != item['value']:
                # A model score cannot manufacture an attributable clinical fact.
                item['value'], item['evidence'], item['risk'] = None, [], 'unknown'
                _review(item, 'input_conflict')
            else:
                # Context provenance belongs to the existing unknown rule result;
                # it is not a source span provided/validated by the model.
                _review(item, 'missing_evidence')
    response['status'], response['route'], response['review_required'] = 'review_required', 'human_review', True
    ranks = {'low': 0, 'moderate': 1, 'high': 2, 'unknown': 3}
    response['risk'] = max((item['risk'] for item in items.values()), key=ranks.get)
    response['reason_codes'] = list(dict.fromkeys(code for item in response['results'] for code in item['reason_codes']))
    if request['cloud_fallback_requested']:
        response['reason_codes'] = list(dict.fromkeys([*response['reason_codes'], 'cloud_disabled']))
    response['timing_ms']['total'] = (monotonic()-started)*1000
    return ResponseModel.from_dict(response, model, bundle.schema_dir).to_dict()
