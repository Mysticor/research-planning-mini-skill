"""Bounded per-source searches, explicit failures and immutable run records.
No endpoint availability is inferred from an aggregate index or landing page.
"""
import argparse,json,os,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from specialists import resolve,load_file,source_class
SOURCES=['wos','sciencedirect','scopus','crossref','openalex','semantic_scholar','arxiv','ieee','ei']
def fetch(url,headers=None):
    with urlopen(Request(url,headers=headers or {}),timeout=20) as r:return json.load(r)
def query_source(source,query,limit):
    if source in ('wos','ieee','ei'):
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
        if source=='scopus':
            from sources.scopus import ScopusSource
            data=ScopusSource().search(query,rows=limit)
        else:
            from sources.sciencedirect import ScienceDirectSource
            data=ScienceDirectSource().search(query,rows=limit)
    elif source=='crossref':data=source_class('crossref').CrossRefSource().search(query,rows=limit)
    elif source=='arxiv':data=source_class('arxiv').ArxivSource().search(query,rows=limit)
    elif source=='openalex':
        mod=load_file('rp_openalex',resolve('nature-academic-search')/'scripts/academic_search.py')
        data={'results':mod.search(query=query,limit=limit),'total':None}
    elif source=='semantic_scholar':
        key=os.environ.get('SEMANTIC_SCHOLAR_API_KEY')
        headers={'x-api-key':key} if key else {}
        d=fetch('https://api.semanticscholar.org/graph/v1/paper/search?'+urlencode({'query':query,'limit':limit,'fields':'title,authors,year,externalIds,url,abstract'}),headers)
        data={'results':d.get('data',[]),'total':d.get('total')}
    else:raise ValueError(source)
    return {'status':'SEARCHED','availability':'AVAILABLE','attempted':True,
            'retrieved_count':len(data.get('results',[])),'reported_result_count':data.get('total'),
            'results':data.get('results',[]),'coverage':'bounded first page; not exhaustive'}
def run(source,query,out,limit=3,variant='probe'):
    record={'run_id':uuid.uuid4().hex,'source':source,'date':datetime.now(timezone.utc).isoformat(),
            'exact_query':query,'query_variant':variant,'filters':{},'year_range':None,
            'document_types':[],'limit':limit,'unique_papers':None,'relevant_papers':None,'core_papers':None}
    try:record.update(query_source(source,query,limit))
    except Exception as e:
        # Do not serialize exceptions that might embed credential-bearing URLs.
        record.update(status='SOURCE_UNAVAILABLE',availability='UNAVAILABLE',attempted=True,
                      reason=type(e).__name__,http_status=getattr(e,'code',None),results=[])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    path=out/f'{source}_{record["run_id"]}.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    return record
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--query',required=True);p.add_argument('--output',required=True)
    p.add_argument('--sources',nargs='+',default=SOURCES,choices=SOURCES);p.add_argument('--limit',type=int,default=3)
    p.add_argument('--variant',default='broad-discovery');a=p.parse_args()
    for s in a.sources:
        r=run(s,a.query,a.output,a.limit,a.variant)
        print(json.dumps({k:r.get(k) for k in ['source','availability','status','retrieved_count','reason','http_status']},ensure_ascii=False),flush=True)
