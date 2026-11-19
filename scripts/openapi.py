"""Generate the local OpenAPI 3.1 contract from a compact endpoint catalogue."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S={"type":"string"}
I={"type":"integer"}
B={"type":"boolean"}
O={"type":"object"}
BR={"type":"string","enum":["north","east"]}
base={"branch":BR,"sku":S,"qty":I,"reason":S,"unit":{"enum":["base","pack"]},"lot":S,"code":S,"expiry":S,"quarantine":B}
routes={}
def add(path,method,summary,props=None,required=(),query=(),public=False):
    route={"summary":summary,"operationId":method+"_"+path.strip("/").replace("/","_").replace("{","").replace("}","").replace(".","_"),
           "security":[] if public else [{"localSession":[]}],"responses":{"200":{"description":"Successful response"},"400":{"description":"Validation failure or conflicting replay"},"401":{"description":"Sign-in required"},"403":{"description":"Role or scope denied"},"404":{"description":"Resource unavailable"}}}
    params=[dict(name=k,**{"in":"query","required":True,"schema":BR if k=="branch" else S}) for k in query]
    if "{" in path:
        key=path.split("{")[1].split("}")[0]
        params.append(dict(name=key,**{"in":"path","required":True,"schema":S}))
    if method=="post":
        if path not in ("/api/login","/api/logout"):
            params.append({"name":"Idempotency-Key","in":"header","required":True,"schema":{"type":"string","pattern":"^[a-zA-Z0-9_-]{8,100}$"}})
        schema={"type":"object","properties":props or {}}
        if required:schema["required"]=list(required)
        route["requestBody"]={"required":True,"content":{"application/json":{"schema":schema}}}
    if params:route["parameters"]=params
    routes.setdefault(path,{})[method]=route

def build():
    add("/health","get","Local process readiness",public=True)
    add("/api/login","post","Start an eight-hour local session",{"username":S,"password":{"type":"string","format":"password"},"ticket":S},public=True)
    add("/api/logout","post","End the active session")
    for path,label in {"session":"Authenticated account","state":"Branch dashboard","market/regions":"Sourced regional records",
         "market/pareto":"Ranked footprint and cumulative share","market/metrics":"All executive indicators","market/metrics/{id}":"Indicator provenance",
         "sources":"Input manifest and workbook metadata","evidence/conflicts":"Source discrepancies","evidence/lineage":"All field lineages",
         "evidence/lineage/{id}":"Cell-level metric lineage","competitors":"Vendor evidence","branches":"Assigned branch registry","skus":"Catalog",
         "lots":"Lot registry and balances","inventory/balances":"Physical and available stock","ledger":"Immutable activity log","alerts":"Near-expiry lot alerts",
         "audit":"Mutation fingerprints and actors","transfers":"Transfer register","presentation":"Deck narrative","scenarios":"Presets and saved scenarios",
         "pilot/report":"Measurement report and eligibility","pilot/measurements":"Authorized field evidence register",
         "pilot/protocol":"Registered study design","pilot/template":"CSV columns and template","exports/market.csv":"Regional CSV",
         "exports/ledger.csv":"Ledger CSV","exports/conflicts.csv":"Source conflict CSV"}.items():
        add("/api/"+path,"get",label)
    for kind in ("receive","return","issue","adjust","count","reserve","unreserve"):
        add("/api/inventory/"+kind,"post","Record "+kind+" in integer base units",base,["branch","sku","qty","reason"])
    add("/api/skus","post","Create or revise catalog item",dict(id=S,name=S,unit=S,expiry=B,pack=I,cost_minor=I),["id","name","unit","expiry","pack","cost_minor"])
    for path in ("decisions/reorder","forecast/backtest","policy"):
        add("/api/"+path,"get","Inspect forecast and policy",query=["branch","sku"])
    add("/api/forecast/backtest","post","Persist versioned rolling-origin evaluation",dict(branch=BR,sku=S),["branch","sku"])
    add("/api/policy","post","Save lead time, review days, quantile, MOQ and capacity",dict(branch=BR,sku=S,lead=I,review=I,service=I,moq=I,capacity=I),["branch","sku","lead","review","service","moq","capacity"])
    add("/api/decisions/reorder","post","Approve current reorder run",dict(branch=BR,sku=S,run=S),["branch","sku","run"])
    add("/api/transfers","post","Draft or advance transfer state",{"action":{"enum":["draft","request","approve","reject","dispatch","receive","cancel"]},"id":S,"lot":S,"qty":I,"destination":BR,"days":I,"freight":I,"arrival_day":S},["action"])
    add("/api/orders/receive","post","Receive an approved order into a lot",dict(id=S,code=S,expiry=S),["id","code"])
    add("/api/scenarios","post","Save scenario assumptions and projections",dict(name=S,assumptions=O),["name","assumptions"])
    add("/api/scenarios/preview","post","Calculate a financial scenario",dict(assumptions=O),["assumptions"])
    add("/api/pilot/protocol","post","Register site, SKU sample, windows and thresholds")
    add("/api/pilot/review","post","Record follow-up governance review")
    add("/api/pilot/measurements","post","Validate a capped CSV or import authorized field evidence",dict(filename=S,csv=S,mode={"enum":["validate","import"]},reference=S,attest_actual=B),["filename","csv","mode"])
    return {"openapi":"3.1.0","info":{"title":"MedCura AI local prototype","version":"1.0.0"},"servers":[{"url":"/"}],"components":{"securitySchemes":{"localSession":{"type":"apiKey","in":"cookie","name":"mc"}}},"paths":routes}
if __name__=="__main__":
    (ROOT/"openapi.json").write_text(json.dumps(build(),indent=2),encoding="utf-8")

