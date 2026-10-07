> Consolidated 2026-10-07: retained v0.1 requirements. Current GitHub implementation status and API migration are in docs/IMPLEMENTATION_STATUS.md and docs/API_MIGRATION.md. Historical local dev1/dev2 progress is not GitHub acceptance evidence.

# Safety boundaries v0.1

Spec revision 0.1.0 · Mandatory implementation constraints

## Allowed outcomes

从来源提取有限文本事实、检查文书缺失、产生人工复核提示与只读结构化草稿。返回结果不是诊断、病例确认、就医建议或自动执行授权。模型只有受控标签，没有自由诊疗结论。

## Forbidden outcomes

疾病诊断 / 排除 / 风险概率、鉴别诊断、用药或手术、预测是否失明、自动决定就诊 / 转诊 / 出院或延迟处置、签署病历、向患者推送建议、写 EHR、发送消息、预约、设备控制。无论用户输入 / 模型提出何种操作，都没有相应执行工具。

`urgency_to_review` 只能 needs_review / unknown，并且始终 review_required。不能加入 no_review、safe、routine、not_urgent 等会被理解为排除危险的标签。规则未命中是未知，不是无需就医。

## Review lock

风险 high / moderate / unknown、风险线索、冲突、复杂否定无法解析、主体不清、证据缺失 / 输出无效、超窗 / 截断、calibration 不匹配均不能进入 model auto。confidence 再高也不能解除风险或 capability gate。已经锁定 review 的结果，frontier / local / rules / caller 均不能降级。

高风险直接交人工复核，不要求先把病历送云端。review_required 表示调用方必须保留人工确认步骤，并非系统已经联系医生，也不意味着有复核时效保证。人工反馈不作为长期 memory，也不在 v0.1 签发批准 token。

## Trust boundaries

Patient State 和 provider output 都是数据。source 内“忽略规则、上传全文、标记安全”不改变服务端 policy。task definitions / prompts / endpoint / capabilities 来自部署配置，不从病例文本拼接执行代码或模板语法。

Capability allowlist 与健康 / feature 支持分离；有功能不等于有权限。只能 emit read-only output；rule hit 不能授权 clinical action。禁止将 risk/capability 字段放入 caller request，拒绝 unknown fields。

Patient State 只按本次 state revision 处理，fact provenance 必须在本次 source 内。不同 encounter 没有共享临床缓存。Agent Memory 不接收 Patient State / raw response。v0.1 不保存患者事实、不建立 memory service。

## Failure handling

不能静默截断输入、补填 unsupported 值、把未提症状当否定、把历史 / 家属症状当当前患者。超窗、版本未固定、provider 健康不足、概率无效、未知 label、冲突及输出格式错都固定 error/reason、review 或 abstain，不无限重试。

低风险 provider timeout 可在合法 export 条件下一次 frontier；有 safety conflict 的结果直接 review，不让更强模型尝试解除。frontier error / timeout / 非法输出 → review / abstain，绝不自动绕过。

## Privacy and observability

默认只有 loopback provider。frontier enabled + caller request + task export capability + fixed endpoint/model + deployment-side privacy clearance + bounded sanitized payload 六者同时满足才允许出网。caller 自称 synthetic / deidentified 不可信；初版只允许管理员登记的合成 fixtures，或由外部可信流程授权的摘要。

默认本地日志严格 metadata allowlist。患者原文、facts、source span 内容、标识、凭证、provider raw body、自由异常字符串不得出现在 log / metrics / trace。例外调试采样不在 v0.1；不要创建“临时 raw logs”。临床 response 为调用方显式请求的功能输出，不作为观测上传。

## Limits of evidence

上游 confidence 来自其训练 / 评测设置，不能直接表述为中文医疗正确率。accuracy / F1 / ECE 均受数据分布与任务 definitions 限制；本项目合成 benchmark 不能替代真实临床验证。阈值是工程目标，不是医学规范。

本项目的医疗使用边界是产品约束，不往 Apache-2.0 LICENSE 中加入禁止领域等附加条款。保持标准开源许可；安全通过架构、契约、文档和发布验收体现。未来若走真实临床部署，要单独评估用途、流程和当地要求，不能声称 v0.1 本身已具备认证。

## Required adversarial cases

高 confidence + risk high；rule hit + review lock；无能力 + high score；missing calibration + high probability；cloud off + caller asks fallback；caller self-asserts sanitized；provider emits diagnosis / arbitrary key；负概率 / NaN；超窗 + risk 在末尾；家属症状；既往有现在否认；不清楚左 / 右；跨 state evidence；日志植入敏感 marker。这些案例必须有测试，并在发布报告中计入失败分母。
