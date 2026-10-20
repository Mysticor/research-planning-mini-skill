import sys,unittest,tempfile,json
from pathlib import Path
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from public_search import search,inverted
from enrich_abstracts import enrich
from corpus import merge,read

class SearchTests(unittest.TestCase):
    def test_crossref_pages_and_full_abstract(self):
        calls=[]
        def request(url,headers=None):
            calls.append(url);i=len(calls)
            return {'message':{'items':[{'DOI':f'10.1/{i}','title':[str(i)],'abstract':'A'*1800}], 'total-results':2,'next-cursor':str(i)}}
        r=search('crossref','test',limit=2,page_size=1,request=request,pause=lambda _:None)
        self.assertEqual(r['pages_retrieved'],2);self.assertEqual(len(r['results'][1]['abstract']),1800)
        self.assertIn('cursor=1',calls[1]);self.assertEqual(r['stop_reason'],'result_limit')
    def test_partial_failure_retains_results_and_cursor(self):
        calls=[]
        def request(url,headers=None):
            calls.append(url)
            if len(calls)>1:raise HTTPError(url,429,'rate',{},None)
            return {'data':[{'title':'a','url':'a','abstract':None}],'next':1,'total':3}
        r=search('semantic_scholar','q',request=request,pause=lambda _:None)
        self.assertEqual(r['status'],'PARTIAL');self.assertEqual(r['next_cursor'],1)
        self.assertEqual(r['results'][0]['abstract_status'],'MISSING')
    def test_repeat_page_stops(self):
        def request(url,headers=None):return {'message':{'items':[{'DOI':'10.1/a','title':['a']}],'next-cursor':'same'}}
        r=search('crossref','q',request=request,pause=lambda _:None)
        self.assertEqual(r['stop_reason'],'pagination_stalled');self.assertEqual(len(r['results']),1)
    def test_openalex_no_truncation(self):
        index={'word':list(range(400))}
        def request(url,headers=None):return {'results':[{'id':'x','abstract_inverted_index':index}],'meta':{'next_cursor':None,'count':1}}
        r=search('openalex','q',request=request)
        self.assertEqual(r['results'][0]['abstract'],inverted(index));self.assertGreater(len(r['results'][0]['abstract']),500)
    def test_arxiv_offset_and_summary(self):
        urls=[]
        def request(url,headers=None):
            urls.append(url);i=len(urls)
            return f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>2</o:totalResults><entry><id>{i}</id><title>title</title><summary>{"z"*1200}</summary></entry></feed>'.encode()
        r=search('arxiv','test',page_size=1,request=request,pause=lambda _:None)
        self.assertIn('start=1',urls[1]);self.assertEqual(r['stop_reason'],'exhausted');self.assertEqual(len(r['results'][0]['abstract']),1200)
    def test_doi_enrichment_rejects_wrong_record(self):
        def request(url,headers):
            if 'crossref' in url:return {'message':{'DOI':'10.1/wrong','abstract':'bad'}}
            return {'doi':'https://doi.org/10.1/a','abstract_inverted_index':{'right':[0]}}
        r=enrich([{'doi':'10.1/a'}],request=request,pause=lambda _:None)
        self.assertEqual(r['records'][0]['abstract'],'right');self.assertEqual(r['missing_abstracts'],[])
    def test_missing_and_no_doi_not_fabricated(self):
        r=enrich([{'title':'unknown'}],request=lambda *_:self.fail('no DOI lookup'))
        self.assertEqual(len(r['missing_abstracts']),1);self.assertEqual(r['lookup_records'],0)
    def test_merge_import_and_roundtrip(self):
        result,_=merge([{'doi':'10.1/a'},{'DI':'10.1/a','AB':'full abstract','source':'wos'}])
        self.assertEqual(result[0]['abstract'],'full abstract');self.assertEqual(result[0]['abstract_source'],'wos')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'merged.json';p.write_text(json.dumps({'records':result}))
            self.assertEqual(read(p)[0]['abstract'],'full abstract')
    def test_enrichment_limit(self):
        calls=[]
        def request(url,headers):calls.append(url);return {'message':{'DOI':'10.1/a','abstract':'full'}}
        r=enrich([{'doi':'10.1/a'},{'doi':'10.1/b'}],limit=1,request=request,pause=lambda _:None)
        self.assertEqual(len(calls),1);self.assertEqual(len(r['missing_abstracts']),1)
    def test_resume_offset(self):
        seen=[]
        def request(url,headers=None):
            seen.append(url);return {'data':[],'total':100}
        r=search('semantic_scholar','q',start='50',request=request)
        self.assertIn('offset=50',seen[0]);self.assertEqual(r['stop_reason'],'exhausted')
    def test_error_does_not_log_url_secrets(self):
        def request(*args):raise HTTPError('https://api/?api_key=secret',403,'secret',{},None)
        r=search('openalex','q',request=request)
        self.assertNotIn('secret',json.dumps(r));self.assertEqual(r['error']['http_status'],403)
    def test_offset_provider_uses_shared_pagination(self):
        offsets=[]
        def loader(source,query,size,token,request):
            offset=int(token or 0);offsets.append(offset)
            return [{'title':str(offset),'abstract':'complete'}],offset+1 if offset<1 else None,2,{}
        r=search('scopus','q',loader=loader,pause=lambda _:None)
        self.assertEqual(offsets,[0,1]);self.assertEqual(r['pages_retrieved'],2)
if __name__=='__main__':unittest.main()
