import json,tempfile,unittest
from pathlib import Path
from test_research_planning import fixture,refresh_approval,write_rows,rc
class InventoryCompatibility(unittest.TestCase):
 def test_inventory_copies_original_and_tracks_unavailable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=fixture((Path(tmp)/'MOCK-project').resolve());original=root/'papers/mock.md';original.write_text('MOCK original paper note, no real publication. Figure 1 page 1, own source.\n')
   p=rc.rb(root)/'literature/literature_visual_inventory.csv'
   write_rows(p,[dict(component_id='MOCK_F1',paper_id='mock_source',original_path='papers/mock.md',original_sha256=rc.sha(original),extracted_path='papers/not-downloaded.svg')])
   refresh_approval(root);out=root/'MANUSCRIPT_HANDOFF';report=rc.package(root,out)
   self.assertEqual(report['status'],'READY',report)
   self.assertTrue((out/'literature_visual_inventory.csv').exists());self.assertEqual((out/'papers/mock.md').read_bytes(),original.read_bytes())
   self.assertEqual([x['available'] for x in json.loads((out/'literature_asset_availability.json').read_text())],[True,False])
 def test_older_project_without_inventories(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=fixture((Path(tmp)/'MOCK-project').resolve())
   for p in (rc.rb(root)/'literature').glob('literature_*_inventory.csv'):p.unlink()
   refresh_approval(root);self.assertEqual(rc.package(root,root/'MANUSCRIPT_HANDOFF')['status'],'READY')
if __name__=='__main__':unittest.main()
