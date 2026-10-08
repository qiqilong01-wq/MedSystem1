# API migration — 0.1.1.dev3

The published v0.1.0 alpha API is preserved at its tag. Main intentionally tightens
safety behavior; applications must not interpret this as a compatible automation
release. No released tag is moved and no stable/PyPI release is created here.

## Legacy advisory interface

RouteRequest(task, confidence, schema_valid, evidence_present, capability, risk,
metadata) retains its Python shape. Its confidence is a native advisory score;
schema/evidence flags are caller assertions, not independently checked evidence.
Task is now checked against the trusted six-task catalog. Requested capability
must match the task-owned definition; caller risk can raise, never lower, risk.
Default model routing is review-only: all valid requests return HUMAN_REVIEW.
Malformed numerical/boolean/task inputs still raise ValueError and must stop work.
Thresholds remain accepted for source compatibility but cannot enable automation.
Caller metadata cannot claim calibration, privacy clearance or export capability.
LOCAL and ESCALATE enum members remain for compatibility/future validated paths;
this slice issues neither. No actual network/provider orchestration occurs here.

## Canonical clinical wire interface

schemas/v0.1 and contracts.py define the planned six-task clinical request/response:
request-scoped Patient State, source-span provenance, no caller risk/capability,
separate native/selected/calibrated confidence, fixed reason codes and version hashes.
MedSystem1.decide(request_dict) now validates these contracts and computes local
rules results. It returns the canonical response envelope with evidence, risk,
review status and versions. RequestModel/ResponseModel snapshot serialized JSON;
later mutation of caller dictionaries cannot alter an accepted snapshot. Invalid
facade input raises DecisionRequestError('invalid_request') without clinical text.
The CLI uses strict JSON decoding: duplicate keys and non-finite numbers fail closed.
Patient State is scoped to a call; configuration is frozen per system instance.
There is no HTTP decide endpoint or conversion between these two APIs yet.
Do not serialize legacy RouteDecision as a canonical clinical response.
Model auto remains disabled, while supported low-risk deterministic computations
may return rules/completed. This is structural output, not clinical approval.

## Regression versioning

The old routing_ophthalmology_zh_v0.2.jsonl and extraction reference files remain
unchanged. Routing fixture v0.3 records new review-only policy expectations;
it is a policy regression, not clinical accuracy or model performance.
Six bounded tasks: laterality, temporal_classification, photopsia, floaters,
missing_fields, urgency_to_review. Legacy extract_iop and clinical-action task
names remain outside that release allowlist and produce review, never authorization.

## Canonical bounded local provider

See [STRANDS_DEPLOYMENT.md](STRANDS_DEPLOYMENT.md) for the separate pinned HTTP
adapter and deployment manifest. Legacy callables retain their legacy contract.
