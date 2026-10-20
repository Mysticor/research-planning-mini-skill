# 分页、摘要与缺口

缺摘要时执行[摘要补查](abstract-recovery.md)。Google Scholar 单独遵守下文的 Description-only 规则，不沿外链补摘要。

`search_sources.py --query '领域检索式' --sources crossref openalex semantic_scholar arxiv --output <project>/literature/search_runs --limit 300 --page-size 50 --max-pages 10`

以上是每来源、每检索式的批次上限，不是相关文献目标。根据题目选择来源并翻译各库语法。可用 `--sources` 只执行一库；查看 `stop_reason`、`next_cursor` 和已存页，未穷尽时用单库 `--start-cursor` 接续，保持查询不变。达到上限、重复页或中途失败均不等于检索穷尽；中途失败保留已获取结果。先查看结果是否有效，再决定扩展查询或接续。原始页与汇总分开落盘，不把整批摘要注入上下文。

Crossref、OpenAlex、Semantic Scholar、arXiv 使用本 Skill 的分页适配器，保存上游实际返回的完整摘要，不做字符截断。Scopus/ScienceDirect 在已有 pybliometrics 配置与有效权限时按 offset 翻页；未配置明确记录不可用，不能因图书馆有订阅就推断 API 已授权。IEEE、PubMed 已接入同一分页入口；WoS 用已授权 Chrome 会话批量导出后导入；Google Scholar 为可选补充来源，限定 Scholar 自身 Description。具体操作见下文。Ei、ACM 没有已验证的直接适配器，不虚构成功状态。OpenAlex 可用 `OPENALEX_API_KEY`，Semantic Scholar 可用 `SEMANTIC_SCHOLAR_API_KEY`；错误/限流记录实际状态，不自动申请或购买。


## 新接入来源

在 Skill 根目录运行上述脚本，Python 环境需有 requests、beautifulsoup4。来源按研究主题选择，不必每次全部执行。IEEE/PubMed 与其他来源使用相同的保存、分页、失败接续和 corpus 合并入口：

`search_sources.py --query 'federated learning' --sources ieee pubmed --output <project>/literature/search_runs --limit 100 --page-size 50 --max-pages 3`

- IEEE：读取 `IEEE_XPLORE_API_KEY`（兼容 `IEEE_API_KEY`），或本机 `~/.config/research-planning-mini/credentials.json` 的 `IEEE_XPLORE_API_KEY`。密钥仅保存在本机私密配置，不放入项目、输出、Skill 或仓库。受账号配额约束，按实际剩余额度分批；401/403 停止并记录，不能推断订阅全文权限。
- PubMed：ESearch 检索 PMID，EFetch 获取完整结构化摘要，保留各段标签。缺摘要记录仍标缺失。单检索式接近 10,000 条时按日期/主题拆分；不能把 API 窗口当作全库结果。
- WoS：调用 `--sources wos` 会返回浏览器操作交接状态，不声称已经搜索。使用可用的 Chrome 浏览器控制工具进入已授权 WoS，模型执行检索、核对结果数和分批导出范围，选择包含 Abstract 的纯文本完整记录格式；仅登录/必要验证由用户处理。不能自动下载导出时请用户保存该导出。无需逐篇打开记录。随后运行：

`import_wos.py <export.txt> --query '<实际WoS检索式>' --expected-count <本批导出条数> --output <project>/literature/search_runs`

原始文件和哈希一并保存；核对条数、UT 去重及摘要数，缺额重导或标记 PARTIAL。导出范围、日期/文类筛选、检索时间记入研究检索记录。多个导出分别导入，再将产生的 `run.json` 交给 `corpus.py`。不得把导出的一批宣称为全部检索结果。WoS 导出支持与实时浏览器授权是否仍有效是两件事。

### Google Scholar：仅在 Scholar 内取 Description

`search_sources.py --query '<检索式>' --sources google_scholar --output <project>/literature/search_runs --limit 30 --page-size 10 --max-pages 3`

搜索结果中的 snippet 只作发现线索，绝不能写入 abstract。脚本只跟随实际出现的 Scholar `view_citation` 详情链接，保存 Description 候选和原始页；普通结果未提供详情链接时，可用浏览器查看 Scholar 自身可见详情。不猜造详情 URL，不进入出版社、机构库或其他外部网站补这个来源的摘要。遇到验证、403 或不识别的页面停止该渠道，保留已得到的结果，不持续重试。

Description 有时是完整作者摘要，有时只是简述或截断内容。模型需读到全文、核对对应论文身份，确认是完整作者摘要后，才将其纳入摘要筛选。脚本默认将其留在 `description`，不会自动冒充 `abstract`。确认后可保存单条记录为 JSON 并运行：

`scholar_description.py <single-record.json> --url '<实际观察到的Scholar详情URL>' --confirm-original-abstract --output <new-result.json>`

可用 `--html-file <同一详情页保存的HTML>`；输出保留详情页快照和哈希。再通过 `corpus.py` 合并该结果。未确认、截断或无 Description 的记录保留缺摘要状态，不进入100篇。已有其他来源对同 DOI 提供的摘要可直接复用，无须追加网页访问；自动去重后仍保留此限制，`enrich_abstracts.py` 不再为该记录发起外部补查。该限制仅针对 Scholar 摘要补取，不改变最后30篇的全文下载流程。

先用 `corpus.py <search-run.json> <export.ris> ... --output <versioned-corpus.json>` 去重并合并已有摘要，再对有筛选价值的缺摘要记录分批执行：

`enrich_abstracts.py <versioned-corpus.json> --output <versioned-enriched.json> --limit 50 --supplement <other-search-run.json>`

此处50是每批尝试补全的论文数。优先把关键候选排在输入前部，保留完整库。先复用同DOI已有摘要，再按精确 DOI 从 Crossref、OpenAlex、Semantic Scholar 依次补缺并记录来源；不靠模糊题名把别篇摘要嫁接过来。不匹配、无 DOI、限流和批次未处理记录仍在缺口清单中，下批可接续；无 DOI 的关键论文由模型核对出版社页/机构库/可获取原文。`PRESENT` 仅表示来源提供了非空摘要，不等于模型读过、摘要语义完整或已达到筛选要求。搜索片段、模型猜测和标题改写不是摘要。

缺摘要时先合并其他来源已有摘要，再按DOI补查可用接口，仍缺失时用可用浏览工具核对出版社/机构库页面；已合法获得全文可提取作者原始摘要。合理修复本地解析、查询或配置问题，不能把本地失败说成网站故障；网络暂时失败可有限重试，429按服务要求退避，不连续撞限流。逐篇保存实际尝试及失败原因（来源不提供、网络/访问限制、本地问题或待处理），不因批次上限便宣称已经尽力。最终没有取得并读过真实摘要的论文保留待查，不进入100篇；重要缺口仍要向用户报告，不静默丢弃。交给用户两类精简清单：影响遴选判断的摘要/内容缺口，以及最终30篇核心组的全文缺口；给 DOI、题名、链接、原因和项目实际接收目录（复用下载规则）。用户一次导出带摘要的 WoS/Scopus RIS/CSV 可批量补齐，不要求逐篇手抄。报告实际缺口数量后再估算人工量，不预报固定缺失比例。

检索计划按主流综合索引、必要专业库、前后向引文追踪覆盖证据角色，不以渠道数量或期刊名替代研究质量。每批保存已看摘要、纳排理由和独特新增贡献；综合时解释一致与冲突的证据、方法差异及未知项。100篇入围与30篇精读之间的选择依据保留在原有文献记录中，不改变交接格式。

参考实现思路：吸收 [scientific-brainstorming](https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/scientific/scientific-brainstorming/references) 的研究维度拆解和 [systematic-literature-review](https://github.com/bytedance/deer-flow/tree/main/skills/public/systematic-literature-review) 的分批提取、跨文献综合；不照搬其检索条数限制、固定代理数或仅摘要流程。

选定核心组后，将含检索来源链接及合并溯源记录的选中记录交给[全文获取与接续](fulltext-recovery.md)，不要仅导出DOI而丢弃已经找到的全文地址。
