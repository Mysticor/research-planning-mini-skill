import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import acquire_fulltext as m
import fitz
class NoNetwork:
 def get(self,u): raise AssertionError('CNKI must be manual')
 def json(self,u): raise AssertionError('CNKI must be manual')
class Tests(unittest.TestCase):
 def test_cnki_provenance_missing_and_resume(self):
  record={'title':'SYNTHETIC DEMO transmission line galloping measurement study','doi':'','provenance_records':[{'source':'cnki','url':'https://kns.cnki.net/example'}]}
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);r=m.acquire(record,out,NoNetwork())
   self.assertEqual(r['stop_reason'],'cnki_manual_download');self.assertEqual(r['attempts'],[])
   item=m.missing_item(r,out);self.assertEqual(item['url'],'https://kns.cnki.net/example')
   (out/'manual').mkdir();d=fitz.open();p=d.new_page();p.insert_text((50,50),record['title']);d.save(out/'manual'/'demo.pdf');d.close()
   got=m.acquire(record,out,NoNetwork());self.assertEqual(got['status'],'verified')
   self.assertNotIn('deep_read',got);self.assertEqual(got['version'],'unknown')
 def test_identification_sources_and_domains(self):
  for r in ({'source':'cnki'},{'sources':['openalex','cnki']},{'source_ids':{'cnki':'x'}},{'source_urls':['https://kns.cnki.net/a']}):self.assertTrue(m.cnki_record(r))
  self.assertFalse(m.cnki_record({'source_urls':['https://cnki.net.example.org/a']}))
 def test_wrong_manual_remains_missing(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);(out/'manual').mkdir();(out/'manual'/'fake.pdf').write_bytes(b'<html>login</html>')
   r=m.acquire({'title':'SYNTHETIC DEMO study','source':'cnki'},out,NoNetwork())
   self.assertEqual(r['status'],'missing')
if __name__=='__main__':unittest.main()
