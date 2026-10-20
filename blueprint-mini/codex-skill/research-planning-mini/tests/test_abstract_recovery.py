import sys,unittest,json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse,parse_qs
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from public_search import fetch,page,normalize
from enrich_abstracts import enrich

class RecoveryTests(unittest.TestCase):
 def test_rate_limit_wait_then_success(self):
  waits=[];calls=[]
  def opener(req,timeout):
   calls.append(req)
   if len(calls)==1:raise HTTPError(req.full_url,429,'limited',{'Retry-After':'15'},None)
   return BytesIO(b'{"ok":true}')
  self.assertEqual(fetch('https://example.org',opener=opener,pause=waits.append),{'ok':True});self.assertEqual(waits,[15])
 def test_persistent_rate_limit_is_bounded(self):
  calls=[];waits=[]
  def opener(req,timeout):calls.append(req);raise HTTPError(req.full_url,429,'limited',{},None)
  with self.assertRaises(HTTPError):fetch('https://example.org',opener=opener,pause=waits.append)
  self.assertEqual(len(calls),3);self.assertEqual(waits,[12,24])
 def test_long_retry_after_no_premature_retry(self):
  def opener(req,timeout):raise HTTPError(req.full_url,429,'limited',{'Retry-After':'120'},None)
  with self.assertRaises(HTTPError):fetch('https://example.org',opener=opener,pause=lambda _:self.fail('must defer'))
 def test_forbidden_not_retried(self):
  def opener(req,timeout):raise HTTPError(req.full_url,403,'forbidden',{},None)
  with self.assertRaises(HTTPError):fetch('https://example.org',opener=opener,pause=lambda _:self.fail('no retry'))
 def test_crossref_cursor_retains_relevance_sort(self):
  def request(url):
   p=parse_qs(urlparse(url).query);self.assertEqual(p['sort'],['relevance']);self.assertEqual(p['order'],['desc']);self.assertEqual(p['cursor'],['next'])
   return {'message':{'items':[]}}
  page('crossref','wind turbine',10,'next',request)
 def test_supplement_doi_match_avoids_network(self):
  r=enrich([{'doi':'https://doi.org/10.1/A','title':'paper'}],supplements=[{'DI':'10.1/a','AB':'Original complete abstract','source':'publisher','url':'https://example.org/paper'}],request=lambda *_:self.fail('already have abstract'))
  self.assertEqual(r['records'][0]['abstract'],'Original complete abstract');self.assertEqual(r['lookup_records'],0)
 def test_title_match_without_doi_not_automerged(self):
  r=enrich([{'title':'paper'}],supplements=[{'doi':'10.1/a','title':'paper','abstract':'other'}])
  self.assertEqual(len(r['missing_abstracts']),1)
 def test_openalex_preserves_repository_links_and_type(self):
  r=normalize('openalex',{'type':'book','locations':[{'landing_page_url':'https://repo.edu/1','pdf_url':None}]})
  self.assertEqual(r['document_type'],'book');self.assertEqual(r['source_urls'],['https://repo.edu/1'])
if __name__=='__main__':unittest.main()
