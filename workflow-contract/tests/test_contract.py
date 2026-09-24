import sys,tempfile,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import project_contract as c
class Contract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='MOCK-contract-');self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name);c.init(self.r,c.STAGES[0])
  with c.edit(self.r) as m:
   for s in c.STAGES:m['completion'][s]='READY';m['stage_status'][s]='READY';m['freshness'][s]='CURRENT'
  for oid,st,deps in [('RESULT_001',0,[]),('RESULT_002',0,[]),('CLAIM_001',1,['RESULT_001']),('ABSTRACT_001',1,['CLAIM_001']),('FIG_004',1,['CLAIM_001']),('TABLE_002',1,['RESULT_001']),('REVIEWED_RESULTS',2,['CLAIM_001']),('PDF_FIG_004',3,['FIG_004'])]:
   (self.r/(oid+'.txt')).write_text('MOCK '+oid+' 92.6')
   c.register(self.r,c.STAGES[st],oid,oid+'.txt','RESULT' if st==0 else 'ASSET',deps,oid)
 def test_A_result_stales_downstream_preserves_completion(self):
  (self.r/'RESULT_001.txt').write_text('94.1');c.change(self.r,c.STAGES[0],['RESULT_001'],'RESULT','MOCK actual result correction')
  m=c.load(self.r)
  for s in c.STAGES[1:]:self.assertEqual(m['stage_status'][s],'STALE');self.assertEqual(m['completion'][s],'READY')
 def test_B_targeted_dependency_closure(self):
  e=c.change(self.r,c.STAGES[0],['RESULT_001'],'RESULT','MOCK correction');ids={x['object_id'] for x in e['affected_items']}
  self.assertIn('ABSTRACT_001',ids);self.assertIn('TABLE_002',ids);self.assertNotIn('RESULT_002',ids);self.assertEqual(e['strategy'],'TARGETED_REVALIDATION')
 def test_C_technical_figure(self):
  c.change(self.r,c.STAGES[1],['FIG_004'],'FIGURE','MOCK color unchanged scientific meaning; redundant labels retained',True)
  m=c.load(self.r);self.assertEqual(m['stage_status'][c.STAGES[2]],'READY');self.assertEqual(m['stage_status'][c.STAGES[3]],'STALE')
 def test_D_scientific_figure(self):
  c.change(self.r,c.STAGES[1],['FIG_004'],'FIGURE','MOCK central panel structure changed');self.assertEqual(c.load(self.r)['stage_status'][c.STAGES[2]],'STALE')
 def test_E_stage4_cannot_change_claim(self):
  with self.assertRaisesRegex(ValueError,'CONTENT_REVISION_REQUIRED'):c.change(self.r,c.STAGES[3],['PDF_FIG_004'],'CLAIM','central claim rewrite')
 def test_F_journal_plan_uses_reviewed_canonical(self):
  (self.r/'reviewed.md').write_text('MOCK science');(self.r/'old-elsevier.tex').write_text('old build')
  with c.edit(self.r) as m:m['canonical_outputs']['reviewed_manuscript']={'path':'reviewed.md','owner':c.STAGES[2],'fingerprint':c.sha(self.r/'reviewed.md')}
  p=c.journal_plan(self.r,c.STAGES[3],'MOCK IEEE');self.assertEqual(p['canonical_source'],'reviewed.md');self.assertFalse(p['reuse_old_tex'])
 def test_G_one_style_auto(self):self.assertEqual(c.decision(1,True),'AUTO')
 def test_H_two_consequential_styles(self):self.assertEqual(c.decision(2,True),'ASK')
 def test_I_legend_auto(self):self.assertEqual(c.decision(3,False,True),'AUTO')
 def test_J_humanizer_absent(self):self.assertEqual(c.humanizer_route(False,True),'NATURE_POLISHING')
 def test_K_humanizer_present_not_default(self):self.assertEqual(c.humanizer_route(True),'NATURE_POLISHING')
 def test_L_humanizer_fact_lock(self):
  self.assertEqual(c.humanizer_route(True,True),'OPTIONAL_PROSE_ONLY')
  report={k:'UNCHANGED' for k in ['claim_strength','causality','terminology','technical_meaning','evidence_boundary']}
  self.assertTrue(c.check_prose('Mean 92.6 [@mock].','The mean is 92.6 [@mock].',report))
  for after in ['Mean 94.1 [@mock].','Mean 92.6 [@other].']:
   with self.assertRaises(ValueError):c.check_prose('Mean 92.6 [@mock].',after,report)
  with self.assertRaises(ValueError):c.check_prose('Mean 92.6.','Mean 92.6.',{})
 def test_M_legacy_recovery(self):
  tmp=tempfile.TemporaryDirectory(prefix='MOCK-legacy-');self.addCleanup(tmp.cleanup);r=Path(tmp.name);(r/'manuscript/checks').mkdir(parents=True);(r/'manuscript/manuscript.md').write_text('MOCK');(r/'manuscript/checks/readiness.json').write_text(json.dumps({'status':'MANUSCRIPT_DRAFT_READY','test_only':True}))
  c.init(r,c.STAGES[2]);m=c.load(r);self.assertEqual(m['completion'][c.STAGES[1]],'READY');self.assertEqual(m['freshness'][c.STAGES[1]],'NEEDS_CHECK');self.assertEqual(c.locate(r/'manuscript'),r.resolve())
 def test_raw_edit_detected_without_upstream_revision_mutation(self):
  before=c.load(self.r)['stage_revision'][c.STAGES[0]];(self.r/'RESULT_001.txt').write_text('MOCK 94.1');self.assertTrue(c.detect(self.r,c.STAGES[2]));self.assertEqual(c.load(self.r)['stage_revision'][c.STAGES[0]],before);self.assertEqual(c.detect(self.r,c.STAGES[2]),[])
 def test_foreign_owner_rejected(self):
  with self.assertRaises(ValueError):c.change(self.r,c.STAGES[1],['RESULT_001'],'RESULT','bad write')
 def test_backtrack_records_reason(self):
  e=c.backtrack(self.r,c.STAGES[3],c.STAGES[2],'MOCK word limit requires substantive revision',['CLAIM_001']);m=c.load(self.r);self.assertEqual(m['current_stage'],c.STAGES[2]);self.assertIn(e['change_id'],(self.r/'change_log.md').read_text());self.assertEqual(m['stage_status'][c.STAGES[2]],'READY')
 def test_assets_provenance_and_paths(self):
  a={'FIG_004':{'kind':'FIGURE','brief':'FIG_004.txt','final':'FIG_004.txt','sources':['RESULT_001.txt'],'reproduction':['FIG_004.txt'],'depends_on':['RESULT_001'],'source_type':'LITERATURE_ADAPTED','provenance':[{}]}}
  self.assertTrue(c.validate_assets(self.r,a));a['FIG_004']['source_type']='OWNED';self.assertFalse(c.validate_assets(self.r,a))
 def test_missing_canonical_is_detectable(self):
  (self.r/'RESULT_001.txt').unlink();self.assertTrue(c.detect(self.r,c.STAGES[1]))
 def test_manifest_invalid_status(self):
  m=c.load(self.r);m['stage_status'][c.STAGES[0]]='GUESS'
  with self.assertRaises(ValueError):c.validate(m)
 def test_output_ownership(self):
  (self.r/'ready.json').write_text('{"status":"MANUSCRIPT_DRAFT_READY"}')
  with self.assertRaises(ValueError):c.publish(self.r,c.STAGES[1],{'reviewed_manuscript':'CLAIM_001.txt'},'ready.json')
 def test_revalidation_requires_current_hash(self):
  e=c.change(self.r,c.STAGES[0],['RESULT_001'],'RESULT','MOCK correction');p=self.r/'audit.yaml';p.write_text('status: PASS\nreviewer: MOCK\nobservations: [checked]\nchecked_objects: [CLAIM_001]\nfingerprints: {}\n')
  with self.assertRaises(ValueError):c.revalidate(self.r,c.STAGES[1],e['change_id'],'audit.yaml')
 def test_csv_row_fingerprint_is_targeted(self):
  p=self.r/'results.csv';p.write_text('result_id,value\nR1,92.6\nR2,50\n')
  c.register(self.r,c.STAGES[0],'R1','results.csv','RESULT',locator='result_id=R1');c.register(self.r,c.STAGES[0],'R2','results.csv','RESULT',locator='result_id=R2')
  p.write_text('result_id,value\nR1,94.1\nR2,50\n');events=c.detect(self.r,c.STAGES[1]);self.assertEqual([e['changed_object'] for e in events],[['R1']])
 def test_conflicting_technical_label_cannot_bypass_material_choice(self):self.assertEqual(c.decision(2,True,True),'ASK')
 def test_prose_seals_and_rejects_tables(self):
  lock=c.prepare_prose('Result 92.6% [@mock].');self.assertNotIn('92.6',lock['prose']);self.assertEqual(c.restore_prose(lock['prose'],lock),'Result 92.6% [@mock].')
  with self.assertRaises(ValueError):c.prepare_prose('| x | y |\n| 1 | 2 |')
 def test_context_journal_change_marks_build(self):
  c.context(self.r,c.STAGES[3],target_journal='MOCK Elsevier')
  c.context(self.r,c.STAGES[3],target_journal='MOCK IEEE',reason='MOCK explicit retarget')
  m=c.load(self.r);self.assertEqual(m['target_journal'],'MOCK IEEE');self.assertEqual(m['stage_status'][c.STAGES[3]],'STALE')
if __name__=='__main__':unittest.main(verbosity=2)
