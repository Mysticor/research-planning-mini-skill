> Coordination update 1.1: [project contract](project-coordination.md) takes precedence for routine AUTO decisions, freshness and optional specialist routing. Gate labels remain checkpoints.

# Specialist adapters and scope
Use scripts/specialists.py to resolve installed ~/.codex/skills/<name>/SKILL.md,
including researchwrite alias, then this module's pinned vendor/nature-skills/skills.
Read only selected specialist manifest/core and matching fragments. Vendor copies
are unmodified resources, not globally installed triggers or activated MCP servers.
Prefer installed equivalents when compatible; record path/version used. If missing,
record SPECIALIST_UNAVAILABLE and use available tools with the same evidence rules.

- nature-academic-search: multi-source-search, reference management and import.
  Override source priority with literature-strategy; do not inherit PubMed-first
  for engineering or call an OpenAlex-only query 'multiple databases'. Reuse
  academic_search.py, provider classes and converters. Adapter uses Python tomllib
  for optional toml config loading and imports requested providers only.
- nature-downloader: lawful retrieval and identity validation. Its SI yes/no and
  institutional fallback gates remain; reuse prior user answers, explain any new
  question's exact source. No library login/password handling by this orchestrator.
- nature-reader: full bilingual reader only when requested/needed; source-map
  extraction feeds nature-paper-card. Do not force all corpus items through it.
- nature-paper-card: prepare_paper.py + audit_paper_card.py; 16-section contract,
  locators and paper-type axes remain intact. Add portfolio outside the card.
- nature-proposal-writer (frontmatter researchwrite): read foundation-files,
  stopping-rules, professor-dispatch, evaluation-rubric, project-structure and scope
  guidance as needed. Use canon/evidence/argument/review designs ONLY. No compose,
  proposal export, section prose or deleting historical negative evidence.
- nature-statistics: design/reporting audit, n/assumptions/uncertainty. Stop before
  manuscript drafting. Raw-data computation requires actual supplied data/scope.
- nature-ref-verifier: DOI and field verification across available sources; persist
  verified fields, sources, dates and mismatches. DOI resolution alone is not full
  verification; preprint/publication status stays explicit.
- nature-experiment-log: local structured logs and attachments, no unsolicited
  external synchronization. Preserve raw evidence and unknowns.
- nature-citation: optional ONLY if user explicitly wants its Nature/CNS-restricted
  scope. Never impose that filter on engineering landscape or general references.
- manuscript-writing: Stage 2 orchestrator and handoff consumer. nature-writing is its internal prose engine, not the handoff entry. Never dispatch manuscript drafting from this Skill.

Expert review is optional when requested or needed for a material unresolved scientific issue. Use focused perspectives, not routine review rounds; same-agent checks are not independent review.

仓库模块 vendor 内包含所需固定版本依赖，无外部符号链接。
下载使用 nature-downloader 的 batch_download.mjs，按需读取其入口，复用已有 SI 选择与授权。
mini 尚未完成真实下载验收；失败保存待获取清单，网页访问不等于取得有效文件。
其他独立下载工具未经适配验证不自动替换本下载器。
