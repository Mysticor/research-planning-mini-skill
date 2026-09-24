# Attribution and adapters

Nature Skills: https://github.com/Yuan1z0825/nature-skills
Pinned commit: c4e4c99fbeaf0168cda090f8739e1508017a610e.
Original skill directories and licence files are preserved in the module's
vendor/nature-skills. Individual skill notices are preserved; see root LICENSE.

research-planning's foundation/state/review design adapts ideas from researchwrite
(nature-proposal-writer): foundation-files, scope control, stopping-rules,
professor-dispatch and evaluation-rubric. It deliberately omits proposal generation.
Search adapters invoke upstream OpenAlex and CrossRef/arXiv providers without
rewriting those engines. The nature-reader evaluation example path was made portable; see upstream-lock.json for the recorded modification. Runtime engines are unchanged.

Project-local Python libraries: bibtexparser 1.4.4, rispy 0.10.0, xlrd 2.0.2,
pyparsing 3.3.2. Distribution metadata and licences are retained under vendor/python.

The vendored runxlrd.py interpreter shebang was changed to /usr/bin/env python3 for portability.
