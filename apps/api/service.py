"""HTTP-independent application dispatch for an authenticated tenant."""
import json
from pathlib import Path
from datetime import date
from . import inventory as inv
from . import study

ROOT=Path(__file__).resolve().parents[2]


def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))


def state(db,user):
    branch=user.get("branch")
    lots=inv.balances(db,branch)
    transfers=inv.rows(db,"""SELECT t.*,l.branch,l.code,l.sku FROM transfer t JOIN lot l ON l.id=t.source
            WHERE ? IS NULL OR l.branch=? OR t.destination=? ORDER BY created DESC""",(branch,branch,branch))
    alerts=[]
    for x in lots:
        if x["expiry"] and x["physical"]>0:
            days=(date.fromisoformat(x["expiry"])-date.fromisoformat(inv.DAY)).days
            if days<=30:
                alerts.append(dict(kind="Expiry review",branch=x["branch"],sku=x["sku"],detail=f'{x["code"]} · {days} days to expiry',days=days))
    catalog=inv.rows(db,"SELECT * FROM sku ORDER BY name")
    queue=[]
    for b in inv.BRANCHES:
        if branch and b!=branch:
            continue
        for s in catalog:
            d=inv.decision(db,b,s["id"])
            if d["reorder"]["quantity"]:
                queue.append(dict(branch=b,sku=s["id"],name=s["name"],**d["reorder"],run=d["run"]))
    candidates=[]
    for x in lots:
        if x["available"] and x["expiry"] and x["expiry"]<= "2027-01-18":
            for dest in inv.BRANCHES:
                if dest==x["branch"]:
                    continue
                try:
                    g=inv.transfer_limit(db,x["id"],dest,1,1200)
                except ValueError:
                    continue
                if g["limit"] and g["net_minor"]>0:
                    candidates.append(dict(lot=x["id"],source_branch=x["branch"],destination=dest,code=x["code"],sku=x["sku"],**g))
    return dict(user=user,day=inv.DAY,branches={b:n for b,n in inv.BRANCHES.items() if branch in (None,b)},
                stock=lots,skus=catalog,queue=queue,alerts=alerts,transfers=transfers,candidates=candidates,
                orders=inv.rows(db,"SELECT * FROM orders WHERE ? IS NULL OR branch=? ORDER BY created DESC",(branch,branch)),
                evidence_level=inv.DEMO)


def dispatch(db,user,method,path,p):
    if path.startswith("/api/pilot/") or path.startswith("/api/scenarios"):
        # Field/study authorizations are verified again by the study service.
        return study.route(db,method,path,p,user["tenant"],user["name"],user["role"])
    if method=="GET":
        files={"/api/market/regions":"data/processed/regions.json","/api/market/pareto":"data/processed/regions.json",
               "/api/market/metrics":"data/processed/metrics.json","/api/sources":"data/source_manifest.json",
               "/api/evidence/conflicts":"data/processed/conflicts.json","/api/evidence/lineage":"data/processed/lineage.json",
               "/api/competitors":"data/processed/competitors.json","/api/presentation":"presentation/story.json"}
        if path in files:
            return read_json(files[path])
        if path.startswith(("/api/evidence/lineage/","/api/market/metrics/")):
            key=path.rsplit("/",1)[1]
            dataset=read_json("data/processed/lineage.json" if "lineage" in path else "data/processed/metrics.json")
            if key not in dataset:
                raise LookupError("Unknown metric.")
            return dataset[key]
        if path=="/api/state":
            return state(db,user)
        if path in ("/api/branches","/api/inventory/balances","/api/skus","/api/lots","/api/transfers","/api/alerts"):
            key=path.rsplit("/",1)[1]
            return state(db,user)[{"balances":"stock","lots":"stock"}.get(key,key)]
        if path=="/api/ledger":
            branch=user.get("branch") or p.get("branch") or None
            if branch:
                inv.scope(user,branch)
            return inv.rows(db,"""SELECT j.*,l.code,l.sku,l.branch FROM ledger j JOIN lot l ON j.lot=l.id
                    WHERE ? IS NULL OR l.branch=? ORDER BY day DESC,seq DESC""",(branch,branch))
        if path=="/api/audit":
            inv.check_role(user,{"owner","auditor"})
            return inv.rows(db,"SELECT * FROM audit ORDER BY stamp DESC LIMIT 500")
    if path in ("/api/forecast/backtest","/api/decisions/reorder","/api/policy"):
        b=p.get("branch")
        sku=p.get("sku")
        inv.scope(user,b)
        if path=="/api/policy" and method=="POST":
            inv.check_role(user,inv.APPROVERS)
            inv.one(db,"SELECT id FROM sku WHERE id=?",(sku,))
            params=[inv.integer(p.get(k),k,lo,hi) for k,lo,hi in
                    [("lead",1,60),("review",1,60),("service",50,99),("moq",1,100000),("capacity",1,1000000)]]
            db.execute("INSERT OR REPLACE INTO policy VALUES(?,?,?,?,?,?,?)",(b,sku,*params))
        d=inv.decision(db,b,sku)
        if method=="POST":
            inv.check_role(user,inv.APPROVERS)
            db.execute("INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?)",(d["run"],b,sku,inv.now(),json.dumps(d)))
        if path=="/api/decisions/reorder" and method=="POST":
            inv.check_role(user,inv.APPROVERS)
            if p.get("run")!=d["run"] or d["reorder"]["quantity"]<=0:
                raise ValueError("The decision changed or no order is due. Refresh before approval.")
            oid=inv.uid()
            db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?)",
                (oid,b,sku,d["reorder"]["quantity"],"confirmed",d["eta"],user["name"],d["run"],inv.now()))
            return {"id":oid,"status":"confirmed","quantity":d["reorder"]["quantity"]}
        return d
    if method=="POST":
        if path=="/api/skus":
            return inv.catalog(db,user,p)
        if path.startswith("/api/inventory/"):
            return inv.movement(db,user,path.rsplit("/",1)[1],p)
        if path=="/api/transfers":
            return inv.transfer_action(db,user,p)
        if path=="/api/orders/receive":
            inv.check_role(user,inv.WRITERS)
            order=inv.one(db,"SELECT * FROM orders WHERE id=?",(p.get("id"),))
            inv.scope(user,order["branch"])
            if order["status"]!="confirmed":
                raise ValueError("Order already received.")
            result=inv.movement(db,user,"receive",dict(branch=order["branch"],sku=order["sku"],code=p.get("code"),
                expiry=p.get("expiry"),qty=order["qty"],reason="Receipt of order "+order["id"]))
            db.execute("UPDATE orders SET status='received' WHERE id=?",(order["id"],))
            return result
    raise LookupError("Unknown route.")

