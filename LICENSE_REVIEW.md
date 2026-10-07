> Consolidated 2026-10-07: retained v0.1 requirements. Current GitHub implementation status and API migration are in docs/IMPLEMENTATION_STATUS.md and docs/API_MIGRATION.md. Historical local dev1/dev2 progress is not GitHub acceptance evidence.

# License and upstream review

Checked: **2026-10-03 (Asia/Shanghai)**. Decision: Apache-2.0 for original MedSystem1 code, schemas, specifications and original synthetic fixtures. External models are optional runtime dependencies; no weights / upstream datasets are distributed with this kit.

## Verified official sources

| Component | Checked revision / source | Finding |
|---|---|---|
| Strands Labs code | `890947e7ccd44c3de4115e26a7f46cc5c3147b44`; [LICENSE](https://github.com/strands-labs/strands-decider/blob/890947e7ccd44c3de4115e26a7f46cc5c3147b44/LICENSE) | Apache-2.0; complete license text retrieved via GitHub public contents API |
| Official reference checkpoint | `StrandsAgents/strands-decider-2B-hobson-v19`; [model card](https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19), [LICENSE.md release commit](https://huggingface.co/StrandsAgents/strands-decider-2B-hobson-v19/commit/bb282d786bc251fd4e3068de3ada9ddbb38127cd) | Release LICENSE.md states Apache-2.0; LoRA adapter + head, base separate |
| Qwen base | [Qwen/Qwen3.5-2B-Base LICENSE](https://huggingface.co/Qwen/Qwen3.5-2B-Base/blob/main/LICENSE) | Apache-2.0; current page checked, exact deployment revision still to resolve |
| Upstream adaptations | [THIRD_PARTY_NOTICES.md](https://github.com/strands-labs/strands-decider/blob/890947e7ccd44c3de4115e26a7f46cc5c3147b44/THIRD_PARTY_NOTICES.md) | Contains adapted Transformers/Qwen code notice; preserve it if redistributing applicable code |
| License obligations | [Apache official text](https://www.apache.org/licenses/LICENSE-2.0.txt) | Preserve license / applicable attribution; mark modified third-party files, carry applicable notices |

模型许可通过官方 release commit 中 LICENSE.md 的完整新增记录核实；直接 raw model 文件在本次网络中不可用，未保存本地 model LICENSE.md / 权重 hash，也没有假定推理环境已固定。`bb282d786bc251fd4e3068de3ada9ddbb38127cd` 是已核实发布 revision，开发须按该 SHA 解析，不能假定它永远是 latest。基座 deployment revision 尚未从模型 provenance / 权重实际核对，因此配置写 null、不能通过 reproducibility gate。

以上是开源工程依赖选择依据，不是商标排他性或真实医疗使用批准。采用同一标准许可，可保持原作兼容；没有新增医疗领域限制条款。不要借依赖名暗示 AWS / Strands / Qwen 为本项目背书。

## Distribution plan

MedSystem1 仓库只包含原创 adapter / contracts / rules / documentation / synthetic fixtures；上游独立本地 HTTP server，不复制上游推理源码。LICENSE 使用检索到的标准 Apache 文本；NOTICE 只说明项目与外部组件关系，不能误称已分发模型。

如将来 bundle / fork 上游 code、container 或 weights：重新审查该版本许可、携带 LICENSE 和 applicable THIRD_PARTY_NOTICES / NOTICE，保留版权、标明改动。上游 training / evaluation sources 的不同数据许可不自动变成 Apache-2.0，本项目不搬运其数据；任何新数据逐来源记录 terms / attribution / 权限。

## Development release gate

M2 必须记录 code SHA、model SHA、base SHA、downloaded artifacts checksum、上游 license files、runtime versions、strict-window。上游文档提示 loader 对 base 未固定 revision，因此需在外部部署锁定本地 base snapshot 并核验健康 manifest；不得编造已存在的 CLI revision 参数。M6 在固定制品上重核实并建立完整 dependency lock / license inventory。

## Name review

已通过 GitHub public repository search 发现 [15071162750/medsystem1](https://github.com/15071162750/medsystem1)。这是明显同名仓库，不表示项目内容相同或命名法律结论。工作名保留；建议 slug `medsystem1-routing`；备选 `MedRoute1`、`ClinicalRouteKit` 未查可用性，不注册、不发布，命名不阻塞开发。

## dev1 core/build dependency inventory

本次安装制品 metadata：setuptools 75.8.0、wheel 0.45.1、jsonschema 4.23.0、attrs 26.1.0、referencing 0.37.0、jsonschema-specifications 2025.9.1、rpds-py 2026.6.3 标示 MIT；typing_extensions 4.16.0 标示 PSF-2.0。setuptools / wheel 的顶层 LICENSE 已读取，记录见 docs/verification/dependency-license-inventory.json。依赖按 package installer 单独安装，源码 ZIP 不 bundle 它们。

这些是固定制品的工程许可记录，不是所有 vendored 子组件的完整分发审计。setuptools 的 vendored build 子组件存在其他许可；若未来分发整个 Python 环境或 container，M6 要携带各组件原有 notices / licenses，不得将整个环境误标为 Apache-2.0。库原创内容的 Apache-2.0 许可不变。
