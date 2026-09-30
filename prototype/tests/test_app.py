import json, re, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from app import Store, make_server
SAMPLE={'fields':{'title':'Jaimika','client':'Клиент'},'costs':[],'result':{'total':100}}
class Tests(unittest.TestCase):
 def test_immutable_versions_and_persistence(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'db.sqlite3';s=Store(p);a=s.save(SAMPLE)
   changed=json.loads(json.dumps(SAMPLE));changed['result']['total']=200;b=s.save(changed,a);s=Store(p)
   self.assertEqual(s.get(a)['snapshot']['result']['total'],100)
   self.assertEqual(s.get(b)['snapshot']['result']['total'],200)
   self.assertEqual(s.get(b)['parent_id'],a);self.assertEqual(len(s.list()),2)
   with self.assertRaises(ValueError):s.save(SAMPLE,999)
 def test_http_save_open_and_access(self):
  with tempfile.TemporaryDirectory() as d:
   server=make_server(0,d);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
   try:
    url=f'http://127.0.0.1:{server.server_port}'
    token=re.search(r'name="bris-token" content="([^"]+)"',urllib.request.urlopen(url).read().decode()).group(1)
    def call(path,data=None,extra=None):
     headers={'X-BRIS-Token':token,'Content-Type':'application/json'};headers.update(extra or {})
     req=urllib.request.Request(url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
     return json.loads(urllib.request.urlopen(req).read())
    a=call('/api/calculations',{'snapshot':SAMPLE})['id']
    self.assertEqual(call(f'/api/calculations/{a}')['snapshot'],SAMPLE)
    self.assertEqual(call('/api/calculations')[0]['id'],a)
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(url+'/api/calculations')
    self.assertEqual(e.exception.code,403)
    with self.assertRaises(urllib.error.HTTPError) as e:call('/api/calculations',{'snapshot':SAMPLE},{'Origin':'https://example.com'})
    self.assertEqual(e.exception.code,403)
    with self.assertRaises(urllib.error.HTTPError) as e:call('/app.py')
    self.assertEqual(e.exception.code,404)
    with self.assertRaises(urllib.error.HTTPError) as e:call('/',extra={'Host':'foreign.example'})
    self.assertEqual(e.exception.code,403)
   finally:server.shutdown();server.server_close();t.join()
if __name__=='__main__':unittest.main()
