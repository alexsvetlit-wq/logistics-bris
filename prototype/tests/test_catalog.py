import tempfile,unittest,sqlite3
from pathlib import Path
from app import Store
class CatalogTests(unittest.TestCase):
 def test_contact_changes_survive_restart_and_stale_writer_cannot_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'db.sqlite3';store=Store(path);old=store.catalog();data=store.catalog();data['providers'][0]['contacts'][0]['email']='test@example.org'
   store.save_catalog(data)
   self.assertEqual(Store(path).catalog()['providers'][0]['contacts'][0]['email'],'test@example.org')
   with self.assertRaises(ValueError):store.save_catalog(old)
   with store.connect() as con:self.assertEqual(con.execute('SELECT count(*) FROM catalog_history').fetchone()[0],1)
 def test_direct_rail_has_no_ocean_price_and_future_quotes_keep_source(self):
  with tempfile.TemporaryDirectory() as d:
   data=Store(Path(d)/'db.sqlite3').catalog();routes=[r for r in data['routes'] if r['mode']=='direct_rail'];self.assertEqual(len(routes),3)
   self.assertFalse(any(o['mode']=='direct_rail' for o in data['offers']))
   self.assertTrue(all(o['source_id'] for o in data['offers']))
   self.assertTrue(any(o['valid_from']=='2026-10-01' for o in data['offers']))
if __name__=='__main__':unittest.main()
