import csv,json,shutil,sys,tempfile,unittest
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import researchctl as rc
import corpus

def write_rows(p,records):
    p=Path(p)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def user_gate(root,g):
    p=rc.rb(root)/'reviews'/f'user-{g}.md'
    p.write_text(f'MOCK USER APPROVAL {g}: this is a simulated test decision only, not real user authorization.\n')
    rc.approve(root,g,'MOCK approved',str(p.relative_to(root)))
def fixture(root):
    rc.init(root,'MOCK evidence study','MOCK test of mean of synthetic numbers; no real science',['experimental'],True)
    base=rc.rb(root)
    for p in base.rglob('*.md'):
        p.write_text(p.read_text().replace('Status: UNFILLED','Status: MOCK COMPLETE').replace('[TO_COMPLETE]','MOCK / FIXTURE: synthetic mean calculation only; no real papers, participants or findings.'))
    s=rc.read_state(root);s.update(study_type_rationale='MOCK controlled numerical fixture, experimental lens for testing only',
        research_route='MOCK calculate mean',target_journal='TARGET_AGNOSTIC',current_phase=6)
    rc.save_state(root,s)
    for g in 'ABC':user_gate(root,g)
    draft=base/'design/blueprint_draft.md';draft.write_text((rc.SKILL/'templates/RESEARCH_BLUEPRINT_FINAL.md').read_text().replace('Status: UNFILLED','Status: MOCK COMPLETE').replace('[TO_COMPLETE]','MOCK protocol: calculate synthetic mean, report all inputs and no real scientific inference.'))
    user_gate(root,'D');rc.freeze(root,str(draft.relative_to(root)))
    raw=root/'data/mock.csv';raw.write_text('value\n1\n2\n3\n')
    code=root/'code/mock_analysis.py';code.write_text('# MOCK deterministic example\nvalues=[1,2,3]\nprint(sum(values)/len(values))\n')
    note=base/'execution/actual_notes.md';note.write_text('MOCK controlled arithmetic: values 1, 2, 3; mean 2; n=3 synthetic values, no inference. Python standard arithmetic.\n')
    with (rc.SKILL/'templates/design/experiment_matrix.csv').open() as f: experiment=dict.fromkeys(next(csv.reader(f)), 'MOCK arithmetic fixture')
    experiment.update(experiment_id='E01',research_question='MOCK mean',status='COMPLETE')
    write_rows(base/'design/experiment_matrix.csv',[experiment])
    result={'experiment_id':'E01','result_id':'R01','kind':'numeric','metric':'mean','value':'2','unit':'dimensionless','sample_size':'3 synthetic values','uncertainty':'N/A: exact arithmetic','ci':'N/A: no inference','p_value':'N/A: no inferential test','repeats':'1','seed':'N/A: deterministic','source_file':'data/mock.csv','source_sha256':rc.sha(raw),'analysis_script':'code/mock_analysis.py','analysis_sha256':rc.sha(code),'analysis_type':'PLANNED','status':'ACTUAL','notes':'MOCK / FIXTURE; not scientific results'}
    write_rows(base/'execution/results_facts.csv',[result])
    claims={'schema_version':1,'claims':[{'claim_id':'C01','claim':'MOCK synthetic numbers have mean 2','importance':'CENTRAL','supporting_experiments':['E01'],'supporting_result_ids':['R01'],'supporting_literature':['mock_source'],'evidence_strength':'Direct synthetic arithmetic','alternative_explanations':['MOCK input change alters mean'],'boundary_conditions':['Only synthetic values 1,2,3'],'allowed_wording':'MOCK mean equals 2','forbidden_overclaim':'No real-world conclusion or new scientific claim','status':'SUPPORTED'}]}
    (base/'execution/claim_registry.yaml').write_text(yaml.safe_dump(claims))
    write_rows(base/'execution/asset_inventory.csv',[{'asset_id':'A01','type':'RAW_DATA','path':'data/mock.csv','source':'MOCK generated fixture','experiment_id':'E01','date':rc.now(),'provenance':'Created for software testing only','what_it_shows':'Three synthetic numbers','processing_history':'None; raw fixture','publication_permission':'OWNED','quality':'MOCK valid CSV','sha256':rc.sha(raw),'notes':'MOCK'}])
    for p in (base/'handoff').glob('*.yaml'):
        d=yaml.safe_load(p.read_text());d['status']='ACTUAL';d['facts']={k:'MOCK: arithmetic; not applicable to real science' for k in d['facts']};d['source_files']=[str(note.relative_to(root))];p.write_text(yaml.safe_dump(d))
    reference=base/'literature/mock_verification.md';reference.write_text('MOCK reference used only to exercise schema; not an actual publication and no fabricated DOI.\n')
    write_rows(base/'literature/reference_verification.csv',[{'reference_id':'mock_source','authors':'MOCK fixture','title':'MOCK synthetic input specification','year':'2026','journal':'N/A: MOCK','volume':'N/A','pages_or_article':'N/A','doi':'','publication_status':'MOCK fixture only','status':'VERIFIED','sources':'MOCK local fixture','checked_at':rc.now(),'record_file':str(reference.relative_to(root))}])
    (base/'literature/references.bib').write_text('@misc{mock_source, title={MOCK synthetic input specification}, author={MOCK fixture}, year={2026}, note={FIXTURE ONLY; not a real paper}}\n')
    write_rows(base/'handoff/09_claim_reference_map.csv',[{'claim_id':'C01','fact_type':'MOCK','reference_id':'mock_source','locator':'MOCK local input','support_boundary':'Software test only'}])
    run=base/'literature/search_runs/mock_refresh.json';rc.write_json(run,{'status':'SEARCHED','date':rc.now(),'exact_query':'MOCK no network query','source':'MOCK'})
    refresh=base/'literature/mock_refresh.md';refresh.write_text('MOCK refresh simulation; no live literature claim. Target-agnostic synthetic test.\n')
    s=rc.read_state(root);s['current_phase']=9
    s['novelty_refresh']={'status':'COMPLETE','checked_at':rc.now(),'record_file':str(refresh.relative_to(root)),'search_run_files':[str(run.relative_to(root))]}
    s['journal_refresh']={'status':'COMPLETE','checked_at':rc.now(),'record_file':str(refresh.relative_to(root))};rc.save_state(root,s)
    refresh_approval(root)
    return root

def refresh_approval(root):
    user_gate(root,'E')
    review=rc.rb(root)/'reviews/scientific.md';review.write_text('MOCK review: verified synthetic mean and links for software acceptance only; no actual scientific validation.\n')
    s=rc.read_state(root);s['scientific_review']={'status':'PASS','fingerprint':rc.fingerprint(root),'record_file':str(review.relative_to(root)),'record_sha256':rc.sha(review)};rc.save_state(root,s)
    user_gate(root,'F')

class WorkflowTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=(Path(self.tmp.name)/'project').resolve()
    def tearDown(self):self.tmp.cleanup()
    def test_idea_init_resume_no_overwrite(self):
        rc.init(self.root,'MOCK camera idea','MOCK 我想识别线路舞动',mock=True)
        self.assertEqual(rc.read_state(self.root)['current_phase'],0)
        self.assertFalse(rc.read_state(self.root)['research_type'])
        for p in ['literature/search_protocol.md','literature/MUST_DOWNLOAD_AND_READ.md','design/experiment_matrix.csv']:
            self.assertTrue((rc.rb(self.root)/p).exists())
        with self.assertRaises(FileExistsError):rc.init(self.root,'other','other')
    def test_study_axis_requires_rationale(self):
        rc.init(self.root,'MOCK ML','MOCK camera recognition',['ml-ai','engineering-method'],True)
        with self.assertRaises(ValueError):rc.transition(self.root,1)
        s=rc.read_state(self.root);s['study_type_rationale']='Learned visual model with field-engineering validation';rc.save_state(self.root,s)
        self.assertEqual(rc.transition(self.root,1)['current_phase'],1)
    def test_invalid_type_rejected(self):
        s=rc.init(self.root,'MOCK','MOCK',mock=True);s['research_type']=['unicorn']
        self.assertTrue(rc.state_errors(s))
    def test_missing_evidence_blocks(self):
        rc.init(self.root,'MOCK','MOCK',mock=True)
        self.assertEqual(rc.check(self.root)['status'],'BLOCKED')
    def test_complete_bundle(self):
        fixture(self.root);report=rc.check(self.root)
        self.assertEqual(report['status'],'READY',report['blockers'])
        dest=self.root/'MANUSCRIPT_HANDOFF';rc.package(self.root,dest)
        self.assertFalse((dest/'READY_FOR_NATURE_WRITING.md').exists())
        self.assertTrue((dest/'MOCK_HANDOFF_ONLY.md').exists())
        self.assertEqual(len([p for p in dest.iterdir() if p.name[:2].isdigit()]),18)
        self.assertTrue((dest/'data/mock.csv').exists());self.assertTrue((dest/'code/mock_analysis.py').exists())
        for rel,digest in json.loads((dest/'package_checksums.json').read_text()).items():self.assertEqual(rc.sha(dest/rel),digest)
        with self.assertRaises(FileExistsError):rc.package(self.root,dest)
    def test_central_claim_no_evidence_blocks_even_with_approval(self):
        fixture(self.root);p=rc.rb(self.root)/'execution/claim_registry.yaml';d=yaml.safe_load(p.read_text());d['claims'][0]['supporting_result_ids']=[];p.write_text(yaml.safe_dump(d));refresh_approval(self.root)
        r=rc.check(self.root);self.assertEqual(r['status'],'BLOCKED');self.assertTrue(any('Central claim' in x for x in r['blockers']))
    def test_hash_tampering_blocks(self):
        fixture(self.root);(self.root/'data/mock.csv').write_text('value\n100\n')
        self.assertTrue(any('hash mismatch' in x for x in rc.check(self.root)['blockers']))
    def test_blueprint_immutable(self):
        fixture(self.root);p=rc.rb(self.root)/'RESEARCH_BLUEPRINT_FINAL.md';p.write_text('Changed after results')
        self.assertTrue(any('Frozen blueprint' in x for x in rc.check(self.root)['blockers']))
    def test_stale_refresh(self):
        fixture(self.root);s=rc.read_state(self.root);s['novelty_refresh']['checked_at']='2020-01-01';rc.save_state(self.root,s)
        self.assertTrue(any('Stale' in x for x in rc.check(self.root)['blockers']))
    def test_route_change_invalidates_gate(self):
        fixture(self.root);s=rc.read_state(self.root);s['research_route']='Different';rc.save_state(self.root,s)
        self.assertTrue(any('Gate F' in x for x in rc.check(self.root)['blockers']))
    def test_author_checks_no_central_escape(self):
        fixture(self.root);s=rc.read_state(self.root);s['author_checks']=[{'impact':'CENTRAL','question':'Unknown real sample size'}];rc.save_state(self.root,s)
        self.assertEqual(rc.check(self.root)['status'],'BLOCKED')
    def test_production_rejects_mock(self):
        fixture(self.root);s=rc.read_state(self.root);s['mock']=False;rc.save_state(self.root,s)
        self.assertEqual(rc.check(self.root)['status'],'BLOCKED')
    def test_path_escape(self):
        fixture(self.root)
        with self.assertRaises(ValueError):rc.local(self.root,'../outside.csv')
    def test_conservative_dedup(self):
        data=[{'doi':'https://doi.org/10.mock/abc','title':'MOCK title','year':'2026','authors':'MOCK A','source':'one'},
              {'doi':'10.mock/ABC','title':'MOCK title','year':'2026','authors':'MOCK A','source':'two'},
              {'doi':'10.mock/different','title':'MOCK title','year':'2026','authors':'MOCK A','source':'three'}]
        merged,conflicts=corpus.merge(data);self.assertEqual(len(merged),2);self.assertEqual(len(merged[0]['provenance_records']),2);self.assertTrue(conflicts)
    def test_import_bib_and_ris(self):
        p=Path(self.tmp.name)/'mock.bib';p.write_text('@misc{mock, title={MOCK {Nested} title}, author={Fixture, A}, year={2026}}');self.assertEqual(corpus.read(p)[0]['year'],'2026')
        p=Path(self.tmp.name)/'mock.ris';p.write_text('TY  - JOUR\nTI  - MOCK fixture\nAU  - Fixture, A\nPY  - 2026\nER  - \n');self.assertTrue(corpus.read(p)[0]['title'])
    def test_wos_column_mapping_and_xlsx(self):
        merged,_=corpus.merge([{'TI':'MOCK WoS title','DI':'10.mock/wos','PY':'2026','AU':'Fixture A','UT':'MOCK-001'}])
        self.assertEqual(merged[0]['title'],'MOCK WoS title')
        import openpyxl
        path=Path(self.tmp.name)/'mock.xlsx';book=openpyxl.Workbook();sheet=book.active
        sheet.append(['Title','DOI']);sheet.append(['MOCK Excel title','10.mock/excel']);book.save(path)
        merged,_=corpus.merge(corpus.read(path));self.assertEqual(merged[0]['doi'],'10.mock/excel')
    def test_malformed_claims_blocked(self):
        fixture(self.root);(rc.rb(self.root)/'execution/claim_registry.yaml').write_text('claims: null')
        self.assertEqual(rc.check(self.root)['status'],'BLOCKED')
    def test_manifest_paths(self):
        m=rc.MANIFEST
        paths=m['always_load']+m['templates']+m['scripts']+list(m['axes']['study_type']['values'].values())
        for group in m['phase_routes'].values():paths+=group
        for path in paths:self.assertTrue((rc.SKILL/path).is_file(),path)
        self.assertEqual(set(m['handoff_sources']),{f'{i:02d}' for i in range(1,19)})
if __name__=='__main__':unittest.main(verbosity=2)
