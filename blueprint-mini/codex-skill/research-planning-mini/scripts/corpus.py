"""Conservative normalized corpus merging; scientific relevance is not automated."""
import argparse,csv,hashlib,json,re,unicodedata,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"vendor/python"))

def norm(s):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',str(s or '')).casefold()))
def doi(s):return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)','',str(s or '').strip(),flags=re.I).lower()
def read(path):
    p=Path(path)
    if p.suffix.lower()=='.bib':
        import bibtexparser
        with p.open(encoding='utf-8-sig') as f:entries=bibtexparser.load(f).entries
        return [{**r,'authors':r.get('author',''),'source_record_ids':r.get('ID','')} for r in entries]
    if p.suffix.lower()=='.ris':
        import rispy
        with p.open(encoding='utf-8-sig') as f:entries=rispy.load(f)
        return [{**r,'title':r.get('title') or r.get('primary_title',''),'authors':'; '.join(r.get('authors',[])),
                 'year':str(r.get('year') or r.get('publication_year',''))[:4],'doi':r.get('doi','')} for r in entries]
    if p.suffix.lower()=='.json':
        d=json.loads(p.read_text());return d if isinstance(d,list) else [{**r,'source':r.get('source',d.get('source',''))} for r in d['results']]
    if p.suffix.lower() in {'.csv','.tsv'}:
        with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t' if p.suffix.lower()=='.tsv' else ','))
    if p.suffix.lower() in {'.xls','.xlsx'}:
        try:
            import pandas as pd
            return pd.read_excel(p).fillna('').to_dict(orient='records')
        except ImportError as e:raise ValueError('Spreadsheet reader missing; preserve export and convert to CSV, do not claim import success') from e
    raise ValueError('Normalize RIS/BibTeX/other formats using specialist converter or mature parser first')
def normalize_record(record):
    r=dict(record);aliases={'title':['Article Title','Document Title','TI','Title'],
      'doi':['DOI','DI'],'year':['Publication Year','PY','Year'],
      'authors':['Authors','AU','Author full names','author'],
      'source_record_ids':['UT','EID','Accession Number','ID']}
    for key,names in aliases.items():
        if not r.get(key):
            for name in names:
                if r.get(name):r[key]=r[name];break
    if isinstance(r.get('authors'),list):
        r['authors']='; '.join(x if isinstance(x,str) else x.get('name',x.get('display_name','')) for x in r['authors'])
    r['raw_import_record']=record
    return r

def merge(records):
    output=[];keys={};conflicts=[]
    for i,r in enumerate(records):
        r=normalize_record(r);r['doi']=doi(r.get('doi'));r.setdefault('paper_id','P'+hashlib.sha256((r['doi'] or json.dumps(r,sort_keys=True,ensure_ascii=False)).encode()).hexdigest()[:12])
        key=('doi',r['doi']) if r['doi'] else ('meta',norm(r.get('title')),str(r.get('year')),norm(r.get('authors')))
        usable=bool(r['doi']) or all(key[1:])
        if usable and key in keys:
            existing=output[keys[key]]
            for k in ['title','year','authors']:
                if existing.get(k) and r.get(k) and norm(existing[k])!=norm(r[k]):conflicts.append({'paper_id':existing['paper_id'],'field':k,'kept':existing[k],'incoming':r[k]})
                elif not existing.get(k):existing[k]=r.get(k,'')
            existing['provenance_records'].append(r)
        else:
            if usable:keys[key]=len(output)
            output.append({**r,'provenance_records':[dict(r)]})
    # Similar-title conflicting DOI records remain separate, flagged for review.
    titles={}
    for r in output:
        k=(norm(r.get('title')),str(r.get('year')))
        if k[0] and k in titles and titles[k].get('doi')!=r.get('doi'):
            conflicts.append({'kind':'possible_duplicate_different_doi','paper_ids':[titles[k]['paper_id'],r['paper_id']]})
        titles[k]=r
    return output,conflicts
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():raise FileExistsError('Refuse overwrite; use versioned corpus output')
    records=[]
    for src in a.inputs:
        for r in read(src):r['import_file']=str(Path(src).resolve());records.append(r)
    merged,conflicts=merge(records);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({'records':merged,'conflicts':conflicts},ensure_ascii=False,indent=2))
    print(json.dumps({'records':len(merged),'conflicts':len(conflicts)}))
