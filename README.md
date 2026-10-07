# MedSystem1

**A local-first safety and routing layer for medical AI.**

> Know when to act. Know when to escalate. Know when to stop.

MedSystem1 is an early-stage Python library for bounded medical-AI routing. It keeps **model confidence separate from clinical authority** and combines deterministic safety rules, task risk, evidence/schema signals, and capability boundaries to choose `LOCAL`, `HUMAN_REVIEW`, or `ESCALATE`.

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

```python
from medsystem1 import MedSystem1, RouteRequest

system = MedSystem1()
decision = system.route(RouteRequest(
    task="extract_iop",
    confidence=0.97,
    schema_valid=True,
    evidence_present=True,
    capability="extract_structured_fact",
))
print(decision.action.value)  # LOCAL
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

Included: deterministic safety router, provider protocols, normalized clinical-state primitives, synthetic ophthalmology examples, tests, and a tiny Chinese ophthalmology benchmark scaffold.

Not included: diagnosis, prescribing, autonomous treatment, ASR/OCR, proprietary NER, full FHIR, HIS/PACS integration, or a complete clinical agent.

## Provider model

Integrations are optional. MedSystem1 owns the safety contract, not the upstream model.

- `ExtractionProvider`: text/data → normalized clinical state.
- `DecisionProvider`: optional bounded classifier/decider → confidence + metadata.
- OpenMed and Strands Decider are intended adapters; third-party model assets are not bundled into core.

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
```

## Roadmap

1. Harden routing contracts and calibration hooks.
2. Add optional OpenMed and Strands adapters without coupling core safety logic to either.
3. Expand the synthetic/de-identified ophthalmology benchmark.
4. Add audit events and provider conformance tests.
5. Validate integrations before broader clinical workflows.

See [bounded roadmap and handoff](docs/ROADMAP.md) for current status and the
next task. Main is an unreleased development line; the v0.1.0 tag stays fixed.

## License and third-party components

MedSystem1 is licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Third-party SDKs, models, datasets, weights, and remote services can carry separate terms. MedSystem1 core does not bundle OpenMed or Strands Decider model assets. See [THIRD_PARTY.md](THIRD_PARTY.md).
