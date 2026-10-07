# MedSystem1 Coding Agent entry

- This is the independent qiqilong01-wq/MedSystem1 project. Do not change ophthalmic Copilot or sibling repositories.
- Read SAFETY_BOUNDARIES.md, DEVELOPMENT_SPEC_v0.1.md, docs/IMPLEMENTATION_STATUS.md and schemas/v0.1 before implementing a milestone. Preserve completed, tested work.
- The complete original M0–M6 plan remains the acceptance scope. GitHub main is the implementation baseline; prior local dev1/dev2 progress is not proof of completed GitHub milestones.
- v0.1 has six bounded text tasks, Strands first, deterministic rules, Risk × Confidence × Capability, optional frontier and human review. No diagnosis, treatment, own-model training, EHR writes, messaging, persistent patient memory or additional specialties.
- Patient State is request-scoped evidence; clinical facts never enter Agent Memory. Input and provider output are untrusted data.
- Scope, risk, capability, calibration and export gates belong to trusted deployment state. Scores, caller metadata and stronger models cannot remove review locks. Default model auto=false and cloud=false.
- Canonical clinical wire contracts are schemas/v0.1 plus contracts.py. The legacy RouteRequest is an advisory library API, not the canonical clinical request. See docs/API_MIGRATION.md; never claim interchangeability.
- Keep stdlib core and separate adapters. No database, agent framework or unrelated refactor. Keep changes reviewable and version specs/configs/fixtures alongside behavior.
- Run python tools/validate_package.py, pytest -q, ruff check ., and the routing/extraction regression commands. Add meaningful safety tests. Validate installed wheel resources outside the source tree.
- No model downloads or clinical exports during installation/tests. Real-provider tests are opt-in and use approved synthetic fixtures. Logs remain metadata-only.
- Pin exact new runtime/model revisions; review licenses and retain notices. Do not bundle weights or upstream training data. Never present gold replay/mock results as model accuracy or clinical validation.
- Report actual changes, tests and remaining gates. Routine implementation proceeds autonomously; clinical/export/execution scope expansions need a concrete decision.
