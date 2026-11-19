"""Matplotlib release figures. Inputs are read from a completed reproduction run."""
import csv
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

NAVY, TEAL, MUTED, PAPER = "#172F48", "#087C77", "#486279", "#FBF9F3"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"figure.facecolor":PAPER,
                     "axes.facecolor":PAPER,"text.color":NAVY,"axes.labelcolor":NAVY,
                     "xtick.color":NAVY,"ytick.color":NAVY,"svg.hashsalt":"medcura-research-v1",
                     "svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False})

REGISTER = [
("F01","Private medical complexes by region","OBSERVED_PUBLIC","2024 · locations","data/processed/T01_regions.csv; 01 Facilities F5:F17","Facility locations ranked across 13 administrative regions."),
("F02","Concentration of private complexes","DERIVED","2024 · locations and percent","T01; cumulative sum / national total","Top three account for 70.1%; top seven account for 89.8%."),
("F03","Private complexes per 100,000 residents","DERIVED","2024 facilities / 2022 residents","T01; 100000 × complexes / population","Mixed-year footprint ratio; operational pressure and patient traffic remain unknown."),
("F04","How evidence enters the prototype","DERIVED","2022–2029 · conceptual","docs/EVIDENCE_BOUNDARIES.md; T03","Public observations, computed indicators, synthetic histories and scenarios retain distinct evidence labels."),
("F05","Inventory lifecycle and ledger controls","SYNTHETIC DATA","Prototype · conceptual","apps/api/inventory.py; tests/test_inventory.py","A simulated receipt or issue records an authenticated inventory movement."),
("F06","One-day forecast errors by baseline","SYNTHETIC DATA","November 2026 · MAE in gloves","experiments/runs/backtest.json; T04","Five baselines evaluated over seven forward one-day origins. Clinic accuracy remains unmeasured."),
("F07","Weekly naive forecast and synthetic observations","SYNTHETIC DATA","September–November 2026 · gloves","experiments/runs/backtest.json","The model was selected by November 11, before the November 12–18 holdout."),
("F08","How a reorder recommendation is built","SYNTHETIC DATA","Prototype · conceptual","apps/api/science.py and inventory.py; T05","Inventory position, lead-time demand and pack constraints inform a human-reviewed recommendation."),
("F09","Transfer approval and stock in transit","SYNTHETIC DATA","Prototype · conceptual","apps/api/inventory.py; T05","Dispatch records an issue at origin. Destination stock increases upon receipt."),
("F10","Geographic expansion gates","SCENARIO","2027–2029 · proposed gates","apps/api/study.py; T06","Later regions depend on evidence readiness and operational feasibility."),
("F11","Modeled break-even branch requirement","SCENARIO","2027–2029 · active branches","T08; apps/api/study.py","Compare equivalent active branches under editable price, branch cost and overhead assumptions."),
("F12","Riyadh pilot measurement design","FIELD OUTCOMES NOT YET MEASURED","Proposed · conceptual","docs/PILOT_PROTOCOL.md; T07","A baseline, silent review and intervention track prespecified stock and effort measures."),
]

def canvas(i, size=(10,5.8), axes=(.19,.17,.75,.65)):
    key,title,level,period,source,caption=REGISTER[i-1]
    fig=plt.figure(figsize=size)
    fig.text(.07,.947,title,fontsize=20,weight="bold",va="top")
    fig.text(.07,.875,f"{key}  |  {level}  |  {period}",color=MUTED,weight="bold",fontsize=9)
    fig.text(.07,.045,caption,color=MUTED,fontsize=8,wrap=True)
    return fig,fig.add_axes(axes)

def diagram(i, items):
    fig,ax=canvas(i,(11,5.4),(.07,.16,.86,.66))
    ax.set(xlim=(0,1),ylim=(0,1))
    ax.axis("off")
    step=1/len(items)
    for index,(head,lines) in enumerate(items):
        x=index*step
        ax.add_patch(FancyBboxPatch((x+.006,.24),step-.043,.54,boxstyle="round,pad=.006",
                                   facecolor="#E5EFEE",edgecolor=TEAL,linewidth=1.1))
        ax.text(x+.018,.68,head,weight="bold",fontsize=10,va="top")
        ax.text(x+.018,.55,lines,fontsize=9,va="top",linespacing=1.5)
        if index+1<len(items):
            ax.annotate("",xy=(x+step+.002,.50),xytext=(x+step-.032,.50),
                        arrowprops={"arrowstyle":"->","color":TEAL,"lw":1.4})
    return fig

def build(out, regions, forecast):
    figures=out/"results/figures"
    figures.mkdir(parents=True,exist_ok=True)
    counts=[r["complexes"] for r in regions]
    names=[r["region"] for r in regions]
    total=sum(counts)
    figs=[]
    for i,values,labels,name in [(1,counts,names,"Private complex locations"),
          (3,[100000*r["complexes"]/r["population"] for r in regions],names,"Locations per 100,000 residents")]:
        ordered=sorted(zip(labels,values),key=lambda p:-p[1])
        fig,ax=canvas(i)
        bars=ax.barh([r[0] for r in ordered],[r[1] for r in ordered],color=TEAL)
        ax.invert_yaxis()
        ax.set(xlabel=name,xlim=(0,max(values)*1.16))
        ax.bar_label(bars,labels=[f"{x[1]:,.0f}" if i==1 else f"{x[1]:.1f}" for x in ordered],padding=4)
        ax.grid(axis="x",alpha=.18,zorder=0)
        figs.append((i,fig))
    fig,ax=canvas(2,(10,5.8),(.1,.27,.79,.53))
    positions=list(range(1,14))
    ax.bar(positions,counts,color=[TEAL if n<=3 else "#70879B" for n in positions])
    ax.set(ylabel="Locations",ylim=(0,1300),xticks=positions)
    ax.set_xticklabels(names,rotation=50,ha="right",fontsize=8)
    cumul=ax.twinx()
    cumulative=[100*sum(counts[:n])/total for n in positions]
    cumul.plot(positions,cumulative,"o-",color=NAVY,markersize=3)
    cumul.set(ylim=(0,109),ylabel="Cumulative share (%)",yticks=[0,25,50,75,100])
    for n in (3,7):
        cumul.annotate(f"{cumulative[n-1]:.1f}%",(n,cumulative[n-1]),xytext=(0,10),textcoords="offset points",ha="center",weight="bold")
    figs.append((2,fig))
    diagrams={
    4:[("Observed","Dated facility and\npopulation tables"),("Derived","Counts, shares and\ndensity with lineage"),("Demo / scenario","Synthetic stock events\nEditable financial inputs"),("Pilot evidence","Collect comparable\nfield observations")],
    5:[("Receive","SKU and lot\nUnit conversion"),("Validate","Quantity, expiry\nand quarantine"),("Authorize","Role and branch\nReservation / issue"),("Record","Immutable movement\nPhysical and held units")],
    8:[("Position","Available + inbound\norders and transfers"),("Demand","Lead-time demand\n+ safety buffer"),("Order size","Pack, minimum order\nand capacity"),("Approve","Human review before\nconfirmed inbound")],
    9:[("Request","Reserve at origin\nValidate recipient need"),("Approve","Named approver\nReject / cancel releases"),("Dispatch","Origin decreases\nUnits in transit"),("Receive","Destination increases\nIn-transit balance clears")],
    10:[("2027: Riyadh","Agree on pilot scope\nand evidence readiness"),("2028: next regions","Review Makkah and\nEastern Province"),("2029: selective scale","Review four more regions\nsubject to readiness")],
    12:[("Baseline","Eligible SKU-days\nStockout episodes"),("Silent review","Completeness and\nworkflow adherence"),("Intervention","Apply approved\nrecommendations"),("Compare","Write-offs, availability\nand counting effort")]}
    figs.extend((i,diagram(i,items)) for i,items in diagrams.items())
    fig,ax=canvas(6)
    scores=forecast["scores"]
    bars=ax.barh([s["model"].title() for s in scores],[s["mae"] for s in scores],
                 color=[TEAL if s["model"]==forecast["chosen"] else "#70879B" for s in scores])
    ax.invert_yaxis()
    ax.bar_label(bars,fmt="%.2f",padding=4)
    ax.set(xlabel="Mean absolute error (gloves per day)",xlim=(0,1.25))
    figs.append((6,fig))
    fig,ax=canvas(7,(10,5.8),(.12,.22,.8,.59))
    asdate=date.fromisoformat
    history=forecast["history"]
    points=forecast["points"]
    hs=[asdate(r["date"]) for r in history]
    hp=[asdate(r["date"]) for r in points]
    selection=asdate(forecast["selection_end"])
    ax.plot(hs,[r["qty"] for r in history],color=NAVY,label="Synthetic observation",linewidth=1.5)
    ax.plot(hp,[r["prediction"] for r in points],"o--",color=TEAL,label="One-day prediction",markersize=4)
    ax.axvline(selection,linestyle=":",color=MUTED,label="Selection ends")
    ax.axvspan(hp[0],hp[-1],color=TEAL,alpha=.13,label="Holdout origins")
    ax.set(ylabel="Gloves per day",ylim=(0,15))
    ax.legend(loc="lower left",ncol=2,frameon=False,fontsize=8)
    fig.autofmt_xdate(rotation=20)
    figs.append((7,fig))
    fig,ax=canvas(11,(10,5.8),(.12,.22,.8,.6))
    with (out/"results/tables/T08.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    for color,style,case in zip((NAVY,TEAL,"#8A512E"),("o-","s--","^:"),("Conservative","Base","Favorable"),strict=True):
        rs=[r for r in rows if r["case"]==case and r["driver_or_metric"]=="break_even_branches"]
        if rs:
            ax.plot([int(r["window"]) for r in rs],[float(r["value"]) if r["value"] else float("nan") for r in rs],style,label=case,color=color)
    ax.set(xlabel="Scenario year",ylabel="Break-even active branches",xticks=[2027,2028,2029],ylim=(0,None))
    ax.legend(frameon=False)
    figs.append((11,fig))
    for i,fig in figs:
        for suffix in ("svg","png","pdf"):
            fig.savefig(figures/f"F{i:02}.{suffix}",dpi=300,
                        metadata={"CreationDate":None,"ModDate":None} if suffix=="pdf" else {"Date":None} if suffix=="svg" else None)
        plt.close(fig)
    return REGISTER
