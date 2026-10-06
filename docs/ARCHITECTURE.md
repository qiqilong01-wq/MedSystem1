# Architecture

MedSystem1 is a control layer, not a diagnostic model.

## Boundaries

```text
ASR / OCR / Text / FHIR
          |
          v
ExtractionProvider
(OpenMed / custom / hospital NLP)
          |
          v
Normalized Clinical State
          |
     +----+----+
     |         |
     v         v
Rules     DecisionProvider
          (e.g. Strands)
     |         |
     +----+----+
          v
Risk x Confidence x Capability Router
          |
   +------+------+ 
   |      |      |
 LOCAL  HUMAN  ESCALATE
```

Provider output never bypasses the router. ESCALATE means "seek more capable reasoning", not "grant permission".

## Why providers are injected

Medical deployments differ in privacy, language, hardware, model licensing, and regulatory requirements. Adapters therefore wrap injected callables instead of forcing heavyweight runtime dependencies into core.

## Clinical state

Clinical facts should carry evidence/provenance whenever possible. Future versions will strengthen provenance, conflict detection, calibration, and audit events without turning conversational memory into a clinical source of truth.
