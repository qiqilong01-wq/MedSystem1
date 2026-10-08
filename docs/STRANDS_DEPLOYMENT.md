# Strands v19 transport and deployment — 2026-10-08

Software 0.1.1.dev3; local administrator Schema local-0.1.0. This is M2 transport
infrastructure with mock acceptance. Real deployment acceptance remains open.

## Fixed upstream contract

The adapter targets code revision `890947e7ccd44c3de4115e26a7f46cc5c3147b44`:
[server](https://github.com/strands-labs/strands-decider/blob/890947e7ccd44c3de4115e26a7f46cc5c3147b44/src/strands_decider/server.py),
[wire types and confidence formula](https://github.com/strands-labs/strands-decider/blob/890947e7ccd44c3de4115e26a7f46cc5c3147b44/src/strands_decider/schema.py),
[CLI](https://github.com/strands-labs/strands-decider/blob/890947e7ccd44c3de4115e26a7f46cc5c3147b44/src/strands_decider/cli.py).
v19 model release is `bb282d786bc251fd4e3068de3ada9ddbb38127cd`. Upstream main
now advertises v21; neither moving main nor v21 is implicitly accepted here.

POST /v1/systemone receives state and a questions map. Trusted tasks.json supplies
instructions, order and labels. Each question is choice with null label descriptions,
which the pinned upstream accepts. Response must contain exactly model, answers,
usage and latency_ms. Every requested task and every label probability must be
present, with no extra answers, diagnoses, truncation claims or arbitrary fields.

For N labels, native confidence is clamp((N*p_max-1)/(N-1), 0, 1), checked within
1e-5; probability sum must be within 1e-5 of one. Native score, selected probability
and future task calibration remain separate. None expresses medical correctness.
The immutable candidate has no evidence span, risk, review override or action grant.
M3 must independently validate evidence and safety before using any candidate.

Only laterality, temporal_classification, photopsia and floaters can be deployed
through this adapter. missing_fields stays deterministic; urgency_to_review stays
review-only and is never delegated through this transport.

## Administrator manifest

Canonical contract: schemas/deployment/v0.1/local.schema.json. Default config is
configs/v0.1/local-deployment.disabled.json, packaged in the wheel. Clinical request
schemas do not accept deployment flags or caller risk/capability overrides.

Loading a deployment validates and freezes manifest/catalog, computes config SHA256
and performs no network activity. An enabled manifest needs verified=true, exact
registry code/model/base revisions, four-task subset, loopback endpoint, strict_window=true,
prefix_cache=false, max_concurrency=1 and launch/artifact/runtime attestations.
The registry's base_revision=null deliberately prevents enabling it today.

The [official release provenance](https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19/commit/bb282d786bc251fd4e3068de3ada9ddbb38127cd)
reports `b1485b2fa6dfa1287294f269f5fb618e03d52d7c` as inferred at training time,
because training hosts did not pin it. This is recorded as reported_base_revision,
separately from a verified local base_revision. Do not copy the inferred value into
verified deployment state without checking the actual local snapshot and loader.

attestation.artifact_sha256 contains code/model/base snapshot digest records;
runtime_versions records independently inspected serving packages and versions;
launch_verified asserts a checked offline launch with the declared flags. These
are **trusted administrator assertions**, not checksums computed by this loader or
cryptographic evidence about a remote process. Keep a separate verification report
listing constituent files/checksums, environment/device and exact launch command.
False assertions cannot be detected by this adapter and do not satisfy M2 acceptance.

Pinned /health does not expose code/model/base revision or strict-window. Before
each inference the adapter checks status, model name, base ID, positive max_length
and prefix_cache=false. A healthy response cannot independently prove all deployment
settings; runtime permission depends on the administrator verification boundary.

## External serving procedure

1. In a separate serving environment, obtain only the approved exact code/model/base
   snapshots; retain licenses/notices and inspect upstream MANIFEST.sha256. Record
   actual artifact digests and complete serving dependencies. MedSystem1 never
   performs this download or installs Torch/Strands as a side effect.
2. The pinned code does not pass a base revision to from_pretrained. Pin the external
   base cache to the verified snapshot, use HF_HUB_OFFLINE=1 and
   TRANSFORMERS_OFFLINE=1, and inspect the loader/cache identity. Offline alone does
   not select a correct revision. Do not invent a --revision serving flag.
3. Run the pinned CLI against a local checkpoint named strands-decider-2B-hobson-v19:

   ```text
   strands-decider serve /approved/snapshots/strands-decider-2B-hobson-v19 --device cpu --host 127.0.0.1 --port 8099 --strict-window --no-prefix-cache --model-name strands-decider-2B-hobson-v19
   ```

   cpu is an illustrative explicit device, not a measured latency recommendation.
   Keep single worker and single-process MedSystem1 client; do not expose the server
   publicly. Disable serving access/body logging and any external telemetry. This
   client only guarantees its own metadata-only outputs; it cannot configure upstream logs.
4. Verify the base snapshot/strict-window failure behavior and capture deployment
   evidence. Only then update trusted providers.json base_revision and prepare an
   enabled manifest from the Schema. Registry/model config is administrator state.
5. Execute the opt-in ten-case command below and save its metadata-only report.
   Contract failures remain in the denominator; label matches are engineering smoke
   evidence, not clinical accuracy/F1 or calibration/ECE.

   ```text
   python tools/run_strands_smoke.py --deployment /approved/local-deployment.json --allow-real-provider
   ```

The command only reads shipped original synthetic fixtures. It never starts a server,
downloads artifacts, accepts patient input or calls cloud. No opt-in means no config
read and no calls. A disabled/unresolved deployment fails before any network call.

## Transport limits and remaining work

IPv4 loopback only; no environment proxies, redirects or retries. Request limit
128 KiB; response limit 1 MiB; strict JSON rejects duplicates, nonfinite numbers,
invalid UTF-8 and malformed payloads. No silent truncation. Queue, health and
inference share one timeout budget (1–120000 ms). Results arriving after the budget
are rejected. Socket operations are bounded; this is not a hard operating-system
watchdog that can forcibly terminate an upstream inference already running.

All provider objects for the same endpoint share a serialization lock in this
process. Locks coordinate no other processes; keep the supported one-process client
deployment. No clinical source/state is cached in this client or candidate result.

Canonical MedSystem1.decide and CLI remain rules-only and cannot enable this adapter
from clinical text. Full M3 orchestration, HTTP decide API, post-validation and
calibration eligibility are separate work. M2 still requires actual artifact/base
verification, runtime lock/license inventory, and at least ten real synthetic
requests with observed results. Mock servers and runner mocks cannot close that gate.
