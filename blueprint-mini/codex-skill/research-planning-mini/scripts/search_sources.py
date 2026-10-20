"""Bounded per-source searches, explicit failures and immutable run records.
No endpoint availability is inferred from an aggregate index or landing page.
"""
import argparse,json,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from specialists import resolve
from public_search import PUBLIC, search
SOURCES=['wos','sciencedirect','scopus','crossref','openalex','semantic_scholar','arxiv','ieee','ei','pubmed','google_scholar']
def query_source(source,query,limit,**options):
    if source in PUBLIC:return search(source,query,limit,**options)
    if source in ('ieee','pubmed','google_scholar'):
        from extended_search import page,ieee_key
        if source=='ieee' and not ieee_key():
            return {'status':'SOURCE_UNAVAILABLE','availability':'USER_ACTION_REQUIRED','attempted':False,'results':[], 'reason':'Configure local IEEE API key; never put it in project files.'}
        return search(source,query,limit,loader=page,**options)
    if source=='wos':
        return {'status':'USER_ACTION_REQUIRED','availability':'USER_EXPORT_AVAILABLE','attempted':False,'results':[],
                'reason':'Use authorized Chrome WoS search and range export with Abstract, then scripts/import_wos.py; browser login if needed. No API request attempted.'}
    if source=='ei':
        return {'status':'SOURCE_UNAVAILABLE','availability':'UNAVAILABLE','attempted':False,
                'reason':'No direct provider/MCP configured. Check authorized browser or user export; not searched.'}
    if source in ('scopus','sciencedirect'):
        try:
            import pybliometrics
            config=Path.home()/'.config/pybliometrics.cfg'
            if not config.exists():raise ImportError('missing configuration')
        except ImportError:
            return {'status':'SOURCE_UNAVAILABLE','availability':'USER_ACTION_REQUIRED','attempted':False,
                    'reason':'pybliometrics runtime/config absent; requires authorized API entitlement or export.'}
        root=resolve('nature-academic-search')/'mcp-server';sys.path.insert(0,str(root))
        import importlib
        module=importlib.import_module('sources.'+source)
        provider=(module.ScopusSource() if source=='scopus' else module.ScienceDirectSource())
        def licensed_page(name,query,size,token,request):
            offset=int(token or 0)
            raw=provider._run('Paginated search',lambda:provider._search_api(
                'ScopusSearch' if name=='scopus' else 'ScienceDirectSearch',
                {'query':query,'count':min(size,25),'start':offset,'view':'COMPLETE' if name=='scopus' else 'STANDARD'}))
            entries=module._search_entries(raw);total=module._total_results(raw)
            batch=[provider._normalize_search_entry(r) for r in entries]
            for r,original in zip(batch,entries):
                r['abstract']=original.get('dc:description') or r.get('abstract') or ''
            nxt=offset+len(entries) if entries and (total is None or offset+len(entries)<int(total)) else None
            return batch,nxt,total,raw
        return search(source,query,limit,loader=licensed_page,**options)
    raise ValueError(source)
def run(source,query,out,limit=300,variant='broad-discovery',page_size=50,max_pages=10,start=None):
    record={'run_id':uuid.uuid4().hex,'source':source,'date':datetime.now(timezone.utc).isoformat(),
            'exact_query':query,'query_variant':variant,'filters':{},'year_range':None,
            'document_types':[],'limit':limit,'unique_papers':None,'relevant_papers':None,'core_papers':None}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    raw_dir=out/(source+'_'+record['run_id']+'_pages')
    def save_page(number,raw):
        raw_dir.mkdir(exist_ok=True)
        (raw_dir/f'{number:04d}.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2))
    record.update(page_size=page_size,max_pages=max_pages,start_cursor=start,raw_response_path=str(raw_dir))
    try:record.update(query_source(source,query,limit,page_size=page_size,max_pages=max_pages,start=start,save_page=save_page))
    except Exception as e:
        # Do not serialize exceptions that might embed credential-bearing URLs.
        record.update(status='SOURCE_UNAVAILABLE',availability='UNAVAILABLE',attempted=True,
                      reason=type(e).__name__,http_status=getattr(e,'code',None),results=[])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    path=out/f'{source}_{record["run_id"]}.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    return record
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--query',required=True);p.add_argument('--output',required=True)
    p.add_argument('--sources',nargs='+',default=SOURCES,choices=SOURCES);p.add_argument('--limit',type=int,default=300)
    p.add_argument('--page-size',type=int,default=50);p.add_argument('--max-pages',type=int,default=10)
    p.add_argument('--start-cursor',help='Resume one source/query from the recorded next_cursor')
    p.add_argument('--variant',default='broad-discovery');a=p.parse_args()
    if a.start_cursor and len(a.sources)!=1:p.error('--start-cursor requires one source')
    if a.limit<1 or not 1<=a.page_size<=100 or a.max_pages<1:p.error('invalid search bounds')
    for s in a.sources:
        r=run(s,a.query,a.output,a.limit,a.variant,a.page_size,a.max_pages,a.start_cursor)
        print(json.dumps({k:r.get(k) for k in ['source','availability','status','retrieved_count','pages_retrieved','stop_reason','reason','http_status','error']},ensure_ascii=False),flush=True)
