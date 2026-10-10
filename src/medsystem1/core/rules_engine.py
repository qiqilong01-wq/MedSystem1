"""Runnable local-only vertical slice. Never invokes a network or model provider."""
from pathlib import Path
from time import monotonic
from uuid import uuid4

from .. import __version__
from ..wire_models import RequestModel, ResponseModel
from ..routing import Risk, Route, RouteContext, decide_route
from ..rules.extract import extract
from ..rules.preflight import preflight
from .config import load_bundle
from .normalize import normalize


def evaluate_rules(data: dict, project_root: Path, *, bundle=None) -> dict:
    started=monotonic()
    bundle=bundle or load_bundle(project_root)
    model=RequestModel.from_dict(data,bundle.schema_dir)
    request=normalize(model)
    catalog=bundle.catalog
    extracted=extract(request.state,tuple(catalog['documentation_profile']['required_fields']))
    guard=preflight(extracted)
    results=[]
    context_evidence=[{'source_id':s.source_id,'start':0,'end':len(s.text)} for s in request.state.sources]
    for task in request.tasks:
        risk=guard.risk
        reasons=list(guard.reasons)
        if task=='urgency_to_review':
            if risk==Risk.LOW:
                risk=Risk.MODERATE
            reasons.append('urgency_review_only')
            # Unknown grammar/data needs workflow review but supplies no clinical cue.
            value='needs_review' if guard.risk==Risk.HIGH or 'input_conflict' in guard.reasons else 'unknown'
        else:
            value=extracted.value(task)
        route=decide_route(RouteContext(risk=risk,review_lock=guard.review_lock,
                          output_valid=True,evidence_valid=True,task_capability=True,
                          deterministic_result=True))
        if task=='missing_fields':
            evidence=[]
            reasons.append('rule_missing_fields')
        else:
            field='symptom_duration' if task=='temporal_classification' else task
            evidence=[o.evidence.to_dict() for o in extracted.observations
                      if o.field==field and o.subject=='patient' and o.temporality=='current']
            # Unknown / workflow labels cite the context checked, not nonexistent words.
            evidence=evidence or context_evidence
            evidence=list({(e['source_id'],e['start'],e['end']):e for e in evidence}.values())[:20]
        if route==Route.RULES:
            reasons.append('deterministic_match')
        results.append({'task_id':task,'value':value,'status':'completed' if route==Route.RULES else 'review_required',
                        'risk':risk.value,'route':route.value,'reason_codes':list(dict.fromkeys(reasons)),
                        'confidence':{'native_score':None,'selected_probability':None,
                                      'calibrated_probability':None,'calibration_status':'not_available','artifact_id':None},
                        'evidence':evidence})
    risk_rank={'low':0,'moderate':1,'high':2,'unknown':3}
    aggregate_risk=max((r['risk'] for r in results),key=risk_rank.get)
    review=any(r['status']=='review_required' for r in results)
    reasons=list(dict.fromkeys(code for r in results for code in r['reason_codes']))
    if request.cloud_fallback_requested:
        # Even a deployment enabling frontier cannot change this local-only runtime.
        reasons.append('cloud_disabled')
    response={'schema_version':'0.1.0','request_id':str(uuid4()),
              'status':'review_required' if review else 'completed','risk':aggregate_risk,
              'route':'human_review' if review else 'rules','review_required':review,
              'results':results,'reason_codes':reasons,
              'versions':{'software':__version__,'policy':bundle.policy['policy_version'],
                          'rules':bundle.policy['rules_version'],'prompt':bundle.policy['prompt_version'],
                          'provider':'rules','model':'none','model_revision':'none','base_revision':'none',
                          'calibration_artifacts':[],'config_sha256':bundle.config_sha256},
              'timing_ms':{'total':(monotonic()-started)*1000,'local':None,'frontier':None}}
    return ResponseModel.from_dict(response,model,bundle.schema_dir).to_dict()


def metadata_event(response: dict) -> dict:
    """Explicit allowlist; never includes source, facts, evidence or state IDs."""
    return {'request_id':response['request_id'],'tasks':[r['task_id'] for r in response['results']],
            'status':response['status'],'risk':response['risk'],'route':response['route'],
            'review_required':response['review_required'],'reason_codes':response['reason_codes'],
            'versions':response['versions'],'timing_ms':response['timing_ms']}
