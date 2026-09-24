"""Deterministic project mechanics; scientific conclusions remain the Agent's job."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,shutil,sys,tempfile,uuid
from datetime import datetime,timezone,timedelta
from pathlib import Path
import yaml
SKILL=Path(__file__).resolve().parents[1]
MANIFEST=yaml.safe_load((SKILL/'manifest.yaml').read_text())
GATES={2:'A',4:'B',5:'C',7:'D',9:'E',10:'F'}
STUDIES=set(MANIFEST['axes']['study_type']['values'])
CLAIM_STATES={'SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','UNRESOLVED'}
ASSET_TYPES={'RAW_DATA','PROCESSED_DATA','RESULT_DATA','RAW_PHOTO','EXPERIMENTAL_PHOTO','RAW_VIDEO','MODEL_OUTPUT','SEGMENTATION_OUTPUT','DETECTION_OUTPUT','TRAJECTORY_OUTPUT','PRELIMINARY_PLOT','SCHEMATIC_SOURCE','LITERATURE_FIGURE','ADAPTED_MATERIAL','OTHER'}
# Shared project coordination; stage logic remains local.
import sys as _coord_sys
_coord_sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'workflow-contract'))
import project_contract as _coord

def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=p.parent,delete=False,encoding='utf-8') as f:
        json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n');tmp=Path(f.name)
    tmp.replace(p)
def rb(root):return Path(root).resolve()/'research_blueprint'
def read_state(root):return json.loads((rb(root)/'state.json').read_text())
def save_state(root,s):
    errors=state_errors(s)
    if errors:raise ValueError('; '.join(errors))
    s['updated_at']=now();write_json(rb(root)/'state.json',s)
def state_errors(s):
    required=['project_id','project_title','research_type','current_phase','current_status','target_journal',
              'candidate_journals','research_route','unresolved_blockers','user_decisions','last_literature_search_date',
              'blueprint_freeze_date','experiment_progress','evidence_completeness','handoff_readiness','technical_debts']
    errors=['Missing state field: '+k for k in required if k not in s]
    phase=s.get('current_phase')
    if type(phase)!=int or phase not in range(11):errors.append('Invalid phase')
    if s.get('current_status') not in {'ACTIVE','WAITING_USER','BLOCKED','PAUSED','COMPLETE'}:errors.append('Invalid status')
    if not isinstance(s.get('research_type'),list) or not set(s.get('research_type',[]))<=STUDIES:errors.append('Invalid study_type')
    for key in ['candidate_journals','unresolved_blockers','user_decisions','technical_debts']:
        if not isinstance(s.get(key),list):errors.append('Expected list: '+key)
    if s.get('handoff_readiness') not in {'BLOCKED','READY','READY_WITH_AUTHOR_CHECKS'}:errors.append('Invalid handoff_readiness')
    return errors

def init(root,title,idea,study=None,mock=False):
    root=Path(root).resolve();base=rb(root)
    if base.exists():raise FileExistsError('Research project already exists; resume it')
    root.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SKILL/'templates',base)
    # Final milestone files must not exist before actual freeze/closure.
    (base/'RESEARCH_BLUEPRINT_FINAL.md').unlink()
    for d in ['literature/search_runs','literature/paper_cards','execution/experiment_logs','reviews','frozen']:(base/d).mkdir(parents=True,exist_ok=True)
    for d in ['data','experiments','figures_source','photos','code','papers']:(root/d).mkdir(exist_ok=True)
    s={'schema_version':1,'project_id':uuid.uuid4().hex,'project_title':title,'idea':idea,
       'research_type':study or [],'study_type_rationale':None,'study_type_confidence':None,
       'current_phase':0,'current_status':'ACTIVE','target_journal':None,'candidate_journals':[],
       'research_route':None,'unresolved_blockers':[],'user_decisions':[],
       'last_literature_search_date':None,'blueprint_freeze_date':None,'experiment_progress':{},
       'evidence_completeness':{},'handoff_readiness':'BLOCKED','technical_debts':[],
       'next_actions':['Classify study by evidence logic and build search protocol'],
       'mock':bool(mock),'revision':0,'blueprint_sha256':None,'freeze_manifest':{},
       'novelty_refresh':None,'journal_refresh':None,'scientific_review':None,
       'author_checks':[],'created_at':now()}
    save_state(root,s);return s

def local(root,value):
    p=Path(value)
    if not value or p.is_absolute() or '..' in p.parts:raise ValueError('Expected project-relative path: '+str(value))
    root=Path(root).resolve();target=(root/p).resolve()
    if not target.is_relative_to(root) or not target.is_file():raise ValueError('Missing/external file: '+value)
    return target

def completed(p):
    s=Path(p).read_text(encoding='utf-8')
    return len(s.strip())>=20 and not re.search(r'\[TO_COMPLETE\]|Status: UNFILLED|status: UNFILLED|\bPLACEHOLDER\b',s,re.I)
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def require_file(root,path,errors,label=None):
    try:
        p=local(root,path)
        if p.stat().st_size==0:raise ValueError('Empty file: '+path)
        return p
    except (ValueError,TypeError,OSError) as e:errors.append((label+': ' if label else '')+str(e));return None

def fingerprint(root):
    base=rb(root);h=hashlib.sha256()
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.name in {'state.json','decision_log.md','readiness.json'} or 'reviews' in p.relative_to(base).parts:continue
        h.update(str(p.relative_to(base)).encode());h.update(p.read_bytes())
    state=read_state(root)
    h.update(json.dumps({k:state.get(k) for k in ['research_route','target_journal','research_type']},sort_keys=True,ensure_ascii=False).encode())
    return h.hexdigest()

def approve(root,gate,choice,record):
    s=read_state(root);p=local(root,record)
    if not completed(p):raise ValueError('Approval record must contain actual user decision, not empty template')
    entry={'gate':gate,'choice':choice,'record':record,'record_sha256':sha(p),'approved_at':now(),
           'approved_by':'user','fingerprint':fingerprint(root)}
    s['user_decisions'].append(entry);s['revision']+=1
    with (rb(root)/'decision_log.md').open('a') as f:f.write('\n'+json.dumps(entry,ensure_ascii=False)+'\n')
    save_state(root,s);return entry

def gate_ok(root,s,gate,fresh=False):
    entries=[d for d in s['user_decisions'] if d.get('gate')==gate and d.get('approved_by') in {'user','agent_auto'}]
    if not entries:return False
    d=entries[-1]
    try:valid=sha(local(root,d['record']))==d['record_sha256']
    except (ValueError,KeyError):return False
    return valid and (not fresh or d.get('fingerprint')==fingerprint(root))

def transition(root,phase):
    s=read_state(root)
    if phase!=s['current_phase']+1:raise ValueError('Sequential transition required; reopening requires a documented state amendment')
    if phase in GATES and not gate_ok(root,s,GATES[phase]):raise ValueError('User Gate '+GATES[phase]+' required')
    if phase==1 and (not s['research_type'] or not s['study_type_rationale']):raise ValueError('Study type and rationale required')
    if phase==5 and (not s['research_route'] or not s['target_journal']):raise ValueError('Selected route and journal/target-agnostic required')
    if phase==7 and not s['blueprint_freeze_date']:raise ValueError('Freeze blueprint first')
    if phase==10:
        r=check(root)
        if r['status']=='BLOCKED':raise ValueError('; '.join(r['blockers']))
    s['current_phase']=phase;s['revision']+=1;save_state(root,s);return s

def freeze(root,source):
    s=read_state(root);base=rb(root)
    if s['current_phase']!=6 or not gate_ok(root,s,'D',fresh=True):raise ValueError('Current Gate D approval at phase 6 required')
    dest=base/'RESEARCH_BLUEPRINT_FINAL.md'
    if dest.exists():raise FileExistsError('Blueprint immutable; log deviation, never overwrite')
    p=local(root,source)
    if not completed(p):raise ValueError('Blueprint draft incomplete')
    for f in (base/'design').glob('*.md'):
        if not completed(f):raise ValueError('Design document incomplete: '+f.name)
    shutil.copy2(p,dest)
    snap=base/'frozen'/'v1';snap.mkdir()
    for name in ['design','literature']:
        shutil.copytree(base/name,snap/name)
    shutil.copy2(dest,snap/dest.name)
    s['blueprint_freeze_date']=now();s['blueprint_sha256']=sha(dest)
    s['freeze_manifest']={str(p.relative_to(base)):sha(p) for p in snap.rglob('*') if p.is_file()}
    save_state(root,s);return s

def _date(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d

def _check(root,max_age_days=30):
    root=Path(root).resolve();base=rb(root);s=read_state(root);errors=state_errors(s)
    if s.get('current_phase',0)<9:errors.append('Research not at final refresh/closure phase')
    if not s.get('research_route'):errors.append('Research route absent')
    if not s.get('target_journal'):errors.append('Journal or explicit target-agnostic absent')
    errors.extend('Unresolved blocker: '+str(x) for x in s.get('unresolved_blockers',[]))
    for g in 'ABCDE':
        if not gate_ok(root,s,g):errors.append('Missing/invalid user Gate '+g)
    if not gate_ok(root,s,'F',fresh=True):errors.append('Gate F must approve current evidence fingerprint')
    try:
        if not s['blueprint_freeze_date'] or sha(base/'RESEARCH_BLUEPRINT_FINAL.md')!=s['blueprint_sha256']:errors.append('Frozen blueprint absent/changed')
        for path,digest in s.get('freeze_manifest',{}).items():
            if sha(base/path)!=digest:errors.append('Frozen snapshot changed: '+path)
        if not s.get('freeze_manifest'):errors.append('Freeze manifest absent')
    except (OSError,KeyError):errors.append('Frozen blueprint unavailable')
    for key in ['novelty_refresh','journal_refresh']:
        r=s.get(key) or {}
        try:
            checked=_date(r['checked_at']);freeze_date=_date(s['blueprint_freeze_date'])
            if checked<freeze_date or checked>datetime.now(timezone.utc)+timedelta(minutes=5) or datetime.now(timezone.utc)-checked>timedelta(days=max_age_days):errors.append('Stale/invalid '+key)
            if r.get('status')!='COMPLETE':errors.append('Incomplete '+key)
            p=require_file(root,r.get('record_file',''),errors,key)
            if p and not completed(p):errors.append('Unfilled '+key+' record')
            if key=='novelty_refresh':
                if not r.get('search_run_files'):errors.append('Novelty refresh lacks actual searches')
                for run in r.get('search_run_files',[]):
                    q=require_file(root,run,errors,'novelty search')
                    if q:
                        d=json.loads(q.read_text())
                        if d.get('status')!='SEARCHED' or not d.get('exact_query') or _date(d['date'])<freeze_date:errors.append('Invalid novelty search evidence')
        except (ValueError,KeyError,TypeError):errors.append('Missing/invalid date or record: '+key)
    # Validate schema headers independently from row count; empty templates cannot
    # silently discard scientific fields during imports.
    for rel in ['execution/results_facts.csv','execution/asset_inventory.csv','design/experiment_matrix.csv','literature/reference_verification.csv','handoff/09_claim_reference_map.csv']:
        with (SKILL/'templates'/rel).open(newline='') as f: expected=next(csv.reader(f))
        with (base/rel).open(newline='') as f: actual=next(csv.reader(f),[])
        for column in expected:
            if column not in actual: errors.append('Missing schema column '+rel+': '+column)
    # Required facts and milestone prose must be filled; structure is not truth.
    mapped=list(MANIFEST['handoff_sources'].values())+['RESEARCH_DOSSIER_FINAL.md','execution/limitations_and_boundaries.md']
    for rel in mapped:
        p=base/rel
        if not p.is_file():errors.append('Missing handoff input: '+rel)
        elif p.suffix=='.md' and not completed(p):errors.append('Unfilled handoff input: '+rel)
    for rel in ['05_methods_fact_sheet.yaml','06_data_fact_sheet.yaml','07_statistics_fact_sheet.yaml','15_terminology_ledger.yaml']:
        try:
            d=yaml.safe_load((base/'handoff'/rel).read_text())
            template=yaml.safe_load((SKILL/'templates/handoff'/rel).read_text())
            if d.get('status')!='ACTUAL':errors.append('Fact sheet not ACTUAL: '+rel)
            for k in template['facts']:
                val=d.get('facts',{}).get(k)
                if val is None or val=='' or val==[]:errors.append('Missing fact '+rel+': '+k)
            if not d.get('source_files'):errors.append('Untraceable facts: '+rel)
            for f in d.get('source_files',[]):require_file(root,f,errors,rel)
        except (OSError,TypeError,AttributeError,yaml.YAMLError):errors.append('Malformed fact sheet: '+rel)
    results=rows(base/'execution/results_facts.csv');resultmap={};expids={r['experiment_id'] for r in rows(base/'design/experiment_matrix.csv')}
    for r in results:
        rid=r.get('result_id','')
        if not rid or rid in resultmap:errors.append('Empty/duplicate result ID: '+rid)
        resultmap[rid]=r
        if r.get('status')!='ACTUAL':errors.append('Result not ACTUAL: '+rid)
        if r.get('experiment_id') not in expids:errors.append('Unknown experiment: '+rid)
        for k in ['metric','value','unit','sample_size','uncertainty','ci','p_value','repeats','seed','analysis_type']:
            if not r.get(k):errors.append('Missing '+k+' for '+rid+' (use reasoned N/A where appropriate)')
        if r.get('kind')=='numeric':
            try:
                if not math.isfinite(float(r['value'])):raise ValueError()
            except (ValueError,KeyError):errors.append('Non-numeric/nonfinite result: '+rid)
        elif r.get('kind')!='synthesis':errors.append('Unknown result kind: '+rid)
        if r.get('analysis_type') not in {'PLANNED','EXPLORATORY','POST_HOC'}:errors.append('Invalid analysis type: '+rid)
        for field,hfield in [('source_file','source_sha256'),('analysis_script','analysis_sha256')]:
            p=require_file(root,r.get(field,''),errors,rid)
            if p and sha(p)!=r.get(hfield):errors.append('Evidence hash mismatch: '+rid+' '+field)
    if not results:errors.append('No actual results/synthesis records')
    try:claims=yaml.safe_load((base/'execution/claim_registry.yaml').read_text())['claims']
    except (KeyError,TypeError,yaml.YAMLError):claims=[];errors.append('Malformed claim registry')
    cids=set();central=[]
    required=['claim','importance','supporting_experiments','supporting_result_ids','supporting_literature','evidence_strength','alternative_explanations','boundary_conditions','allowed_wording','forbidden_overclaim','status']
    for c in claims:
        cid=c.get('claim_id','')
        if not cid or cid in cids:errors.append('Duplicate/empty claim ID')
        cids.add(cid)
        for k in required:
            if k not in c:errors.append('Missing claim field '+cid+': '+k)
        if c.get('status') not in CLAIM_STATES:errors.append('Invalid claim status '+cid)
        if c.get('importance')=='CENTRAL':central.append(c)
        for rid in c.get('supporting_result_ids',[]):
            if rid not in resultmap:errors.append('Unknown result for '+cid+': '+rid)
            elif resultmap[rid]['experiment_id'] not in c.get('supporting_experiments',[]):errors.append('Claim experiment/result mismatch: '+cid)
        if c.get('importance')=='CENTRAL' and (c.get('status')!='SUPPORTED' or not c.get('supporting_result_ids')):errors.append('Central claim lacks supported actual evidence: '+cid)
        for field in ['allowed_wording','forbidden_overclaim','boundary_conditions','alternative_explanations']:
            if not c.get(field):errors.append('Claim missing boundary: '+cid+' '+field)
    if not central:errors.append('No bounded central claim')
    refs=rows(base/'literature/reference_verification.csv');refmap={r.get('reference_id'):r for r in refs}
    bib=(base/'literature/references.bib').read_text()
    if not refs or not re.search(r'@\w+\s*[{(]',bib):errors.append('No verified bibliography')
    for r in refs:
        if r.get('status')!='VERIFIED':errors.append('Unverified important reference: '+str(r.get('reference_id')))
        for k in ['authors','title','year','journal','publication_status','sources','checked_at']:
            if not r.get(k):errors.append('Incomplete reference metadata: '+k)
        require_file(root,r.get('record_file',''),errors,'reference verification')
        if not re.search(r'@\w+\s*[{(]\s*'+re.escape(r.get('reference_id',''))+r'\s*,',bib):errors.append('Reference key absent from bibliography')
    for c in claims:
        for ref in c.get('supporting_literature',[]):
            if ref not in refmap:errors.append('Unknown supporting reference: '+ref)
    for r in rows(base/'handoff/09_claim_reference_map.csv'):
        if r.get('reference_id') not in refmap:errors.append('Unverified claim-reference map entry')
    assets=rows(base/'execution/asset_inventory.csv');aids=set()
    if not assets:errors.append('No evidence asset inventory')
    for a in assets:
        aid=a.get('asset_id','')
        if not aid or aid in aids:errors.append('Duplicate/empty asset ID')
        aids.add(aid)
        if a.get('type') not in ASSET_TYPES:errors.append('Invalid asset type '+aid)
        for k in ['provenance','source','date','what_it_shows','processing_history','quality']:
            if not a.get(k):errors.append('Missing asset provenance: '+aid+' '+k)
        if a.get('publication_permission') not in {'OWNED','LICENSED','PERMISSION_GRANTED','PUBLIC_DOMAIN'}:errors.append('Unresolved asset permission: '+aid)
        p=require_file(root,a.get('path',''),errors,aid)
        if p and sha(p)!=a.get('sha256'):errors.append('Asset hash mismatch: '+aid)
    audit=s.get('scientific_review') or {}
    if audit.get('status')!='PASS' or audit.get('fingerprint')!=fingerprint(root):errors.append('Current source-grounded scientific review required')
    review_file=require_file(root,audit.get('record_file',''),errors,'scientific review')
    if review_file and (not completed(review_file) or sha(review_file)!=audit.get('record_sha256')):errors.append('Scientific review record missing, unfilled or changed')
    for a in s.get('author_checks',[]):
        if not isinstance(a,dict) or a.get('impact')!='NONCENTRAL' or not a.get('question'):errors.append('Author check cannot conceal a central blocker')
    # MOCK is an explicit test lane; cannot produce production readiness.
    mock=s.get('mock',False)
    if not mock:
        for p in base.rglob('*'):
            if p.is_file() and p.suffix in {'.md','.json','.yaml','.csv','.bib'}:
                if re.search(r'\b(?:MOCK|FIXTURE)\b',p.read_text(errors='replace')):errors.append('Fixture marker in production project: '+str(p.relative_to(base)))
    status='BLOCKED' if errors else ('READY_WITH_AUTHOR_CHECKS' if s.get('author_checks') else 'READY')
    return {'status':status,'test_only':mock,'production_ready':not mock and status!='BLOCKED','blockers':sorted(set(errors)),
            'checked_at':now(),'fingerprint':fingerprint(root),'author_checks':s.get('author_checks',[])}

def check(root,max_age_days=30):
    try:return _check(root,max_age_days)
    except (ValueError,KeyError,TypeError,AttributeError,OSError,yaml.YAMLError) as e:
        return {'status':'BLOCKED','production_ready':False,'test_only':False,
                'blockers':['Malformed or missing evidence/state: '+str(e)],'checked_at':now()}

def package(root,destination):
    root=Path(root).resolve();dest=Path(destination).resolve()
    if dest.exists():raise FileExistsError('Use a fresh versioned handoff destination')
    # Prevent recursive package copy.
    if dest.is_relative_to(rb(root)):raise ValueError('Package outside research_blueprint; use PROJECT/MANUSCRIPT_HANDOFF')
    result=check(root)
    if result['status']=='BLOCKED':return result
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.handoff-',dir=dest.parent))
    try:
        base=rb(root)
        # Copy the complete factual record preserving project-relative paths.
        for p in base.rglob('*'):
            if p.is_file():
                target=local(root,str(p.relative_to(root)))
                out=stage/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,out)
        referenced=[]
        for r in rows(base/'execution/results_facts.csv'):referenced += [r['source_file'],r['analysis_script']]
        for a in rows(base/'execution/asset_inventory.csv'):referenced.append(a['path'])
        for r in rows(base/'literature/reference_verification.csv'):referenced.append(r['record_file'])
        for n in ['05_methods_fact_sheet.yaml','06_data_fact_sheet.yaml','07_statistics_fact_sheet.yaml','15_terminology_ledger.yaml']:
            referenced+=yaml.safe_load((base/'handoff'/n).read_text())['source_files']
        for path in set(referenced):
            p=local(root,path);out=stage/path;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        from literature_evidence import export as export_literature_evidence
        export_literature_evidence(root,base,stage)
        aliases={'03':'03_claim_registry.yaml','04':'04_results_facts.csv','11':'11_asset_inventory.csv'}
        for number,rel in MANIFEST['handoff_sources'].items():shutil.copy2(base/rel,stage/aliases.get(number,Path(rel).name))
        shutil.copy2(base/'literature/references.bib',stage/'references.bib')
        write_json(stage/'readiness.json',result)
        (stage/'README.md').write_text('# MANUSCRIPT_HANDOFF_PACKAGE\n\n'+('MOCK / FIXTURE: not for scientific writing.\n' if result['test_only'] else '')+
            'Read readiness.json, actual claims/results, fact sheets, canon/references, assets and limitations.\n'
            'All structured source paths resolve from this package root. research_blueprint/ contains protocol, history and evidence.\n'
            'manuscript-writing owns Stage 2 Manuscript Blueprint, narrative order, figure/table numbering and main/SI allocation; nature-writing is its prose engine.\n'
            'Inventories and Paper Cards are DISCOVERY / NAVIGATION LAYER, not authoritative evidence.\n'
            'Paper Card tells us WHERE TO LOOK. Original Paper tells us WHAT IS TRUE.\n'
            'At actual use of a figure/panel/table/formula/number/complex claim, Stage 2 must reopen the original for TARGETED SOURCE VERIFICATION: original figure/table, caption, surrounding text, context, original claim, limitations and exact meaning.\n'
            'literature_assets contains INTERNAL RESEARCH / MANUSCRIPT PLANNING ASSETS, not publication-ready or permission-cleared reproductions. Candidate importance and POSSIBLE use modes are not final manuscript decisions.\n'
            'No manuscript prose has been generated. Recheck evidence before making claims.\n')
        marker='MOCK_HANDOFF_ONLY.md' if result['test_only'] else 'READY_FOR_NATURE_WRITING.md'
        (stage/marker).write_text(result['status']+'\n'+('MOCK validation only.\n' if result['test_only'] else 'Approved actual-evidence handoff; read readiness.json and listed author checks.\n'))
        write_json(stage/'package_checksums.json',{str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()})
        stage.rename(dest)
        state=read_state(root);state['handoff_readiness']=result['status']
        state['current_phase']=10;state['current_status']='COMPLETE'
        state['next_actions']=['Read handoff package in manuscript-writing when the user requests manuscript writing']
        state['evidence_completeness']={'structural_check':'PASS','fingerprint':result['fingerprint']}
        state['last_handoff']={'path':str(dest),'test_only':result['test_only'],'created_at':now()}
        save_state(root,state)
    except Exception:
        shutil.rmtree(stage);raise
    return result

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    for cmd in ['init','state','approve','transition','freeze','fingerprint','check','package']:
        q=sub.add_parser(cmd);q.add_argument('project')
        if cmd=='init':q.add_argument('--title',required=True);q.add_argument('--idea',required=True);q.add_argument('--study-type',action='append',choices=sorted(STUDIES));q.add_argument('--mock',action='store_true')
        if cmd=='approve':q.add_argument('--gate',choices=list('ABCDEF'),required=True);q.add_argument('--choice',required=True);q.add_argument('--record',required=True)
        if cmd=='transition':q.add_argument('--phase',type=int,required=True)
        if cmd=='freeze':q.add_argument('--source',required=True)
        if cmd=='package':q.add_argument('--output',required=True)
    a=p.parse_args()
    try:
        if a.cmd!='init':_coord.enter(a.project,'research_planning',a.cmd=='package')
        if a.cmd=='init':r=init(a.project,a.title,a.idea,a.study_type,a.mock)
        elif a.cmd=='state':
            r=read_state(a.project)
            if state_errors(r):raise ValueError('; '.join(state_errors(r)))
        elif a.cmd=='approve':r=approve(a.project,a.gate,a.choice,a.record)
        elif a.cmd=='transition':r=transition(a.project,a.phase)
        elif a.cmd=='freeze':r=freeze(a.project,a.source)
        elif a.cmd=='fingerprint':r={'fingerprint':fingerprint(a.project)}
        elif a.cmd=='check':r=check(a.project)
        else:r=package(a.project,a.output)
        if a.cmd=='init':_coord.enter(a.project,'research_planning')
        if a.cmd=='package':_coord.completed(a.project,'research_planning',Path(a.output)/'readiness.json',{'manuscript_handoff':Path(a.output)})
        if a.cmd=='approve':_coord.record_decision(a.project,'research_planning',r)
        print(json.dumps(r,ensure_ascii=False,indent=2))
        return 2 if r.get('status')=='BLOCKED' else 0
    except (ValueError,FileExistsError,FileNotFoundError,KeyError,TypeError) as e:
        print(json.dumps({'status':'ERROR','error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':sys.exit(main())
