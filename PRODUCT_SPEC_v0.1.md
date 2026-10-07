> Consolidated 2026-10-07: retained v0.1 requirements. Current GitHub implementation status and API migration are in docs/IMPLEMENTATION_STATUS.md and docs/API_MIGRATION.md. Historical local dev1/dev2 progress is not GitHub acceptance evidence.

# Product specification v0.1

Spec revision: 0.1.0 · Date: 2026-10-03 · Status: approved project scope, implementation pending

## 1. Charter

建立独立、可替换 provider、可测试的医疗 AI 结构化与路由基础设施。首个使用者是开发医疗 AI 工作流的工程师及复核输出的专业人员；v0.1 面向本地研究与开发，不是患者自助诊疗产品。可在未来被眼科 Copilot 通过依赖接入，当前不访问、不修改其主仓库。

交付形态：小型 Python library + CLI demo + 薄 HTTP API；一个本地 Strands adapter、一个可关闭的 frontier adapter、一组可审查的规则与眼科合成 benchmark。先单进程、顺序请求，避免服务编排、数据库和 agent 框架。

## 2. User stories and bounded tasks

开发者可提交一个 Patient State 与固定 task IDs，得到结构化草稿、证据引用、路由原因和复核状态；更换 provider 不改变公共请求 / 响应契约。医生可看见原文与冲突，不会被“高置信度”隐藏复核要求。维护者可重现某一 policy / prompt / model 组合的指标。

| Task ID | Output labels | Meaning and boundary |
|---|---|---|
| `laterality` | left / right / bilateral / unknown / conflicting | 文本明确描述的当前主诉侧别；不同症状不同眼且不能归一时 conflicting |
| `temporal_classification` | recent / longstanding / longstanding_with_recent_change / unknown / conflicting | 文本时间关系，不能输出临床严重度；演示 recent 为 ≤7 天，属于工程标签 |
| `photopsia` | present / absent / unknown / conflicting | 当前患者闪光感的明确陈述，区分否定、既往、家属描述与不确定 |
| `floaters` | present / absent / unknown / conflicting | 同上，针对飞蚊 / 黑影飘动的文本表述 |
| `missing_fields` | list of laterality / symptom_duration / visual_acuity / examination | 当前输入相对指定 documentation profile 的缺失字段，不等于建议进行某项检查 |
| `urgency_to_review` | needs_review / unknown | 工作流复核提示，始终需人确认；不输出“无需复核”、诊断、处置或就医时间建议 |

字段 definitions 在 `configs/v0.1/tasks.json`，类型在 `schemas/v0.1/decision.schema.json`。标签 `unknown` 是有效语义，区别于 provider 没有能力或网络错误。

## 3. Example

合成输入：“患者右眼看东西模糊三个月，昨天开始明显加重，还有闪光感和黑影飘动。”

预期事实草稿：right、longstanding_with_recent_change、photopsia present、floaters present；文书缺失 visual_acuity / examination。`urgency_to_review=needs_review`。请求 overall route 为 human_review；即使本地或 frontier 每项分数很高也不能自动放行。没有输出疾病名、治疗建议或排除危险的结论。

## 4. Invariants

- Risk 由服务端固定任务注册表与守门规则计算；调用者 / provider 不得降低。
- Capability 来自受信任部署注册表与健康检查；模型说“我能做”不算授权。
- Confidence 分别保留原始分数、选中项概率、域内校准概率及 artifact ID；未知校准默认不自动完成。
- Patient State 是输入事实快照；Agent Memory 是开发 / 工作流偏好，两者使用不同模型、存储和生命周期。v0.1 没有长期记忆存储或检索。
- 每次结果绑定 schema、policy、rules、prompt、provider、model、calibration 版本；没有诊疗执行工具。
- local-first：出网关闭，Strands endpoint 为固定 loopback；默认观测但不记录临床文本。

## 5. Non-goals

疾病诊断、鉴别诊断、疾病概率、处方 / 剂量 / 手术建议、自动分诊或自行决定转诊 / 出院 / 延迟就医；EHR 写入、发消息、预约、设备控制；自有模型训练、LoRA、训练语料搬运；图像 / OCT、ASR、RAG、长期 Patient State 数据库；真实患者运行、认证医疗器械主张；实现 Laya、多个云厂商 SDK、插件生态、多 agent runtime、Kubernetes、向量数据库、dashboard。

“医疗”表示围绕医疗工作流设计边界，不表示模型已获临床验证。规则例子是合成工程策略，不是医学指南。

## 6. v0.1 Definition of Done

以下全部通过才可发布软件 `0.1.0`，不能用规格完成替代实现验收：

1. 公共 Schema、Python models 和 HTTP contract 一致；六项任务与 unknown / conflicting 语义有测试。
2. 规则、Strands HTTP adapter、风险 / 能力 / 置信路由、post-validation、human review envelope 贯通；有固定版本真实本地 Strands 冒烟证据。
3. Frontier adapter 在显式启用、固定 endpoint、允许 export 能力与受信任隐私审查均满足时可调用一次；默认关闭测试证明零请求；故障返回 human_review，不循环。
4. 所有决策可追溯；日志不泄露原文、facts、患者标识或鉴权信息；不保存 Agent Memory / Patient State。
5. 固定合成 benchmark 达到 BENCHMARK_SPEC 的数据 / 安全硬门槛；accuracy、macro-F1、ECE、Brier、延迟、escalation、unsafe auto-action 均有真实报告和分母。
6. 对未达质量门槛的 task/provider 保持 auto disabled；可发布 review-only v0.1，必须标明未完成 calibration，不能宣称自动可靠。
7. routing / provider 故障、注入、截断、跨患者混用、云关闭、权限缺失测试全过；没有诊疗工具或执行能力。
8. 许可记录、依赖锁定、安装步骤、离线步骤、已知限制、changelog 与复现命令齐备；外部 weights / datasets 不打包。

## 7. Acceptance vs autonomy

`completed` 只表示本次结构化计算完成并可返回读数据，不表示病历已验证或已写入。`review_required` 不得在 UI 中显示为绿色通过。实际人工复核与下游写入由调用方负责，MedSystem1 v0.1 不签发可执行审批 token。

## 8. Roadmap

v0.1：六项 bounded task、单本地 provider、可选 frontier、可复现 benchmark。v0.2 候选：扩展语言 / 外部域验证、Laya adapter、校准覆盖改进；训练自有模型、其他科室、EHR 集成均需重新立项，不属于自动后续任务。
