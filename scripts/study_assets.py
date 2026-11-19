"""Regenerate measurement and scenario CSV assets from the application definitions."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api import study


METRICS = [
    ("Stockout incidence","New SKU stockout episodes","Observed eligible SKU-days with starts and hours","starts per 1,000 SKU-days","Continuing episodes have zero new starts. Closed or unobserved days are missing."),
    ("Stockout duration","Hours with zero usable stock","SKU-days with observed stockout hours","hours per SKU-day","Within a SKU-day count overlapping outages once. Maximum 24 hours."),
    ("Expiry quantity","Expired base units recorded","Tracked SKU-days with expiry values","base units summed","Combine units only for comparable base units. Inspect mix changes."),
    ("Expiry write-off","Sum of expired units times their actual weighted unit cost","Tracked SKU-days with expiry and cost","SAR summed","Use disposal records. Do not impute cost from procurement quotes."),
    ("Expiry share","Expiry write-off in SAR","Opening value plus new tracked receipts in SAR","percent","Count opening value once per window. Missing cost suppresses the metric when coverage is inadequate."),
    ("Counting effort","Counting hours attributed to this SKU","Standardized SKU-count sessions","hours per SKU session","Allocate a shared session's staff time once across observed SKUs. Keep scope constant."),
    ("Reconciliation discrepancy","Count lines differing from physical check","All counted lines","percent","Use the same line-level discrepancy tolerance in both periods."),
    ("Barcode adoption","Eligible CRUD events with successful scan","Eligible inventory events","percent","Exclude predeclared manual-only lines from both counts."),
    ("Correction rate","Entries requiring correction","All recorded entries","percent","Count each corrected entry once even when amended more than once."),
    ("Completeness","Eligible SKU-days with all core fields","Registered SKUs multiplied by local calendar days","percent","Core fields are issued, received, on_hand, stockout_hours, stockout_starts, scan_eligible, scanned."),
    ("Forecast error","Sum of absolute frozen forecast minus actual issues","Matched forecast/issue SKU-days","MAE in base units","Archive the forecast before each day begins. Issues can understate demand on stockout days."),
    ("Adherence","Reviewed alerts with a followed action","Eligible alerts","percent","Record reason codes for overrides in source records.")
]


def write(path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as dest:
        writer=csv.writer(dest)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    templates=ROOT/"data"/"templates"
    write(templates/"pilot_observations.csv",study.FIELDS,[])
    write(templates/"T03_pilot_protocol.csv",["measure","numerator","denominator_or_scope","unit","protocol_note","result_status"],[(*r,"Not measured") for r in METRICS])
    rows=[]
    for case,inputs in study.PRESETS.items():
        for k,label,unit,_,_ in study.DRIVERS:
            rows.append((case,"assumption","2027-2029",label,unit,inputs[k],"SCENARIO"))
        for year in study.calculate(inputs):
            for key in ("contracts","paying_branches","mrr","arr","revenue","cogs","gross_margin_pct","operating_result","break_even_branches"):
                units = {"contracts":"contracts","paying_branches":"branches","gross_margin_pct":"%","break_even_branches":"branches"}
                rows.append((case,"model output",year["year"],key,units.get(key,"SAR"),year[key],"SCENARIO"))
    write(ROOT/"data"/"demo"/"T04_scenario_sensitivity.csv",["case","type","window","driver_or_metric","unit","value","evidence_level"],rows)


if __name__ == "__main__":
    main()
