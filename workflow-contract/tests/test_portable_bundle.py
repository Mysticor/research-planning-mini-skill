import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('bundle', Path(__file__).resolve().parents[1] / 'portable_bundle.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'project'
        self.root.mkdir()
        (self.root / 'resume.md').write_text('SYNTHETIC/DEMO: 未精读，待本地下载', encoding='utf-8')
        (self.root / 'data.csv').write_text('id,value\nDEMO,1\n')
        self.out = self.base / 'step.zip'
    def pack(self, names=None, base=None):
        return b.pack(self.root, names or ['resume.md', 'data.csv'], '仅执行DEMO本地任务，返回失败记录。', self.out, base)
    def test_roundtrip_and_return(self):
        original = self.pack()
        self.assertEqual(b.verify(self.out)['bundle_id'], original['bundle_id'])
        local = self.base / 'local'
        local.mkdir()
        # Explicit staged import of known, verified test files, not automatic live merging.
        with zipfile.ZipFile(self.out) as z:
            for name in ('resume.md', 'data.csv'):
                (local / name).write_bytes(z.read('project/' + name))
        (local / 'result.md').write_text('SYNTHETIC/DEMO: 本地任务完成，未标记科学READY')
        ret = self.base / 'return.zip'
        b.pack(local, ['resume.md', 'data.csv', 'result.md'], '核对结果后继续', ret, original['bundle_id'])
        self.assertEqual(b.verify(ret, original['bundle_id'])['base_id'], original['bundle_id'])
        self.assertFalse((self.root / 'result.md').exists())
    def test_wrong_base(self):
        self.pack(base='old')
        with self.assertRaises(ValueError): b.verify(self.out, 'new')
    def test_tamper(self):
        self.pack()
        bad = self.base / 'bad.zip'
        with zipfile.ZipFile(self.out) as src, zipfile.ZipFile(bad, 'w') as dest:
            for name in src.namelist():
                dest.writestr(name, b'changed' if name == 'project/data.csv' else src.read(name))
        with self.assertRaises(ValueError): b.verify(bad)
    def test_no_overwrite(self):
        self.pack()
        with self.assertRaises(FileExistsError): self.pack()
    def test_traversal(self):
        with self.assertRaises(ValueError): self.pack(['../outside'])
    def test_no_secrets_paths(self):
        for name in ('.env', 'cookies.json', 'keys/private_key.pem'):
            with self.subTest(name=name), self.assertRaises(ValueError): self.pack([name])
    def test_symlink(self):
        (self.root / 'link.md').symlink_to(self.root / 'resume.md')
        with self.assertRaises(ValueError): self.pack(['link.md'])
    def test_duplicate_files(self):
        with self.assertRaises(ValueError): self.pack(['resume.md', 'resume.md'])
    def test_output_inside_project(self):
        with self.assertRaises(ValueError): b.pack(self.root, ['resume.md'], 'next', self.root / 'out.zip')

if __name__ == '__main__': unittest.main()
