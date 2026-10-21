import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import search_sources as s
from corpus import read,merge
import json

class CnkiIntegrationTests(unittest.TestCase):
    def test_browser_handoff_never_claims_executed_search(self):
        with patch.object(s,'search',side_effect=AssertionError('Must not call index API')):
            with tempfile.TemporaryDirectory() as d:
                result=s.run('cnki','输电线路舞动',d)
                self.assertFalse(result['attempted'])
                self.assertEqual(result['results'],[])
                self.assertEqual(result['status'],'USER_ACTION_REQUIRED')
        self.assertNotIn('cnki',s.DEFAULT_SOURCES)
    def test_cnki_original_abstract_enriches_matching_doi_and_keeps_sources(self):
        long_abstract='合成测试摘要。'*1000
        cnki={'source':'cnki','results':[{'title':'DEMO','authors':'A','year':'2025','doi':'10.demo/a',
             'abstract':long_abstract,'abstract_source':'cnki','abstract_status':'PRESENT'}]}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'run.json';path.write_text(json.dumps(cnki))
            records=read(path)
        merged,conflicts=merge([{'source':'crossref','title':'DEMO','authors':'A','year':'2025','doi':'10.demo/a','abstract':''},*records])
        self.assertEqual(len(merged),1)
        self.assertEqual(merged[0]['abstract'],long_abstract)
        self.assertEqual(merged[0]['abstract_source'],'cnki')
        self.assertEqual({r['source'] for r in merged[0]['provenance_records']},{'crossref','cnki'})
    def test_truncated_excerpt_not_promoted_by_import(self):
        records=[{'source':'cnki','title':'DEMO','authors':'A','year':'2025','abstract':'',
                  'raw_excerpt':'截断内容...更多','abstract_status':'TRUNCATED'}]
        merged,_=merge(records)
        self.assertEqual(merged[0]['abstract'],'')
        self.assertEqual(merged[0]['abstract_status'],'TRUNCATED')

if __name__=='__main__':unittest.main()
