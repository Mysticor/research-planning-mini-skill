"""Saved MOCK artifacts for semantic intake and complete evidence-package test."""
from pathlib import Path
import json,sys,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_research_planning as test
import researchctl as rc
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
idea=out/'mock-intake'
rc.init(idea,'MOCK 线路摄像头舞动识别','MOCK 我想研究基于线路摄像头的输电线路舞动识别和预警。',mock=True)
s=rc.read_state(idea)
s.update(research_type=['ml-ai','engineering-method'],study_type_confidence='PROVISIONAL',
    study_type_rationale='Agent assessment: visual recognition suggests learned models; field warning requires engineering validation. No simulation/controlled physical experiment assumed without evidence.',
    unresolved_blockers=['Need actual available videos, event labels, deployment objective and resource constraints'],
    next_actions=['Execute broad/focused searches across available sources','Present preliminary landscape and Gate A'])
rc.save_state(idea,s)
b=rc.rb(idea)
(b/'design/problem_definition.md').write_text('''# MOCK intake
Study: camera-based transmission-line galloping recognition/warning.
Provisional ML + engineering-method axes: video recognition and operational warning.
Do not assume calibrated 3D displacement, training labels, field access or performance.
Unknown: detection vs quantitative reconstruction, per-site data, false-alarm costs,
required lead time and compute. Existing event timestamps and camera motion may confound.
No claim of novelty or field evidence; this is a synthetic intake exercise.
''')
(b/'literature/search_protocol.md').write_text('''# MOCK search plan (NOT EXECUTED for this mock study)
Broad: (transmission line OR overhead conductor) AND (galloping OR aeolian vibration).
Focused: conductor galloping AND (camera OR video OR visual monitoring).
Competitor: (optical flow OR tracking OR displacement reconstruction) AND conductor galloping.
Legacy/new: image-based monitoring, remote visual sensing, vision transformer, event warning.
Separate WoS, ScienceDirect, Scopus, CrossRef, OpenAlex, Semantic Scholar, arXiv;
IEEE/Ei for engineering. Record exact syntax and coverage per source.
Search backward/forward/related for real core papers once identified.
No starting year exclusion until field history is mapped. Record incremental relevant/core yield.
No saturation claim; all mock search counts unknown.
''')
(b/'literature/MUST_DOWNLOAD_AND_READ.md').write_text('''# MOCK must-download queue
FIXTURE PAPER M01 — invented software test record, not a real publication.
DOI: absent; do not generate a DOI. Journal: MOCK only.
Role: DIRECT_COMPETITOR. Need method, calibration and validation sections to compare
claimed quantitative displacement with camera-motion confounding. No full text.
Decision blocked: whether a quantitative-reconstruction route is distinguishable.
In production replace only after locating and verifying an actual critical paper.
''')
rc.transition(idea,1)
blocked=rc.check(idea);rc.write_json(out/'mock-intake-readiness.json',blocked)
complete=test.fixture(out/'mock-complete')
actual=subprocess.check_output([sys.executable,str(complete/'code/mock_analysis.py')],text=True).strip()
assert actual=='2.0'
report=rc.package(complete,complete/'MANUSCRIPT_HANDOFF')
assert report['status']=='READY' and report['test_only']
assert not (complete/'MANUSCRIPT_HANDOFF/READY_FOR_NATURE_WRITING.md').exists()
rc.write_json(out/'mock-dry-run-report.json',{'intake':'PASS','agent_study_classification':'ml-ai + engineering-method (provisional rationale saved)',
 'literature_plan':'PASS: planned queries, not reported searched','must_download_queue':'PASS: explicitly fictional record without fabricated DOI',
 'source_computation':actual,'missing_evidence_gate':blocked['status'],'complete_bundle':report['status'],
 'test_only':True,'production_ready_marker':False,'manuscript_prose_generated':False})
print(json.dumps({'status':'PASS','mock_only':True,'output':str(out)},ensure_ascii=False))
