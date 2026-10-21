"""Recover lawful full text from selected records; no browser credentials or paywall bypass.
Dependencies: requests, beautifulsoup4, PyMuPDF. Institution/API routes remain in nature-downloader.
"""
import argparse,hashlib,json,os,re,time,unicodedata
from pathlib import Path
from urllib.parse import urljoin,urlparse,quote
import requests
from bs4 import BeautifulSoup
import fitz

def norm(s):return re.sub(r'\W','',unicodedata.normalize('NFKC',s).casefold())
def doi(s):return re.sub(r'^https?://(?:dx\.)?doi.org/','',str(s or '').strip(),flags=re.I).lower()
def public_url(u):
    h=urlparse(u).hostname or ''
    return urlparse(u).scheme in ('https','http') and h not in ('localhost','127.0.0.1','::1') and bool(h)
def identity(text,record):
    title=norm(record.get('title',''));d=doi(record.get('doi'))
    words=set(re.findall(r'[a-z0-9]{3,}',record.get('title','').lower())); available=set(re.findall(r'[a-z0-9]{3,}',text.lower()))
    return bool((len(title)>20 and title in norm(text)) or (d and d in text.lower() and words and len(words & available)/len(words)>=.8))
def candidates(record):
    out=[]
    def add(u,source,version='unknown'):
        if isinstance(u,str) and public_url(u) and u not in [x['url'] for x in out]:out.append(dict(url=u,source=source,version=version))
    def visit(r):
        for u in r.get('pdf_urls',[]):add(u,'search_pdf')
        for u in r.get('source_urls',[]):add(u,'search_location')
        for loc in r.get('locations',[]):
            for k in ('pdf_url','landing_page_url'):add(loc.get(k),'index_location',loc.get('version','unknown'))
        for k in ('best_oa_location','primary_location','openAccessPdf'):
            loc=r.get(k) or {}
            for key in ('pdf_url','landing_page_url','url'):add(loc.get(key),'index_location',loc.get('version','unknown'))
        for key in ('url','source_url'):add(r.get(key),'record')
        for sub in r.get('provenance_records',[]):visit(sub)
    visit(record)
    return out

def cnki_record(record):
    """CNKI provenance is a manual-download route, including merged records."""
    sources = record.get('sources', [])
    if isinstance(sources, str): sources = [sources]
    if any(str(s).casefold() in ('cnki', '知网') for s in [record.get('source', ''), *sources]): return True
    if any(str(k).casefold() == 'cnki' for k in (record.get('source_ids') or {})): return True
    for item in candidates(record):
        host = (urlparse(item['url']).hostname or '').lower()
        if host == 'cnki.net' or host.endswith('.cnki.net') or host == 'cnki.com.cn' or host.endswith('.cnki.com.cn'): return True
    return any(cnki_record(r) for r in record.get('provenance_records', []))

def missing_item(record, out):
    return {'doi': record['doi'], 'title': record['title'], 'authors': record.get('authors', []), 'year': record.get('year'),
            'url': record.get('landing_url') or ('https://doi.org/'+record['doi'] if record['doi'] else ''),
            'reason': record.get('stop_reason', ''), 'manual_directory': str((out/'manual').resolve())}

def page_links(html,base,record):
    soup=BeautifulSoup(html,'xml' if isinstance(html,bytes) and b'<?xml' in html[:100] else 'html.parser')
    # Only follow article PDF metadata or article-specific PDF links; never guessed URLs.
    out=[]
    for m in soup.select('meta[name="citation_pdf_url"], meta[name="wkhealth_pdf_url"]'):
        if m.get('content'):out.append(urljoin(base,m['content']))
    if identity(soup.get_text(' ',strip=True),record):
        for a in soup.find_all('a',href=True):
            u=urljoin(base,a['href']);label=a.get_text(' ',strip=True).lower()
            if re.search(r'\.pdf(?:$|\?)|/pdf(?:/|$|\?)',u,re.I) and not re.search(r'supp|appendix|supporting',u+' '+label,re.I):out.append(u)
    return list(dict.fromkeys(u for u in out if public_url(u)))[:4]

class Client:
    def __init__(self):self.session=requests.Session();self.session.headers['User-Agent']='ResearchPlanningMini/1.0 (selected-article fulltext retrieval)'
    def get(self,url):
        last=None
        for attempt in range(3):
            try:
                r=self.session.get(url,timeout=(12,35),stream=True)
                if r.status_code in (429,500,502,503,504):
                    delay=r.headers.get('Retry-After','')
                    wait=int(delay) if delay.isdigit() else 3*(attempt+1)
                    if wait>30 or attempt==2:r.close();return None,f'HTTP_{r.status_code}_deferred'
                    r.close();time.sleep(wait);continue
                if r.status_code!=200:r.close();return None,f'HTTP_{r.status_code}'
                chunks=[];size=0
                for chunk in r.iter_content(65536):
                    size+=len(chunk)
                    if size>60*1024*1024:r.close();return None,'over_60MB'
                    chunks.append(chunk)
                data=b''.join(chunks);result=(data,r.url,r.headers.get('Content-Type',''));r.close();return result,None
            except requests.RequestException as e:
                last=type(e).__name__
                if attempt<2:time.sleep(3*(attempt+1))
        return None,'network_'+str(last)
    def json(self,url):
        result,error=self.get(url)
        if error:return None,error
        try:return json.loads(result[0]),None
        except (ValueError,UnicodeError):return None,'invalid_json'

def atomic(path,data):
    tmp=path.with_suffix(path.suffix+'.part');tmp.write_bytes(data);tmp.replace(path)

def validate(data,record):
    if data.startswith(b'%PDF'):
        try:
            with fitz.open(stream=data,filetype='pdf') as doc:
                text=' '.join(p.get_text() for p in list(doc)[:3])
                if len(doc)==0 or not identity(text,record):return None,'pdf_identity_unverified'
                return {'format':'pdf','extension':'.pdf','pages':len(doc)},None
        except Exception:return None,'invalid_pdf'
    is_xml=b'<?xml' in data[:100]
    soup=BeautifulSoup(data,'xml' if is_xml else 'html.parser');text=soup.get_text(' ',strip=True)
    if re.search(r'checking your browser|verify you are human|access denied|captcha|just a moment',text[:2000],re.I):return None,'verification_or_access_page'
    headings=[h.get_text(' ',strip=True).lower() for h in soup.select('h2,h3,sec > title')]
    sections={k for k in ('introduction','methods','methodology','results','discussion','conclusion') if any(k in h for h in headings)}
    if identity(text,record) and len(text)>8000 and len(sections)>=3 and bool(sections & {'methods','methodology','results'}) and (soup.find('article') or soup.find('body')):
        fmt='xml' if b'<article' in data[:4000] and (b'<?xml' in data[:100] or b'<front>' in data[:10000]) else 'html'
        return {'format':fmt,'extension':'.'+fmt,'needs_figures_check':True},None
    return None,'not_verified_fulltext'

def acquire(record,out,client,email='',max_candidates=16):
    key=hashlib.sha256((doi(record.get('doi')) or record['title']).encode()).hexdigest()[:16]
    folder=out/key;folder.mkdir(parents=True,exist_ok=True);statefile=folder/'record.json'
    if statefile.exists():
        old=json.loads(statefile.read_text());f=Path(old.get('file',''))
        if old.get('status')=='verified' and f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==old.get('sha256') and validate(f.read_bytes(),record)[0]:return old
    # User-added PDFs are accepted only after the same content/identity verification.
    for manual in sorted((out/'manual').glob('*.pdf')):
        data=manual.read_bytes();info,error=validate(data,record)
        if info and info['format']=='pdf':
            state={**info,'doi':doi(record.get('doi')),'title':record.get('title',''),'status':'verified','file':str(manual.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'source_url':'user_provided','version':'unknown','attempts':[]}
            atomic(statefile,json.dumps(state,ensure_ascii=False,indent=2).encode());return state
    state={'doi':doi(record.get('doi')),'title':record.get('title',''),'status':'missing','attempts':[],'unpaywall':'enabled' if email else 'not_configured'}
    if cnki_record(record):
        links = candidates(record)
        state.update(stop_reason='cnki_manual_download', authors=record.get('authors', []), year=record.get('year'), landing_url=next((c['url'] for c in links if 'cnki' in (urlparse(c['url']).hostname or '')), links[0]['url'] if links else ''))
        atomic(statefile,json.dumps(state,ensure_ascii=False,indent=2).encode())
        return state
    queue=candidates(record);seen=set();d=state['doi'];resolved=False;backup=None
    def persist():atomic(statefile,json.dumps(state,ensure_ascii=False,indent=2).encode())
    def add(u,source,version='unknown',depth=0):
        if public_url(u) and u not in seen and u not in [x['url'] for x in queue]:queue.append(dict(url=u,source=source,version=version,depth=depth))
    def resolve():
        if not d:return
        # Exact DOI only. Index responses never count as full text.
        apis=[('openalex','https://api.openalex.org/works/https://doi.org/'+quote(d,safe='')),
              ('europepmc','https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query='+quote('DOI:'+d))]
        if email:apis.append(('unpaywall','https://api.unpaywall.org/v2/'+quote(d,safe='')+'?email='+quote(email)))
        for source,url in apis:
            data,err=client.json(url);state['attempts'].append({'resolver':source,'error':err})
            if not data:continue
            if source=='openalex' and doi(data.get('doi'))==d:
                for c in candidates(data):add(c['url'],source,c['version'])
            elif source=='unpaywall' and doi(data.get('doi'))==d:
                for loc in [data.get('best_oa_location')]+data.get('oa_locations',[]):
                    if loc:
                        for k in ('url_for_pdf','url'):add(loc.get(k) or '',source,loc.get('version','unknown'))
            elif source=='europepmc':
                for r in data.get('resultList',{}).get('result',[]):
                    if doi(r.get('doi'))==d and r.get('pmcid'):
                        pmcid=r['pmcid'];add('https://pmc.ncbi.nlm.nih.gov/articles/'+pmcid+'/',source)
                        if r.get('isOpenAccess')=='Y':add('https://www.ebi.ac.uk/europepmc/webservices/rest/'+pmcid+'/fullTextXML',source)
        add('https://doi.org/'+d,'doi_publisher')
    while len(seen)<max_candidates:
        if not queue:
            if resolved:break
            resolved=True;resolve()
            if not queue:break
        c=queue.pop(0);url=c['url']
        if url in seen:continue
        seen.add(url);response,error=client.get(url)
        attempt={**c,'error':error};state['attempts'].append(attempt)
        if response:
            data,final,mime=response;info,error=validate(data,record);attempt.update(final_url=final,content_type=mime,error=error)
            if info:
                path=folder/('fulltext'+info['extension']);atomic(path,data)
                found={**info,'file':str(path.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'source_url':final,'version':c.get('version','unknown')}
                if info['format']=='pdf':state.update(found,status='verified');persist();return state
                backup=found
            if not data.startswith(b'%PDF') and c.get('depth',0)<1:
                for u in page_links(data,final,record):add(u,'page_pdf',c.get('version','unknown'),1)
        persist();time.sleep(.5)
    if backup:state.update(backup,status='verified')
    state['stop_reason']='candidate_limit' if queue else 'available_routes_exhausted';persist();return state

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--out',required=True);p.add_argument('--email',default=os.getenv('UNPAYWALL_EMAIL',''));p.add_argument('--limit',type=int,default=30);p.add_argument('--max-candidates',type=int,default=16);a=p.parse_args()
    if a.limit<1 or a.max_candidates<1:p.error('positive limits required')
    email=a.email
    config=Path.home()/'.config/lit-dl/settings.json'
    if not email and config.exists():email=json.loads(config.read_text()).get('open_access',{}).get('contact_email','')
    raw=json.loads(Path(a.input).read_text());records=raw if isinstance(raw,list) else raw.get('records',raw.get('results',[]));out=Path(a.out);out.mkdir(parents=True,exist_ok=True);(out/'manual').mkdir(exist_ok=True)
    results=[];client=Client();seen=set()
    for r in records:
        key=doi(r.get('doi')) or norm(r.get('title',''))
        if not key or key in seen:continue
        if len(results)>=a.limit:break
        seen.add(key);print('START',len(results)+1,r.get('doi',''),flush=True)
        row=acquire(r,out,client,email,a.max_candidates);results.append(row)
        atomic(out/'manifest.json',json.dumps(results,ensure_ascii=False,indent=2).encode())
        print('DONE',len(results),row['status'],row.get('format',''),flush=True)
    missing=[missing_item(r,out) for r in results if r['status']!='verified']
    atomic(out/'missing.json',json.dumps(missing,ensure_ascii=False,indent=2).encode())
    print(json.dumps({'tested':len(results),'pdf':sum(r.get('format')=='pdf' for r in results),'other_fulltext':sum(r.get('format') in ('xml','html') for r in results),'missing':len(missing)}))
if __name__=='__main__':main()
