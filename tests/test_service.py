import json, sqlite3, unittest
from moon_cake.workflow import Workflow
class ServiceTest(unittest.TestCase):
    def setUp(self): self.w = Workflow(sqlite3.connect(':memory:'))
    def test_idempotent_apply(self):
        a = self.w.apply('k','主体','approved',{'v':1},'甲','r1','2026-09-28T00:00:00+00:00')
        b = self.w.apply('k','主体','approved',{'v':1},'甲','r1','2026-09-28T00:00:00+00:00')
        self.assertEqual(a.version, b.version); self.assertEqual(len(self.w.show('k')['history']), 1)
    def test_history_and_summary(self):
        self.w.apply('a','甲','pending',{},'甲','r1','2026-09-28T00:00:00+00:00')
        self.w.apply('b','乙','approved',{'ok':1},'乙','r2','2026-09-28T00:00:00+00:00')
        self.assertEqual(self.w.summary()['total'], 2)
if __name__ == '__main__': unittest.main()
