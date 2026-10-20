"""Import actual WoS tagged exports, preserving original bytes and multiline abstracts."""
import argparse,json,hashlib,uuid,shutil
from pathlib import Path
from datetime import datetime,timezone

def parse(text):
    if not text.lstrip('\ufeff').startswith('FN ') or '\nEF' not in text:raise ValueError('Not a complete WoS tagged export')
    records=[];fields={};key=None
    for line in text.splitlines():
        if line=='ER':
            if not fields.get('UT') or not fields.get('TI'):raise ValueError('Missing WoS identity/title')
            records.append({'title':fields['TI'],'doi':fields.get('DI',''),'year':fields.get('PY',''),
             'authors':fields.get('AF') or fields.get('AU',''),'abstract':fields.get('AB',''),
             'source':'wos','source_record_ids':fields['UT'],'url':'https://www.webofscience.com/wos/woscc/full-record/'+fields['UT'],
             'abstract_source':'wos' if fields.get('AB') else None,'abstract_status':'PRESENT' if fields.get('AB') else 'MISSING',
             'raw_import_record':dict(fields)})
            fields={};key=None
        elif len(line)>=3 and line[:2].isupper() and line[2]==' ':key=line[:2];fields[key]=line[3:]
        elif line.startswith('   ') and key:fields[key]+=' '+line[3:]
    if fields.get('UT'):raise ValueError('Unterminated WoS record')
    return records

def run(path,out,query,expected=None):
    p=Path(path);rows=parse(p.read_text(encoding='utf-8-sig'));ids=[r['source_record_ids'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate IDs inside export')
    folder=Path(out)/('wos_'+uuid.uuid4().hex);folder.mkdir(parents=True)
    shutil.copy2(p,folder/'original.txt')
    report={'source':'wos','status':'IMPORTED','availability':'AVAILABLE','exact_query':query,
     'date':datetime.now(timezone.utc).isoformat(),'retrieved_count':len(rows),'expected_export_count':expected,
     'export_count_matches':len(rows)==expected if expected is not None else None,
     'coverage':'exported selection only; not evidence of exhaustive search',
     'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'raw_response_path':str(folder/'original.txt'),'results':rows}
    if expected is not None and len(rows)!=expected:report['status']='PARTIAL'
    (folder/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return {'path':str(folder/'run.json'),'records':len(rows),'with_abstract':sum(bool(r['abstract']) for r in rows),'status':report['status']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--query',required=True);p.add_argument('--expected-count',type=int);a=p.parse_args()
    print(json.dumps(run(a.input,a.output,a.query,a.expected_count)))
