import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import extended_search as e
from public_search import search
from import_wos import parse,run
from enrich_abstracts import enrich
from corpus import merge

class ExtendedSearchTests(unittest.TestCase):
    def test_ieee_paging(self):
        calls=[]
        def request(url):
            calls.append(url);n=len(calls)
            return {'total_records':2,'articles':[{'title':str(n),'article_number':n,'abstract':'A'*3000,'doi':'10/test'+str(n)}]}
        with patch.object(e,'ieee_key',return_value='test'):
            r=search('ieee','query',2,page_size=1,loader=e.page,request=request,pause=lambda _:None)
        self.assertEqual(r['pages_retrieved'],2);self.assertIn('start_record=2',calls[1]);self.assertEqual(len(r['results'][1]['abstract']),3000)
    def test_pubmed_structured(self):
        xml='<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>7</PMID><Article><ArticleTitle>A <i>title</i></ArticleTitle><Abstract><AbstractText Label="METHODS">Study <i>one</i></AbstractText><AbstractText Label="RESULTS">Full result</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
        def request(url):return xml.encode() if 'efetch' in url else {'esearchresult':{'idlist':['7'],'count':'2'}}
        with patch.object(e.time,'sleep'):
            rows,nxt,total,_=e.page('pubmed','x',1,None,request)
        self.assertEqual(rows[0]['abstract'],'METHODS: Study one\nRESULTS: Full result');self.assertEqual(nxt,1)
    def test_pubmed_boundary(self):
        with self.assertRaises(ValueError):e.page('pubmed','x',10,10000,lambda _:self.fail('request beyond limit'))
    def test_scholar_no_external(self):
        html='<div id="gs_res_ccl"><div class="gs_ri"><h3 class="gs_rt"><a href="https://publisher.example/a">A paper</a></h3><div class="gs_rs">This is only a snippet</div></div></div>'
        with patch.object(e,'html_fetch',return_value=html) as fetch:
            rows,*_=e.page('google_scholar','x',50,None)
        self.assertEqual(fetch.call_count,1);self.assertEqual(rows[0]['abstract'],'');self.assertIn('num=10',fetch.call_args.args[0])
    def test_description_validation(self):
        html='<div id="gsc_oci_title">A paper</div><div class="gsc_oci_field">Description</div><div class="gsc_oci_value">Complete author abstract.</div>'
        self.assertEqual(e.scholar_description(html,'A paper')[1],'DESCRIPTION_CANDIDATE')
        self.assertEqual(e.scholar_description(html,'Another paper')[1],'IDENTITY_UNVERIFIED')
        self.assertEqual(e.scholar_description(html.replace('abstract.','abstract...'),'A paper')[0],'')
        self.assertFalse(e.description_url('https://publisher.example/citations?view_op=view_citation'))
    def test_description_preserved_not_promoted(self):
        detail='https://scholar.google.com/citations?view_op=view_citation&citation_for_view=abc'
        html=f'<div class="gs_ri"><h3 class="gs_rt"><a href="{detail}">A paper</a></h3></div>'
        desc='<div id="gsc_oci_title">A paper</div><div class="gsc_oci_field">Description</div><div class="gsc_oci_value">Study result</div>'
        with patch.object(e,'html_fetch',side_effect=[html,desc]),patch.object(e.time,'sleep'):
            rows,_,_,raw=e.page('google_scholar','x',10,None)
        self.assertEqual(rows[0]['abstract'],'');self.assertEqual(rows[0]['description'],'Study result');self.assertEqual(raw['description_pages'][detail],desc)
    def test_scholar_policy_survives_merge(self):
        rows,_=merge([{'title':'A','doi':'10/a','source':'crossref'},{'title':'A','doi':'10/a','source':'google_scholar','abstract_recovery_policy':'scholar_description_only'}])
        r=enrich(rows,request=lambda *a:self.fail('external request'),pause=lambda _:None)
        self.assertEqual(len(r['missing_abstracts']),1)
    def test_scholar_confirmed_result_merges_without_doi(self):
        r={'title':'A paper','source':'google_scholar','url':'https://example.org/paper','abstract':''}
        rows,_=merge([r,{**r,'abstract':'Verified complete abstract','abstract_source':'Scholar Description'}])
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['abstract'],'Verified complete abstract')
    def test_wos_multiline(self):
        text='FN Clarivate\nVR 1.0\nPT J\nTI A paper\nAB First\n   second\nUT WOS:1\nER\nEF\n'
        self.assertEqual(parse(text)[0]['abstract'],'First second')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.txt';p.write_text(text)
            self.assertEqual(run(p,Path(d)/'out','q',2)['status'],'PARTIAL')
        with self.assertRaises(ValueError):parse(text.replace('EF',''))

if __name__=='__main__':unittest.main()
