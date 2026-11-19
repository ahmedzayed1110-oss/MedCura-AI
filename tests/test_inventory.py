import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from apps.api import inventory as inv
from apps.api import service

OWNER=dict(name="director",role="owner",tenant="training",branch=None)
STORE=dict(name="stores",role="storekeeper",tenant="training",branch="north")


class Inventory(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.file=Path(self.folder.name)/"db"
        self.db=inv.connect(self.file)
        self.addCleanup(self.db.close)
        inv.init(self.db)

    def post(self,path,body,user=OWNER):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            result=service.dispatch(self.db,user,"POST","/api/"+path,body)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    def move(self,kind,**changes):
        p=dict(branch="north",sku="gloves",qty=3,reason="test count")
        return self.post("inventory/"+kind,{**p,**changes})

    def lot(self,code):
        return next(x for x in inv.balances(self.db,"north") if x["sku"]=="gloves" and x["code"]==code)

    def draft(self):
        return self.post("transfers",dict(action="draft",lot=self.lot("G-NEAR")["id"],destination="east",qty=25,days=1,freight=1200))["id"]

    def step(self,id,action,user=OWNER):
        return self.post("transfers",dict(id=id,action=action),user)

    def test_receive_pack_and_fefo(self):
        self.move("receive",qty=2,unit="pack",code="fresh",expiry="2027-12-01")
        self.assertEqual(self.lot("fresh")["physical"],100)
        self.assertEqual(self.move("issue",qty=170)["allocations"],[{"lot":"G-NEAR","units":160},{"lot":"R-104","units":10}])

    def test_expiry_quarantine_and_null(self):
        for code,expiry,quarantine in [("old",inv.DAY,False),("hold","2027-12-01",True)]:
            self.move("receive",code=code,expiry=expiry,quarantine=quarantine)
            with self.assertRaises(ValueError):
                self.move("issue",lot=self.lot(code)["id"])
        with self.assertRaises(ValueError):
            self.move("receive",code="bad")
        self.move("receive",sku="masks",code="no-expiry")

    def test_validation_and_immutable_ledger(self):
        before=self.lot("G-NEAR")["physical"]
        for p in [dict(qty=-1),dict(qty=1000000),dict(qty=1.5),dict(unit="crate"),dict(qty=True)]:
            with self.assertRaises(ValueError):
                self.move("issue",**p)
        self.assertEqual(self.lot("G-NEAR")["physical"],before)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE ledger SET delta=0")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM ledger")

    def test_count_and_reservation(self):
        lot=self.lot("G-NEAR")["id"]
        self.move("reserve",lot=lot,qty=30)
        with self.assertRaises(ValueError):
            self.move("count",lot=lot,qty=12)
        self.move("unreserve",lot=lot,qty=15)
        self.move("count",lot=lot,qty=40)
        self.assertEqual(self.lot("G-NEAR")["available"],25)
        with self.assertRaises(PermissionError):
            self.post("inventory/adjust",dict(branch="north",sku="gloves",lot=lot,qty=45,reason="test"),STORE)

    def test_transfer_conservation_and_incoming(self):
        original=sum(b["physical"] for b in inv.balances(self.db))
        t=self.draft()
        with self.assertRaises(ValueError):
            self.step(t,"dispatch")
        self.step(t,"request")
        with self.assertRaises(ValueError):
            self.move("unreserve",lot=self.lot("G-NEAR")["id"],qty=1)
        with self.assertRaises(PermissionError):
            self.step(t,"approve",STORE)
        self.step(t,"approve")
        position=lambda:inv.decision(self.db,"east","gloves")["reorder"]["position"]
        pos=position()
        self.step(t,"dispatch")
        self.assertEqual(sum(b["physical"] for b in inv.balances(self.db))+25,original)
        self.assertEqual(position(),pos)
        with self.assertRaises(ValueError):
            self.step(t,"cancel")
        self.step(t,"receive")
        self.assertEqual(position(),pos)
        self.assertEqual(sum(b["physical"] for b in inv.balances(self.db)),original)
        with self.assertRaises(ValueError):
            self.step(t,"receive")

    def test_cancel_releases_and_invalid_transport(self):
        t=self.draft();self.step(t,"request");self.step(t,"cancel")
        self.assertEqual(self.lot("G-NEAR")["reserved"],0)
        for days,cost in [(22,0),(1,50000)]:
            with self.assertRaises(ValueError):
                self.post("transfers",dict(action="draft",lot=self.lot("G-NEAR")["id"],destination="east",qty=25,days=days,freight=cost))

    def test_demo_ledger_survives_database_reopen(self):
        self.move("receive",sku="masks",qty=2,unit="pack",code="release-demo")
        mask_lot=next(x for x in inv.balances(self.db,"north") if x["code"]=="release-demo")
        self.move("issue",sku="masks",qty=3,lot=mask_lot["id"])
        transfer=self.draft()
        for action in ("request","approve","dispatch","receive"):
            self.step(transfer,action)
        self.db.close()
        reopened=inv.connect(self.file)
        self.addCleanup(reopened.close)
        restored=next(x for x in inv.balances(reopened,"north") if x["id"]==mask_lot["id"])
        self.assertEqual(restored["physical"],47)
        deltas=list(reopened.execute("SELECT delta FROM ledger WHERE lot=? ORDER BY seq",(restored["id"],)))
        self.assertEqual([x[0] for x in deltas],[50,-3])
        result=reopened.execute("SELECT qty,transit_days,freight,status FROM transfer WHERE id=?",(transfer,)).fetchone()
        self.assertEqual(tuple(result),(25,1,1200,"RECEIVED"))
        moves=reopened.execute("SELECT delta FROM ledger WHERE link=? AND delta<>0 ORDER BY seq",(transfer,))
        self.assertEqual([x[0] for x in moves],[-25,25])

    def test_order_receipt_and_stale_recommendation(self):
        d=inv.decision(self.db,"east","gloves")
        approval=dict(branch="east",sku="gloves",run=d["run"])
        order=self.post("decisions/reorder",approval)
        self.assertEqual(order["quantity"]%50,0)
        with self.assertRaises(ValueError):
            self.post("decisions/reorder",approval)
        old=inv.decision(self.db,"east","gloves")
        self.post("orders/receive",dict(id=order["id"],code="PO-1",expiry="2028-04-01"))
        new=inv.decision(self.db,"east","gloves")
        self.assertEqual(old["reorder"]["position"],new["reorder"]["position"])
        self.assertEqual(new["atp"]-old["atp"],order["quantity"])

    def test_negative_stock_concurrent(self):
        self.move("receive",qty=5,code="race",expiry="2028-01-01")
        lot=self.lot("race")["id"]
        gate=threading.Barrier(2)
        outcomes=[]
        def issue():
            db=inv.connect(self.file)
            gate.wait()
            try:
                db.execute("BEGIN IMMEDIATE")
                inv.movement(db,OWNER,"issue",dict(branch="north",sku="gloves",lot=lot,qty=4,reason="parallel"))
                db.commit();outcomes.append(True)
            except ValueError:
                db.rollback();outcomes.append(False)
            finally:
                db.close()
        threads=[threading.Thread(target=issue) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(sorted(outcomes),[False,True])
        self.assertEqual(self.lot("race")["physical"],1)

    def test_catalog_cold_start_and_reseed(self):
        s=dict(id="wipe",name="Test wipe",unit="wipe",pack=4,expiry=False,cost_minor=22)
        self.post("skus",s);self.post("skus",{**s,"name":"Updated"})
        self.assertIsNone(inv.decision(self.db,"north","wipe")["forecast"]["chosen"])
        with self.assertRaises(ValueError):
            self.post("skus",{**s,"unit":"carton"})
        before=self.db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        inv.init(self.db)
        self.assertEqual(before,self.db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0])
