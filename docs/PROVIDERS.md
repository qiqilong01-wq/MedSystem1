# Provider contract (unreleased main)

These adapters wrap injected synchronous callables. They do not install or
validate an OpenMed SDK, Strands SDK, model, remote service, or clinical workflow.
Canonical clinical validation uses jsonschema 4.23.0; core installs no model/SDK.
Deployment owns permission and clinical state. Provider confidence is advisory;
the review-only facade does not use it to grant LOCAL or export authority.

## Normalized extraction state

`validate_clinical_state(state, source_text=...)` checks:

- A `ClinicalState` containing a tuple of `ClinicalFact` objects.
- Each fact has a non-empty text name and a non-null value. `False` and `0`
  are valid values; unknown facts should be absent rather than fabricated.
- Confidence is `None` or a finite actual number in [0, 1].
- Evidence/provenance is `None` or non-empty text.
- If source text is supplied, every supplied evidence string occurs literally
  in that source. The error message does not echo the source or fact value.

Missing confidence and evidence remain `None`. An empty state is structurally
valid but provides no evidence. `all(...)` over an empty collection is true;
do not use it alone to assert `evidence_present`.

This checks data shape and literal attribution only. It does not prove that
evidence supports the normalized value, resolve laterality/negation/corrections,
or validate the application's authoritative Patient State schema. That schema,
State Merger, conflict checks, and doctor-confirmation rules remain with Copilot.

## OpenMed callable adapter

The callable receives text and returns an iterable of mappings (a list, tuple,
or synchronous generator). A bare mapping, string, `None`, or non-mapping item
is a contract error. Mixed valid/invalid items reject the whole result.

| Normalized field | Upstream mapping |
| --- | --- |
| name | `label`, otherwise `type`, otherwise `entity` |
| value | Explicit `value`, otherwise `text` |
| confidence | `score`, otherwise `confidence`; absent/`None` stays unknown |
| evidence | `text`, when present; it must occur in the input |
| provenance | `openmed` (adapter identifier, not independent evidence) |

Numeric confidence strings are converted then validated. A present but malformed
field is an error; no silent fallback repairs it. If `text` is absent but a
normalized `value` exists, the fact has no evidence. Setting `value` allows an
English normalized code to retain its Chinese literal evidence separately.

```python
from medsystem1.adapters import OpenMedExtractionProvider

# A synthetic fixture-backed callable, not an extraction model.
provider = OpenMedExtractionProvider(lambda _: [{
    "label": "laterality", "value": "left", "text": "左眼", "score": "0.98",
}])
state = provider.extract("合成示例：左眼视物模糊")
assert state.facts[0].value == "left"
assert state.facts[0].evidence == "左眼"
```

## Strands callable adapter

The callable receives keyword arguments `task` (non-empty text) and `state`
(validated normalized state). Supported results:

| Result | Confidence | Metadata |
| --- | --- | --- |
| Mapping | `confidence` entry | Shallow copy of the mapping |
| Two-element tuple | First element | Second element, a mapping |
| Object | `confidence` attribute | `metadata` mapping attribute, or `{}` if absent |

Confidence must exist and be finite in [0, 1]. Numeric strings are supported;
booleans are rejected. Metadata must have text keys. Arbitrary lists and opaque
raw result objects are not preserved as metadata. Copies are shallow; callers
must not assume nested objects are immutable or appropriate to log.

Provider metadata is advisory. `action`, `capability`, or `risk` suggestions
cannot override the caller's RouteRequest or the router's authority boundary.
Confidence never authorizes prescribing, treatment changes, or record submission.

## Failures and caller behavior

- `ProviderContractError` (a `ValueError`) rejects malformed provider data.
- `ProviderExecutionError` (a `RuntimeError`) reports an upstream execution or
  generator failure. No partial state or RouteDecision is returned.
- Non-callable configuration and non-text extraction input raise `TypeError`.

On any failure, stop the current operation and request repair/review under the
application's policy. Do not catch an exception and continue with a LOCAL action.
Exception messages are bounded, but chained upstream exceptions can contain
clinical text or secrets. Do not automatically log tracebacks, raw input, or
arbitrary metadata. The core does not write logs or send telemetry.

## Conformance verification

Run `pytest -q tests/test_provider_contracts.py`. It exercises supported output
shapes, missing evidence, normalized values, source attribution, generator
failures, malformed state, and provider suggestions at the router boundary.
Passing fixture-backed tests establishes adapter behavior only; validate a real
provider separately with versioned synthetic inputs before using it in a clinic.

