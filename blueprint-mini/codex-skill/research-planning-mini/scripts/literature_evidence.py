"""Prepare reviewed indexes and reader-supplied copies; no scientific extraction engine."""
from pathlib import Path
import argparse,csv,json,hashlib,shutil
SKILL=Path(__file__).resolve().parents[1]
SCHEMA=json.loads((SKILL/'references/literature-evidence-schema.json').read_text())
KINDS={'visual':'figures','table':'tables','formula':'formulas'}
ALIASES={'original_path':'local_pdf_path','extracted_path':'asset_path','caption':'original_caption','potential_role':'scientific_role','licence':'license_status','status':'extraction_status'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
 with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write(p,kind,records):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=SCHEMA['fields'][kind]);w.writeheader();w.writerows(records)
def local(root,rel,required=True):
 if not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('Expected project-relative evidence path: '+str(rel))
 root=Path(root).resolve();p=(root/rel).resolve()
 if not p.is_relative_to(root):raise ValueError('External evidence path: '+rel)
 if required and not p.is_file():raise ValueError('Missing evidence: '+rel)
 return p

def normalize(kind,row):
 d=dict.fromkeys(SCHEMA['fields'][kind],'');d.update({k:str(v) if v is not None else '' for k,v in row.items() if k in d})
 legacy=not row.get('source_pointer')
 for old,new in ALIASES.items():
  if not d[new] and row.get(old):d[new]=row[old]
 number={'visual':'figure_number','table':'table_number','formula':'equation_number'}[kind]
 if not d[number]:d[number]=row.get('figure_table_formula','')
 if row.get('source_url'):d['notes']+=' Source URL: '+row['source_url']
 if legacy:d['notes']+=' LEGACY_NEEDS_ENRICHMENT: missing semantics/locators must be checked, not inferred.'
 return d

def prepare(root,entries):
 root=Path(root).resolve();base=root/'research_blueprint/literature'
 if not base.is_dir():raise ValueError('Initialize a research project first')
 for kind in KINDS:
  p=base/f'literature_{kind}_inventory.csv'
  if p.exists() and rows(p) and set(rows(p)[0])!=set(SCHEMA['fields'][kind]):
   raise ValueError('Legacy populated inventory: export normalizes without rewriting; enrich explicitly before appending')
 existing={k:[normalize(k,r) for r in rows(base/f'literature_{k}_inventory.csv')] if (base/f'literature_{k}_inventory.csv').exists() else [] for k in KINDS}
 known={r['component_id'] for rs in existing.values() for r in rs};planned=[];copies=[]
 for entry in entries:
  kind=entry['kind']
  if kind not in KINDS:raise ValueError('Unknown inventory kind')
  d=normalize(kind,entry);cid=d['component_id']
  if not cid or any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for x in cid):raise ValueError('Use a stable alphanumeric component_id')
  if cid in known:raise ValueError('Component already exists; explicit revision required: '+cid)
  known.add(cid)
  for k in ['paper_id','paper_title','asset_type','source_pointer','scientific_role','what_it_shows','original_claim','why_potentially_useful']:
   if not d[k]:raise ValueError('Missing reviewed field '+k)
  if d['importance'] not in SCHEMA['importance'] or d['potential_use_mode'] not in SCHEMA['potential_use_modes']:raise ValueError('Use candidate importance and provisional use mode only')
  if kind=='visual' and d['visual_type'] not in SCHEMA['visual_types']:raise ValueError('Unknown visual_type')
  if any(k in entry for k in ['manuscript_figure','manuscript_panel','final_figure_number','final_table_number','placement','main_or_supplementary']):raise ValueError('Stage 1 cannot bind final manuscript placement')
  if d['pdf_page'] and (not d['pdf_page'].isdigit() or int(d['pdf_page'])<1):raise ValueError('PDF page must be positive 1-based or honestly unknown')
  if d['local_pdf_path']:
   original=local(root,d['local_pdf_path'],False)
   if original.is_file():
    if d['original_sha256'] and d['original_sha256']!=sha(original):raise ValueError('Original hash mismatch')
    d['original_sha256']=sha(original)
   elif not d['notes']:raise ValueError('Unavailable original requires explanation')
  d['asset_path']='';d['verification_status']='PREPARED_SOURCE_INDEX';d['license_status']=d['license_status'] or 'UNKNOWN'
  d['extraction_status']='NOT_REQUESTED' if d['importance']=='REFERENCE_ONLY' else 'UNAVAILABLE'
  if kind=='table':d['structured_data_path']='';d['structured_data_status']='NOT_ATTEMPTED'
  if d['importance']!='REFERENCE_ONLY':
   for inputkey,outkey in [('working_copy_path','asset_path'),('structured_working_copy_path','structured_data_path')]:
    if not entry.get(inputkey):continue
    if outkey=='structured_data_path' and kind!='table':raise ValueError('Structured table source for tables only')
    src=local(root,entry[inputkey]);suffix=src.suffix.lower()
    if outkey=='structured_data_path' and suffix not in {'.csv','.tsv'}:raise ValueError('Structured table must be CSV/TSV')
    rel=f'literature_assets/{KINDS[kind]}/{cid}'+('_data' if outkey=='structured_data_path' else '')+suffix
    dest=local(root,rel,False)
    if dest.exists():raise FileExistsError(rel)
    copies.append((src,dest));d[outkey]=rel
    if outkey=='asset_path':d['extraction_status']='WORKING_COPY'
    else:d['structured_data_status']='READER_VERIFIED_WORKING_COPY'
   if d['extraction_status']=='UNAVAILABLE' and not d['notes']:raise ValueError('Missing extraction requires reason')
  d['provenance']=(d['provenance']+'; INTERNAL RESEARCH / MANUSCRIPT PLANNING ASSET; source='+d['local_pdf_path']).lstrip('; ')
  planned.append((kind,d))
 # Validate full batch before copying files or changing any index.
 for src,dest in copies:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 for kind,d in planned:existing[kind].append(d)
 for kind,records in existing.items():write(base/f'literature_{kind}_inventory.csv',kind,records)
 return {'indexed':len(planned),'working_copies':len(copies),'status':'PREPARED_NOT_SELECTED'}

def export(root,base,stage):
 """Normalize on export only; original/frozen projects stay untouched."""
 root=Path(root);base=Path(base);stage=Path(stage);availability=[]
 for kind,folder in KINDS.items():
  (stage/'literature_assets'/folder).mkdir(parents=True,exist_ok=True)
  name=f'literature_{kind}_inventory.csv';p=base/'literature'/name
  records=[normalize(kind,r) for r in rows(p)] if p.exists() else []
  write(stage/name,kind,records)
  for r in records:
   for field in ['local_pdf_path','asset_path','structured_data_path']:
    rel=r.get(field,'')
    if not rel:continue
    src=local(root,rel,False);available=src.is_file()
    availability.append({'component_id':r['component_id'],'field':field,'path':rel,'available':available})
    if available:
     if field=='local_pdf_path' and r['original_sha256'] and sha(src)!=r['original_sha256']:raise ValueError('Literature original changed: '+rel)
     out=stage/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
 (stage/'literature_assets/README.md').write_text('INTERNAL RESEARCH / MANUSCRIPT PLANNING ASSETS\n\nWorking copies are navigation aids, not publication-ready or permission-cleared assets. Stage 2 decides reproduction/adaptation/synthesis and verifies original context and rights.\n')
 (stage/'literature_asset_availability.json').write_text(json.dumps(availability,ensure_ascii=False,indent=2))
 return availability
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare']);p.add_argument('project');p.add_argument('--entries',required=True);a=p.parse_args()
 print(json.dumps(prepare(a.project,json.loads(Path(a.entries).read_text())),ensure_ascii=False,indent=2))
