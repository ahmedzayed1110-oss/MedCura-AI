"""Local development launcher. Python 3.12+. No third-party server dependencies."""
import argparse
import csv
import hashlib
import hmac
import io
import json
import logging
import mimetypes
import os
import re
import secrets
import sqlite3
import time
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Timer
from urllib.parse import urlsplit, parse_qs, unquote

from apps.api import inventory as inv, service, study

ROOT=Path(__file__).resolve().parent
LOG=logging.getLogger("medcura")
USERS={"director":("training","owner",None),"north.manager":("training","manager","north"),
       "east.manager":("training","manager","east"),"stores":("training","storekeeper","north"),
       "observer":("training","viewer",None),"audit":("training","auditor",None),"sandbox.director":("sandbox","owner",None)}
LIMIT=2_000_000


def sanitized(v):
    if isinstance(v,(dict,list)):
        v=json.dumps(v,ensure_ascii=False)
    if isinstance(v,str) and (v.lstrip().startswith(("=","+","-","@")) or v.startswith(("\t","\r","\n"))):
        return "'"+v
    return v


def as_csv(data):
    out=io.StringIO(newline="")
    if data:
        keys=list(dict.fromkeys(k for row in data for k in row))
        w=csv.DictWriter(out,keys)
        w.writeheader()
        w.writerows({k:sanitized(v) for k,v in r.items()} for r in data)
    return out.getvalue().encode("utf-8-sig")


class Settings:
    def __init__(self,folder):
        self.folder=Path(folder)
        self.folder.mkdir(exist_ok=True,parents=True)
        self.lock=Lock()
        self.sessions={}
        self.attempts={}
        self.ticket=None
        path=self.folder/"local-accounts.json"
        if not path.exists():
            with path.open("x", encoding="utf-8") as f:
                json.dump({u:secrets.token_urlsafe(18) for u in USERS},f,indent=2)
            path.chmod(0o600)
        accounts=json.loads(path.read_text())
        self.salt=secrets.token_bytes(24)
        self.passwords={u:self.digest(accounts[u]) for u in USERS}
        for tenant in {v[0] for v in USERS.values()}:
            db=self.db(tenant)
            try:
                inv.init(db)
                study.init(db)
            finally:
                db.close()

    def digest(self,p):
        return hashlib.scrypt(p.encode(),salt=self.salt,n=2**14,r=8,p=1)

    def db(self,tenant):
        return inv.connect(self.folder/(tenant+".sqlite3"))


class Handler(BaseHTTPRequestHandler):
    server_version="MedCuraLocal/1"
    def log_message(self,fmt,*args):
        LOG.info("%s %s",self.command,self.path.split("?")[0][:120])

    def send(self,status,body,mime="application/json",cookie=None,download=None):
        if mime=="application/json":
            body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        for key,value in {"Content-Type":mime,"Content-Length":str(len(body)),"X-Content-Type-Options":"nosniff",
                          "Cache-Control":"no-store","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer",
                          "X-Request-ID":self.rid,"Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items():
            self.send_header(key,value)
        if cookie:
            self.send_header("Set-Cookie",cookie)
        if download:
            self.send_header("Content-Disposition",'attachment; filename="'+download+'"')
        self.end_headers()
        self.wfile.write(body)

    def handle_app(self):
        self.rid=inv.uid()
        cfg=self.server.cfg
        try:
            port=self.server.server_port
            host=self.headers.get("Host","")
            if host not in {f"localhost:{port}",f"127.0.0.1:{port}"}:
                raise PermissionError("Use the local application address.")
            url=urlsplit(self.path)
            path=unquote(url.path)
            p={k:v[0] for k,v in parse_qs(url.query).items()}
            if self.command=="POST":
                origin=self.headers.get("Origin")
                if origin and origin!=f"http://{host}":
                    raise PermissionError("Origin rejected.")
                if self.headers.get_content_type()!="application/json":
                    raise ValueError("Use an application/json request.")
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=LIMIT:
                    raise ValueError("Empty or oversized request.")
                p=json.loads(self.rfile.read(length))
                if not isinstance(p,dict):
                    raise ValueError("Expected a JSON object.")
            if path=="/health" and self.command=="GET":
                return self.send(200,{"status":"ready","version":1})
            if path=="/api/login" and self.command=="POST":
                name=p.get("username")
                with cfg.lock:
                    tick=time.monotonic()
                    ticket_ok=bool(cfg.ticket and tick<cfg.ticket[1] and secrets.compare_digest(str(p.get("ticket","")),cfg.ticket[0]))
                    if ticket_ok:
                        cfg.ticket=None
                        name="director"
                    else:
                        recent=[v for v in cfg.attempts.get(self.client_address[0],[]) if tick-v<60]
                        if len(recent)>=20:
                            raise PermissionError("Too many sign-in attempts. Try again in one minute.")
                        password=p.get("password","")
                        if not isinstance(password,str) or len(password)>256 or not isinstance(name,str):
                            raise ValueError("Invalid credentials.")
                        if not hmac.compare_digest(cfg.digest(password),cfg.passwords.get(name,b"")):
                            cfg.attempts[self.client_address[0]]=recent+[tick]
                            raise PermissionError("Sign-in failed.")
                    token=secrets.token_urlsafe(32)
                    cfg.sessions={k:v for k,v in cfg.sessions.items() if v[1]>tick}
                    cfg.sessions[token]=(name,tick+8*3600)
                return self.send(200,{"signed_in":True},cookie=f"mc={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800")
            if self.command=="GET" and path in {"/","/app.js","/study.js","/style.css","/favicon.svg"}:
                f=ROOT/"apps"/"web"/("index.html" if path=="/" else path[1:])
                return self.file(f)
            cookies=SimpleCookie()
            cookies.load(self.headers.get("Cookie",""))
            token=cookies["mc"].value if "mc" in cookies else ""
            with cfg.lock:
                session=cfg.sessions.get(token)
            if not session or session[1]<time.monotonic():
                return self.send(401,{"error":"Sign in to the local workspace.","request_id":self.rid})
            name=session[0]
            tenant,role,branch=USERS[name]
            user=dict(name=name,tenant=tenant,role=role,branch=branch)
            if path=="/api/logout" and self.command=="POST":
                with cfg.lock:
                    cfg.sessions.pop(token,None)
                return self.send(200,{"signed_in":False},cookie="mc=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0")
            if self.command=="GET" and path=="/api/session":
                return self.send(200,user)
            if self.command=="GET" and path=="/openapi.json":
                return self.file(ROOT/"openapi.json")
            if self.command=="GET" and path.startswith("/assets/"):
                sections=("figures/","presentation/","docs/","data/templates/","data/processed/","data/demo/")
                tail=path[len("/assets/"):]
                if not tail.startswith(sections) or ".." in tail or "\\" in tail or ":" in tail:
                    raise LookupError("Asset unavailable.")
                f=(ROOT/tail).resolve()
                if not f.is_relative_to(ROOT) or f.suffix.lower() not in (".png",".svg",".pdf",".pptx",".md",".csv",".json",".xlsx",".mmd",".html"):
                    raise LookupError("Asset unavailable.")
                return self.file(f)
            db=cfg.db(tenant)
            try:
                if self.command=="GET" and path.startswith("/api/exports/"):
                    src={"market.csv":"/api/market/regions","conflicts.csv":"/api/evidence/conflicts","ledger.csv":"/api/ledger"}.get(path.rsplit("/",1)[1])
                    if not src:
                        raise LookupError("Unknown export.")
                    return self.send(200,as_csv(service.dispatch(db,user,"GET",src,p)),"text/csv; charset=utf-8",download=path.rsplit("/",1)[1])
                if self.command=="POST":
                    key=self.headers.get("Idempotency-Key","")
                    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,100}",key):
                        raise ValueError("An idempotency key of 8 to 100 characters is required.")
                    fingerprint=hashlib.sha256(json.dumps([path,p],sort_keys=True).encode()).hexdigest()
                    db.execute("BEGIN IMMEDIATE")
                    old=db.execute("SELECT * FROM replay WHERE actor=? AND key=?",(name,key)).fetchone()
                    if old:
                        if old["digest"]!=fingerprint:
                            raise ValueError("Key already used for a different command.")
                        result=json.loads(old["result"])
                    else:
                        result=service.dispatch(db,user,self.command,path,p)
                        db.execute("INSERT INTO replay VALUES(?,?,?,?)",(name,key,fingerprint,json.dumps(result)))
                        detail={k:v for k,v in p.items() if k in {"branch","sku","id","action","qty","reason","run","lot","unit","code"}}
                        detail["digest"]=fingerprint
                        db.execute("INSERT INTO audit VALUES(?,?,?,?,?)",(inv.uid(),inv.now(),name,path,json.dumps(detail)))
                    db.commit()
                else:
                    db.execute("BEGIN")
                    result=service.dispatch(db,user,self.command,path,p)
                    db.commit()
            finally:
                db.close()
            return self.send(200,result)
        except PermissionError as exc:
            self.send(403,{"error":str(exc),"request_id":self.rid})
        except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as exc:
            self.send(400,{"error":str(exc),"request_id":self.rid})
        except (FileNotFoundError,LookupError) as exc:
            self.send(404,{"error":str(exc),"request_id":self.rid})
        except (BrokenPipeError,ConnectionResetError):
            pass
        except Exception:
            LOG.exception("request failed %s",self.rid)
            self.send(500,{"error":"Internal error. See local server log.","request_id":self.rid})

    def file(self,f):
        if not f.is_file():
            raise FileNotFoundError("File unavailable.")
        mime=mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if mime.startswith("text/"):
            mime+="; charset=utf-8"
        if mime=="application/json":
            return self.send(200,json.loads(f.read_text(encoding="utf-8-sig")))
        self.send(200,f.read_bytes(),mime)

    do_GET=handle_app
    do_POST=handle_app


def server(folder,port=8765,bind="127.0.0.1"):
    cfg=Settings(folder)
    http=ThreadingHTTPServer((bind,port),Handler)
    http.cfg=cfg
    return http


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--open",action="store_true",help="Open a short-lived one-time local director session")
    ap.add_argument("--data-dir",default=os.environ.get("MEDCURA_DATA",str(ROOT/".local")))
    ap.add_argument("--port",type=int,default=8765)
    ap.add_argument("--container",action="store_true",help="Container network only; publish port on loopback")
    args=ap.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s")
    http=server(args.data_dir,args.port,"0.0.0.0" if args.container else "127.0.0.1")
    url=f"http://127.0.0.1:{http.server_port}"
    print(f"MedCura AI ready at {url}\nLocal sign-in file: {http.cfg.folder/'local-accounts.json'}",flush=True)
    if args.open:
        ticket=secrets.token_urlsafe(32)
        http.cfg.ticket=(ticket,time.monotonic()+90)
        Timer(.35,lambda:webbrowser.open(url+"/#ticket="+ticket)).start()
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()

if __name__=="__main__":
    main()

