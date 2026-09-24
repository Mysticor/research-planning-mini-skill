# Research Planning

A resumable Idea → Research → Evidence → writer-ready handoff orchestrator.
It separates an approved, immutable research protocol from actual findings and a
self-contained manuscript handoff. It does not draft manuscript prose or determine
final figure numbering, paragraph order, or main-versus-SI layout.

Read SKILL.md and manifest.yaml, then only the current phase/study-type references.
Use existing Nature specialists through references/adapters.md. Installed skills
are preferred; the module's pinned vendor tree (portability changes documented in THIRD_PARTY.md) is the fallback.
Proposal-writer/researchwrite supplies foundation and critique patterns only.

Use `python scripts/researchctl.py --help` for project mechanics:
init, state, approve, transition, freeze, fingerprint, check and package.
Approvals must record actual user choices. Scientific reasoning and semantic
verification remain the agent's responsibility; mechanical checks do not prove
scientific truth. Search logs distinguish unavailable sources from queried sources.
The bundled search command fetches bounded result pages, not exhaustive coverage.

The handoff exports 18 numbered facts/evidence files, references, source records,
raw evidence and analysis with project-relative paths and checksums. The downstream
nature-writing agent reads the package README and builds its own Manuscript Blueprint.
No undocumented upstream importer is assumed.

Run `python tests/test_research_planning.py`. All synthetic
examples are MOCK/FIXTURE. Test bundles never carry the production writing-ready
marker. See the repository README.md for installation and validation commands.
