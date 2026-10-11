# 按问题与覆盖缺口检索
初步选题先使用适合领域且可用的少量互补来源。正式缺口或创新结论需补足独立来源及直接竞争工作。
方向确定后，按实际需要覆盖基础工作、近期竞争研究、方法来源、不同结论与适用边界，不能把早期少量探索或核心精读名单当作文献库上限。已有引用目标作为覆盖规划的输入；候选库、已核验证据和最终实引数分别统计，不要求所有候选同等深读，也不靠无关记录凑量。
完整研究准备按[核心文献遴选](core-literature.md)实际筛查至少100篇有效候选，再选择20篇全文精读；先写清筛选标准、质量判断依据和覆盖缺口，数量不能用搜索命中总数代替。核心组学习本领域同类型领先研究，不受拟投期刊档次限制；期刊体量对照另按 journal-strategy.md，可共用合适原文。
系统综述按预先制定的多库协议执行，不用少量检索冒充完整覆盖。WoS、ScienceDirect、Scopus、CrossRef、OpenAlex、Semantic Scholar、arXiv 是候选来源；工程按需使用 IEEE/Ei，生医按需使用 PubMed。
记录实际检索的来源；聚合索引不代表直接检索全部上游数据库。不可用来源记录限制，条件未变时不反复尝试。


Use nature-academic-search through adapters.md. The bundled search_sources.py
reuses upstream public-provider code and gives a bounded first page only. For a
real review paginate or use the specialist's API/MCP/browser/export workflows;
record truncation/coverage. Script defaults include unavailable-source records.
WoS/IEEE/Ei require a separately available API/MCP or authorized browser; their
absence is SOURCE_UNAVAILABLE, not zero results. ScienceDirect/Scopus adapters
require pybliometrics and authorized credentials. Check existing sessions only via
available browser tools; do not claim lack of institutional entitlement from lack
of an API. Never install runtimes or collect passwords without authorization.

Record every attempt in literature/search_runs: source, timestamp, exact query,
variant, filters, year range, document types, reported count, retrieved count,
availability, coverage and raw-response path. Status is AVAILABLE, UNAVAILABLE,
USER_EXPORT_AVAILABLE or USER_ACTION_REQUIRED; failed source status additionally
SOURCE_UNAVAILABLE. Search logs are append-only. Never log secrets or cookies.

Construct exact phrases, synonyms, methods, applications, legacy/new terminology,
broader terms and narrow competitor queries. Sequence broad → focused → competitor
→ backward and forward citation chasing → related-paper discovery → novelty.
Translate terms for relevant local literature. Agent writes domain-specific query
variants; don't rely solely on an auto-generated synonym list.

Import user WoS/Scopus/Ei RIS, BibTeX, CSV, XLS/XLSX or reference manager exports.
Preserve original export and source record IDs. Use corpus.py for CSV/JSON/TSV/XLS/XLSX and conservative deduplication; its
RIS/BibTeX routes reuse rispy/bibtexparser, and XLS uses the project-local xlrd.
Do not parse nested BibTeX with regex. Verify column mapping and preserve unknown
fields in the raw record. Report a missing spreadsheet reader if unavailable. Cite conversion tool/version in import log.
DOI-identical records may merge; conflicting DOIs with similar titles must remain
separate and be flagged. Metadata-only title/year duplicates without authors are
review candidates, not automatic merges. Preserve source provenance and conflicts.

Keep SCREENING (titles/abstracts), FOCUSED (relevant available methods/results) and
DEEP_READING (obtained and actually read full texts) distinct. Record exclusions.
For each additional source/query record unique/relevant/core yield. Saturation
requires consecutive meaningful searches with no important additions and adequate
competitor/anchor coverage; save rationale, coverage limits and unavailable sources.
Do not claim exhaustive or saturated solely from counts or database quantity.
