"""Audit candidate or staged release paths. Does not read ignored private files."""
import argparse
import csv
from hashlib import sha256
import mimetypes
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    "absolute local path":re.compile(rb"(?:[A-Za-z]:[\\/]+Users[\\/]|[/]home/[^/\s]+/)",re.I),
    "token or private key":re.compile(rb"gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "patient identifier value":re.compile(rb"patient[_ -]?(?:id|name)[\x22']?\s*[:=]\s*[\x22']?[A-Za-z]*\d{4,}",re.I),
    "personal email":re.compile(rb"[\w.+-]+@(?:gmail|icloud|outlook|hotmail|yahoo)\.[a-z]{2,}",re.I)}
RESTRICTED=re.compile(r"(^|/)(\.env(?!\.example$)|\.local/|data/raw/|local-only/|pages_(guide|blueprint)\.json|.*\.(?:pem|key|sqlite3?|wal|shm|zip)(?:$|/))",re.I)

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT)

def audit(staged, manifest):
    mode=["--cached"] if staged else ["--cached","--others","--exclude-standard"]
    names=sorted(set(git("ls-files","-z",*mode).decode().strip("\0").split("\0")))
    failures=[]
    rows=[]
    for name in names:
        if name==manifest or not name:
            continue
        path=ROOT/name
        data=git("show",":"+name) if staged else path.read_bytes()
        if RESTRICTED.search(name) or len(data)>15_000_000:
            failures.append((name,"restricted name or >15 MB"))
        streams=[(name,data)]
        if path.suffix.lower() in (".pptx",".xlsx"):
            with ZipFile(path) as archive:
                if archive.testzip():
                    failures.append((name,"OOXML archive integrity"))
                for member in archive.namelist():
                    if member.endswith((".xml",".rels")):
                        xml=archive.read(member)
                        ElementTree.fromstring(xml)
                        streams.append((name+"#"+member,xml))
        for location,blob in streams:
            for label,pattern in PATTERNS.items():
                if pattern.search(blob):
                    failures.append((location,label))
        rows.append((name,len(data),sha256(data).hexdigest(),mimetypes.guess_type(name)[0] or "application/octet-stream"))
    if failures:
        for path,reason in failures:
            print(f"REVIEW {path}: {reason}")
        raise SystemExit(1)
    if not staged:
        with (ROOT/manifest).open("w",encoding="utf-8",newline="") as fp:
            w=csv.writer(fp)
            w.writerow(["path","bytes","sha256","content_type"])
            w.writerows(rows)
    print(f"Audit passed: {len(rows)} hashed artifacts; largest {max(rows,key=lambda r:r[1])[0]} ({max(r[1] for r in rows)} bytes). Manifest excludes its own hash.")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--staged",action="store_true")
    args=ap.parse_args()
    audit(args.staged,"docs/release/ARTIFACT_MANIFEST.csv")
