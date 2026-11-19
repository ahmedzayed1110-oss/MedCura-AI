"""Regenerate T05 from the exact same ledger and forecasting code as the app."""
import csv
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api import inventory as inv

def main():
    db=inv.connect(":memory:")
    inv.init(db)
    result=inv.decision(db,"east","gloves")["forecast"]
    result.update(branch="Riyadh East",sku="Nitrile gloves")
    target=ROOT/"data"/"demo"
    target.mkdir(exist_ok=True,parents=True)
    (target/"backtest.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    with (target/"T05.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["evidence_level","cutoff",*result["scores"][0]])
        w.writeheader()
        w.writerows(dict(evidence_level=inv.DEMO,cutoff=result["cutoff"],**r) for r in result["scores"])
    print(result["chosen"],result["scores"])

if __name__=="__main__":
    main()

