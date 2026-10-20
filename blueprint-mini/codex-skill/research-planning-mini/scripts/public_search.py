"""Paginated public indexes. Returned abstracts are source text, never inferred."""
import json, os, time, re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PUBLIC = ('crossref', 'openalex', 'semantic_scholar', 'arxiv')

def fetch(url, headers=None, *, opener=urlopen, pause=time.sleep):
    """Bounded retry for transient failures; never retry authentication denial."""
    from urllib.error import HTTPError, URLError
    from email.utils import parsedate_to_datetime
    from datetime import datetime, timezone
    for attempt in range(3):
        try:
            with opener(Request(url, headers={'User-Agent':'ResearchPlanningMini/1.0', **(headers or {})}), timeout=30) as response:
                body = response.read()
            return body if ('export.arxiv.org' in url or '/efetch.fcgi?' in url) else json.loads(body)
        except (HTTPError, URLError, TimeoutError) as error:
            code = getattr(error, 'code', None)
            if attempt == 2 or (code is not None and code not in (429, 500, 502, 503, 504)):
                raise
            delay = (12 * (attempt + 1)) if code == 429 else (3 * (attempt + 1))
            retry_after = (getattr(error, 'headers', None) or {}).get('Retry-After')
            if retry_after:
                try:delay = max(delay, float(retry_after))
                except ValueError:
                    try:delay = max(delay, (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds())
                    except (ValueError, TypeError, OverflowError):raise error
            # Leave longer waits for a later run instead of retrying prematurely.
            if delay > 60:raise
            pause(delay)

def inverted(index):
    return ' '.join(word for _, word in sorted((pos, word) for word, positions in (index or {}).items() for pos in positions))

def normalize(source, item):
    if source == 'openalex':
        return {'title':item.get('display_name'), 'doi':item.get('doi'), 'year':item.get('publication_year'),
                'authors':[a.get('author',{}).get('display_name','') for a in item.get('authorships',[])],
                'abstract':inverted(item.get('abstract_inverted_index')), 'url':item.get('id'), 'document_type':item.get('type'),
                'source_urls':list(dict.fromkeys(u for loc in item.get('locations',[]) for u in [loc.get('landing_page_url'),loc.get('pdf_url')] if u))}
    if source == 'crossref':
        dates=item.get('published',{}).get('date-parts', [[]])
        return {'title':next(iter(item.get('title',[])), ''), 'doi':item.get('DOI'),
                'year':dates[0][0] if dates and dates[0] else None,
                'authors':[' '.join(filter(None,[a.get('given'),a.get('family')])) for a in item.get('author',[])],
                'abstract':item.get('abstract') or '', 'url':item.get('URL'), 'document_type':item.get('type')}
    return {'title':item.get('title'), 'doi':(item.get('externalIds') or {}).get('DOI'),
            'authors':item.get('authors',[]), 'year':item.get('year'), 'abstract':item.get('abstract') or '', 'url':item.get('url'), 'document_type':item.get('publicationTypes')}

def page(source, query, size, token, request=fetch):
    headers={}
    if source=='crossref':
        raw=request('https://api.crossref.org/works?'+urlencode({'query':query,'rows':size,'cursor':token or '*','sort':'relevance','order':'desc'}))
        msg=raw['message']; items=msg['items']; nxt=msg.get('next-cursor') if items else None; total=msg.get('total-results')
    elif source=='openalex':
        params={'search':query,'per_page':size,'cursor':token or '*'}
        if os.getenv('OPENALEX_API_KEY'):params['api_key']=os.environ['OPENALEX_API_KEY']
        raw=request('https://api.openalex.org/works?'+urlencode(params)); items=raw['results']; nxt=raw.get('meta',{}).get('next_cursor'); total=raw.get('meta',{}).get('count')
    elif source=='semantic_scholar':
        if os.getenv('SEMANTIC_SCHOLAR_API_KEY'):headers['x-api-key']=os.environ['SEMANTIC_SCHOLAR_API_KEY']
        raw=request('https://api.semanticscholar.org/graph/v1/paper/search?'+urlencode({'query':query,'limit':size,'offset':token or 0,'fields':'title,authors,year,externalIds,url,abstract,publicationTypes'}),headers)
        items=raw['data']; nxt=raw.get('next'); total=raw.get('total')
    else:
        offset=int(token or 0)
        expression=query if re.search(r'\b(?:all|ti|abs|au|cat):',query) else 'all:'+query
        raw=request('https://export.arxiv.org/api/query?'+urlencode({'search_query':expression,'start':offset,'max_results':size,'sortBy':'relevance'}))
        root=ET.fromstring(raw); ns={'a':'http://www.w3.org/2005/Atom','o':'http://a9.com/-/spec/opensearch/1.1/','x':'http://arxiv.org/schemas/atom'}
        total=int(root.findtext('o:totalResults','0',ns)); items=[]
        for entry in root.findall('a:entry',ns):
            if '/api/errors' in entry.findtext('a:id','',ns):raise ValueError('arXiv query error')
            items.append({'title':entry.findtext('a:title','',ns), 'doi':entry.findtext('x:doi','',ns),
                          'year':entry.findtext('a:published','',ns)[:4], 'authors':[a.findtext('a:name','',ns) for a in entry.findall('a:author',ns)],
                          'abstract':entry.findtext('a:summary','',ns), 'url':entry.findtext('a:id','',ns)})
        nxt=offset+len(items) if items and offset+len(items)<total else None
        return items,nxt,total,raw.decode()
    return [normalize(source,i) for i in items],nxt,total,raw

def search(source, query, limit=300, page_size=50, max_pages=10, start=None, request=fetch, pause=time.sleep, save_page=None, loader=page):
    if limit<1 or not 1<=page_size<=100 or max_pages<1:raise ValueError('invalid search bounds')
    results=[]; seen=set(); token=start; total=None; pages=0; error=None; stop='max_pages'
    for _ in range(max_pages):
        if pages:pause(3.1 if source=='arxiv' else 1.0)
        try:
            batch,nxt,total,raw=loader(source,query,min(page_size,limit-len(results)),token,request)
        except Exception as e:
            error={'type':type(e).__name__,'http_status':getattr(e,'code',None)};stop='request_failed';break
        pages+=1
        if save_page:save_page(pages,raw)
        added=0
        for r in batch:
            key=r.get('doi') or r.get('url') or r.get('title')
            if key in seen:continue
            seen.add(key);added+=1
            results.append({**r,'source':source,'abstract_status':'PRESENT' if r.get('abstract','').strip() else 'MISSING', 'abstract_source':(r.get('abstract_source') or source) if r.get('abstract','').strip() else None})
        old=token;token=nxt
        if not batch or nxt is None:stop='exhausted';break
        if nxt==old or not added:stop='pagination_stalled';break
        if len(results)>=limit:stop='result_limit';break
    return {'status':'SEARCHED' if not error else ('PARTIAL' if results else 'SOURCE_UNAVAILABLE'),
            'availability':'AVAILABLE' if results or not error else 'UNAVAILABLE','attempted':True,
            'results':results,'retrieved_count':len(results),'reported_result_count':total,
            'pages_retrieved':pages,'next_cursor':token,'stop_reason':stop,'error':error,
            'coverage':'query exhausted' if stop=='exhausted' else 'bounded or incomplete query; not exhaustive'}
