"""IEEE/PubMed adapters and Scholar-only discovery. Never follow publisher links."""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlparse,parse_qs
import xml.etree.ElementTree as ET
from public_search import fetch

class AccessBlocked(RuntimeError): pass
class CredentialMissing(RuntimeError): pass

def ieee_key():
    key=os.getenv('IEEE_XPLORE_API_KEY') or os.getenv('IEEE_API_KEY')
    if key:return key
    p=Path.home()/'.config/research-planning-mini/credentials.json'
    if p.exists():return json.loads(p.read_text()).get('IEEE_XPLORE_API_KEY','')
    return ''

def html_fetch(url):
    # No external-site redirects, CAPTCHA solving, or retries around access denial.
    if not scholar_url(url):raise ValueError('Scholar URL required')
    import requests
    r=requests.get(url,headers={'User-Agent':'ResearchPlanningMini/1.0'},timeout=30,allow_redirects=False)
    if r.status_code!=200:raise AccessBlocked('Scholar access denied or redirected')
    if 'gs_captcha' in r.text or 'unusual traffic' in r.text.lower():raise AccessBlocked('Scholar verification required')
    return r.text

def scholar_url(url):
    u=urlparse(url)
    return u.scheme=='https' and u.hostname=='scholar.google.com'

def description_url(url):
    u=urlparse(url);q=parse_qs(u.query)
    return scholar_url(url) and u.path=='/citations' and q.get('view_op')==['view_citation']

def scholar_description(html,title):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,'html.parser');heading=soup.select_one('#gsc_oci_title')
    norm=lambda x:' '.join(re.findall(r'\w+',x.casefold()))
    if not heading or norm(heading.get_text(' ',strip=True))!=norm(title):return '', 'IDENTITY_UNVERIFIED'
    for field in soup.select('.gsc_oci_field'):
        if field.get_text(' ',strip=True).casefold() not in ('description','摘要','描述'):continue
        value=field.find_next_sibling(class_='gsc_oci_value')
        if not value:return '', 'MISSING'
        text=value.get_text(' ',strip=True)
        if not text or '…' in text or '...' in text or value.select('.gsc_oci_abstract_more'):return '', 'TRUNCATED_OR_UNCONFIRMED'
        # Description is a candidate; actual reading must confirm author abstract semantics.
        return text,'DESCRIPTION_CANDIDATE'
    return '', 'MISSING'

def page(source,query,size,token,request=fetch):
    if source=='ieee':
        key=ieee_key()
        if not key:raise CredentialMissing('IEEE API key not configured')
        start=int(token or 1)
        raw=request('https://ieeexploreapi.ieee.org/api/v1/search/articles?'+urlencode({'apikey':key,'querytext':query,'max_records':size,'start_record':start,'format':'json'}))
        if 'articles' not in raw:raise ValueError('Invalid IEEE response')
        items=raw['articles'];total=int(raw.get('total_records',0));rows=[]
        for x in items:
            rows.append({'title':x.get('title',''),'doi':x.get('doi',''),'year':x.get('publication_year'),
             'authors':[a.get('full_name','') for a in x.get('authors',{}).get('authors',[])],
             'abstract':x.get('abstract',''),'url':x.get('html_url') or x.get('abstract_url'),
             'source_record_ids':str(x.get('article_number','')),'document_type':x.get('content_type'),
             'source_urls':[u for u in [x.get('html_url'),x.get('pdf_url')] if u]})
        return rows,(start+len(items) if items and start+len(items)<=total else None),total,raw
    if source=='pubmed':
        start=int(token or 0)
        if start>=10000:raise ValueError('Split PubMed query by date to retrieve beyond 10000')
        size=min(size,10000-start);base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
        raw=request(base+'esearch.fcgi?'+urlencode({'db':'pubmed','term':query,'retmode':'json','retstart':start,'retmax':size,'sort':'relevance'}))
        ids=raw['esearchresult']['idlist'];total=int(raw['esearchresult']['count']);rows=[];xml=''
        if ids:
            time.sleep(.36)
            xml=request(base+'efetch.fcgi?'+urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml'}))
            if isinstance(xml,bytes):xml=xml.decode()
            root=ET.fromstring(xml)
            for a in root.findall('.//PubmedArticle'):
                pmid=a.findtext('./MedlineCitation/PMID','');article=a.find('./MedlineCitation/Article')
                if article is None:continue
                txt=lambda e:''.join(e.itertext()).strip() if e is not None else ''
                abstract=[]
                for node in article.findall('./Abstract/AbstractText'):
                    label=node.get('Label');abstract.append((label+': ' if label else '')+txt(node))
                rows.append({'title':txt(article.find('ArticleTitle')),'doi':next((txt(n) for n in a.findall('./PubmedData/ArticleIdList/ArticleId') if n.get('IdType')=='doi'),''),
                 'year':article.findtext('./Journal/JournalIssue/PubDate/Year') or article.findtext('./Journal/JournalIssue/PubDate/MedlineDate','')[:4],
                 'authors':[' '.join(filter(None,[n.findtext('ForeName'),n.findtext('LastName'),n.findtext('CollectiveName')])) for n in article.findall('./AuthorList/Author')],
                 'abstract':'\n'.join(abstract),'url':'https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/', 'source_record_ids':pmid,
                 'document_type':[txt(n) for n in article.findall('./PublicationTypeList/PublicationType')]})
            if {r['source_record_ids'] for r in rows}!=set(ids):raise ValueError('PubMed fetch incomplete; retain search IDs for retry')
        # ESearch only exposes the first 10,000; never call that exhausted.
        return rows,(start+len(ids) if ids and start+len(ids)<total else None),total,{'search':raw,'fetch_xml':xml}
    if source!='google_scholar':raise ValueError(source)
    from bs4 import BeautifulSoup
    start=int(token or 0);size=min(size,10)
    url='https://scholar.google.com/scholar?'+urlencode({'q':query,'start':start,'num':size,'hl':'en'})
    html=html_fetch(url);soup=BeautifulSoup(html,'html.parser');rows=[];description_pages={}
    blocks=soup.select('.gs_ri')
    if not blocks and not soup.select('#gs_res_ccl'):raise AccessBlocked('Scholar results not recognized')
    for b in blocks:
        h=b.select_one('.gs_rt');a=h.find('a',href=True) if h else None
        if not h:continue
        title=h.get_text(' ',strip=True);title=re.sub(r'^\[(?:PDF|HTML|CITATION)\]\s*','',title)
        desc=next((urljoin(url,n['href']) for n in b.select('a[href]') if description_url(urljoin(url,n['href']))),None)
        row={'title':title,'url':a['href'] if a else '', 'abstract':'','snippet':b.select_one('.gs_rs').get_text(' ',strip=True) if b.select_one('.gs_rs') else '',
         'authors':b.select_one('.gs_a').get_text(' ',strip=True) if b.select_one('.gs_a') else '',
         'abstract_recovery_policy':'scholar_description_only','scholar_description_url':desc,'description_status':'MISSING'}
        if desc:
            try:
                time.sleep(1);detail_html=html_fetch(desc);description_pages[desc]=detail_html
                description,status=scholar_description(detail_html,title)
                row.update(description=description,description_status=status)
            except Exception as e:row['description_status']=type(e).__name__
        rows.append(row)
    next_link=soup.select_one('a[aria-label="Next"]')
    if not next_link:
        next_link=next((a for a in soup.select('#gs_n a[href]') if a.select_one('.gs_ico_nav_next')),None)
    nxt=None
    if next_link:
        target=urljoin(url,next_link['href'])
        if scholar_url(target):nxt=int(parse_qs(urlparse(target).query).get('start',[str(start+len(blocks))])[0])
    return rows,nxt,None,{'search_html':html,'description_pages':description_pages,'description_policy':'Scholar only; no publisher requests'}
