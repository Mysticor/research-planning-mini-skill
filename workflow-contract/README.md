# Four-stage project contract 1.1

This directory is a shared deterministic library, schema and tests, not a Skill or a fifth
workflow. Each of the four existing Skills has a fixed-stage `scripts/projectctl.py` adapter.
Use Python 3.11+ with the repository dependencies installed. PyYAML and jsonschema are required; no network service or Humanizer dependency.

Every stage first opens the intended research project's manifest (nearest ancestor), or
initializes it from existing canonical files. Do not create a manifest in the research tooling
repository merely because it hosts the Skills. Conventional manuscript/review/publication
subdirectories share their parent; custom layouts use an existing ancestor manifest or an
explicit project root. No directories or historical scientific files are moved.

```text
projectctl.py open PROJECT
projectctl.py register PROJECT --payload object.yaml
projectctl.py change PROJECT --payload change.yaml
projectctl.py consume PROJECT
projectctl.py revalidate PROJECT --payload revalidation.yaml
projectctl.py publish PROJECT --payload publication.yaml
projectctl.py validate PROJECT
```

The adapter fixes the calling stage; payloads cannot choose another actor. `register` records
stable IDs and dependency edges derived from existing claim/result/asset maps. `change` is the
owner's explicit change record with classification evidence. `detect` observes raw fingerprint
drift without modifying the upstream author's revision. It conservatively marks freshness,
never regenerates work. An owner subsequently records the actual revision and downstream
stages close the observed and classified changes after targeted checks. Hashes detect change;
they do not determine scientific scope. A canonical package fingerprint is a signal, not an
instruction to rewrite the entire manuscript. Input revisions and fingerprints are captured
by `consume` when a stage reads its chosen upstream snapshot. `publish` is allowed only after
local readiness and all pending targeted checks; it publishes only the actor's canonical.

`stage_status` is navigation status (NOT_STARTED/IN_PROGRESS/READY/STALE/BLOCKED).
`completion` preserves historical completion. `freshness` is CURRENT/STALE/NEEDS_CHECK.
Old files alone give IN_PROGRESS + NEEDS_CHECK. Valid local readiness may recover historical
READY while freshness remains NEEDS_CHECK until inputs are verified. Never invent prior input
revisions or force an old study back to Stage 1. `canonical_history` preserves replaced paths.

Each object has stage, path, kind, stable ID, locator, revision and depends_on IDs. Export/import
existing CSV/YAML registries without renumbering. Agent supplies edges from source evidence;
unmapped changes remain IMPACT_ANALYSIS_REQUIRED, not an invented dependency graph.
Targeted list is the transitive closure with section/panel locators. Verify only affected content
plus required consistency checks. Record real `checked_objects`, their current fingerprints,
reviewer and observations; `revalidate` clears only the actor's freshness obligations.

Scientific result/claim/architecture changes stale downstream stages. Technical-only figure
changes (supported by evidence of unchanged meaning) stale Stage 4 builds, not Stage 3 science.
Stage 3 scientific display revision affecting interpretation also creates Stage 2 revalidation
request; it does not silently edit Stage 2. Backtracks record reason, IDs and destination in
manifest and change_log.md; the originating stage stays blocked until its targeted check closes.
Stage 4 cannot register/publish an upstream canonical. Scientific edits return
CONTENT_REVISION_REQUIRED → Stage 3. Journal changes use journal-plan: frozen reviewed Markdown,
fresh build directory, old build preserved, never conversion of old publisher main.tex.

Canonical facts: actual data + results_facts + claim_registry + RESEARCH_DOSSIER_FINAL and
MANUSCRIPT_HANDOFF outrank the plan RESEARCH_BLUEPRINT_FINAL. Stage 2 manuscript/manuscript.md
and Stage 3 review/reviewed_manuscript.md are their single content mothers. Existing equivalent
paths are registered, not duplicated. Stage 4 tex/PDF/ZIP are build artifacts only.

AUTO BY DEFAULT; ask only for two or more real, materially different scientific/submission
alternatives, or an actual major commitment requiring authorization. Missing necessary facts
may be requested; don't fabricate them to avoid a question. Prior authorization persists.
Technical dimensions, legend position, palette/font details, line width, naming, conversions,
compiler choice and bibliography passes are AUTO. Use user visual references first. Without
a reference use the one evidence-appropriate style; never manufacture a style/story/route menu.
Gate names remain checkpoints. `auto-gate` records evidence as agent_auto, not user approval;
all existing evidence, freeze and review checks still apply. For native gate freshness, store
AUTO records in `decisions/` at the stage working-root (outside hashed scientific directories).
The four-stage contract takes precedence over a specialist's routine backend/style prompts;
reuse existing code/backend and otherwise choose an available appropriate backend automatically.

Figure/Table source-of-truth: preserve current equivalent layout and stable IDs. Figure brief
is scientific specification, sources are evidence, code/editable are reproduction source,
final PDF (or journal-permitted artifact) is publication input. Stage 2 designs; Stage 3 reviews;
Stage 4 adapts final files technically. Table source data differs from manuscript-ready final
content; Stage 4 does not recalculate, round or delete rows for fit. Asset registry records
brief/final/sources/reproduction/dependency paths. Literature modes remain REFERENCE_ONLY,
LITERATURE_REPRODUCED/ADAPTED/SYNTHESIZED with paper_id, DOI (explicit UNKNOWN when absent),
original figure/panel/page/source_pointer/license and notes; unknown rights block publication
use, not internal inventory. REFERENCE_ONLY is never permission to publish.

Humanizer is OPTIONAL. Default Stage 3 language engine is nature-polishing. Route Humanizer
only for explicit humanize/去 AI 味, supplied author voice, or observed residual chatbot phrasing
after polishing. If absent continue normal four-stage flow. Operate on extracted prose only;
exclude equations, tables, numeric ledgers, citations/bibliography, code and figure source data.
Keep immutable before-copy + numeric/citation/terminology/claim fact lock. Deterministic token
checks are necessary, semantic comparison of claim strength/causality/technical meaning is also
required. Priority: accuracy > evidence boundary > journal style > nature-polishing > Humanizer.
Revert drift. No detector-score optimization and no automatic colloquialization.


Use `projectctl.py context PROJECT --payload context.yaml` to record the known project title,
study_type and inherited/resolved target_journal from local state. A journal change needs a reason
and invalidates appropriate publication work; do not infer a journal from template branding.
CSV object locators can be `result_id=RESULT_001`; these use a stable row hash so an unrelated
row is not falsely detected as changed. Other locators are human navigation pointers and use
file-level change signals until the agent classifies impact. No scientific inference is hardcoded.
`publish` checks consumed input revisions against current upstream revisions. After targeted
revalidation, consume the verified current input snapshot before marking output current.
