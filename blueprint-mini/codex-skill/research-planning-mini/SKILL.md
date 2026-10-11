---
name: research-planning-mini
description: >
  Research Planning Mini：轻量推进选题、文献证据、研究设计与实施，分批保存并接续，
  支持可恢复的研究状态与写作交接。用于选题调研、精简科研规划或低上下文研究流程。
---
# Research Planning Mini

Research Workflow Skills · 01 · Planning. See the repository README for the four-stage series and installation.

从研究问题推进到真实证据的写作交接。先完成用户当前需要的研究工作，不因模板存在就展开全部流程。

## 开始与恢复
- 确认实际研究目录；已有项目先读 `research_blueprint/state.json` 和 `research_blueprint/resume.md`（如有），再读取当前问题需要的证据。摘要是导航，不是科学证据；不重建已有项目。
- 新研究用 `scripts/researchctl.py init PROJECT --title TITLE --idea IDEA`。使用已安装仓库依赖的 Python 3.11+；脚本相对于本 Skill。
- 运行 `scripts/projectctl.py open PROJECT`。首次涉及版本、跨阶段交接或 Gate 时读[共享契约](../../../workflow-contract/README.md)，同一上下文不重复加载。
- 只加载[当前阶段规则](references/workflow.md)与实际需要的研究类型。原版与 mini 共用研究状态格式，同一项目不并发编辑。

## 尽早确定研究方向
先做足以判断方向的少量探索，不先完成全面检索或批量精读再交代选题。早期给出简短选题说明：研究对象与核心问题、论文类型与暂定题目、已有依据和拟验证的价值、范围边界，以及下一步所需数据或文献。拟议贡献是待验证假设，不是预定结论。
若用户尚未明确选择方向与范围，展示推荐方案并取得实际确认后，再扩大检索、批量下载和精读；只有存在重大不同选择时才列备选。不用 AUTO 替用户选题，也不为定题强行凑方案数量。
已有明确选题或授权时沿用并简短复述，不重复确认。将说明及实际决定记入现有 decision_log/state/resume，供恢复读取，不新增一套状态文件。A 记录早期范围，B 在核心阅读后核验方向；发现研究问题、范围或论文类型需实质变化时，解释证据与影响，确认转向后继续。细化措辞、补证据不必再问。
暂定标题可随证据调整；论文正文交给 manuscript-writing-mini（也兼容 manuscript-writing）完成。定方向不等于提前决定研究结果。

## 按需推进
- 选题与检索：先明确问题，读[检索规则](references/literature-strategy.md)。方向确定后的完整研究准备按[核心文献遴选](references/core-literature.md)筛查至少100篇相关候选，选20篇取得全文并完成科学精读，再形成内容方案；恢复复用已有工作。
- 获取与阅读：读[精读规则](references/deep-reading.md)。普通文献保存简短证据笔记，核心文献按需要展开。下载按[工具适配](references/adapters.md)，网页访问或题录成功不等于 PDF 已取得。
- 期刊与范例：目标期刊确定后按[期刊策略](references/journal-strategy.md)准备目标刊约10篇及同领域同文类、水平相近期刊合计约10篇全文对照，供写作校准体量、图表与引用；复用现有库，分批核对。
- 设计与实施：读[设计规则](references/research-design.md)及适用研究类型。高成本执行前冻结计划；实际结果、失败、偏离和主张记入原有账本。综述记录筛选与综合，不编造实验。
- 写作交接：需要交接时读[交接契约](references/handoff-contract.md)和[就绪校验](references/readiness-gates.md)，运行 check/package 后交给 `manuscript-writing-mini`（或兼容的 `manuscript-writing`）。不在这里写论文正文。

## 分批与接续
- 精读通常每批 1–3 篇，按篇幅和问题调整；这是保存粒度，不是科研覆盖上限。保存后可继续下一批，不因分批反复要求确认。
- 全文、长检索结果、完整论文卡、图像字节和长日志留在文件或工具内部；对话返回关键证据、定位、路径及简短状态。必要原文按页或章节读取。
- 每批结束更新 state 的 next_actions/unresolved_blockers，并保存 `research_blueprint/resume.md`：目标与阶段、已完成项和文件路径、未解决问题、下一步及所需文件、已有决定。通常不超过一页，不复制整份分析。
- 出现可见的上下文紧张提示、频繁压缩或将读取大量新材料时，先保存接续记录并报告如何从项目目录继续。不自行创建任务，不依赖精确 token 计数，也不承诺避免远程压缩故障。

## 证据与决定
结论不得强于证据；数字和引用保留来源定位，计划与实际结果分开。核心证据缺失就记录阻塞。
Gate 是检查点：唯一合理选择按共享契约记录 AUTO，重大不同路线或实际高成本承诺才需要用户决定。
不为轻量化跳过科学核验，也不为满足模板制造内容。不适用项说明原因。
