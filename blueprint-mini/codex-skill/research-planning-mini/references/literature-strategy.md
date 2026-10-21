# 按问题与覆盖缺口检索
初步选题先使用适合领域且可用的少量互补来源。正式缺口或创新结论需补足独立来源及直接竞争工作。
方向确定后，按实际需要覆盖基础工作、近期竞争研究、方法来源、不同结论与适用边界，不能把早期少量探索或核心精读名单当作文献库上限。已有引用目标作为覆盖规划的输入；候选库、已核验证据和最终实引数分别统计，不要求所有候选同等深读，也不靠无关记录凑量。
完整研究准备按[核心文献遴选](core-literature.md)广泛检索并阅读摘要后默认形成至少100篇有依据的入围文献（客观不足时按核心文献规则征求用户调整），阶段汇报并停止后再选择30篇全文精读；先写清筛选标准、质量判断依据和覆盖缺口，数量不能用搜索命中总数代替。核心组学习本领域同类型领先研究，不受拟投期刊档次限制；期刊体量对照另按 journal-strategy.md，可共用合适原文。
系统综述按预先制定的多库协议执行，不用少量检索冒充完整覆盖。WoS、ScienceDirect、Scopus、CrossRef、OpenAlex、Semantic Scholar、arXiv 是候选来源；工程按需使用 IEEE/Ei，生医按需使用 PubMed。
中文证据按研究对象、国内场景与覆盖缺口选择[知网浏览器检索](cnki-browser.md)；中文论文优先考虑，英文的国内相关研究也适用。收益低时可不启用，简记理由，不固定中文配额，也不以中文替代必要国际文献。
记录实际检索的来源；聚合索引不代表直接检索全部上游数据库。不可用来源记录限制，条件未变时不反复尝试。


执行分页、摘要补全与导入时读[检索执行](search-execution.md)。聚合索引交叉补缺，不能把登记过的全部来源说成已可用；PubMed、IEEE Xplore、ACM Digital Library、Web of Science、Scopus 以及适合题目的中文索引按领域选用，缺少直接接口时用授权网页或用户导出，不要求每个题目把所有库搜一遍。Google Scholar 已作为可选发现渠道接入，仅取 Scholar 自身可核实的 Description，不沿外链补摘要；无摘要不入围，不能承诺稳定自动批量检索。Crossref 主要用于 DOI/元数据核验，摘要缺失不能当作论文没有相关内容。

Record every attempt in literature/search_runs: source, timestamp, exact query,
variant, filters, year range, document types, reported count, retrieved count,
availability, coverage and raw-response path. Status is AVAILABLE, UNAVAILABLE,
USER_EXPORT_AVAILABLE or USER_ACTION_REQUIRED; failed source status additionally
SOURCE_UNAVAILABLE. Search logs are append-only. Never log secrets or cookies.

Construct exact phrases, synonyms, methods, applications, legacy/new terminology,
broader terms and narrow competitor queries. Sequence broad → focused → competitor
→ backward and forward citation chasing → related-paper discovery → novelty.
将对象、场景、方法、测量指标和关键假设拆成检索维度，检查遗漏的组合、跨领域可迁移方法与反例；不强制套用整套头脑风暴仪式。Translate terms for relevant local literature. Agent writes domain-specific query
variants; don't rely solely on an auto-generated synonym list.

Import user WoS/Scopus/Ei RIS, BibTeX, CSV, XLS/XLSX or reference manager exports. WoS tagged full-record TXT uses `import_wos.py` before corpus merging.
Preserve original export and source record IDs. Use corpus.py for CSV/JSON/TSV/XLS/XLSX and conservative deduplication; its
RIS/BibTeX routes reuse rispy/bibtexparser, and XLS uses the project-local xlrd.
Do not parse nested BibTeX with regex. Verify column mapping and preserve unknown
fields in the raw record. Report a missing spreadsheet reader if unavailable. Cite conversion tool/version in import log.
DOI-identical records may merge; conflicting DOIs with similar titles must remain
separate and be flagged. Metadata-only title/year duplicates without authors are
review candidates, not automatic merges. Preserve source provenance and conflicts.

阶段汇报按渠道列：实际取回记录数、渠道内去重数、带原始摘要数、实际读过摘要的论文数、入围数；没有执行或不可用的渠道标状态，不伪装成零命中。由既有search_runs、master_corpus与逐篇筛选记录生成，不新建重复手填台账。另报跨渠道去重总数、已读摘要总数、入围总数、重合及覆盖缺口。保留所有发现来源与实际摘要来源；渠道“带摘要数”按该渠道实际取得的摘要统计，不把其他渠道补全冒记为本渠道提供。按发现来源分组的已读/入围数可在多渠道重复归属，明确不可相加；总体阅读数按唯一论文计一次。报告新增量时说明比对基线，不能把有先后顺序的新增量当作渠道固有覆盖率。搜索页面估计总数与实际取回数分开。

Keep SCREENING (titles/abstracts), FOCUSED (relevant available methods/results) and
DEEP_READING (obtained and actually read full texts) distinct. Record exclusions.
For each additional source/query record unique/relevant/core yield. Saturation
requires consecutive meaningful searches with no important additions and adequate
competitor/anchor coverage; save rationale, coverage limits and unavailable sources.
Do not claim exhaustive or saturated solely from counts or database quantity.
