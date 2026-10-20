"""Exact-DOI abstract recovery; unresolved records remain pending, not excluded."""
import argparse,json,os,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import quote,urlencode
from corpus import read,doi,normalize_record
from public_search import fetch,normalize

def enrich(records, limit=50, request=fetch, pause=time.sleep, supplements=()):
    records=[normalize_record(r) for r in records]
    known={}
    for candidate in [*records, *[normalize_record(r) for r in supplements]]:
        key=doi(candidate.get('doi'))
        if key and str(candidate.get('abstract') or '').strip():known.setdefault(key,candidate)
    output=[]; missing=[]; attempted=0; blocked=set()
    for record in records:
        r=dict(record)
        cached=known.get(doi(r.get('doi')))
        if not str(r.get('abstract') or '').strip() and cached:
            r.update(abstract=cached['abstract'],abstract_source=cached.get('abstract_source') or cached.get('source') or cached.get('import_file') or 'provided_record')
            r.setdefault('abstract_provenance',[]).append({'source':r['abstract_source'],'doi':doi(r.get('doi')),'abstract':cached['abstract'],'method':'existing_record_reuse','url':cached.get('url'),'abstract_locator':cached.get('abstract_locator'),'retrieved_at':cached.get('retrieved_at'),'identity_check':cached.get('identity_check')})
        if not str(r.get('abstract') or '').strip():
            identifier=doi(r.get('doi')); attempts=[]
            if r.get('abstract_recovery_policy')=='scholar_description_only':
                attempts.append({'source':'google_scholar','status':'DESCRIPTION_ONLY_NO_EXTERNAL_LOOKUP'})
            elif identifier and attempted<limit:
                attempted+=1
                for source in ('crossref','openalex','semantic_scholar'):
                    if source in blocked:continue
                    pause(1)
                    headers={}
                    if source=='crossref':url='https://api.crossref.org/works/'+quote(identifier,safe='')
                    elif source=='openalex':
                        url='https://api.openalex.org/works/https://doi.org/'+quote(identifier,safe='')
                        if os.getenv('OPENALEX_API_KEY'):url+='?'+urlencode({'api_key':os.environ['OPENALEX_API_KEY']})
                    else:
                        url='https://api.semanticscholar.org/graph/v1/paper/DOI:'+quote(identifier,safe='')+'?fields=title,authors,year,externalIds,url,abstract'
                        if os.getenv('SEMANTIC_SCHOLAR_API_KEY'):headers['x-api-key']=os.environ['SEMANTIC_SCHOLAR_API_KEY']
                    try:
                        raw=request(url,headers); candidate=normalize(source,raw['message'] if source=='crossref' else raw)
                        if doi(candidate.get('doi'))!=identifier:
                            attempts.append({'source':source,'status':'IDENTITY_UNVERIFIED'});continue
                        if str(candidate.get('abstract') or '').strip():
                            r.update(abstract=candidate['abstract'],abstract_source=source)
                            r.setdefault('abstract_provenance',[]).append({'source':source,'doi':identifier,'abstract':candidate['abstract']})
                            attempts.append({'source':source,'status':'FOUND'});break
                        attempts.append({'source':source,'status':'NO_ABSTRACT'})
                    except Exception as e:
                        code=getattr(e,'code',None)
                        attempts.append({'source':source,'status':'ERROR','type':type(e).__name__,'http_status':code})
                        if code in (401,403,429) or code is None:blocked.add(source)
            r.setdefault('abstract_lookup_history',[]).extend(r.get('abstract_lookup_attempts',[]))
            r['abstract_lookup_attempts']=attempts
            r['abstract_lookup_date']=datetime.now(timezone.utc).isoformat()
        present=bool(str(r.get('abstract') or '').strip());r['abstract_status']='PRESENT' if present else 'MISSING'
        if not present:missing.append({'paper_id':r.get('paper_id'),'title':r.get('title'),'doi':r.get('doi'),'url':r.get('url'),'source_urls':r.get('source_urls',[]),'lookup_attempts':r.get('abstract_lookup_attempts',[]),'search_queries':[doi(r.get('doi'))+' abstract' if r.get('doi') else '', '"'+str(r.get('title') or '')+'" abstract'],'action':('Check Scholar Description only; no external-site follow-up. Ineligible without confirmed author abstract.' if r.get('abstract_recovery_policy')=='scholar_description_only' else 'Obtain and read the original abstract (publisher page or abstract section of full text); ineligible for shortlist until then')})
        output.append(r)
    return {'records':output,'missing_abstracts':missing,'lookup_records':attempted,'temporarily_blocked_sources':sorted(blocked)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--limit',type=int,default=50);p.add_argument('--supplement',nargs='*',default=[],help='Other search runs, corpora or exports with abstracts');a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():raise FileExistsError('Use a new versioned output')
    if a.limit<1:p.error('--limit must be positive')
    supplements=[]
    for path in a.supplement:
        for row in read(path):supplements.append({**row,'import_file':str(Path(path).resolve())})
    result=enrich(read(a.input),a.limit,supplements=supplements);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'records':len(result['records']),'missing_abstracts':len(result['missing_abstracts']),'lookup_records':result['lookup_records']}))
