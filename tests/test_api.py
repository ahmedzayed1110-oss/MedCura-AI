import http.cookiejar
import os
from http.cookies import SimpleCookie
from types import SimpleNamespace
from tests.http_transport import response
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from uuid import uuid4

import run


class HTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.memory=os.environ.get("MEDCURA_HTTP_TRANSPORT")=="memory"
        if cls.memory:
            cls.srv=SimpleNamespace(cfg=run.Settings(cls.temp.name),server_port=8765)
        else:
            cls.srv=run.server(cls.temp.name,0)
            cls.t=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.t.start()
        cls.url="http://127.0.0.1:"+str(cls.srv.server_port)
        cls.accounts=json.loads((Path(cls.temp.name)/"local-accounts.json").read_text())

    @classmethod
    def tearDownClass(cls):
        if not cls.memory:
            cls.srv.shutdown();cls.t.join();cls.srv.server_close()
        cls.temp.cleanup()

    def setUp(self):
        self.cookie=SimpleCookie()
        self.client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def req(self,path,p=None,key=None,headers=None):
        hdr={"Content-Type":"application/json","Idempotency-Key":key or str(uuid4()),**(headers or {})}
        req=urllib.request.Request(self.url+path,data=json.dumps(p).encode() if p is not None else None,headers=hdr)
        if self.memory:
            hdr["Cookie"]=self.cookie.output(header="",sep=";").strip()
            r=response(self.srv,req.get_method(),path,hdr,req.data or b"")
            if r.getheader("Set-Cookie"):
                self.cookie.load(r.getheader("Set-Cookie"))
            status,body=r.status,r.read()
        else:
            try:
                with self.client.open(req,timeout=15) as r:status,body=r.status,r.read()
            except urllib.error.HTTPError as e:
                status,body=e.code,e.read()
        try:return status,json.loads(body)
        except (ValueError,UnicodeError):return status,body

    def login(self,name):
        self.assertEqual(self.req("/api/login",dict(username=name,password=self.accounts[name]))[0],200)

    def test_health_auth_and_origin(self):
        self.assertEqual(self.req("/health")[0],200)
        self.assertEqual(self.req("/api/state")[0],401)
        self.assertEqual(self.req("/api/login",dict(username="wrong",password="bad"))[0],403)
        self.login("director")
        self.assertEqual(self.req("/api/logout",{},headers={"Origin":"https://elsewhere.invalid"})[0],403)
        self.assertEqual(self.req("/api/logout",{})[0],200)
        self.assertEqual(self.req("/api/state")[0],401)

    def test_market_endpoints_and_lineage(self):
        self.login("observer")
        region=self.req("/api/market/regions")[1][0]
        self.assertEqual(self.req("/api/evidence/lineage/"+region["id"]+".complexes")[1]["value"],region["complexes"])
        self.assertIn(b"source_ref",self.req("/api/exports/market.csv")[1])
        self.assertEqual(self.req("/api/evidence/conflicts")[0],200)
        self.assertEqual(self.req("/api/skus",{})[0],403)

    def test_idempotent_write_and_tenant_isolation(self):
        self.login("director")
        p=dict(branch="north",sku="masks",qty=3,code="http-test",reason="api test",tenant="sandbox")
        path="/api/inventory/receive";k=str(uuid4())
        first=self.req(path,p,k);self.assertEqual(first[0],200)
        self.assertEqual(first,self.req(path,p,k))
        self.assertEqual(self.req(path,{**p,"qty":8},k)[0],400)
        self.assertEqual([v["physical"] for v in self.req("/api/lots")[1] if v["code"]=="http-test"],[3])
        self.login("sandbox.director")
        self.assertFalse(any(v["code"]=="http-test" for v in self.req("/api/lots?tenant=training")[1]))
        self.assertEqual(self.req("/api/inventory/count",dict(branch="north",sku="masks",lot=first[1]["lot"],qty=5,reason="cross tenant"))[0],400)

    def test_branch_scope(self):
        self.login("stores")
        self.assertEqual(set(v["branch"] for v in self.req("/api/lots")[1]),{"north"})
        self.assertEqual(self.req("/api/inventory/receive",dict(branch="east",sku="masks",qty=1,code="unauthorized",reason="test"))[0],403)
        self.assertEqual(self.req("/api/decisions/reorder?branch=east&sku=gloves")[0],403)
        self.assertEqual(self.req("/api/audit")[0],403)

    def test_csv_and_path_guards(self):
        self.assertIn(b"'=1+1",run.as_csv([dict(name="=1+1")]))
        self.login("observer")
        self.assertEqual(self.req("/assets/docs/../.local/local-accounts.json")[0],404)
        self.assertEqual(self.req("/api/state",{},headers={"Idempotency-Key":"bad"})[0],400)

    def test_transfer_receipt_replay(self):
        self.login("director")
        lot=next(v for v in self.req("/api/lots")[1] if v["code"]=="G-NEAR")
        tid=self.req("/api/transfers",dict(action="draft",lot=lot["id"],destination="east",qty=20,days=1,freight=1200))[1]["id"]
        for step in ["request","approve","dispatch"]:
            self.assertEqual(self.req("/api/transfers",dict(action=step,id=tid))[0],200)
        p=dict(action="receive",id=tid);k=str(uuid4())
        first=self.req("/api/transfers",p,k)
        self.assertEqual(first[0],200)
        self.assertEqual(self.req("/api/transfers",p,k),first)
        self.assertEqual(self.req("/api/transfers",p)[0],400)

