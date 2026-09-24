# Literature Visual Evidence Library

Prepare early → Decide late → Verify at use.

During LEVEL 3 deep reading, maintain this library for valuable figures/panels,
tables and important equations. Prioritize it for review/systematic review,
perspective and literature-heavy introductions/discussions. Examine sources with
nature-paper-card/nature-reader and reuse their figure/table/equation inventory,
source bundle and stable block IDs. Do not redo their extraction or invent locators.
Paper Card's fixed 16 sections stay intact; attach the visual summary as an appendix
or linked companion using templates/literature/visual_evidence_summary.md.

Classify the selected evidence, not every image:
- REFERENCE_ONLY: index for understanding; no copied image by default.
- CANDIDATE: likely useful in later manuscript design; retain an internal working copy when feasible.
- KEY_VISUAL: competitor method, experiment/evidence architecture, journal exemplar,
  taxonomy source or representative setup/comparison; add more detailed context and a working copy.
Explain WHY a candidate matters. Inventory all six relevant figures if useful, but
only extract/copy the two selected candidates when the other four are reference-only.
Missing/unreliable extraction is NOT an invented asset: keep source pointer, failure
reason and extraction_status=UNAVAILABLE. Render/crop via nature-reader's existing
source workflow. Confirm the crop includes the intended panel and context. Mark crops
INTERNAL RESEARCH / MANUSCRIPT PLANNING, never publication-ready or permission-cleared.

## Shared schema

references/literature-evidence-schema.json is the authoritative Stage 1 schema;
Stage 2 consumes these exact CSVs and relative paths (not a second inventory family).
Every record has a stable component_id, paper metadata and local_pdf_path/hash,
asset_type, original number/panel/physical PDF page, original_caption and source_pointer
(e.g. P017 → PDF p.8 → Fig.3 → panel a); add source_block_id if nature-reader supplies it.
Physical PDF page is 1-based. If unknown, leave blank and explain a structure-grounded
locator; never invent a page or DOI. Distinguish original_claim from our interpretation,
what_it_shows, scientific_role, why_potentially_useful and potential_future_use.
Asset paths are project-relative, preserved unchanged in the handoff. Store internal
working copies in literature_assets/{figures,tables,formulas}/. Keep source path/hash
and processing provenance; retain licence/permission as UNKNOWN where unresolved.
verification_status=PREPARED_SOURCE_INDEX requires Stage 2 re-verification at actual use.

Tables additionally describe rows/columns, contents and structured_data_status/path.
Reliable structured CSV/TSV may be copied from source-reader outputs; verify every
cell, units, merged headers and missing-value meaning against the original. Otherwise
leave UNAVAILABLE/NOT_ATTEMPTED with reason, not an invented table. Formula text/LaTeX
is optional and must be reliable; retain variable definitions, relevance and original
locator even when transcription is unavailable. Do not mechanically extract all equations.

potential_use_mode is provisional only: REFERENCE_ONLY, POSSIBLE_REPRODUCED,
POSSIBLE_ADAPTED, POSSIBLE_SYNTHESIS_SOURCE. Never assign manuscript Figure 2b,
Table 1, final panel IDs or MAIN/SI. Original paper numbering is retained for navigation.
Final modes and publication rights are decided by manuscript-writing.

## Optional deterministic helper

`scripts/literature_evidence.py prepare PROJECT --entries reviewed-entries.json`
accepts an array of Agent-reviewed records with kind=visual/table/formula and schema
fields. Optional working_copy_path/structured_working_copy_path reference existing
nature-reader working files inside PROJECT. It copies only CANDIDATE/KEY_VISUAL
assets, never extracts every PDF page. A prepare batch must be complete for new records;
existing indexes are merged by component_id, existing records require explicit revision
outside this helper (no silent overwrite). Use reader tools to extract, not this helper.

Legacy field aliases are normalized only on export: original_path→local_pdf_path,
extracted_path→asset_path, caption→original_caption, potential_role→scientific_role,
licence→license_status, status→extraction_status; old missing semantics remain blank
with LEGACY_NEEDS_ENRICHMENT, never fabricated. No existing project/frozen inventory is
rewritten. Handoff exports canonical headers, working assets and availability records.
