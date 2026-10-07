# Offline extraction evaluation (unreleased main)

This evaluates recorded normalized facts against synthetic, task-specific gold
annotations. It adds no model runtime, clinical workflow, or clinical authority.
It uses the existing `ClinicalFact` / `ClinicalState` contract. It does not replace
Copilot's Patient State schema, State Merger, or doctor-confirmation rules.

## Run

Install the source checkout or current development wheel. From the checkout:

```bash
# Verifies the scorer by replaying gold annotations; no extraction model runs.
python benchmarks/run_extraction.py --self-test

# Scores recorded normalized predictions from a separately run provider.
python benchmarks/run_extraction.py --predictions predictions.jsonl --provider-label provider-name@version-run-id
```

Modes are mutually exclusive. Recorded predictions require an explicit label.
That label is caller-supplied provenance, not independent proof of a model run.
Self-test output is labeled `fixture_replay_self_test` and
`gold_fixture_replay_no_model`. Never report its perfect score as model accuracy.

Exit codes: `0` every case passes, `1` a factual/evidence/output failure,
`2` invalid configuration or invalid/unreadable reference/prediction files.
The runner rejects empty files, duplicate case IDs, unknown prediction IDs,
duplicate JSON fields, and non-finite JSON numbers. A missing prediction or
malformed per-case state remains a visible failed case rather than being skipped.

## Reference format

`benchmarks/extraction_ophthalmology_zh_v0.1.jsonl` has 24 newly authored synthetic
cases covering laterality, negation, duration, corrections, IOP, and decimal visual
acuity. It includes abstention cases for unasked, unknown, or unresolved facts.
No patient records, external datasets, or real clinician annotations were used.
The annotations share this repository's Apache-2.0 license.

Each row contains `schema_version: "0.1"`, unique `id`, `synthetic: true`,
`dimension`, a target `task`, source `text`, and an `expected` fact list:

```json
{"schema_version":"0.1","id":"extract-oph-001","synthetic":true,"dimension":"laterality","task":"extract_laterality","text":"左眼视物模糊。","expected":[{"name":"laterality","value":"left","evidence":"左眼"}]}
```

The fixture version describes this evaluation format, not the Copilot schema.
Score only the complete target-task output. Unrelated facts should not be exported
for that task; within-target extra facts count as false positives.

Annotation conventions:

- Laterality is `left`, `right`, or `bilateral`; unresolved laterality is absent.
- `eye_pain` and `headache` are true/false only when explicitly addressed.
  Not asking a symptom does not mean the symptom is absent.
- Duration has separate numeric `duration_value` and text `duration_unit` facts;
  units are `day`, `week`, or `month`. Do not convert months to an assumed day count.
- Corrections use the explicitly confirmed final fact. Unresolved corrections
  have no gold fact. This annotation policy is not a production correction engine.
- IOP names encode eye and units: `right_iop_mmHg`, `left_iop_mmHg`.
  Visual-acuity names encode eye and these fixtures explicitly specify decimal
  notation: `right_visual_acuity`, `left_visual_acuity`.
- Gold fact names are unique per case. Values are JSON scalars; nested clinical
  objects and repeated time-series measurements are outside this scorer's scope.
- Every gold fact requires a literal source-evidence anchor. Do not infer facts
  that the targeted source/task does not establish.

## Prediction format

Record one row per case, after normalizing the provider's output:

```json
{"id":"extract-oph-001","facts":[{"name":"laterality","value":"left","confidence":0.98,"evidence":"左眼","provenance":"your-provider"}]}
```

`facts: []` is a valid abstention. Missing evidence is represented by `null` or
an omitted `evidence`; it never earns source-supported credit. Keep provider
errors out of the facts list; an omitted case is reported as `missing_prediction`.
The evaluator does not import provider modules, load arbitrary plugins, download
models, call remote services, or require API keys.

For an injected provider, call `provider.extract(case_text)` under its documented
contract, then export each `ClinicalFact` field to the recorded format. Keep the
original case ID, provider/model version, prompt/config version, and run identifier.
Do not let a provider see gold annotations when generating predictions.

## Scoring

Matching is exact by fact name and scalar value, one-to-one. `False` is not `0`,
and `True` is not `1`. Numbers `16` and `16.0` are equivalent; string `"16"`
is a different value. There is no numeric tolerance, unit guessing, or synonym
normalization. Duplicate predictions cannot create additional true positives.

**Fact match** counts correct name/value pairs. **Supported match** additionally
requires the predicted evidence to occur in the source and contain the gold's
literal anchor. A correct left-eye value citing a right-eye span may earn factual
credit but earns no supported credit and cannot pass the full case.

Micro precision = correct / valid predicted facts; recall = correct / all gold
facts; F1 = 2 × correct / (valid predicted facts + gold facts). Supported metrics
use source-supported correct facts in the numerator. A zero denominator is
reported as `null`, not as an invented perfect rate.

Exact-case success requires all gold facts to match with support and no extra
predictions. Empty gold plus empty valid output is a correct abstention. Invalid
outputs fail the whole case: they contribute zero valid predictions and all gold
facts stay unmatched. This can leave precision high despite failures, so always
inspect `output_error_cases`, recall, and exact-case rate together.

Reports include package/fixture versions, input SHA-256 hashes, per-dimension
metrics, and per-case failure counts. They omit raw source text, fact values,
quoted evidence, provider metadata, and upstream exception messages. These hashes
identify local artifacts for reproducibility; they do not prove data provenance.

## Limits and next validation

Literal evidence matching is a reproducible annotation rule, not a proof of
clinical correctness. Longer quotations containing the anchor can pass; semantic
support and source ambiguity still require review. Public synthetic examples are
regression data, not held-out clinical validation or confidence calibration.
No independent clinician consensus or inter-rater agreement is claimed.

Before comparing real providers, choose their versions, licenses and runtime;
freeze task prompts/normalization; generate predictions without gold access; and
review failures. Do not tune on these cases then claim generalization. A later
clinical evaluation needs a separately governed dataset and clinician annotation.

The reusable API is `medsystem1.evaluation.ExtractionCase` and
`evaluate_extraction(cases, predictions, provider_label=...)`. It returns metrics;
it does not route, merge, sign, prescribe, or submit anything.
