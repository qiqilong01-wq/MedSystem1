# MedSystem1

**A local-first safety and routing layer for medical AI.**

> Know when to act. Know when to escalate. Know when to stop.

MedSystem1 is an early-stage Python library for bounded medical-AI routing. It keeps **model confidence separate from clinical authority**. Current main is review-only until the original task, evidence, deployment and calibration gates are fully integrated; native scores cannot authorize LOCAL or cloud export.

The complete original v0.1 plan, canonical schemas and M0–M6 acceptance requirements are restored. See [implementation status](docs/IMPLEMENTATION_STATUS.md), [product scope](PRODUCT_SPEC_v0.1.md), [development plan](DEVELOPMENT_SPEC_v0.1.md) and [API migration](docs/API_MIGRATION.md). Historical local progress is not GitHub acceptance evidence.

## Architecture

```text
Clinical input → ExtractionProvider → Normalized Clinical State
                                      ↓
                          Rules + DecisionProvider
                                      ↓
                    Risk × Confidence × Capability
                                      ↓
                    LOCAL | HUMAN_REVIEW | ESCALATE
```

## 60-second quick start

Python 3.10+:

```bash
pip install medsystem1
```

This command requires a completed PyPI upload. Until the first upload is
verified, install the GitHub alpha tag:

```bash
python -m pip install "medsystem1 @ git+https://github.com/qiqilong01-wq/MedSystem1.git@v0.1.0"
```

Maintainers: see [publishing and recovery](docs/PUBLISHING.md).

The example below targets unreleased main 0.1.1.dev1. The fixed v0.1.0 alpha
retains earlier routing behavior. To use the review-only behavior described here,
install a checkout of the development branch with `python -m pip install -e .`.
No new PyPI/stable release is claimed by this change.

```python
from medsystem1 import MedSystem1, RouteRequest

system = MedSystem1()
decision = system.route(RouteRequest(
    task="laterality",
    confidence=0.97,
    schema_valid=True,
    evidence_present=True,
    capability="extract_structured_fact",
))
print(decision.action.value)  # HUMAN_REVIEW: native score is not calibrated authority
```

High confidence does **not** authorize a high-risk action:

```python
decision = system.route(RouteRequest(
    task="change_glaucoma_treatment",
    confidence=0.99,
    schema_valid=True,
    evidence_present=True,
    capability="change_treatment",
))
print(decision.action.value)  # HUMAN_REVIEW
```

## v0.1 scope

Included: review-only safety router, trusted six-task catalog, canonical clinical schemas/validators, provider protocols, normalized-state primitives, synthetic examples and engineering evaluation tools. The canonical wire request/response is not yet integrated with the legacy route facade.

The six release tasks are laterality, temporal_classification, photopsia, floaters, missing_fields and urgency_to_review. The last always requires review. Existing generic extraction/IOP scorer fixtures remain optional engineering experiments; they do not expand release scope. Default model auto and cloud calls are disabled; model auto coverage is currently 0.

Not included: diagnosis, prescribing, autonomous treatment, ASR/OCR, proprietary NER, full FHIR, HIS/PACS integration, or a complete clinical agent.

## Provider model

Integrations are optional. MedSystem1 owns the safety contract, not the upstream model.

- `ExtractionProvider`: text/data → normalized clinical state.
- `DecisionProvider`: optional bounded classifier/decider → confidence + metadata.
- OpenMed and Strands Decider are intended adapters; third-party model assets are not bundled into core.

Callable adapter shapes, evidence checks, and error handling are documented in
[Provider contracts](docs/PROVIDERS.md). Tests cover injected synthetic callables;
real upstream SDK/model integrations remain unvalidated.

## Safety

MedSystem1 is research/developer infrastructure, **not a medical device and not a substitute for clinician judgment**. It does not authorize diagnosis, prescribing, treatment changes, record submission, procedures, or other high-risk clinical actions. See [SAFETY.md](SAFETY.md).

## Ophthalmology reference example

```bash
python examples/ophthalmology_zh.py
```

## Development

For a source checkout:

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
python tools/validate_package.py
python benchmarks/run_routing.py
python benchmarks/run_extraction.py --self-test
```

The extraction self-test replays synthetic gold to verify the scorer. To score
recorded provider output, see [offline extraction evaluation](docs/EXTRACTION_EVALUATION.md).

## Roadmap

Follow the retained M0–M6 plan: contracts, deterministic rules/Patient State,
real pinned Strands deployment, full routing/CLI/API, opt-in frontier gates,
evaluation/calibration, then complete release acceptance. See DEVELOPMENT_SPEC_v0.1.md.

See [bounded roadmap and handoff](docs/ROADMAP.md) for current status and the
next task. Main is an unreleased development line; the v0.1.0 tag stays fixed.

## License and third-party components

MedSystem1 is licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Third-party SDKs, models, datasets, weights, and remote services can carry separate terms. MedSystem1 core does not bundle OpenMed or Strands Decider model assets. See [THIRD_PARTY.md](THIRD_PARTY.md).

