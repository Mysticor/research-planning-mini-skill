import sys,unittest,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import acquire_fulltext as m
import fitz
R={'doi':'10.1234/test','title':'Accurate battery health prediction from measured experimental data'}
def pdf(text):
 d=fitz.open();p=d.new_page();p.insert_text((50,50),text);b=d.tobytes();d.close();return b
class Tests(unittest.TestCase):
 def test_pdf_identity(self):
  self.assertIsNotNone(m.validate(pdf(R['title']),R)[0]);self.assertIsNone(m.validate(pdf('Another unrelated paper\n10.1234/test'),R)[0])
 def test_abstract_is_not_fulltext(self):
  self.assertIsNone(m.validate(('<html><body>'+R['title']+' Abstract '+'text '*3000+'</body></html>').encode(),R)[0])
 def test_paywall_with_references_is_not_fulltext(self):
  data=('<html><body><article>'+R['title']+'<h2>Abstract</h2><h2>Access this article</h2><h2>References</h2>'+'introduction methods results discussion '*500+'</article></body></html>').encode()
  self.assertIsNone(m.validate(data,R)[0])
 def test_jats_body(self):
  data=('<?xml version="1.0"?><article><front><article-title>'+R['title']+'</article-title></front><body>'+''.join('<sec><title>'+h+'</title><p>'+'Scientific content. '*200+'</p></sec>' for h in ['Introduction','Methods','Results'])+'</body></article>').encode()
  self.assertEqual(m.validate(data,R)[0]['format'],'xml')
 def test_challenge_is_not_fulltext(self):
  self.assertIsNone(m.validate(b'<html>Verify you are human captcha</html>',R)[0])
 def test_merge_locations(self):
  r={'source_urls':['https://a.org/p'],'provenance_records':[{'pdf_urls':['https://b.org/p.pdf']}]}
  self.assertEqual(len(m.candidates(r)),2)
 def test_links_exclude_si_and_unrelated(self):
  html=R['title']+'<a href="/x.pdf">PDF</a><a href="/supp.pdf">Supporting</a>'
  self.assertEqual(m.page_links(html,'https://a.org/',R),['https://a.org/x.pdf'])
  self.assertEqual(m.page_links('<a href="/x.pdf">PDF</a>','https://a.org/',R),[])
 def test_fallback_and_resume(self):
  class C:
   def get(self,u):return ((pdf(R['title']),u,'application/pdf'),None) if u.endswith('good') else (None,'HTTP_403')
   def json(self,u):raise AssertionError('No resolver needed')
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);r={**R,'source_urls':['https://a.org/bad','https://a.org/good']}
   z=m.acquire(r,out,C());self.assertEqual(z['status'],'verified');self.assertEqual(len(z['attempts']),2)
   class Fail:
    def get(self,u):raise AssertionError('Resume should not fetch')
   self.assertEqual(m.acquire(r,out,Fail())['sha256'],z['sha256'])
 def test_manual_pdf(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);(out/'manual').mkdir();(out/'manual'/'p.pdf').write_bytes(pdf(R['title']))
   self.assertEqual(m.acquire(R,out,None)['source_url'],'user_provided')
if __name__=='__main__':unittest.main()
