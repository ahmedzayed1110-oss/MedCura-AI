"""Controlled software validations on synthetic data only. Costs are scenario assumptions."""
import json
import sys
from datetime import date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api import inventory as inv
from apps.api.science import forecast

def bench():
    db=inv.connect(":memory:")
    inv.init(db)
    user=dict(name="bench",role="owner",branch=None)
    d=inv.decision(db,"east","gloves")
    h=d["forecast"]["history"]
    today=date.fromisoformat(inv.DAY)
    def inventory_policy(dynamic):
        """Last 14 days independent, lots omitted. Compare explicit fixed min/max and demand-informed policy."""
        stock=40
        incoming=[]
        shortage=holding=0
        for i in range(len(h)-14,len(h)):
            stock+=sum(q for arrival,q in incoming if arrival==i)
            incoming=[v for v in incoming if v[0]>i]
            position=stock+sum(q for _,q in incoming)
            threshold,target=25,80
            if dynamic:
                fc=forecast(h[:i],h[i]["date"],12)
                from apps.api.science import reorder
                requested=reorder(fc,position,5,7,.90,50,20,4000)["quantity"]
            else:
                requested=100 if position<=threshold and position<target else 0
            if requested:
                incoming.append((i+5,requested))
            used=min(stock,h[i]["qty"])
            stock-=used
            shortage+=h[i]["qty"]-used
            holding+=stock
        return dict(shortage_units=shortage,unit_days_held=holding)
    spike=[dict(r) for r in h]
    spike[-1]["qty"]*=4
    missing=forecast(h[:-2]+h[-1:],inv.DAY)
    inv.movement(db,user,"return",dict(branch="east",sku="gloves",code="RET-1",expiry="2027-08-01",qty=7,reason="Returned unused pack, condition pending"))
    returned=next(b for b in inv.balances(db,"east") if b["code"]=="RET-1")
    origin=next(b for b in inv.balances(db,"north") if b["code"]=="G-NEAR")
    g=inv.transfer_limit(db,origin["id"],"east",1,1200)
    try:
        inv.transfer_limit(db,origin["id"],"east",20,1200)
        expired=False
    except ValueError:
        expired=True
    db.execute("INSERT INTO policy VALUES(?,?,?,?,?,?,?)",("east","gloves",10,7,90,20,4000))
    delay=inv.decision(db,"east","gloves")
    db.close()
    return dict(evidence_level=inv.DEMO,as_of=today.isoformat(),label="Software stress cases on generated issues",
                lead_delay=dict(before_point=d["reorder"]["point"],after_point=delay["reorder"]["point"]),
                demand_spike=dict(before=d["forecast"]["scores"][1],after=forecast(spike,inv.DAY)["scores"][1]),
                missing_scan=dict(fallback=missing["chosen"] is None,coverage=missing["coverage"]),
                return_quarantine=dict(physical=returned["physical"],available=returned["available"]),
                short_shelf_life_rejected=expired,redistribution=g,
                policy_comparison={"fixed threshold 25 / fixed order 100":inventory_policy(False),
                                   "rolling demand reorder policy":inventory_policy(True)},
                assumptions="14 simulated days; initial stock 40; 5-day deterministic supply lead; lost demand; zero backorders; integer items. No costs validated.")
if __name__=="__main__":
    r=bench()
    (ROOT/"data/demo/stress.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
    print("Wrote six simulated stress cases and fixed-policy comparison.")

