"""Canonical local CLI: default rules, optional administrator deployment, no cloud."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from jsonschema.exceptions import ValidationError

from .core.config import load_bundle
from .core.rules_engine import evaluate_rules, metadata_event
from .core.orchestrator import build_local_runtime, evaluate
from .contracts import parse_request_json
from .errors import DecisionRequestError
from .policy import _resource_root


def main(argv=None):
    parser=argparse.ArgumentParser(prog='medsystem1')
    parser.add_argument('--project-root',type=Path,default=_resource_root(),
                        help='administrator-owned source/config root; never a request field')
    parser.add_argument('--deployment',type=Path,
                        help='administrator opt-in local manifest; absent means no provider calls')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('demo',help='run packaged synthetic ophthalmology input with local rules')
    decide=commands.add_parser('decide',help='compute canonical JSON request with local rules')
    decide.add_argument('--input',type=Path,required=True)
    args=parser.parse_args(argv)
    path=args.project_root/'examples/ophthalmology/request.json' if args.command=='demo' else args.input
    try:
        bundle=load_bundle(args.project_root)
        runtime=build_local_runtime(args.project_root,args.deployment,bundle=bundle) if args.deployment else None
    except Exception:
        return _error('service_unavailable')
    try:
        request=parse_request_json(path.read_text(encoding='utf-8-sig'))
        response=(evaluate(request,args.project_root,bundle=bundle,runtime=runtime)
                  if runtime is not None else evaluate_rules(request,args.project_root,bundle=bundle))
    except (ValidationError,ValueError,TypeError,KeyError,RecursionError,DecisionRequestError):
        return _error('invalid_request')
    except Exception:
        return _error('service_unavailable')
    print(json.dumps(response,ensure_ascii=True,allow_nan=False))
    try:
        print(json.dumps(metadata_event(response),ensure_ascii=True,allow_nan=False),file=sys.stderr)
    except OSError:
        # No raw log fallback or remote exporter. Output is still a read-only result.
        pass
    return 0


def _error(code):
    print(json.dumps({'schema_version':'0.1.0','error':{'code':code},
                      'request_id':str(uuid4())}),file=sys.stderr)
    return 2
