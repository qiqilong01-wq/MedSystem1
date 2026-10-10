# Local candidate orchestration — 2026-10-09

Software 0.1.1.dev4; spec consolidation 0.1.5; clinical wire Schema stays 0.1.0.
This implements the conservative M3 library/CLI slice. It does not close M2 real
deployment acceptance or the complete M3/M0–M6 Definition of Done.

## Administrator entry

Default MedSystem1() and medsystem1 decide/demo make zero provider calls.
To opt in, an administrator supplies project_root and deployment_path to the
library constructor, or --project-root and --deployment before the CLI subcommand:

```python
from pathlib import Path
from medsystem1 import MedSystem1

system = MedSystem1(
    project_root=Path('/approved/medsystem1'),
    deployment_path=Path('/approved/local-deployment.json'),
)
result = system.decide(request_dict)
```

```text
medsystem1 --project-root /approved/medsystem1 --deployment /approved/local-deployment.json decide --input /approved/synthetic-request.json
```

These paths are trusted application configuration, not new clinical request fields.
The existing local-0.1.0 administrator Schema/registry/attestation gates apply; the
default verified base_revision remains null and cannot enable an actual deployment.
Initialization validates/freezes configuration without contacting health or inference.
Bundle policy/catalog and provider questions share the same frozen snapshot.

Original synthetic example: examples/ophthalmology/local-candidate.request.synthetic.json.
Without deployment its laterality is right and symptom labels are unknown via rules.
With an approved local deployment, unknown authorized tasks may receive candidates.
No real-model prediction or score is pre-recorded as the expected provider outcome.

## Routing order

1. Validate an immutable request snapshot and execute rules/preflight on all sources
   and request-scoped facts, including text unrelated to the requested subset.
2. Any risk/unknown-grammar/conflict or urgency review lock stops every local call,
   including a health probe. Known deterministic facts also skip the model.
3. Only an authorized, low-risk unknown label in laterality, temporal_classification,
   photopsia or floaters is eligible for one local call. missing_fields stays rules;
   urgency_to_review always stays review. An ungranted task never infers permission
   from a provider feature list. A missing/mismatched authorized provider yields review.
4. Serialize every source kind/text in original order, without state/encounter/source
   identifiers, caller facts, memory, caller instructions or configuration. Clinical
   text remains untrusted input; prompts/criteria come from the trusted catalog.
   No source tail is dropped. UTF-8 provider state is bounded at 128 KiB; the adapter
   independently caps its full wire request and returns failure rather than truncating.
5. Core independently snapshots and validates candidates: exact dataclass shape,
   pinned descriptor, requested order/coverage, Schema-derived labels, finite normalized
   probabilities, argmax and native-confidence formula. No arbitrary metadata,
   diagnosis, risk, evidence or calibration fields are accepted. All failures remain
   fixed codes; no exception text or raw provider body enters response/log metadata.
6. Every valid model candidate stays human_review. For matching unknown, the response
   retains the existing rule context provenance and reports missing_evidence and
   uncalibrated. It does not claim a model-supplied evidence span. Disagreement with
   the unknown rule result clears value/evidence, raises risk to unknown and reports
   input_conflict. No model facts are merged into Patient State.

Native score and selected probability are separate. Calibrated probability/artifact
remain null and status not_available. Even a policy auto_enabled flag or score=1
cannot enable local_auto in this slice. Calibration eligibility needs later M5
artifacts and evidence validation; native confidence is never medical correctness.

contracts.py rejects aggregate route downgrades using the priority
blocked > human_review > frontier_fallback > abstain > local_auto > rules.
This tightens unreleased cross-field validation without changing caller Schema fields.
Known rules results can coexist with reviewed candidates, but the aggregate stays review.

## Timing, provenance and privacy

The core bounds the local call with the smaller remaining total/local policy budget;
rule work consumes total budget. The pinned HTTP provider includes lock wait, health
and inference in its budget. Core rejects a late result, measures local elapsed time
itself and records only independently validated pinned model identity. Invalid/timeout
results cannot claim validated model identity. Configuration SHA includes the deployment
digest when explicitly configured, so rules-only and deployed runs are distinguishable.

The provider protocol is synchronous. Custom trusted adapters must honor timeout_ms;
the core does not forcibly kill an arbitrary stuck Python function. No cancellation
thread/queue/runtime is introduced. Supported transport remains bounded, serialized
loopback HTTP. Do not claim an operating-system hard deadline or concurrent deployment.

Patient State is scoped to the call. Clinical sources are neither cached nor retained
in runtime fields. CLI stdout is the explicit clinical response; stderr is the existing
metadata allowlist, with no source/facts/evidence/state IDs/raw exceptions. Initialization
and ordinary tests never download models, start a server or export clinical text.

## Remaining gates

Cloud fallback is unimplemented in this slice, even if a request asks for it or an
administrator edits frontier policy. The response reports cloud_disabled and performs
no cloud call. Availability failures lead directly to review, without retries.

HTTP decide service, optional frontier/export clearance, calibrated auto eligibility,
formal split/annotation benchmarks and actual real-provider acceptance remain open.
Mock native-score tests and fake-server end-to-end checks are engineering conformance,
not model accuracy/F1/ECE, latency promises or clinical validation.
