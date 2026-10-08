> Consolidated 2026-10-07: retained v0.1 requirements. Current GitHub implementation status and API migration are in docs/IMPLEMENTATION_STATUS.md and docs/API_MIGRATION.md. Historical local dev1/dev2 progress is not GitHub acceptance evidence.

# API schema v0.1

Schema version 0.1.0 · Spec revision 0.1.4

Current GitHub 0.1.1.dev3 implements MedSystem1.decide(request_dict) and local
CLI demo/decide using this wire contract. Immutable wire models and whole-source
rules/review checks are ported. The HTTP endpoints below remain planned on GitHub;
historical local dev1 HTTP status is not this branch's acceptance evidence.
Legacy RouteRequest is a separate advisory API. No model/cloud providers are called.

## Canonical artifacts

`schemas/v0.1/*.schema.json` 是公共 JSON 契约；`src/medsystem1/contracts.py` 补充跨字段语义。不是 Markdown 中的示例作为真源。使用 Draft 2020-12，顶层及业务对象 `additionalProperties=false`。暂不生成 OpenAPI；M3 从 canonical Schema 与 models 生成并 CI 核对，禁止维护第二份手写 OpenAPI。

| File | Root role |
|---|---|
| patient-state.schema.json | 请求范围事实与源文本 |
| request.schema.json | DecideRequest |
| decision.schema.json | 六类 task 的逐项结果 |
| response.schema.json | 聚合状态与审计版本 |
| policy.schema.json | 固定部署路由策略 |
| benchmark-case.schema.json | 合成 gold case |
| error.schema.json | 固定错误 envelope，无原文回显 |

## Development endpoints

`POST /v1/decide`：只读，无持久写入；每次 response 包含 request_id。`GET /health`：status 与公开版本信息，不暴露凭证、缓存位置或患者信息。0.1.0.dev1 已提供 rules-only stdlib HTTP API，固定 loopback、单请求、不出网。Strands adapter 单独实现，尚未接进该 API；frontier 路径未实现。服务不是远程多租户或临床生产入口。

## Request

必填 `schema_version="0.1.0"`、`patient_state`、`tasks`（唯一 task IDs，最多六项）、`cloud_fallback_requested`。没有任意 instructions、provider endpoint、caller confidence / risk / capability、Agent Memory、诊疗 action 或配置路径。

Patient State 有 state_id / revision / encounter_id（opaque references）、language、sources、facts。sources: source_id、kind、text；text 长度限制只是请求资源上限，token 截断由 provider strict-window 防止。facts: field（六类受支持事实字段）、value（非空来源值）、assertion（affirmed / negated / uncertain）、temporality（current / historical / unknown）、subject（patient / other / unknown）、evidence。输入 fact 是有来源的候选，不因为结构化就视作医生确认。

空 facts 合法；unknown 是信息不明确，不是用空字符串编码。sources 至少一条；source_id 唯一，fact evidence 必须有至少一条本次 source span。代码校验 source reference / offset，不允许跨 state evidence。真实标识不能代替 opaque encounter_id；服务不声称能从字符串格式检测 PHI。

完整例子：`examples/ophthalmology/request.json`。

## Per-task Decision

`task_id` + discriminator 决定 `value` 类型。status 为 completed / review_required / abstained / blocked；value 可为 null（没有可用草稿）。每项带 risk、route、reason_codes、confidence、evidence。reason_codes 是固定受控 code，不能塞入 provider 自由回复。

confidence 字段：`native_score`（上游原始分数或 null）、`selected_probability`（当前 label 概率或 null）、`calibrated_probability`（域内标签正确率估计或 null）、`calibration_status`（not_available / validated / mismatch）、`artifact_id`。生成模型自述数字不会填 calibrated_probability。rules confidence 三个值均 null，calibration_status=not_available。

calibrated_probability 仅是本任务在被验证分布的统计估计，不是疾病概率，也不能独立决定是否可自动操作。status=validated 必须 artifact 非空且 probability 非空；其他 status 两者均 null。数值必须有限且 0–1。

任何非空 value 需要 source evidence；missing_fields 的证据是 documentation profile 与输入结构比对，因此可无文本 span，但需 reason rule_missing_fields。null 结果不得伪造 evidence。症状 present / absent 分别对应明确陈述 / 否定，不提及必须 unknown；规则不知道时不能填 absent。

## Response and route meanings

必填 `schema_version`、`request_id`、`status`、`risk`、`route`、`review_required`、`results`、`reason_codes`、`versions`、`timing_ms`。versions 包含 software、policy、rules、prompt、provider、model、model_revision、base_revision、calibration artifact IDs 和 config_sha256。无模型参与可用 `none`，示例合成输出必须标注 synthetic，不能伪装真实 model revision。

| route | Meaning | Permitted aggregate status |
|---|---|---|
| rules | 受信任规则完成纯结构化 | completed |
| local_auto | 校准和所有 guard 合格的本地结构化 | completed |
| frontier_fallback | 进行了唯一一次允许的 frontier call，仍需复核 | review_required |
| human_review | 需要人工确认；不等于已通知或已复核 | review_required |
| abstain | 无合法结果 / task 不可计算 | abstained |
| blocked | 动作 / 权限 / 范围被阻止 | blocked |

请求所有 tasks 精确各一项；输出顺序和 request.tasks 相同。总体优先级 blocked > review_required > abstained > completed；risk 用最严格值；route blocked / human_review / abstain 优先，若实际用了 frontier 则 review outcome route=frontier_fallback。review lock 即使所有 value 都有也必须 review_required。部分值未知是 completed 的语义输出，计算失败 / 无输出是 abstained，两者不混淆。

跨字段代码验证：completed 只允许 low risk，review_required=false、没有较严 task status；高 / moderate / unknown risk 必须 review_required=true，且不能 completed。urgency_to_review 不能 completed。rules 不能带模型 confidence；local_auto 必须 validated artifact 且不低于对应配置阈值（orchestrator 的语义检查），本包契约 validator 只检查 validated 形状，不能独自证明 threshold / capability 已满足。

## HTTP errors / operational outcomes

- 400：非法 JSON。422：Schema / task / input semantic 不合法；固定 code `invalid_request`，不回显原文。
- 200：合法请求的结构化结果，包括 review / abstained / blocked；provider timeout 通过 reason `provider_timeout` 与复核 envelope 表达。
- 503：服务无法加载 policy 或核心不可用；固定 code `service_unavailable`，不给猜测结果。
- 413：请求 body 大于部署上限（建议 128 KiB）；具体字符 / source / fact 个数上限由 Schema 定义。
- 415：非 application/json 或 unsupported Transfer-Encoding；固定 invalid_request。404：非公开路径，同样不回显 URI。

Error envelope 为 `{ "schema_version":"0.1.0", "error":{"code":"invalid_request"}, "request_id":"opaque" }`，真源为 error.schema.json；M3 测试 HTTP 状态码与该 envelope 的对应。不接收 arbitrary upstream error message，不从错误 fallback 到更大权限。

## Compatibility

旧 schema 目录 immutable 发布；新增 enum label 属于 breaking change。所有配置 / calibration artifact 明确绑定 schema + task labels + prompt / model / language。Schema 无法表达事实证据真实支持程度，必须由 validators / guard / benchmark 共同实现，不把 JSON validity 当医学正确性。

## Strands transport slice — 0.1.1.dev3

The separate `StrandsHttpProvider` implements the pinned v19 choice wire contract
behind a trusted local deployment manifest. See [deployment procedure](docs/STRANDS_DEPLOYMENT.md)
for exact configuration, source links, opt-in synthetic smoke and remaining gates.

Clinical schemas/v0.1 remain 0.1.0. The new independent administrator contract
`schemas/deployment/v0.1/local.schema.json` (local-0.1.0) grants no caller fields.
Canonical decide remains rules-only; no transport/public API truth is duplicated.
