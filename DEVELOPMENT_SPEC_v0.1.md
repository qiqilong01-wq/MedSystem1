> Consolidated 2026-10-07: retained v0.1 requirements. Current GitHub implementation status and API migration are in docs/IMPLEMENTATION_STATUS.md and docs/API_MIGRATION.md. Historical local dev1/dev2 progress is not GitHub acceptance evidence.

# Development specification v0.1

Spec revision 0.1.4 · Coding Agent execution contract · 2026-10-07

GitHub development update: the original M0–M6 scope remains. 0.1.1.dev3 ports
immutable wire models and finite M1 rules/Patient State, adds canonical decide/CLI,
and preserves review-only legacy model routing. Next implement real Strands and
full provider/HTTP orchestration under the same boundaries. Current acceptance
and remaining gates are in docs/IMPLEMENTATION_STATUS.md; historical local dev1
completion below does not imply GitHub provider or clinical acceptance.

## Current inventory

当前 0.1.0.dev1：M0 的 Schema-backed immutable models、catalog / adapter label 一致性、core/build lock 与安装验收已完成；M1 的有限句式规则与请求隔离已完成。M2 的 Strands adapter / 本机 fake server 测试、M3 的 rules-only CLI / API 已完成部分切片。真实 Strands 推理、统一 provider 编排、frontier、校准及正式 benchmark 未完成。详细状态见 docs/IMPLEMENTATION_STATUS.md。

M0 的 models 使用 canonical Schema 直接验证，并保存不可变 JSON 快照，避免生成第二套手写字段定义；往返 / 非法字段 / Schema labels 一致性由测试锁定。这个实现选择替代“生成重复 models”，不改变 wire contract。依赖 lock 目前只覆盖 core/build，不包含未来模型与云端 runtime。

任务按依赖顺序执行，每个阶段用可审查的小提交。不要因当前只交付规格就勾选软件 DoD。没有指定组织 / GitHub 账号，因此当前为本地独立仓库；上传开源时由维护者选择目标组织。

## Milestones

| ID / dependency | Scope and files | Acceptance / deliverable |
|---|---|---|
| M0 / none | 契约与开发基线；schemas、Schema-backed models、contracts、pyproject、tests | 本包检查全过；models 与 schema 一致；保存 core/build lock；0 个下载模型 / 云调用（已通过） |
| M1 / M0 | core/normalize.py、rules/preflight.py、rules/extract.py、task registry loader | 六任务明确规则 / unknown / conflict；原文不改、来源可追；所有任务均运行安全扫描；单请求 memory 隔离 |
| M2 / M1 | providers/strands.py、本地 deployment manifest、wire fixtures | 精确匹配已核实 /v1/systemone contract；fake server 错误 / 缺项 / 超限 / timeout 测试；固定真实 v19 冒烟至少 10 case，保存环境与输出摘要 |
| M3 / M2 | core/orchestrator.py、routing 与 post-validation、CLI / api | server-side risk/capability；完整路由优先级；跨字段 validator；请求聚合采用最严格 route；端到端低风险 / review / 故障示例 |
| M4 / M3 | providers/frontier.py + privacy/export guard | 单一 bounded HTTP adapter；固定 endpoint；默认零出网；启用条件覆盖，invalid / timeout → review；mock 验收可在无凭证下完成，不能宣称真实云端已测试 |
| M5 / M2,M3 | evaluation/runner.py、calibration/、benchmarks/releases/ | 正式数据分割与评估报告；校准 artifacts；门槛不过则 review-only；记录所有 provider / config / 数据 hash |
| M6 / M4,M5 | README 安装 / 离线 / demo、依赖 lock、license record、CHANGELOG、CI | 全部 Product DoD 通过；源码包不带 PHI / weights；版本发布说明准确；发布前检查新依赖许可 |

M0–M3 为本地贯通主线。M4 是可关闭 fallback，不能阻塞默认本地运行；M5 数据建设可在 M2 后开始，但质量报告等待 M3。单机单进程，不给日历工期承诺。

## Implementation decisions

- library core 用 dataclass / Enum / Protocol，I/O 放 adapter；当前 HTTP layer 使用 stdlib 单请求 server，Schema-backed models 不复制字段契约。后续仅在实际需要时换薄 FastAPI wrapper。
- deterministic guard 与抽取规则分开；复核 lock 单向提升，不写出“no urgent risk”。规则要小、明确、可版本化；复杂语言不尝试巨大正则规则库。
- Strands 用独立本地 server、受信任部署 manifest；不用隐式 `latest`。服务器 / checkpoint 下载不作为安装库的副作用。
- providers 只返回候选；risk、capability、export、auto decisions 在 core；frontier 只完成同样 bounded task。
- 不添加任务队列、数据库、专用 memory engine、agent supervisor、Web UI、向量检索或云监控。

## Test strategy

| Layer | Required cases | Pass rule |
|---|---|---|
| Contract | 所有 shipped fixtures、额外 diagnosis / memory 字段、未知 task、无来源 fact、非法 evidence、output shape | invalid 必须拒绝；all schemas 自身合法；requested task 精确覆盖 |
| Deterministic | 左右 / 双眼、否定 / 不确定、既往 / 家属、时间单位 / 改变、缺失 / 未知 / 冲突 | provenance 可验证；模糊输入不猜；risk guard 不漏掉固定 adversarial cases |
| Router | risk × capability × calibration × threshold × privacy 的组合；0.9499 / 0.95 / 0.9501 | 高风险无 auto；没权限不绕过；unknown calibration 不自动；threshold boundary 一致 |
| Provider | 固定 wire request/response、缺项 / 多项、invalid label、NaN、概率和、HTTP error、timeout、模型版本错配 | 确定性 error code；不能静默补值、截断、无界 retry |
| Safety | prompt injection、请求内 risk / prompt override、未知主体、旧 state revision、跨患者事实 | model / text 不授予 capability；锁定 review；不写 patient state / memory |
| Privacy | default no cloud、请求说 synthetic 但未获 privacy clearance、日志植入 PHI marker | mock network count=0；日志 / 异常无敏感 marker |
| End-to-end | 本地规则、真实 Strands、云关闭、云 mock failure、partial tasks | status / route / reason / versions 一致；不执行任何 clinical action |

单元和 mock contract 为普通 CI；真实 Strands 测试 opt-in，不能在 CI 自动下载几个 GB 权重。cloud mock 不需要密钥；真实云 smoke 仅发送已登记合成样例。benchmark 单独 job，不把大量推理当每次 PR 测试。

## Agent handoff prompt

```text
在此独立 MedSystem1 仓库开发。先读 AGENTS.md、SAFETY_BOUNDARIES.md、
DEVELOPMENT_SPEC_v0.1.md 和 schemas/v0.1。执行下一个未完成 milestone；
当前 M0/M1 已有验收；从 M2 的真实部署固定与 M3 的 provider 编排继续。
保持 default cloud disabled 和 default model auto disabled。
不要添加诊断、训练、EHR 写入、长期 memory 或其他科室。
每次只实现一个可验证切片，更新契约、样例、测试与 CHANGELOG。
报告完成内容、运行过的测试、剩余项；不得把 mock 通过说成真实模型通过。
```

## Collaboration and change governance

Codex / Claude Code 共用 AGENTS.md，CLAUDE.md 仅指向它。每个 agent 当前修改一个切片，先检查其他未提交文件，禁止覆盖他人修改；有多人协作时用独立 branch / worktree，不预设必须多 agent。小提交附测试证据，不要求创建 PR 才能推进本地开发。

新增诊疗目标、真实患者数据、出网目标、执行权限、改动兄弟仓库均超出本 scope，先提出具体需求变更；日常 fixes、mock tests、同一契约内实现自主推进。不要做无关重构。

## Release checklist

Product DoD 逐条有证据链接。记录精确依赖版本、adapter / model / base SHA、strict-window 设置、hardware、language、所有失败数。未验证的能力默认 false；未过自动门槛的 task 继续 review-only。发布软件 tag 前重复核实变更过的依赖 / 模型许可，维护 LICENSE_REVIEW 与 NOTICE。

## Strands transport slice — 0.1.1.dev3

The separate `StrandsHttpProvider` implements the pinned v19 choice wire contract
behind a trusted local deployment manifest. See [deployment procedure](docs/STRANDS_DEPLOYMENT.md)
for exact configuration, source links, opt-in synthetic smoke and remaining gates.
