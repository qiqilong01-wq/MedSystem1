# Third-party software and assets

## Canonical validation dependency (0.1.1.dev1)

The restored clinical contracts use jsonschema 4.23.0 (MIT). The observed Windows
Python 3.12 dependency lock is requirements-core-py312.txt; other platforms require
their own installation/CI evidence. Installed artifact license metadata, including
dev/build tools, is recorded in docs/verification/dependencies-dev1.json.
Dependencies are installed separately and are not vendored into MedSystem1.
pathspec's MPL-2.0 applies to that build tool's files; it does not relicense the
original MedSystem1 library. Redistributed environments/containers require their
own complete license/notice inventory. Original code remains Apache-2.0.

MedSystem1 core is distributed under Apache-2.0 and intentionally keeps third-party model/runtime dependencies out of the core package.

## OpenMed

MedSystem1 contains an independently written optional adapter interface intended to interoperate with OpenMed-compatible analyzers. As of the v0.1.0 release audit, the OpenMed SDK source is published under Apache-2.0.

**Important:** OpenMed-supported models, datasets, downloaded artifacts, remote providers, and other assets may have their own terms. MedSystem1 does not grant rights to those assets. Deployment owners must review the exact license, privacy behavior, and clinical fitness of each selected asset.

Project: https://github.com/maziyarpanahi/openmed

## Strands Decider

MedSystem1 contains an independently written optional adapter interface intended to interoperate with a Strands-Decider-compatible callable. As of the v0.1.0 release audit, the Strands Decider repository is published under Apache-2.0.

MedSystem1 v0.1.0 does not bundle Strands Decider source code or model assets.

Project: https://github.com/strands-labs/strands-decider

## Policy for future integrations

Before bundling any third-party code, model, dataset, weights, tokenizer, binary, or generated asset:

1. identify the exact artifact and version;
2. record its license and required notices;
3. verify redistribution and commercial-use terms;
4. check model/data-specific restrictions separately from SDK code;
5. preserve required attribution and NOTICE material;
6. document privacy/security/network behavior;
7. do not merge the asset into a release until its licensing is understood.

A permissive license on an SDK does not imply the same license for models or datasets used through that SDK.

