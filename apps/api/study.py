"""Tenant-scoped economics and prospective pilot evaluation. No external services."""
import csv
import hashlib
import io
import json
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP


DEMO_TENANTS = {"training", "sandbox"}
CODE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,47}\Z")
YEARS = (2027, 2028, 2029)
D = Decimal
GATES = [
    "Riyadh: register a one-branch baseline and clear data access.",
    "Makkah and Eastern Province: expand after pilot review and support readiness.",
    "Four additional regions: qualify each chain and review unit economics before rollout.",
]
CASES = {
    "Conservative": [8, 18, 28, 40, 35, 30, 1, 420, 1000, 1600, 100, 220, 18, 3800, 11000],
    "Base": [12, 25, 40, 50, 50, 50, 2, 600, 1500, 1200, 80, 170, 10, 3000, 9000],
    "Favorable": [18, 36, 55, 60, 60, 65, 3, 820, 2200, 900, 65, 135, 5, 2200, 8000],
}
DRIVERS = [
    ("reach_2027", "New reachable chain accounts in 2027", "accounts", 0, 10000),
    ("reach_2028", "New reachable chain accounts in 2028", "accounts", 0, 10000),
    ("reach_2029", "New reachable chain accounts in 2029", "accounts", 0, 10000),
    ("qualified_pct", "Qualified share of reached chains", "%", 0, 100),
    ("pilot_pct", "Pilot share of qualified chains", "%", 0, 100),
    ("conversion_pct", "Paid conversion of completed pilots", "%", 0, 100),
    ("branches", "Branches per paying chain", "branches", 1, 100),
    ("price", "Monthly subscription per branch", "SAR", 0, 100000),
    ("onboard_fee", "One-time onboarding fee per new chain", "SAR", 0, 1000000),
    ("deployment", "Deployment cost per new chain", "SAR", 0, 1000000),
    ("hosting", "Monthly hosting cost per active branch", "SAR", 0, 100000),
    ("support", "Monthly support cost per active branch", "SAR", 0, 100000),
    ("churn_pct", "Annual churn of opening contracts", "%", 0, 100),
    ("cac", "Acquisition expense per new paying chain", "SAR", 0, 1000000),
    ("fixed", "Monthly fixed operating expense", "SAR", 0, 1000000),
]
PRESETS = {k: dict(zip([r[0] for r in DRIVERS], v)) for k, v in CASES.items()}
FIELDS = ("branch", "sku", "lot", "date", "issued", "received", "on_hand", "stockout_hours",
          "stockout_starts", "expired_qty", "unit_cost_sar", "tracked_value_added_sar",
          "counting_hours", "count_sessions", "scan_eligible", "scanned", "entries",
          "corrected", "count_lines", "discrepant_lines", "alerts", "actions_followed", "prior_forecast")
COUNTS = set("issued received on_hand stockout_starts expired_qty count_sessions scan_eligible scanned entries corrected count_lines discrepant_lines alerts actions_followed".split())
CORE = ("issued", "received", "on_hand", "stockout_hours", "stockout_starts", "scan_eligible", "scanned")
PROTOCOL = {"branch": "RUH-PILOT", "skus": ["GLV", "MSK", "DRS"], "baseline_start": "2027-01-04",
            "baseline_end": "2027-01-31", "intervention": "2027-02-01", "post_start": "2027-02-08",
            "post_end": "2027-03-07", "minimum_days": 28, "completeness_pct": 95,
            "scan_pct": 85, "improvement_pct": 10, "integration_reviewed": False,
            "security_reviewed": False, "confounders": []}
FLAGS = ["Seasonality", "Staffing change", "Supplier delay", "SKU scope change", "Closures", "Stock rationing"]
SCENARIO_WRITERS = {"owner", "manager"}
def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_today():
    return datetime.now(timezone(timedelta(hours=3))).date()


def init(db):
    """Called during migration. Do not commit the caller's surrounding transaction."""
    ddl = (
        "CREATE TABLE IF NOT EXISTS study_scenarios (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL, saved TEXT NOT NULL, name TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS study_scenario_tenant ON study_scenarios(tenant, saved)",
        "CREATE TABLE IF NOT EXISTS study_protocol (tenant TEXT PRIMARY KEY, actor TEXT NOT NULL, saved TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS study_reviews (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL, saved TEXT NOT NULL, payload TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS study_access (tenant TEXT PRIMARY KEY, authorization_ref TEXT NOT NULL, created TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS study_imports (id TEXT PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL, saved TEXT NOT NULL, reference TEXT NOT NULL, digest TEXT NOT NULL, auth_ref TEXT NOT NULL, protocol TEXT NOT NULL, UNIQUE(tenant,digest))",
        "CREATE TABLE IF NOT EXISTS study_days (tenant TEXT NOT NULL, sku TEXT NOT NULL, day TEXT NOT NULL, batch TEXT NOT NULL REFERENCES study_imports(id), payload TEXT NOT NULL, PRIMARY KEY(tenant,sku,day))",
    )
    for stmt in ddl:
        db.execute(stmt)


def num(value, label, minimum=0, maximum=10**9, integer=False):
    try:
        n = D(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be numeric") from None
    if not n.is_finite() or n < minimum or n > maximum or (integer and n != n.to_integral_value()):
        raise ValueError(f"{label} must be {'a whole number ' if integer else ''}between {minimum} and {maximum}")
    if n.as_tuple().exponent < -4:
        raise ValueError(f"{label} permits up to four decimal places")
    return n


def safe_code(value, name):
    if not isinstance(value, str) or not CODE.fullmatch(value):
        raise ValueError(f"{name} must be a coded identifier (letters, digits, hyphen or underscore)")
    return value


def fields(body, allowed):
    if not isinstance(body, dict) or set(body) - set(allowed):
        raise ValueError("Unknown or invalid input fields")


def money(n):
    return float(D(n).quantize(D(".01"), rounding=ROUND_HALF_UP))


def ratio(n, d, scale=100):
    return money(D(n) * scale / D(d)) if d else None


def calculate(inputs):
    if not isinstance(inputs, dict) or set(inputs) != {d[0] for d in DRIVERS}:
        raise ValueError("Supply every named scenario assumption")
    p = {key: num(inputs[key], label, lo, hi, unit in {"accounts", "branches"})
         for key, label, unit, lo, hi in DRIVERS}
    opening = 0
    rows = []
    for year, gate in zip(YEARS, GATES):
        reached = int(p[f"reach_{year}"])
        qualified = int(reached * p["qualified_pct"] / 100)
        pilots = int(qualified * p["pilot_pct"] / 100)
        new = int(pilots * p["conversion_pct"] / 100)
        lost = int((opening * p["churn_pct"] / 100).to_integral_value(rounding=ROUND_HALF_UP))
        retained = opening - lost
        closing = retained + new
        branches = int(p["branches"])
        branch_months = branches * (retained * 12 + new * 6)
        mrr = branches * closing * p["price"]
        revenue = branch_months * p["price"] + new * p["onboard_fee"]
        cogs = branch_months * (p["hosting"] + p["support"]) + new * p["deployment"]
        gross = revenue - cogs
        unit_margin = p["price"] - p["hosting"] - p["support"]
        be = int((p["fixed"] / unit_margin).to_integral_value(rounding=ROUND_CEILING)) if unit_margin > 0 else None
        rows.append(dict(year=year, gate=gate, reachable=reached, qualified=qualified, pilots=pilots,
                         new_contracts=new, churned=lost, retained=retained, contracts=closing, paying_branches=closing*branches,
                         branch_months=branch_months, mrr=money(mrr), arr=money(mrr*12), revenue=money(revenue),
                         cogs=money(cogs), gross_profit=money(gross), gross_margin_pct=ratio(gross, revenue),
                         acquisition=money(new*p["cac"]), operating_result=money(gross-new*p["cac"]-12*p["fixed"]),
                         break_even_branches=be, evidence_level="SCENARIO"))
        opening = closing
    return rows


def scenario_state(db, tenant):
    records = db.execute("SELECT id,name,saved,payload FROM study_scenarios WHERE tenant=? ORDER BY rowid DESC LIMIT 20", (tenant,)).fetchall()
    return dict(evidence_level="SCENARIO", drivers=DRIVERS, presets=PRESETS, gates=GATES,
                saved=[dict(id=r[0], name=r[1], saved=r[2], **json.loads(r[3])) for r in records],
                comparison={k: calculate(v) for k,v in PRESETS.items()}, target_chain_population=None)


def get_protocol(db, tenant):
    row = db.execute("SELECT payload FROM study_protocol WHERE tenant=?", (tenant,)).fetchone()
    return json.loads(row[0]) if row else dict(PROTOCOL)


def day(value, name):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed
    except (ValueError, TypeError):
        raise ValueError(f"{name} requires YYYY-MM-DD") from None


def validate_protocol(p):
    fields(p, PROTOCOL)
    if set(p) != set(PROTOCOL):
        raise ValueError("Supply the full pilot protocol")
    safe_code(p["branch"], "branch")
    skus = p["skus"]
    if not isinstance(skus, list) or not 1 <= len(skus) <= 50:
        raise ValueError("Register 1 to 50 eligible SKU codes")
    for sku in skus:
        safe_code(sku, "sku")
    if len(set(skus)) != len(skus):
        raise ValueError("Duplicate SKU code")
    b0,b1,i,p0,p1 = [day(p[key],key) for key in ("baseline_start","baseline_end","intervention","post_start","post_end")]
    if not b0 <= b1 < i <= p0 <= p1 or (p1-b0).days > 730:
        raise ValueError("Baseline and post windows must be ordered, disjoint, and span at most two years")
    result = dict(p)
    result["minimum_days"] = int(num(p["minimum_days"], "Minimum days", 7, 366, True))
    if min((b1-b0).days+1,(p1-p0).days+1) < result["minimum_days"]:
        raise ValueError("Both registered windows must meet the minimum length")
    for k in ("completeness_pct","scan_pct","improvement_pct"):
        result[k] = float(num(p[k],k,1,100))
    for k in ("integration_reviewed","security_reviewed"):
        if not isinstance(p[k],bool):
            raise ValueError("Review flags must be Boolean")
    if not isinstance(p["confounders"],list) or any(x not in FLAGS for x in p["confounders"]):
        raise ValueError("Select recognized confounding factors")
    return result


def read_csv(body, p):
    name, raw = body.get("filename"), body.get("csv")
    if not isinstance(name,str) or not name.lower().endswith(".csv") or not isinstance(raw,str):
        raise ValueError("Choose a UTF-8 CSV with the supplied header")
    if len(raw.encode("utf-8")) > 180000 or "\x00" in raw:
        raise ValueError("CSV exceeds 180 KB or contains binary content")
    try:
        reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff"), newline=""),strict=True)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Header must exactly match the template. Remove all extra fields.")
        results = []
        keys = set()
        today = local_today()
        for line,row in enumerate(reader,2):
            if line > 1201:
                raise ValueError("The import limit is 1,200 SKU-days")
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"Row {line}: incorrect field count")
            try:
                if row["branch"] != p["branch"] or row["sku"] not in p["skus"]:
                    raise ValueError("Branch or SKU is outside the registered scope")
                if row["lot"]:
                    safe_code(row["lot"],"lot")
                dt = day(row["date"],"date")
                if dt > today:
                    raise ValueError("Future observations cannot be submitted")
                if not any(p[k+"_start"] <= row["date"] <= p[k+"_end"] for k in ("baseline","post")):
                    raise ValueError("Observation falls outside both windows")
                key = (row["sku"],row["date"])
                if key in keys:
                    raise ValueError("Duplicate SKU-day; aggregate all lots once")
                keys.add(key)
                for k in FIELDS[4:]:
                    row[k] = None if row[k] == "" else str(num(row[k],k,0,24 if k=="stockout_hours" else 10**9,k in COUNTS))
                for n,d in [("scanned","scan_eligible"),("corrected","entries"),("discrepant_lines","count_lines"),("actions_followed","alerts")]:
                    if (row[n] is None) != (row[d] is None) or (row[n] is not None and D(row[n]) > D(row[d])):
                        raise ValueError(f"Supply a valid {n}/{d} pair or leave both blank")
                if not any(v is not None for k,v in row.items() if k in CORE):
                    raise ValueError("At least one core observation is required")
                if (row["stockout_starts"] is not None and D(row["stockout_starts"]) > 0
                        and row["stockout_hours"] is not None and D(row["stockout_hours"]) == 0):
                    raise ValueError("Stockout starts require positive observed duration")
            except ValueError as exc:
                raise ValueError(f"Row {line}: {exc}") from None
            results.append(row)
        if not results:
            raise ValueError("Template has no observation rows")
        return results
    except csv.Error:
        raise ValueError("Malformed CSV") from None


def summarize(rows, start, end, p):
    rows = [r for r in rows if start <= r["date"] <= end]
    expected = ((day(end,"end") - day(start,"start")).days+1) * len(p["skus"])
    complete = [r for r in rows if all(r[k] is not None for k in CORE)]
    coverage = ratio(len(complete), expected)
    qualified = coverage >= p["completeness_pct"] and all(sum(r["sku"] == sku for r in complete) >= p["minimum_days"] for sku in p["skus"])
    out = dict(expected_sku_days=expected, received_sku_days=len(rows), complete_sku_days=len(complete),
               completeness_pct=coverage, sufficient=qualified, metrics={}, observed_days={})
    def metric(name, keys, f):
        eligible = [r for r in rows if all(r[k] is not None for k in keys)]
        out["observed_days"][name] = len(eligible)
        covered = eligible and len(eligible)*100 >= expected*p["completeness_pct"]
        out["metrics"][name] = f(eligible) if qualified and covered else None
    def total(rr,k):
        return sum(D(r[k]) for r in rr)
    metric("stockout_starts_per_1000_sku_days",["stockout_starts","stockout_hours"],lambda rr: ratio(total(rr,"stockout_starts"),len(rr),1000))
    metric("stockout_hours_per_sku_day",["stockout_hours"],lambda rr: ratio(total(rr,"stockout_hours"),len(rr),1))
    metric("expired_units",["expired_qty"],lambda rr: int(total(rr,"expired_qty")))
    metric("expiry_writeoff_sar",["expired_qty","unit_cost_sar"],lambda rr: money(sum(D(r["expired_qty"])*D(r["unit_cost_sar"]) for r in rr)))
    metric("expiry_pct_of_tracked_value",["expired_qty","unit_cost_sar","tracked_value_added_sar"],lambda rr: ratio(sum(D(r["expired_qty"])*D(r["unit_cost_sar"]) for r in rr),total(rr,"tracked_value_added_sar")))
    metric("counting_hours_per_session",["counting_hours","count_sessions"],lambda rr: ratio(total(rr,"counting_hours"), total(rr,"count_sessions"),1))
    for name,n,d in [("barcode_adoption_pct","scanned","scan_eligible"),("correction_pct","corrected","entries"),
                     ("discrepancy_pct","discrepant_lines","count_lines"),("adherence_pct","actions_followed","alerts")]:
        metric(name,[n,d],lambda rr: ratio(total(rr,n),total(rr,d)))
    metric("forecast_mae_units",["prior_forecast","issued"],lambda rr: ratio(sum(abs(D(r["prior_forecast"])-D(r["issued"])) for r in rr),len(rr),1))
    return out


def report(db, tenant):
    p = get_protocol(db,tenant)
    reviews = [dict(actor=r[0],saved=r[1],**json.loads(r[2])) for r in db.execute(
        "SELECT actor,saved,payload FROM study_reviews WHERE tenant=? ORDER BY rowid DESC",(tenant,))]
    review = reviews[0] if reviews else p
    rows = [json.loads(r[0]) for r in db.execute("SELECT payload FROM study_days WHERE tenant=?",(tenant,))]
    baseline,post = [summarize(rows,p[k+"_start"],p[k+"_end"],p) for k in ("baseline","post")]
    m = "stockout_starts_per_1000_sku_days"
    a,b = baseline["metrics"][m],post["metrics"][m]
    change = ratio(D(str(a))-D(str(b)), D(str(a))) if a and b is not None else None
    adoption = post["metrics"]["barcode_adoption_pct"]
    if not rows:
        decision = "Not measured"
    elif not (review["security_reviewed"] and review["integration_reviewed"]):
        decision = "No-go: complete safety and integration review"
    elif not all(x["sufficient"] for x in (baseline,post)) or change is None or adoption is None:
        decision = "Hold: evidence insufficient"
    elif review["confounders"] or adoption < p["scan_pct"] or change < p["improvement_pct"]:
        decision = "Pivot: investigate comparability, adoption or KPI change"
    else:
        decision = "Eligible for human go review"
    batches = [dict(id=r[0],reference=r[1],sha256=r[2],actor=r[3],imported_at=r[4],authorization=r[5]) for r in
               db.execute("SELECT id,reference,digest,actor,saved,auth_ref FROM study_imports WHERE tenant=? ORDER BY saved",(tenant,))]
    enrollment = db.execute("SELECT 1 FROM study_access WHERE tenant=?",(tenant,)).fetchone()
    return dict(protocol=p, reviews=reviews, confounder_options=FLAGS, field_enabled=bool(enrollment and tenant not in DEMO_TENANTS),
                evidence_level="PILOT_MEASURED" if batches else "UNKNOWN", decision=decision,
                baseline=baseline, post=post, stockout_incidence_improvement_pct=change, imports=batches,
                uncertainty="Single-site descriptive association. Clustered SKU-days preclude an independent-day interval. A stable causal effect and precision interval require additional independent sites or time blocks.")


def enroll(db, tenant, authorization):
    safe_code(tenant,"tenant")
    safe_code(authorization,"authorization")
    if tenant in DEMO_TENANTS:
        raise ValueError("Seeded demo tenants are permanently ineligible for field imports")
    db.execute("INSERT INTO study_access VALUES(?,?,?)",(tenant,authorization,now()))


def route(db, method, path, body, tenant, actor, role):
    if not tenant or not actor:
        raise PermissionError("An authenticated tenant session is required")
    if method == "GET":
        if path == "/api/scenarios":
            return scenario_state(db,tenant)
        if path in {"/api/pilot/report","/api/pilot/measurements"}:
            return report(db,tenant)
        if path == "/api/pilot/protocol":
            return get_protocol(db,tenant)
        if path == "/api/pilot/template":
            return {"csv": ",".join(FIELDS)+"\r\n", "columns":FIELDS}
    if method != "POST":
        raise ValueError("Unsupported study route")
    if path == "/api/scenarios/preview":
        fields(body,["assumptions"])
        return {"evidence_level":"SCENARIO","years":calculate(body.get("assumptions"))}
    if role not in SCENARIO_WRITERS:
        raise PermissionError("Owner or manager access required")
    if path == "/api/scenarios":
        fields(body,["name","assumptions"])
        name = body.get("name","")
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,47}",name):
            raise ValueError("Use a scenario name of 1–48 letters, digits, spaces, hyphens or underscores")
        params = body.get("assumptions")
        years = calculate(params)
        payload = dict(assumptions=params, years=years, evidence_level="SCENARIO")
        key = str(uuid.uuid4())
        db.execute("INSERT INTO study_scenarios VALUES(?,?,?,?,?,?)",(key,tenant,actor,now(),name,json.dumps(payload)))
        return dict(id=key,name=name,**payload)
    if path == "/api/pilot/protocol":
        p = validate_protocol(body)
        if db.execute("SELECT 1 FROM study_imports WHERE tenant=?",(tenant,)).fetchone():
            raise ValueError("Protocol is locked after first field import")
        if tenant not in DEMO_TENANTS:
            if role != "owner":
                raise PermissionError("Field registration requires the tenant owner")
            existing = get_protocol(db,tenant)
            registered = db.execute("SELECT 1 FROM study_protocol WHERE tenant=?",(tenant,)).fetchone()
            cutoff = min(existing["baseline_start"],p["baseline_start"]) if registered else p["baseline_start"]
            if cutoff <= local_today().isoformat():
                raise ValueError("Field scope and thresholds must be registered before the baseline starts")
        db.execute("INSERT INTO study_protocol VALUES(?,?,?,?) ON CONFLICT(tenant) DO UPDATE SET actor=excluded.actor,saved=excluded.saved,payload=excluded.payload",
                   (tenant,actor,now(),json.dumps(p)))
        return p
    if path == "/api/pilot/review":
        if role != "owner":
            raise PermissionError("Pilot governance review requires the tenant owner")
        if not db.execute("SELECT 1 FROM study_protocol WHERE tenant=?",(tenant,)).fetchone():
            raise ValueError("Register the pilot protocol before reviewing it")
        allowed = {"integration_reviewed","security_reviewed","confounders"}
        fields(body,allowed)
        if set(body) != allowed:
            raise ValueError("Supply all review fields")
        validate_protocol(dict(get_protocol(db,tenant),**body))
        db.execute("INSERT INTO study_reviews VALUES(?,?,?,?,?)",
                   (str(uuid.uuid4()),tenant,actor,now(),json.dumps(body)))
        return report(db,tenant)
    if path == "/api/pilot/measurements":
        fields(body,["filename","csv","mode","reference","attest_actual"])
        mode = body.get("mode")
        if mode not in ("validate","import"):
            raise ValueError("Choose validate or import")
        p = get_protocol(db,tenant)
        if mode == "import":
            access = db.execute("SELECT authorization_ref FROM study_access WHERE tenant=?",(tenant,)).fetchone()
            if tenant in DEMO_TENANTS or role != "owner" or not access:
                raise PermissionError("This tenant is not authorized for measured field evidence")
            if not db.execute("SELECT 1 FROM study_protocol WHERE tenant=?",(tenant,)).fetchone():
                raise ValueError("Register the pilot protocol before import")
            safe_code(body.get("reference"),"Custodian source reference")
            if body.get("attest_actual") is not True:
                raise ValueError("Attestation of authorized actual branch data is required")
        rows = read_csv(body,p)
        digest = hashlib.sha256(body["csv"].encode("utf-8")).hexdigest()
        if mode == "validate":
            return dict(rows=len(rows), sha256=digest, status="Validated only", evidence_level="UNKNOWN")
        if db.execute("SELECT 1 FROM study_imports WHERE tenant=? AND digest=?",(tenant,digest)).fetchone():
            raise ValueError("This file was already imported")
        if any(db.execute("SELECT 1 FROM study_days WHERE tenant=? AND sku=? AND day=?",(tenant,r["sku"],r["date"])).fetchone() for r in rows):
            raise ValueError("One or more SKU-days already exist; no rows imported")
        batch = str(uuid.uuid4())
        db.execute("INSERT INTO study_imports VALUES(?,?,?,?,?,?,?,?)",(batch,tenant,actor,now(),body["reference"],digest,access[0],json.dumps(p)))
        db.executemany("INSERT INTO study_days VALUES(?,?,?,?,?)",[(tenant,r["sku"],r["date"],batch,json.dumps(r)) for r in rows])
        return dict(batch=batch,rows=len(rows),sha256=digest,evidence_level="PILOT_MEASURED")
    raise ValueError("Unknown study route")
