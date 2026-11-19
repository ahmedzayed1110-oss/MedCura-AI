"""Reproduce the research release without overwriting any source inputs."""
import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apps.api import study
from figures.publication import build

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def csv_table(path, rows):
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)
    with path.open(encoding="utf-8",newline="") as stream:
        if len(list(csv.DictReader(stream)))!=len(rows):
            raise ValueError(f"CSV readback mismatch: {path.name}")

def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

def registry(regions, fc):
    n=sum(r["complexes"] for r in regions)
    def claim(key,label,value,unit,src,ref,period,calc,evidence,caveat,dest):
        return dict(claim_id=key,display_text=label,value=value,unit=unit,source_file=src,
                    source_sheet_cell_or_artifact=ref,observation_period=period,calculation=calc,
                    evidence_type=evidence,caveats=caveat,output_destinations=dest)
    c=[claim(r["id"],r["region"]+" private complexes",r["complexes"],"locations",
       "data/processed/T01_regions.csv",r["source_ref"],2024,"transcription","OBSERVED_PUBLIC",
       "Administrative regions; facility footprints","F01; F02; F03; T01; deck; report") for r in regions]
    for k,label,v,unit,ref,period,formula in [
        ("national","National private complexes",n,"locations","01 Facilities F5:F17",2024,"sum complexes"),
        ("top3","Top three share",100*sum(r["complexes"] for r in regions[:3])/n,"%", "T01 rank 1 to 3",2024,"sum top three / national × 100"),
        ("top7","Top seven share",100*sum(r["complexes"] for r in regions[:7])/n,"%", "T01 rank 1 to 7",2024,"sum top seven / national × 100"),
        ("population","National population",sum(r["population"] for r in regions),"people","02 Population B2:B14",2022,"sum regional population")]:
        c.append(claim(k,label,v,unit,"data/processed/T01_regions.csv",ref,period,formula,"DERIVED",
                       "Facility counts and population use different reference years","README; T01; F01–F03; deck; report"))
    for s in fc["scores"]:
        c.append(claim("mae-"+s["model"].replace(" ","-"),s["model"]+" MAE",s["mae"],"gloves/day",
                       "experiments/runs/backtest.json","scores",fc["holdout_start"]+" to "+fc["cutoff"],
                       "mean absolute error across seven forward origins","SYNTHETIC_DEMO","Small simulated holdout","F06; F07; T04; README; report"))
    c.extend([
      claim("insured","Regional insurance allocation",None,"insured people","data/processed/T02_conflicts.csv","Workbook B insurance allocation","workbook assumptions","65% facilities and 35% population","SCENARIO","Regional official observations unavailable","F04; T02"),
      claim("commercial","Break-even scenario",None,"branches","results/tables/T08.csv","break_even_branches","2027–2029","fixed cost / branch contribution, rounded up","SCENARIO","Driver assumptions are editable","F11; README"),
      claim("pilot","Field effects",None,"various","docs/PILOT_PROTOCOL.md","measurement dictionary","prospective","pending authorized data","UNKNOWN","FIELD OUTCOMES NOT YET MEASURED","F12; T07; README")
    ])
    return c

def reproduce(out, ingest_python):
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Choose a new empty output directory.")
    out.mkdir(parents=True,exist_ok=True)
    log=out/"logs"
    log.mkdir()
    raw_manifest=read(ROOT/"data/source_manifest.json")
    missing=[]
    for src in raw_manifest["files"]:
        p=ROOT/src["source_path"]
        if not p.is_file():
            missing.append(src["id"])
        elif digest(p)!=src["sha256"]:
            raise ValueError(f"Source hash changed: {src['id']}")
    commands=[]
    with tempfile.TemporaryDirectory(prefix="medcura-repro-") as tmp:
        t=Path(tmp)
        for directory in ("scripts","apps","data/processed","data/demo","data/templates"):
            shutil.copytree(ROOT/directory,t/directory,ignore=shutil.ignore_patterns("__pycache__"))
        def run(script, interpreter=sys.executable):
            result=subprocess.run([interpreter,"-X","utf8","scripts/"+script],cwd=t,capture_output=True)
            commands.append(dict(command="python -X utf8 scripts/"+script,exit_code=result.returncode))
            (log/(script+".log")).write_bytes(result.stdout+result.stderr)
            result.check_returncode()
        if not missing:
            for src in raw_manifest["files"]:
                rel=Path(src["source_path"])
                copy(ROOT/rel,t/rel)
            run("ingest.py",ingest_python)
        for script in ("benchmark.py","stress.py","study_assets.py"):
            run(script)
        processed=t/"data/processed"
        regions=read(processed/"regions.json")
        counts=[r["complexes"] for r in regions]
        if (len(set(r["id"] for r in regions)),sum(counts),sum(counts[:3]),sum(counts[:7]),sum(r["population"] for r in regions))!=(13,3607,2527,3238,32175224) or counts!=sorted(counts,reverse=True):
            raise ValueError("Regional source totals failed")
        if counts[:3]!=[1171,880,476] or [(r["reference_year"],r["population_year"]) for r in regions]!=[(2024,2022)]*13:
            raise ValueError("Regional anchors or reference years changed")
        fc=read(t/"data/demo/backtest.json")
        if (len(fc["scores"]),len(fc["points"]))!=(5,7) or not fc["selection_end"]<fc["holdout_start"]==fc["points"][0]["date"] or not all(a["date"]<b["date"] for a,b in zip(fc["points"],fc["points"][1:])):
            raise ValueError("Forecast holdout dates overlap or evaluation is incomplete")
        if [round(s["mae"],2) for s in fc["scores"]]!=[.86,.14,1,.71,1.06]:
            raise ValueError("Prior MAEs did not reproduce")
        for name in ("backtest.json","stress.json","T04_scenario_sensitivity.csv","T05.csv"):
            if (t/"data/demo"/name).read_bytes()!=(ROOT/"data/demo"/name).read_bytes():
                raise ValueError(f"Prior result differs: {name}")
            copy(t/"data/demo"/name,out/"experiments/runs"/name)
        tables=out/"results/tables"
        tables.mkdir(parents=True)
        for n, name in ((1,"T01_regions"),(2,"T02_conflicts")):
            p=processed/(name+".csv")
            if p.read_bytes()!=(ROOT/"data/processed"/p.name).read_bytes():
                raise ValueError(f"Source-derived table differs: {p.name}")
            copy(p,tables/f"T{n:02}.csv")
        conflicts=read(processed/"conflicts.json")
        lineage=read(processed/"lineage.json")
        for p in ("regions.json","conflicts.json","lineage.json","metrics.json"):
            if read(processed/p)!=read(ROOT/"data/processed"/p):
                raise ValueError(f"Source-derived JSON differs: {p}")
            copy(processed/p,out/"results/metrics"/p)
        write(out/"experiments/configs/forecast.json",dict(config=fc["config"],coverage=fc["coverage"],selection_end=fc["selection_end"],holdout_start=fc["holdout_start"],cutoff=fc["cutoff"],seed="fixed seeded inventory history in apps/api/inventory.py"))
        claims=registry(regions,fc)
        assert all(x["evidence_type"]!="PILOT_MEASURED" for x in claims)
        csv_table(tables/"T03.csv",claims)
        csv_table(tables/"T04.csv",[dict(evidence_type="SYNTHETIC_DEMO",holdout_n=7,holdout_start=fc["holdout_start"],cutoff=fc["cutoff"],selection=fc["reason"],selected=s["model"]==fc["chosen"],**s) for s in fc["scores"]])
        stress=read(t/"data/demo/stress.json")
        csv_table(tables/"T05.csv",[
            dict(case="mask receipt and issue",quantity=47,unit="masks",assumption="2 packs of 25 less 3 issued",evidence_type="SYNTHETIC_DEMO"),
            dict(case="transfer receipt",quantity=25,unit="gloves",assumption="one shipping day and SAR 12 freight",evidence_type="SYNTHETIC_DEMO"),
            dict(case="synthetic redistribution limit",quantity=stress["redistribution"]["limit"],unit="gloves",assumption=stress["redistribution"]["notes"],evidence_type="SYNTHETIC_DEMO"),
            dict(case="lead-time delay",quantity=stress["lead_delay"]["after_point"],unit="reorder units",assumption=f"Before delay: {stress['lead_delay']['before_point']} units",evidence_type="SYNTHETIC_DEMO")])
        csv_table(tables/"T06.csv",[dict(year=y,gate=g,status="Proposed",evidence_type="SCENARIO",criterion=c,threshold="Pending partner agreement") for y,g,c in zip(study.YEARS,study.GATES,["data access and baseline completeness","pilot review and service readiness","chain qualification and unit economics"],strict=True)])
        copy(t/"data/templates/T03_pilot_protocol.csv",tables/"T07.csv")
        copy(t/"data/demo/T04_scenario_sensitivity.csv",tables/"T08.csv")
    figures=build(out,regions,fc)
    from PIL import Image, ImageOps, ImageDraw
    sheet=Image.new("RGB",(1440,4*294),"#FBF9F3")
    for i in range(12):
        image=Image.open(out/"results"/"figures"/f"F{i+1:02}.png").convert("RGB")
        sheet.paste(ImageOps.contain(image,(474,273)),(i%3*480,i//3*294))
        ElementTree.parse(out/"results"/"figures"/f"F{i+1:02}.svg")
    sheet.save(out/"results/figures/contact-sheet.png")
    captions=out/"results/captions"
    captions.mkdir()
    (captions/"FIGURE_REGISTER.md").write_text("# Matplotlib figure register\n\nRebuild each figure with `python scripts/reproduce_all.py --out reproduction`.\n\n"+"".join(f"## {i} · {t}\n\n{c}\n\n**Status and units** {e}. {p}. **Source** {s}. [SVG](../figures/{i}.svg) · [PNG](../figures/{i}.png) · [PDF](../figures/{i}.pdf)\n\n" for i,t,e,p,s,c in figures),encoding="utf-8")
    node=shutil.which("node")
    files={p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob("*")) if p.is_file()}
    write(out/"run_manifest.json",dict(generated_utc=datetime.now(timezone.utc).isoformat(),
        platform=platform.platform(),python=platform.python_version(),node=subprocess.check_output([node,"--version"],text=True).strip() if node else None,
        packages={p:importlib.metadata.version(p) for p in ("matplotlib","numpy","pillow")},missing_raw_ids=missing,
        source_manifest_sha256=digest(ROOT/"data/source_manifest.json"),dataset=raw_manifest["canonical_version"],
        commands=commands, counts=dict(regions=len(regions),lineage=len(lineage),conflicts=len(conflicts),figures=len(figures),tables=8),artifacts=files))
    (out/"EXPERIMENT_REPORT.md").write_text(f"# Reproduction report\n\nRecomputed {len(regions)} regions and {len(lineage)} lineage records against {len(conflicts)} conflict decisions. Raw source mode: {not missing}.\n\nThe five baseline scores and stress outputs were reproduced from the fixed synthetic inventory code. Seven holdout origins support only a small descriptive comparison. Fiscal results use editable scenarios. Field outcomes remain unmeasured.\n",encoding="utf-8")
    print("Reproduced",len(regions),"regions;",len(figures),"figures; eight tables; five baselines.")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--ingest-python",default=sys.executable,help="Python with optional evidence extraction dependencies")
    args=ap.parse_args()
    reproduce(args.out.resolve(),args.ingest_python)
