"""Small project coordination contract. No research, writing, review or TeX orchestration."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
import argparse,collections,csv,fcntl,hashlib,json,os,re,tempfile,uuid
import yaml
from jsonschema import Draft202012Validator
_SCHEMA_VALIDATOR=Draft202012Validator(json.loads(Path(__file__).with_name("project_manifest.schema.json").read_text()))
STAGES=['research_planning','manuscript_writing','manuscript_review','publication_build']
OWNERS={'research_blueprint':0,'research_dossier':0,'manuscript_handoff':0,'manuscript_draft':1,'reviewed_manuscript':2,'publication_package':3}
CANONICAL={'research_blueprint':['research_blueprint/RESEARCH_BLUEPRINT_FINAL.md','RESEARCH_BLUEPRINT_FINAL.md'], 'research_dossier':['research_blueprint/RESEARCH_DOSSIER_FINAL.md','RESEARCH_DOSSIER_FINAL.md'], 'manuscript_handoff':['MANUSCRIPT_HANDOFF'], 'manuscript_draft':['manuscript/manuscript.md','manuscript.md'], 'reviewed_manuscript':['review/reviewed_manuscript.md','reviewed_manuscript.md'], 'publication_package':['publication/submission_source.zip','submission_source.zip']}
TYPES={'DATA','RESULT','CLAIM','METHOD','REFERENCE','ASSET','FIGURE','TABLE','JOURNAL','TEXT_ONLY'}
STATES={'NOT_STARTED','IN_PROGRESS','READY','STALE','BLOCKED'}
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stable(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def inside(root,relative,exists=True):
 p=Path(relative)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Project-relative path required: '+str(p))
 q=(Path(root)/p).resolve()
 if not q.is_relative_to(Path(root).resolve()) or (exists and not q.exists()):raise ValueError('Missing/external canonical: '+str(p))
 return q
def fingerprint(root,path):
 p=inside(root,path)
 if p.is_file():return sha(p)
 # Content package, excluding volatile operational artifacts; object hashes remain available.
 ignore={'state.json','project_manifest.yaml','change_log.md','readiness.json','checksums.json','package_checksums.json'}
 return stable({x.relative_to(p).as_posix():sha(x) for x in sorted(p.rglob('*')) if x.is_file() and not x.is_symlink() and x.name not in ignore and not any(z in ['.git','__pycache__','logs','preview','previews','evidence'] for z in x.relative_to(p).parts)})
def locate(path):
 p=Path(path).resolve();p=p if p.is_dir() else p.parent
 for d in [p,*p.parents]:
  if (d/'project_manifest.yaml').is_file():return d
 return None
def load(root):return yaml.safe_load((Path(root)/'project_manifest.yaml').read_text())
def validate(m,root=None):
 errors=list(_SCHEMA_VALIDATOR.iter_errors(m))
 if errors:raise ValueError("Manifest schema: "+errors[0].message)
 required=['workflow_version','project_id','project_title','study_type','current_stage','target_journal','created_at','updated_at','canonical_outputs','stage_status','stage_revision','staleness','open_blockers','author_decisions','last_major_change','completion','freshness','input_revision','output_revision','objects','changes','revalidation_requests']
 for k in required:
  if k not in m:raise ValueError('Missing manifest field '+k)
 if m['workflow_version']!='1.1':raise ValueError('Unsupported workflow version')
 if m['current_stage'] not in STAGES:raise ValueError('Invalid current stage')
 for s in STAGES:
  if m['stage_status'].get(s) not in STATES or m['completion'].get(s) not in STATES:raise ValueError('Invalid stage status')
  if type(m['stage_revision'].get(s)) is not int or m['stage_revision'][s]<0:raise ValueError('Invalid revision')
 for k,v in m['canonical_outputs'].items():
  if k not in OWNERS:raise ValueError('Unknown canonical output '+k)
  if v:
   if root:inside(root,v['path'])
   if v.get('owner')!=STAGES[OWNERS[k]]:raise ValueError('Canonical owner mismatch')
 for oid,o in m['objects'].items():
  if o['stage'] not in STAGES or not isinstance(o.get('depends_on',[]),list):raise ValueError('Bad object '+oid)
  if root and o.get('path'):inside(root,o['path'])
 return True
def atomic(p,text):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(mode='w',dir=p.parent,delete=False,encoding='utf-8') as f:f.write(text);tmp=Path(f.name)
 tmp.replace(p)
def save(root,m):
 validate(m);m['updated_at']=now();atomic(Path(root)/'project_manifest.yaml',yaml.safe_dump(m,allow_unicode=True,sort_keys=False))
 # Manifest change entries are authoritative; Markdown is a recoverable projection.
 atomic(Path(root)/'change_log.md','# Change log\n\n'+''.join('## '+e['change_id']+'\n\n```yaml\n'+yaml.safe_dump(e,allow_unicode=True,sort_keys=False)+'```\n\n' for e in m['changes']))
@contextmanager
def edit(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 with (root/'.project_manifest.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);m=load(root);validate(m)
  yield m
  save(root,m)
def init(root,stage,title=None):
 root=Path(root).resolve();found=locate(root)
 if found:return found
 root.mkdir(parents=True,exist_ok=True)
 m={'workflow_version':'1.1','project_id':str(uuid.uuid4()),'project_title':title or root.name,'study_type':'UNKNOWN','current_stage':stage,'target_journal':None,'created_at':now(),'updated_at':now(),'canonical_outputs':{k:None for k in OWNERS},'stage_status':{s:'NOT_STARTED' for s in STAGES},'completion':{s:'NOT_STARTED' for s in STAGES},'freshness':{s:'NEEDS_CHECK' for s in STAGES},'stage_revision':{s:0 for s in STAGES},'staleness':{s:[] for s in STAGES},'input_revision':{s:{} for s in STAGES},'output_revision':{},'open_blockers':[],'author_decisions':[],'last_major_change':None,'objects':{},'changes':[],'revalidation_requests':[],'legacy_recovery':[]}
 for k,paths in CANONICAL.items():
  found=[p for p in paths if (root/p).exists()]
  if not found:
   # Imported canonical snapshots are valid legacy evidence when original stage directories
   # were not supplied; retain NEEDS_CHECK and do not invent their earlier revisions.
   fallback={'manuscript_handoff':['manuscript/inputs/handoff','inputs/handoff','review/inputs/handoff'], 'manuscript_draft':['review/input_snapshot/manuscript.md','input_snapshot/manuscript.md'], 'reviewed_manuscript':['publication/canonical/reviewed_manuscript.md','canonical/reviewed_manuscript.md']}
   for candidate in fallback.get(k,[]):
    if (root/candidate).exists():found=[candidate];break
  if len(found)==1:
   p=found[0];s=STAGES[OWNERS[k]];m['canonical_outputs'][k]={'path':p,'owner':s,'fingerprint':fingerprint(root,p)};m['output_revision'][k]=1;m['stage_revision'][s]=1;m['completion'][s]='IN_PROGRESS';m['stage_status'][s]='IN_PROGRESS'
   m['legacy_recovery'].append({'output':k,'status':'NEEDS_CHECK','reason':'File existence is not evidence of a completed stage'})
  elif found:m['legacy_recovery'].append({'output':k,'status':'NEEDS_CHECK','candidates':found})
 # Recover READY only from explicit readiness alongside matching canonical, not file names alone.
 markers={1:('checks/readiness.json','MANUSCRIPT_DRAFT_READY'),2:('qa/readiness.json','REVIEWED_MANUSCRIPT_READY')}
 for idx,key in [(1,'manuscript_draft'),(2,'reviewed_manuscript')]:
  out=m['canonical_outputs'][key]
  if out:
   base=(root/out['path']).parent;rel,expected=markers[idx];p=base/rel
   if not p.is_file() and idx==2:p=base/'readiness.json'
   if p.is_file():
    try:ready=json.loads(p.read_text())
    except ValueError:continue
    if ready.get('status')==expected:m['completion'][STAGES[idx]]='READY';m['stage_status'][STAGES[idx]]='READY'
 # Provenance of historical input revisions is unknown: retain freshness NEEDS_CHECK.
 with (root/'.project_manifest.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if not (root/'project_manifest.yaml').exists():save(root,m)
 return root

def stale(m,stage,change):
 if change not in m['staleness'][stage]:m['staleness'][stage].append(change)
 m['freshness'][stage]='STALE'
 if m['completion'][stage]!='NOT_STARTED':m['stage_status'][stage]='STALE'
def impact(m,ids):
 seen=set(ids);todo=list(ids);found=[]
 while todo:
  cur=todo.pop()
  for oid,o in m['objects'].items():
   if cur in o.get('depends_on',[]) and oid not in seen:
    seen.add(oid);todo.append(oid);found.append({'object_id':oid,'stage':o['stage'],'path':o.get('path'),'locator':o.get('locator')})
 return found

def object_fingerprint(root,path,locator=None):
 p=inside(root,path)
 # Optional stable row locator: changing one result does not change every row fingerprint.
 if p.suffix.lower()=='.csv' and isinstance(locator,str) and '=' in locator:
  column,value=locator.split('=',1)
  with p.open(encoding='utf-8-sig',newline='') as f:rows=[r for r in csv.DictReader(f) if r.get(column)==value]
  if len(rows)!=1:raise ValueError('Object row missing or ambiguous: '+locator)
  return stable(rows[0])
 return fingerprint(root,path)

def register(root,stage,oid,path,kind,depends_on=None,locator=None):
 with edit(root) as m:
  if oid in m['objects'] and m['objects'][oid]['stage']!=stage:raise ValueError('Cannot replace another stage object')
  if oid in m['objects'] and object_fingerprint(root,path,locator)!=m['objects'][oid]['fingerprint']:raise ValueError('Use change to record revisions before registering changed objects')
  inside(root,path);m['objects'][oid]={'stage':stage,'path':path,'kind':kind,'depends_on':depends_on or [],'locator':locator,'fingerprint':object_fingerprint(root,path,locator),'revision':m['objects'].get(oid,{}).get('revision',1)}
 return oid

def apply_change(m,root,stage,ids,kind,reason,technical=False,interpretation=False,detected=False):
 if kind not in TYPES or not reason.strip():raise ValueError('Change type and reason required')
 if stage=='publication_build' and (kind not in {'JOURNAL','ASSET','FIGURE','TABLE'} or (kind!='JOURNAL' and not technical)):
  raise ValueError('CONTENT_REVISION_REQUIRED: Stage 4 must return to Stage 3')
 for oid in ids:
  if oid not in m['objects']:raise ValueError('Register stable object ID before change: '+oid)
  if m['objects'][oid]['stage']!=stage:raise ValueError('Only owner may revise object '+oid)
 if technical and not reason.strip():raise ValueError('Technical classification needs evidence')
 old=m['stage_revision'][stage];m['stage_revision'][stage]+=1;cid='CHANGE_'+str(len(m['changes'])+1).zfill(5)
 affected=impact(m,ids);down=STAGES[STAGES.index(stage)+1:]
 if technical:down=['publication_build'] if stage!='publication_build' else []
 # Planning blueprint alone is not an actual-fact update; agent can narrow impact after inspection.
 for dest in down:stale(m,dest,cid)
 if interpretation and stage=='manuscript_review':m['revalidation_requests'].append({'stage':'manuscript_writing','change_id':cid,'reason':reason,'status':'NEEDS_CHECK','objects':ids})
 for oid in ids:
  o=m['objects'][oid];o['revision']+=1;o['fingerprint']=object_fingerprint(root,o['path'],o.get('locator'))
 e={'change_id':cid,'timestamp':now(),'source_stage':stage,'changed_object':ids,'old_revision':old,'new_revision':old+1,'change_type':kind,'technical_only':technical,'affected_downstream':down,'affected_items':affected,'severity':'TECHNICAL' if technical else 'SCIENTIFIC_CHECK_REQUIRED','revalidation_required':True,'reason':reason,'status':'IMPACT_ANALYSIS_REQUIRED','detected_by_hash':detected,'strategy':'TARGETED_REVALIDATION','unmapped_dependencies':not bool(affected)}
 m['changes'].append(e);m['last_major_change']=cid
 return e

def change(root,stage,ids,kind,reason,technical=False,interpretation=False):
 with edit(root) as m:e=apply_change(m,root,stage,ids,kind,reason,technical,interpretation)
 return e

def observed(root,path,locator=None):
 try:return object_fingerprint(root,path,locator)
 except ValueError:return 'MISSING_OR_EXTERNAL'

def detect(root,stage):
 with edit(root) as m:
  events=[]
  # Any stage may detect upstream drift; it can mark downstream stale but cannot update upstream revisions.
  for oid,o in m['objects'].items():
   current=observed(root,o['path'],o.get('locator'))
   if current!=o['fingerprint']:
    token=stable([oid,current])
    if any(e.get('detection_token')==token for e in m['changes']):continue
    cid='CHANGE_'+str(len(m['changes'])+1).zfill(5);owner=o['stage'];down=STAGES[STAGES.index(owner)+1:]
    for dest in down:stale(m,dest,cid)
    if owner==stage:stale(m,stage,cid)
    e={'change_id':cid,'timestamp':now(),'source_stage':owner,'changed_object':[oid],'old_revision':o['revision'],'new_revision':'PENDING_OWNER_SYNC','change_type':o['kind'],'affected_downstream':down,'affected_items':impact(m,[oid]),'severity':'UNCLASSIFIED','revalidation_required':True,'status':'IMPACT_ANALYSIS_REQUIRED','strategy':'TARGETED_REVALIDATION','detection_token':token,'reason':'Hash drift: owner must classify technical/scientific impact; no automatic rewriting'}
    m['changes'].append(e);events.append(e)
  for key,o in m['canonical_outputs'].items():
   if not o:continue
   if observed(root,o['path'])!=o['fingerprint']:
    token=stable([key,observed(root,o['path'])])
    if any(e.get('detection_token')==token for e in m['changes']):continue
    owner=o['owner'];cid='CHANGE_'+str(len(m['changes'])+1).zfill(5);down=STAGES[STAGES.index(owner)+1:]
    for dest in down:stale(m,dest,cid)
    if owner==stage:stale(m,stage,cid)
    e={'change_id':cid,'timestamp':now(),'source_stage':owner,'changed_object':[key],'old_revision':m['output_revision'].get(key,0),'new_revision':'PENDING_OWNER_SYNC','change_type':'TEXT_ONLY' if key in ['manuscript_draft','reviewed_manuscript'] else 'DATA','affected_downstream':down,'affected_items':impact(m,[key]),'severity':'UNCLASSIFIED','revalidation_required':True,'status':'IMPACT_ANALYSIS_REQUIRED','strategy':'TARGETED_REVALIDATION','detection_token':token,'reason':'Canonical content changed; classify impact by IDs; do not regenerate whole manuscript'}
    m['changes'].append(e);events.append(e)
 return events

def consume(root,stage):
 detect(root,stage)
 with edit(root) as m:
  m['current_stage']=stage;m['input_revision'][stage]={k:m['output_revision'].get(k,0) for k,v in m['canonical_outputs'].items() if v and OWNERS[k]<STAGES.index(stage)}
  m.setdefault('input_fingerprints',{})[stage]={k:fingerprint(root,v['path']) for k,v in m['canonical_outputs'].items() if v and OWNERS[k]<STAGES.index(stage)}
  if m['completion'][stage]=='NOT_STARTED':m['completion'][stage]='IN_PROGRESS';m['stage_status'][stage]='IN_PROGRESS'
 return load(root)
def revalidate(root,stage,change_id,report):
 p=inside(root,report);r=yaml.safe_load(p.read_text())
 if r.get('status')!='PASS' or not r.get('reviewer') or not r.get('observations') or not r.get('checked_objects'):raise ValueError('Actual targeted revalidation evidence required')
 with edit(root) as m:
  e=next(x for x in m['changes'] if x['change_id']==change_id)
  expected=[x['object_id'] for x in e.get('affected_items',[]) if x['stage']==stage]
  if not set(expected).issubset(r['checked_objects']):raise ValueError('Report omits affected objects')
  hashes={oid:object_fingerprint(root,m['objects'][oid]['path'],m['objects'][oid].get('locator')) for oid in r['checked_objects'] if oid in m['objects']}
  if r.get('fingerprints')!=hashes:raise ValueError('Revalidation hashes missing or stale')
  m.setdefault('revalidation',{}).setdefault(stage,{})[change_id]={'report':report,'sha256':sha(p),'object_hashes':hashes,'at':now()}
  m['staleness'][stage]=[x for x in m['staleness'][stage] if x!=change_id]
  m['freshness'][stage]='STALE' if m['staleness'][stage] else 'CURRENT'
  e.setdefault('revalidated_stages',[])
  if stage not in e['revalidated_stages']:e['revalidated_stages'].append(stage)
  e['status']='RESOLVED' if all(change_id not in m['staleness'][dest] for dest in e.get('affected_downstream',[])) else 'PARTIALLY_REVALIDATED'
  m['open_blockers']=[b for b in m['open_blockers'] if not (b['stage']==stage and b['change_id']==change_id)]
  m['stage_status'][stage]='STALE' if m['staleness'][stage] else m['completion'][stage]
 return load(root)
def publish(root,stage,outputs,evidence):
 detect(root,stage)
 p=inside(root,evidence);r=json.loads(p.read_text()) if p.suffix=='.json' else yaml.safe_load(p.read_text())
 accepted={'research_planning':['READY_FOR_NATURE_WRITING','MANUSCRIPT_HANDOFF','READY','READY_WITH_AUTHOR_CHECKS'],'manuscript_writing':['MANUSCRIPT_DRAFT_READY'],'manuscript_review':['REVIEWED_MANUSCRIPT_READY'],'publication_build':['PUBLICATION_PACKAGE_READY','MOCK_PUBLICATION_PACKAGE_READY','GENERIC_ACADEMIC_BUILD_READY']}
 if r.get('status') not in accepted[stage]:raise ValueError('Stage-local readiness evidence required')
 with edit(root) as m:
  if any(b['stage']==stage for b in m['open_blockers']):raise ValueError('Open stage blockers')
  required_upstream={'manuscript_writing':'manuscript_handoff','manuscript_review':'manuscript_draft','publication_build':'reviewed_manuscript'}.get(stage)
  if required_upstream and not m['canonical_outputs'][required_upstream]:raise ValueError('Register supplied upstream canonical before READY: '+required_upstream)
  expected_inputs={k:m['output_revision'].get(k,0) for k,v in m['canonical_outputs'].items() if v and OWNERS[k]<STAGES.index(stage)}
  if m['input_revision'][stage]!=expected_inputs:raise ValueError('Consume and validate current upstream canonical revisions before publishing')
  if m['staleness'][stage]:raise ValueError('Targeted change impact/revalidation required before READY')
  required={'research_planning':'manuscript_handoff','manuscript_writing':'manuscript_draft','manuscript_review':'reviewed_manuscript','publication_build':'publication_package'}[stage]
  if required not in outputs:raise ValueError('Missing stage canonical output '+required)
  for k,path in outputs.items():
   if k not in OWNERS or STAGES[OWNERS[k]]!=stage:raise ValueError('Stage cannot publish another stage canonical')
   q=inside(root,path)
   if k in ['manuscript_draft','reviewed_manuscript'] and q.suffix!='.md':raise ValueError('Scientific manuscript canonical must be Markdown, not build artifacts')
   if any(other!=k and v and v['path']==path for other,v in m['canonical_outputs'].items()):raise ValueError('Canonical roles cannot share one mutable path')
  for k,path in outputs.items():
   fp=fingerprint(root,path);old=m['canonical_outputs'][k]
   if old and old['path']!=path: m.setdefault('canonical_history',[]).append({'output':k,**old,'at':now()})
   changed=not old or old['fingerprint']!=fp
   m['canonical_outputs'][k]={'path':path,'owner':stage,'fingerprint':fp}
   if changed:
    m['output_revision'][k]=m['output_revision'].get(k,0)+1
    if old or any(m['completion'][dest]!='NOT_STARTED' for dest in STAGES[STAGES.index(stage)+1:]):
     cid='CHANGE_'+str(len(m['changes'])+1).zfill(5);down=STAGES[STAGES.index(stage)+1:]
     for dest in down:stale(m,dest,cid)
     m['changes'].append({'change_id':cid,'timestamp':now(),'source_stage':stage,'changed_object':[k],'old_revision':m['output_revision'][k]-1,'new_revision':m['output_revision'][k],'change_type':'TEXT_ONLY','affected_downstream':down,'affected_items':impact(m,[k]),'severity':'CHECK_REQUIRED','revalidation_required':True,'status':'IMPACT_ANALYSIS_REQUIRED','strategy':'TARGETED_REVALIDATION','reason':'Canonical output revision published'})
  m['stage_revision'][stage]+=1;m['completion'][stage]='READY';m['freshness'][stage]='CURRENT';m['stage_status'][stage]='READY';m['current_stage']=stage
  m.setdefault('completion_evidence',{})[stage]={'path':evidence,'sha256':sha(p),'test_only':bool(r.get('test_only')),'at':now()}
 return load(root)
def backtrack(root,stage,target,reason,objects):
 if STAGES.index(target)>=STAGES.index(stage):raise ValueError('Backtrack must target upstream')
 if not reason.strip():raise ValueError('Backtrack reason required')
 with edit(root) as m:
  cid='CHANGE_'+str(len(m['changes'])+1).zfill(5)
  e={'change_id':cid,'timestamp':now(),'source_stage':stage,'changed_object':objects,'old_revision':m['stage_revision'][stage],'new_revision':m['stage_revision'][stage],'change_type':'CLAIM','affected_downstream':[stage],'severity':'CONTENT_REVISION_REQUIRED','revalidation_required':True,'status':'ROUTED','target_stage':target,'reason':reason,'strategy':'TARGETED_REVALIDATION'}
  m['changes'].append(e);m['revalidation_requests'].append(e);m['current_stage']=target;m['stage_status'][stage]='BLOCKED';m['open_blockers'].append({'stage':stage,'change_id':cid,'reason':reason});stale(m,stage,cid);m['stage_status'][stage]='BLOCKED'
 return e

def journal_plan(root,stage,journal):
 if stage!='publication_build':raise ValueError('Publication build plan belongs to Stage 4')
 m=load(root);o=m['canonical_outputs']['reviewed_manuscript']
 if not o:raise ValueError('Reviewed canonical required, never old main.tex')
 inside(root,o['path'])
 return {'target_journal':journal,'canonical_source':o['path'],'source_fingerprint':fingerprint(root,o['path']),'output_directory':'publication/build-'+uuid.uuid4().hex[:12],'preserve_previous_build':True,'reuse_old_tex':False}
def decision(alternatives=1,material=False,technical=False,commitment=False):
 if commitment:return 'CONFIRM_COMMITMENT'
 return 'ASK' if alternatives>=2 and material else 'AUTO'
def humanizer_route(installed,explicit=False,residue=False,voice=False):
 return 'OPTIONAL_PROSE_ONLY' if installed and (explicit or residue or voice) else 'NATURE_POLISHING'
def prose_lock(text):
 return {'numbers':re.findall(r'(?<!\w)[+-]?\d+(?:\.\d+)?%?',text),'citations':re.findall(r'\[@[^\]]+\]|\\cite\w*\{[^}]+\}',text),'math':re.findall(r'\$\$.*?\$\$|\$[^$]+\$',text,re.S)}
def check_prose(before,after,semantic_report):
 if prose_lock(before)!=prose_lock(after):raise ValueError('FACT_LOCK_FAILED: numeric/citation/equation drift')
 for key in ['claim_strength','causality','terminology','technical_meaning','evidence_boundary']:
  if semantic_report.get(key)!='UNCHANGED':raise ValueError('Semantic fact lock required: '+key)
 return True

def validate_assets(root,registry):
 errors=[]
 for oid,a in registry.items():
  known=set(registry)|set(load(root)['objects']) if (Path(root)/'project_manifest.yaml').exists() else set(registry)
  for dependency in a.get('depends_on',[]):
   if dependency not in known:errors.append(oid+': unresolved dependency '+dependency)
  if a.get('publication_use') and a.get('source_type','').startswith('LITERATURE_') and any(x.get('license') in [None,'','UNKNOWN','NEEDS_CHECK'] for x in a.get('provenance',[]) or [{}]):errors.append(oid+': publication license unresolved')
  for k in ['kind','brief','final','sources','reproduction','depends_on']:
   if k not in a:errors.append(oid+': missing '+k)
  for k in ['brief','final']:
   if a.get(k):
    try:inside(root,a[k])
    except ValueError as e:errors.append(str(e))
  for p in a.get('sources',[])+a.get('reproduction',[]):
   try:inside(root,p)
   except ValueError as e:errors.append(str(e))
  if a.get('source_type') in ['REFERENCE_ONLY','LITERATURE_REPRODUCED','LITERATURE_ADAPTED','LITERATURE_SYNTHESIZED']:
   for p in a.get('provenance',[]) or [{}]:
    for k in ['paper_id','doi','original_figure','panel','page','source_pointer','license','adaptation_notes']:
     if not p.get(k):errors.append(oid+': missing provenance '+k)
  if a.get('source_type')=='REFERENCE_ONLY' and a.get('publication_use'):errors.append(oid+': REFERENCE_ONLY is not publication permission')
 return errors

def main(stage):
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['open','validate','detect','register','change','consume','publish','revalidate','backtrack','journal-plan','assets','context']);parser.add_argument('project');parser.add_argument('--payload');a=parser.parse_args()
 root=locate(a.project) or init(a.project,stage);d=yaml.safe_load(Path(a.payload).read_text()) if a.payload else {}
 if a.command=='open':detect(root,stage);result={'root':str(root),'manifest':load(root)}
 elif a.command=='validate':result={'valid':validate(load(root),root)}
 elif a.command=='assets':result={'errors':validate_assets(root,d)}
 else:result=globals()[a.command.replace('-','_')](root,stage,**d)
 print(json.dumps(result,ensure_ascii=False,indent=2,default=str))

# Stage-local gate compatibility. Automatic decisions are labelled agent_auto,
# never recorded as user consent. Existing scientific checks still run unchanged.
def auto_gate(module,root,stage,gate,record):
 root=Path(root);p=inside(root,record);v=yaml.safe_load(p.read_text())
 if v.get('decision')!='AUTO' or not v.get('evidence') or not v.get('rationale'):raise ValueError('AUTO gate needs actual evidence and rationale')
 if decision(v.get('reasonable_alternatives',1),v.get('material_difference',False),v.get('technical',False),v.get('major_commitment',False))!='AUTO':raise ValueError('Consequential choice requires user decision')
 if stage=='research_planning':
  s=module.read_state(root);d={'gate':gate,'choice':v['rationale'],'record':record,'record_sha256':module.sha(p),'approved_at':now(),'approved_by':'agent_auto','fingerprint':module.fingerprint(root)};s['user_decisions'].append(d);s['revision']+=1;module.save_state(root,s)
 elif stage=='manuscript_writing':
  s=module.state(root);d={'gate':gate,'record':record,'hash':module.digest(p),'choice':v['rationale'],'at':now(),'by':'agent_auto','fingerprint':module.fingerprint(root,gate!='D')};s['author_decisions'].append(d);module.save(root,s)
 elif stage=='manuscript_review':
  s=module.state(root);d={'gate':gate,'record':record,'hash':module.sha(p),'fingerprint':module.fingerprint(root),'accept_minor':False,'issue_hash':module.issue_hash(root),'at':now(),'by':'agent_auto'};s['author_decisions'].append(d);module.save(root,s)
 else:raise ValueError('Stage 4 has no mandatory approval gates')
 record_decision(root,stage,d)
 return d

def project_root(stage_path):
 p=Path(stage_path).resolve();existing=locate(p)
 if existing:return existing
 return p.parent if p.name in ['manuscript','review','publication','research_blueprint'] else p

def enter(stage_path,stage,final=False):
 root=init(project_root(stage_path),stage);detect(root,stage);m=load(root)
 if final and (m['staleness'][stage] or any(x['stage']==stage for x in m['open_blockers'])):raise ValueError('PROJECT_STALE: resolve targeted impact before local finalization')
 if not m['input_revision'][stage]:consume(root,stage)
 return root

def completed(stage_path,stage,evidence,outputs):
 root=project_root(stage_path);rel=lambda p:Path(p).resolve().relative_to(root).as_posix()
 return publish(root,stage,{k:rel(p) for k,p in outputs.items()},rel(evidence))


def prepare_prose(text):
    if re.search(r'^\s*(```|~~~|\|)|^\s*\w+:\s*$',text,re.M):
        raise ValueError('PROSE_ONLY: remove code/tables/structured facts before Humanizer')
    protected={}
    def seal(match):
        token='__FACT_LOCK_'+str(len(protected))+'__';protected[token]=match.group();return token
    masked=re.sub(r'\$\$.*?\$\$|\$[^$]+\$|\[@[^\]]+\]|\\cite\w*\{[^}]+\}|(?<!\w)[+-]?\d+(?:\.\d+)?%?',seal,text,flags=re.S)
    return {'prose':masked,'protected':protected,'source_hash':stable(text)}
def restore_prose(text,lock):
    if set(re.findall(r'__FACT_LOCK_\d+__',text))!=set(lock['protected']):raise ValueError('FACT_LOCK_FAILED: protected token set changed')
    for token,value in lock['protected'].items():
        if text.count(token)!=1:raise ValueError('FACT_LOCK_FAILED: protected token lost/duplicated')
        text=text.replace(token,value)
    return text


def context(root,stage,project_title=None,study_type=None,target_journal=None,reason=None):
    with edit(root) as m:
        if project_title is not None:m['project_title']=project_title
        if study_type is not None:m['study_type']=study_type
        if target_journal is not None and target_journal!=m['target_journal']:
            if m['target_journal'] is not None and not reason:raise ValueError('Journal change requires recorded reason and resolved consequential choice')
            old=m['target_journal'];m['target_journal']=target_journal
            cid='CHANGE_'+str(len(m['changes'])+1).zfill(5)
            down=STAGES[STAGES.index(stage)+1:]
            if stage=='publication_build':down=['publication_build']
            if old is not None:
                for dest in down:stale(m,dest,cid)
            m['changes'].append({'change_id':cid,'timestamp':now(),'source_stage':stage,'changed_object':['target_journal'],'old_revision':old,'new_revision':target_journal,'change_type':'JOURNAL','affected_downstream':down if old is not None else [],'severity':'SUBMISSION_CHECK','revalidation_required':old is not None,'status':'IMPACT_ANALYSIS_REQUIRED' if old is not None else 'RECORDED','reason':reason or 'Inherited target journal','strategy':'TARGETED_REVALIDATION'})
        m['current_stage']=stage
    return load(root)


def record_decision(stage_path,stage,decision_record):
    root=init(project_root(stage_path),stage)
    entry={'stage':stage,'recorded_at':now(),'by':decision_record.get('by',decision_record.get('approved_by','user')),'local_decision':decision_record}
    entry['decision_id']=stable([stage,decision_record])
    with edit(root) as m:
        if not any(d.get('decision_id')==entry['decision_id'] for d in m['author_decisions']):m['author_decisions'].append(entry)
    return entry
