# Chinese ophthalmology benchmark scaffold

This v0.1 file is intentionally tiny and synthetic. Its purpose is to define evaluation shape before collecting or curating larger datasets.

Initial target dimensions: laterality, negation, symptom, duration, medication, procedure, visual acuity, IOP, anatomy, examination/imaging, missing-field detection, urgency-to-review, and routing.

Do not add identifiable patient information. Future benchmark releases should document provenance, annotation policy, licensing, inter-rater agreement where applicable, and train/test contamination controls.

## Runnable routing-policy regression (fixture schema v0.2)

Install the checkout or wheel, then run from the source checkout:

```bash
python benchmarks/run_routing.py
python benchmarks/run_routing.py --cases benchmarks/routing_ophthalmology_zh_v0.2.jsonl
```

The 30 cases cover laterality, negation, duration, corrections, numeric values,
confidence thresholds, missing evidence, task risk, and clinical authority.
Each case supplies a synthetic scenario, an explicit `RouteRequest`, and the
expected action. Signals such as `schema_valid` are **fixture annotations**;
this runner does not extract facts or detect conflicts from the Chinese text.

JSON output includes package/schema versions, per-dimension coverage, and each
case's expected/actual action or error class. It excludes raw scenario text,
request data, and provider metadata. Exit codes: `0` all pass, `1` a regression
or request-validation failure, `2` invalid/unreadable/empty fixture data.
Duplicate case IDs and non-finite JSON numbers are rejected.

### Provenance and annotation policy

- All cases are newly authored synthetic policy regressions under this
  repository's Apache-2.0 license. No patient cases or downloaded datasets were used.
- `schema_version: "0.2"` describes this fixture format, not the Copilot Patient State schema.
- Each row includes a unique ID, `synthetic: true`, a dimension, source scenario,
  routing inputs, and one exact expected action.
- Use LOCAL only for a permitted low-risk task with validated structure,
  supplied evidence, and confidence at/above the default local threshold.
- High-risk/unknown capabilities and high/unknown task risk require human
  review. Missing evidence/invalid structure on otherwise bounded tasks must
  escalate. Medium confidence/risk requires review.
- Expected actions come from the checked-in policy, not model output. Review
  safety invariants before changing expectations to make a failed run pass.
- Cases are public regression fixtures, not a held-out evaluation set. Do not
  train on these examples and report the resulting score as generalization.
- No clinician consensus annotation, inter-rater agreement, clinical validation,
  extraction accuracy, or confidence calibration is claimed.

The original `ophthalmology_zh_v0.1.jsonl` remains an extraction annotation
scaffold. The routing runner does not score that file or claim model performance.

## Offline extraction evaluator

The separate 24-case `extraction_ophthalmology_zh_v0.1.jsonl` defines task-specific
scalar facts and source-evidence anchors. Use:

```bash
python benchmarks/run_extraction.py --self-test
python benchmarks/run_extraction.py --predictions predictions.jsonl --provider-label provider@version-run-id
```

Self-test replays gold and verifies the scorer; it is not a model result.
Recorded predictions are scored with one-to-one fact matching, source-supported
metrics, output-error counts, exact-case rates, and per-dimension coverage.
See [extraction evaluation](../docs/EXTRACTION_EVALUATION.md) for schemas,
annotation conventions, failure behavior, and metric limitations.

# Policy consolidation — fixture v0.3

The default routing runner now uses routing_ophthalmology_zh_v0.3.jsonl with
review-only model policy expectations. The 0.2 fixture is preserved for the old
alpha behavior. A passing regression reports policy conformance; model auto
coverage is 0 and no confidence calibration/model accuracy is claimed.

