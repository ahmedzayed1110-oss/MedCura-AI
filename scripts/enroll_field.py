"""Local custodian operation. No demo accounts can be promoted to field tenants."""
import argparse
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api import study


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",type=Path,required=True,help="Directory of the separately provisioned field database")
    parser.add_argument("--tenant",required=True,help="Pre-provisioned field tenant ID")
    parser.add_argument("--authorization-ref",required=True,help="Coded custodian approval reference")
    args=parser.parse_args()
    tenant=study.safe_code(args.tenant,"tenant")
    if tenant in study.DEMO_TENANTS:
        parser.error("Training and sandbox tenants are permanently excluded.")
    path=(args.data_dir/(tenant+".sqlite3")).resolve()
    if not path.is_file():
        parser.error("No separately provisioned tenant database found.")
    db=sqlite3.connect(path.as_uri()+"?mode=rw",uri=True)
    try:
        with db:
            study.init(db)
            study.enroll(db,tenant,args.authorization_ref)
    finally:
        db.close()
    print("Field tenant approval recorded.")


if __name__ == "__main__":
    main()
