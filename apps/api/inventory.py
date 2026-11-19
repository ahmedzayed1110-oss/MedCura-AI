"""Tenant-local SQLite inventory. Caller holds BEGIN IMMEDIATE around each command."""
import hashlib
import json
import math
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from .science import forecast, reorder

DAY = "2026-11-19"
DEMO = "SYNTHETIC_DEMO"
BRANCHES = {"north": "Riyadh North", "east": "Riyadh East"}
APPROVERS = {"owner", "manager"}
WRITERS = APPROVERS | {"storekeeper"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def uid():
    return str(uuid4())


def rows(db, query, args=()):
    return [dict(r) for r in db.execute(query,args)]


def one(db, query, args=()):
    row = db.execute(query,args).fetchone()
    if row is None:
        raise ValueError("Record does not exist in this workspace.")
    return dict(row)


def integer(value, name, low=1, high=1_000_000):
    if isinstance(value,bool) or not isinstance(value,int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer from {low} to {high}.")
    return value


def word(value, name, size=80):
    if not isinstance(value,str) or not 0 < len(value.strip()) <= size or any(ord(c)<32 for c in value):
        raise ValueError(f"Enter a valid {name} (up to {size} characters).")
    return value.strip()


def check_role(user, roles):
    if user["role"] not in roles:
        raise PermissionError("This role cannot perform that action.")


def scope(user, branch):
    if branch not in BRANCHES or user.get("branch") not in (None,branch):
        raise PermissionError("Branch outside your assigned scope.")


def connect(path):
    db=sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sku(id TEXT PRIMARY KEY,name TEXT NOT NULL,unit TEXT NOT NULL,pack INTEGER NOT NULL CHECK(pack>0),expiry INTEGER NOT NULL,cost_minor INTEGER NOT NULL CHECK(cost_minor>=0));
CREATE TABLE IF NOT EXISTS lot(id TEXT PRIMARY KEY,branch TEXT NOT NULL,sku TEXT NOT NULL REFERENCES sku(id),code TEXT NOT NULL,expiry TEXT,quarantine INTEGER DEFAULT 0,UNIQUE(branch,sku,code));
CREATE TABLE IF NOT EXISTS ledger(seq INTEGER PRIMARY KEY,id TEXT UNIQUE NOT NULL,lot TEXT NOT NULL REFERENCES lot(id),kind TEXT NOT NULL,delta INTEGER NOT NULL,held INTEGER NOT NULL,day TEXT NOT NULL,stamp TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL,link TEXT,evidence_level TEXT NOT NULL DEFAULT 'SYNTHETIC_DEMO' CHECK(evidence_level='SYNTHETIC_DEMO'));
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'Immutable ledger'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'Immutable ledger'); END;
CREATE VIEW IF NOT EXISTS balance AS SELECT l.*,COALESCE(SUM(j.delta),0) AS physical,COALESCE(SUM(j.held),0) AS reserved FROM lot l LEFT JOIN ledger j ON l.id=j.lot GROUP BY l.id;
CREATE TABLE IF NOT EXISTS day_close(branch TEXT,sku TEXT,day TEXT,PRIMARY KEY(branch,sku,day));
CREATE TABLE IF NOT EXISTS transfer(id TEXT PRIMARY KEY,source TEXT REFERENCES lot(id),destination TEXT NOT NULL,qty INTEGER NOT NULL,transit_days INTEGER NOT NULL,freight INTEGER NOT NULL,status TEXT NOT NULL,approver TEXT,created TEXT NOT NULL,updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,branch TEXT NOT NULL,sku TEXT REFERENCES sku(id),qty INTEGER NOT NULL,status TEXT NOT NULL,eta TEXT NOT NULL,approver TEXT NOT NULL,run TEXT NOT NULL,created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS policy(branch TEXT,sku TEXT,lead INTEGER,review INTEGER,service INTEGER,moq INTEGER,capacity INTEGER,PRIMARY KEY(branch,sku));
CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,stamp TEXT NOT NULL,actor TEXT NOT NULL,path TEXT NOT NULL,detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS replay(actor TEXT NOT NULL,key TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(actor,key));
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,branch TEXT,sku TEXT,stamp TEXT,payload TEXT);
"""


def event(db, lot, kind, delta, held, actor, reason, link=None, day=DAY):
    b=one(db,"SELECT * FROM balance WHERE id=?",(lot,))
    physical=b["physical"]+delta
    reserved=b["reserved"]+held
    if physical<0 or reserved<0 or physical<reserved:
        raise ValueError("Insufficient unreserved stock for this movement.")
    db.execute("INSERT INTO ledger(id,lot,kind,delta,held,day,stamp,actor,reason,link) VALUES(?,?,?,?,?,?,?,?,?,?)",
               (uid(),lot,kind,delta,held,day,now(),actor,reason,link))


def get_lot(db, branch, sku, code, expiry, quarantine=False):
    s=one(db,"SELECT * FROM sku WHERE id=?",(sku,))
    if s["expiry"]:
        try:
            expiry=date.fromisoformat(expiry).isoformat()
        except (ValueError, TypeError):
            raise ValueError("This SKU requires a valid expiry date.") from None
    elif expiry:
        raise ValueError("This SKU has no expiry tracking.")
    else:
        expiry=None
    existing=db.execute("SELECT * FROM lot WHERE branch=? AND sku=? AND code=?",(branch,sku,code)).fetchone()
    if existing:
        if existing["expiry"]!=expiry or bool(existing["quarantine"])!=bool(quarantine):
            raise ValueError("The existing lot has different expiry or quarantine metadata.")
        return existing["id"]
    lot=uid()
    db.execute("INSERT INTO lot VALUES(?,?,?,?,?,?)",(lot,branch,sku,code,expiry,int(quarantine)))
    return lot


def init(db):
    db.executescript(SCHEMA)
    db.execute("BEGIN IMMEDIATE")
    try:
        if not db.execute("SELECT 1 FROM meta WHERE k='version'").fetchone():
            seed(db)
            db.execute("INSERT INTO meta VALUES('version','1')")
        db.commit()
    except Exception:
        db.rollback()
        raise


def seed(db):
    catalog=[("gloves","Nitrile gloves","glove",50,1,120),("masks","Procedure masks","mask",25,0,80),
             ("dressings","Sterile dressings","dressing",10,1,450)]
    db.executemany("INSERT INTO sku VALUES(?,?,?,?,?,?)",catalog)
    end=date.fromisoformat(DAY)
    for branch in BRANCHES:
        for idx,(sku,_,__,___,exp,____) in enumerate(catalog):
            use=[(2 if branch=="north" else 9)+idx+(i%7 in (0,1))*2+(i%17==5) for i in range(63)]
            residual=(210 if branch=="north" else 12)+idx*15
            lot=get_lot(db,branch,sku,"R-104",(end+timedelta(days=260)).isoformat() if exp else None)
            event(db,lot,"receive",sum(use)+residual,0,"demo-generator","Opening simulated delivery",day=(end-timedelta(days=64)).isoformat())
            for i,q in enumerate(use):
                d=(end-timedelta(days=63-i)).isoformat()
                event(db,lot,"issue",-q,0,"demo-generator","Recorded simulated consumption",day=d)
                db.execute("INSERT INTO day_close VALUES(?,?,?)",(branch,sku,d))
    short=get_lot(db,"north","gloves","G-NEAR",(end+timedelta(days=19)).isoformat())
    event(db,short,"receive",160,0,"demo-generator","Near-expiry simulated supplier lot")


def balances(db, branch=None):
    return rows(db,"""SELECT b.*,s.name,s.unit,s.pack,s.cost_minor,
        CASE WHEN quarantine=0 AND (b.expiry IS NULL OR b.expiry>?) THEN physical-reserved ELSE 0 END available
        FROM balance b JOIN sku s ON s.id=b.sku WHERE (? IS NULL OR branch=?) ORDER BY branch,name,b.expiry IS NULL,b.expiry,b.rowid""".replace("b.rowid","b.code"),(DAY,branch,branch))


def movement(db,u,kind,p):
    check_role(u,APPROVERS if kind in ("adjust","count") else WRITERS)
    branch=p.get("branch")
    scope(u,branch)
    sku=p.get("sku")
    s=one(db,"SELECT * FROM sku WHERE id=?",(sku,))
    reason=word(p.get("reason"),"reason",180)
    unit=p.get("unit","base")
    if unit not in ("base","pack"):
        raise ValueError("Unit must be base or pack.")
    qty=integer(p.get("qty"),"Quantity",-1_000_000 if kind=="adjust" else 0 if kind=="count" else 1)
    qty*=s["pack"] if unit=="pack" else 1
    if kind in ("receive","return"):
        if not isinstance(p.get("quarantine",False),bool):
            raise ValueError("Invalid quarantine flag.")
        lot=get_lot(db,branch,sku,word(p.get("code"),"lot code"),p.get("expiry"),kind=="return" or p.get("quarantine",False))
        event(db,lot,kind,qty,0,u["name"],reason)
        return {"lot":lot,"units":qty}
    items=[b for b in balances(db,branch) if b["sku"]==sku]
    if p.get("lot"):
        items=[b for b in items if b["id"]==p["lot"]]
    if kind in ("adjust","count","unreserve"):
        if not p.get("lot") or len(items)!=1:
            raise ValueError("Choose a matching lot.")
        b=items[0]
        if kind=="unreserve":
            generic=one(db,"SELECT COALESCE(SUM(held),0) n FROM ledger WHERE lot=? AND kind IN ('reserve','unreserve')",(b["id"],))["n"]
            if qty>generic:
                raise ValueError("Only a manual reservation can be released here.")
            event(db,b["id"],kind,0,-qty,u["name"],reason)
        else:
            event(db,b["id"],kind,qty-b["physical"] if kind=="count" else qty,0,u["name"],reason)
        return {"lot":b["id"],"units":qty}
    if kind not in ("reserve","issue"):
        raise ValueError("Unknown stock movement.")
    if sum(b["available"] for b in items)<qty:
        raise ValueError("Insufficient usable stock. Check reservations, quarantine and expiry.")
    remaining=qty
    allocations=[]
    for b in items:
        take=min(remaining,b["available"])
        if take:
            event(db,b["id"],kind,-take if kind=="issue" else 0,take if kind=="reserve" else 0,u["name"],reason)
            allocations.append({"lot":b["code"],"units":take})
            remaining-=take
        if not remaining:
            break
    return {"allocations":allocations,"units":qty}


def history(db, branch, sku):
    return rows(db,"""SELECT c.day AS date,COALESCE(SUM(-j.delta),0) AS qty FROM day_close c
        LEFT JOIN lot l ON l.branch=c.branch AND l.sku=c.sku
        LEFT JOIN ledger j ON j.lot=l.id AND j.day=c.day AND j.kind='issue'
        WHERE c.branch=? AND c.sku=? AND c.day<? GROUP BY c.day ORDER BY c.day""",(branch,sku,DAY))


def decision(db,branch,sku):
    s=one(db,"SELECT * FROM sku WHERE id=?",(sku,))
    policy=db.execute("SELECT * FROM policy WHERE branch=? AND sku=?",(branch,sku)).fetchone()
    params=dict(policy) if policy else dict(lead=5,review=7,service=90,moq=20,capacity=4000)
    fc=forecast(history(db,branch,sku),DAY,params["lead"]+params["review"])
    atp=sum(x["available"] for x in balances(db,branch) if x["sku"]==sku)
    orders=one(db,"SELECT COALESCE(SUM(qty),0) AS n FROM orders WHERE branch=? AND sku=? AND status='confirmed'",(branch,sku))["n"]
    incoming=one(db,"SELECT COALESCE(SUM(qty),0) AS n FROM transfer t JOIN lot l ON l.id=t.source WHERE destination=? AND l.sku=? AND status IN ('APPROVED','DISPATCHED')",(branch,sku))["n"]
    rec=reorder(fc,atp+orders+incoming,params["lead"],params["review"],params["service"]/100,s["pack"],params["moq"],params["capacity"])
    key=hashlib.sha256(json.dumps([fc["calculation_id"],branch,sku,rec,params,atp,orders,incoming],sort_keys=True).encode()).hexdigest()[:20]
    return dict(branch=branch,sku=sku,forecast=fc,reorder=rec,policy=params,atp=atp,orders=orders,incoming=incoming,
                eta=(date.fromisoformat(DAY)+timedelta(days=params["lead"])).isoformat(),run=key,evidence_level=DEMO)


def transfer_limit(db, lot, dest, days, cost, reserved_self=0, incoming_self=0):
    b=next((b for b in balances(db) if b["id"]==lot),None)
    if not b or b["branch"]==dest or dest not in BRANCHES or not b["expiry"] or b["quarantine"]:
        raise ValueError("Choose a usable dated lot and a different destination.")
    life=(date.fromisoformat(b["expiry"])-date.fromisoformat(DAY)).days
    remain=life-days-2
    a=decision(db,b["branch"],b["sku"])
    r=decision(db,dest,b["sku"])
    if remain<=0 or not a["forecast"]["chosen"] or not r["forecast"]["chosen"]:
        raise ValueError("Insufficient shelf life or closed demand history.")
    origin_daily=sum(a["forecast"]["future"])/len(a["forecast"]["future"])
    dest_daily=sum(r["forecast"]["future"])/len(r["forecast"]["future"])
    dest_committed=r["reorder"]["position"]-incoming_self
    origin_excess=max(0,b["available"]+reserved_self-math.ceil(life*origin_daily))
    safe=max(0,a["atp"]+reserved_self-a["reorder"]["point"])
    deficit=max(0,r["reorder"]["target"]-dest_committed)
    consumption=max(0,math.floor(remain*dest_daily)-dest_committed)
    cap=min(origin_excess,safe,deficit,consumption)
    return dict(limit=cap,net_minor=cap*b["cost_minor"]-cost,unit_minor=b["cost_minor"],origin_excess=origin_excess,
                safety_surplus=safe,destination_deficit=deficit,consumable=consumption,life_days=life,buffer_days=2,
                notes="Scenario assumes stable daily usage, linear sell-through and no incremental handling or shortage cost beyond the quoted all-in freight.")


def transfer_action(db,u,p):
    action=p.get("action","draft")
    if action=="draft":
        check_role(u,WRITERS)
        lot=one(db,"SELECT * FROM lot WHERE id=?",(p.get("lot"),))
        scope(u,lot["branch"])
        qty=integer(p.get("qty"),"Transfer units")
        days=integer(p.get("days",1),"Transport days",1,30)
        freight=integer(p.get("freight",1200),"All-in cost in halalas",0)
        dest=p.get("destination")
        gate=transfer_limit(db,lot["id"],dest,days,freight)
        if qty>gate["limit"] or qty*gate["unit_minor"]<=freight:
            raise ValueError("Transfer fails surplus, shelf-life, recipient need or net-value gate.")
        tid=uid()
        db.execute("INSERT INTO transfer VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,lot["id"],dest,qty,days,freight,"DRAFT",None,now(),now()))
        return {"id":tid,"status":"DRAFT"}
    t=one(db,"SELECT t.*,l.branch,l.sku,l.expiry,l.code FROM transfer t JOIN lot l ON l.id=t.source WHERE t.id=?",(p.get("id"),))
    scope(u,t["destination"] if action=="receive" else t["branch"])
    check_role(u,APPROVERS if action in ("approve","reject") else WRITERS)
    rules={"request":({"DRAFT"},"REQUESTED"),"approve":({"REQUESTED"},"APPROVED"),"reject":({"REQUESTED"},"REJECTED"),
           "dispatch":({"APPROVED"},"DISPATCHED"),"receive":({"DISPATCHED"},"RECEIVED"),"cancel":({"DRAFT","REQUESTED","APPROVED"},"CANCELLED")}
    if action not in rules or t["status"] not in rules[action][0]:
        raise ValueError("Illegal transfer transition.")
    qty=t["qty"]
    if action in ("request","approve","dispatch"):
        gate=transfer_limit(db,t["source"],t["destination"],t["transit_days"],t["freight"],
                            qty if action!="request" else 0,qty if action=="dispatch" else 0)
        if qty>gate["limit"] or qty*gate["unit_minor"]<=t["freight"]:
            raise ValueError("Current stock or destination need no longer supports this transfer.")
    if action=="request":
        event(db,t["source"],"transfer hold",0,qty,u["name"],action,t["id"])
    elif action=="dispatch":
        event(db,t["source"],"transfer out",-qty,-qty,u["name"],action,t["id"])
    elif action=="receive":
        arrival=p.get("arrival_day",DAY)
        try:
            arrival=date.fromisoformat(arrival).isoformat()
        except (TypeError,ValueError):
            raise ValueError("Enter a valid receipt date.") from None
        if arrival!=DAY or arrival>=t["expiry"]:
            raise ValueError("Receive on the active business date, within the usable shelf life.")
        destlot=get_lot(db,t["destination"],t["sku"],t["code"],t["expiry"])
        event(db,destlot,"transfer in",qty,0,u["name"],action,t["id"],arrival)
    elif action in ("reject","cancel") and t["status"]!="DRAFT":
        event(db,t["source"],"transfer release",0,-qty,u["name"],action,t["id"])
    status=rules[action][1]
    db.execute("UPDATE transfer SET status=?,approver=?,updated=? WHERE id=?",
               (status,u["name"] if action=="approve" else t["approver"],now(),t["id"]))
    return {"id":t["id"],"status":status}


def catalog(db,u,p):
    check_role(u,APPROVERS)
    code=word(p.get("id"),"SKU identifier",40)
    if not re.fullmatch(r"[a-zA-Z0-9_-]+",code):
        raise ValueError("Use letters, numbers, hyphens or underscores in the SKU code.")
    name=word(p.get("name"),"name")
    unit=word(p.get("unit"),"base unit",25)
    pack=integer(p.get("pack"),"Pack size")
    cost=integer(p.get("cost_minor"),"Unit cost (halalas)",0)
    exp=p.get("expiry")
    if not isinstance(exp,bool):
        raise ValueError("Specify whether lot expiry applies.")
    existing=db.execute("SELECT * FROM sku WHERE id=?",(code,)).fetchone()
    if existing and (existing["unit"]!=unit or existing["expiry"]!=exp):
        raise ValueError("Create a new SKU to change its base unit or expiry semantics.")
    db.execute("""INSERT INTO sku VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                  name=excluded.name,pack=excluded.pack,cost_minor=excluded.cost_minor""",(code,name,unit,pack,int(exp),cost))
    return {"id":code}

