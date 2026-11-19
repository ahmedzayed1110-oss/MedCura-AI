"""Render publication figures from the canonical observations and synthetic forecast run.

Requires reportlab and Poppler's pdftoppm on PATH. Run scripts/ingest.py and
scripts/benchmark.py first. Editable text and vectors are preserved in SVG.
"""
import argparse
import json
import math
import subprocess
import tempfile
import textwrap
from pathlib import Path
from xml.etree import ElementTree as ET

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Polygon, PolyLine
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
W, H = 1080, 660
NAVY, TEAL, BLUE = '#10263E', '#007F86', '#356CB1'
INK, MUTED, RULE, PALE, PAPER = '#21394D', '#465E6B', '#CFDAD8', '#E7F1EE', '#F8F8F3'
GOLD = '#925B19'
MARKET = "Workbook A, 01 Facilities!A5:H18 (2024)."
GUIDE = 'Supplied Arabic presentation guide and research blueprint, November 2026.'
CAT = []


class Figure:
    def __init__(self, code, title, sub, level, source):
        self.code, self.title, self.sub = code, title, sub
        self.level, self.source = level, source
        self.draw = Drawing(W, H)
        self.box(0, 0, W, H, PAPER)
        self.txt(48, 44, 'MEDCURA AI   /   RESEARCH FIGURES', 13, 'Helvetica-Bold', TEAL)
        self.txt(W - 48, 44, code + '    /    ' + level, 13, 'Helvetica-Bold', MUTED, 'end')
        self.line(48, 61, W - 48, 61)
        self.txt(48, 112, title, self.fit(title, 43, W - 96, 'Times-Bold'), 'Times-Bold', NAVY)
        self.txt(48, 148, sub, self.fit(sub, 19, W - 96), color=MUTED)
        self.line(48, 605, W - 48, 605)
        self.txt(48, 635, source, self.fit(source, 15, W - 96), color=MUTED)

    @staticmethod
    def fit(val, size, width, font='Helvetica'):
        return min(size, size * width / max(1, stringWidth(val, font, size)))

    def txt(self, x, y, val, size=20, font='Helvetica', color=INK, anchor='start'):
        self.draw.add(String(x, H - y, str(val), fontName=font, fontSize=size,
                             fillColor=HexColor(color), textAnchor=anchor))

    def box(self, x, y, w, h, fill, stroke=None):
        self.draw.add(Rect(x, H-y-h, w, h, fillColor=HexColor(fill),
                           strokeColor=HexColor(stroke) if stroke else None, strokeWidth=1))

    def line(self, x1, y1, x2, y2, color=RULE, weight=1, dash=None):
        self.draw.add(Line(x1,H-y1,x2,H-y2,strokeColor=HexColor(color),
                           strokeWidth=weight,strokeDashArray=dash))

    def dot(self,x,y,r=5,c=TEAL):
        self.draw.add(Circle(x,H-y,r,fillColor=HexColor(c),strokeColor=None))

    def arrow(self,x1,y1,x2,y2,color=TEAL):
        self.line(x1,y1,x2,y2,color,2)
        dx,dy=x2-x1,y2-y1
        n=math.hypot(dx,dy)
        dx,dy=dx/n,dy/n
        points=[x2,H-y2,x2-9*dx+4*dy,H-(y2-9*dy-4*dx),
                x2-9*dx-4*dy,H-(y2-9*dy+4*dx)]
        self.draw.add(Polygon(points,fillColor=HexColor(color),strokeColor=None))

    def para(self,x,y,txt,width,size=19,spacing=27,color=INK,font='Helvetica'):
        line=''
        for word in txt.split():
            next_line = (line+' '+word).strip()
            if line and stringWidth(next_line,font,size)>width:
                self.txt(x,y,line,size,font,color)
                y+=spacing
                line=word
            else:
                line=next_line
        if line:
            self.txt(x,y,line,size,font,color)
            y+=spacing
        return y

    def node(self,x,y,w,h,title,body,active=False):
        self.box(x,y,w,h,PALE if active else '#FFFFFF',RULE)
        self.box(x,y,4,h,TEAL if active else BLUE)
        self.txt(x+15,y+30,title,self.fit(title,22,w-30,'Helvetica-Bold'),'Helvetica-Bold',NAVY)
        self.para(x+15,y+57,body,w-30,18,23)

    def finish(self,caption):
        svg = FIG / (self.code+'.svg')
        renderSVG.drawToFile(self.draw,str(svg))
        # Ensure accessibility without rewriting the renderer's namespace prefixes.
        content=svg.read_text(encoding='utf-8')
        first=content.index('>',content.index('<svg'))
        import html
        content=content[:first]+' role="img" aria-labelledby="medcura-title medcura-desc"'+content[first:first+1] + '<title id="medcura-title">'+html.escape(self.title)+'</title><desc id="medcura-desc">'+html.escape(caption)+'</desc>'+content[first+1:]
        svg.write_text(content,encoding='utf-8')
        ET.parse(svg)
        CAT.append(dict(id=self.code,title=self.title,caption=caption,evidence_level=self.level,
                        source_ref=self.source,svg=self.code+'.svg',png=self.code+'.png'))
        return self.draw


def ranking(rows):
    f=Figure('F01','Where private medical complexes are located',
             'Private complexes by Saudi administrative region, 2024. Teal marks the three largest counts.',
             'OBSERVED_PUBLIC',MARKET)
    axis, top, width, dy = 250, 191, 700, 29
    maxval=math.ceil(max(r['complexes'] for r in rows)/200)*200
    for val in range(0,maxval+1,200):
        x=axis+width*val/maxval
        f.line(x,173,x,563)
        f.txt(x,587,f'{val:,}',15,color=MUTED,anchor='middle')
    for i,r in enumerate(rows):
        y=top+dy*i
        n=r['complexes']
        f.txt(axis-16,y+4,r['region'],18,anchor='end')
        f.box(axis,y-11,width*n/maxval,18,TEAL if i<3 else '#90A9B4')
        f.txt(axis+width*n/maxval+9,y+4,f'{n:,}',17,'Helvetica-Bold')
    return f.finish('All 13 administrative regions. Counts describe facility locations. The workbook cites MOH statistics.')

def pareto(rows):
    total=sum(r['complexes'] for r in rows)
    f=Figure('F02','How quickly the footprint accumulates',
             'Regions ordered by private complex count. Cumulative share of the national total, 2024.',
             'DERIVED',MARKET)
    left,top,span,height=100,218,875,270
    for pct in [0,25,50,75,100]:
        y=top+height*(1-pct/100)
        f.line(left,y,left+span,y)
        f.txt(left-10,y+5,str(pct)+'%',17,color=MUTED,anchor='end')
    counts=[r['complexes'] for r in rows]
    points=[]
    for i,ct in enumerate(counts):
        x=left+i*span/(len(rows)-1)
        pct=100*sum(counts[:i+1])/total
        y=top+height*(1-pct/100)
        points.append((x,y))
        if i: f.line(*points[-2],x,y,TEAL,4)
        f.dot(x,y,5)
        f.txt(x,520,str(i+1),17,color=MUTED,anchor='middle')
        if i in [2,6,12]:
            f.txt(x,y-18,f'{pct:.1f}%',20,'Helvetica-Bold',TEAL,'middle')
    f.txt(left+span/2,554,'Number of regions included, highest count first',19,color=MUTED,anchor='middle')
    return f.finish('Cumulative sum of the 2024 regional counts divided by their national sum. Ties use canonical region order.')

def stage(rows):
    totals=[sum(r['complexes'] for r in rows[:k]) for k in (1,3,7)]
    total=sum(r['complexes'] for r in rows)
    f=Figure('F03','Geographic sequence for partner discovery',
             'Proposed geographies, with cumulative 2024 facility counts. Placement is schematic.',
             'SCENARIO',MARKET+' Strategy from the supplied guide, slides 6 and 8.')
    for i,(k,year,scope,detail) in enumerate([(1,'2027','Riyadh','Seek one participating branch.'),(3,'2028','Makkah and Eastern','Add the two administrative regions after the pilot review.'),(7,'2029','Four further regions','Consider Asir, Madinah, Qassim and Jazan after replication.')]):
        x=48+i*337
        f.box(x,203,305,7,TEAL if i==0 else BLUE)
        f.txt(x,253,year,32,'Times-Bold',NAVY)
        f.txt(x,307,scope,23,'Helvetica-Bold')
        f.para(x,348,detail,279,20,27)
        f.txt(x,470,f'{totals[i]:,}',45,'Times-Bold',TEAL)
        f.para(x,501,f'facilities across {k} region'+('s' if k>1 else '')+f' ({100*totals[i]/total:.1f}%)',280,18,24)
    return f.finish('The phase sequence is an editable commercial strategy. Counts establish geographic scale only. Contract, conversion and deployment counts remain unknown.')

def provenance():
    f=Figure('F04','Tracing a number back to its source',
             'The two workbooks may agree on a value while using a different definition or period.',
             'DERIVED','Source reconciliation design. See data/source_manifest.json and the conflict register.')
    f.node(48,197,270,106,'Record provenance','File hash, sheet, cell, value and reporting period.')
    f.node(405,197,270,106,'Compare definitions','Check population, unit, geography and method.',True)
    f.node(762,197,270,106,'Publish lineage','Preserve the observation and every derived formula.')
    f.arrow(318,253,404,253)
    f.arrow(675,253,761,253)
    f.arrow(540,303,540,345,GOLD)
    f.node(405,347,270,125,'Conflicting claim','Quarantine an allocation or unverifiable price. Retain missing values.')
    f.arrow(675,406,760,406,GOLD)
    f.node(762,347,270,125,'Record decision','Show competing source cells and the reason for their treatment.')
    f.para(48,536,'Example: Workbook B allocates insurance by weighted facility and population shares. The regional values enter the scenario register.',970,21,29)
    return f.finish('Users can follow a regional total through its contributing cells. A regional insurance allocation appears only with scenario evidence.')

def architecture():
    f=Figure('F05','The inventory decision workflow',
             'Each action has an actor, a branch, a lot and a record of what changed.',
             'SYNTHETIC_DEMO','Prototype mechanism. Actual operational benefit requires prospective branch observations.')
    for i,(ttl,body) in enumerate([('Capture','Record receipt, issue, count or reservation.'),('Validate','Check permission, unit, lot and quantity.'),('Post ledger','Append a signed quantity delta in a transaction.'),('Evaluate','Compare demand and expiry exposure with stock.')]):
        x=48+i*250
        f.node(x,207,223,146,ttl,body,i==2)
        if i<3:f.arrow(x+223,275,x+247,275)
    f.arrow(908,353,908,393)
    f.node(781,395,240,125,'Human review','Review the proposed quantity, assumptions and rationale.',True)
    f.arrow(781,458,686,458)
    f.node(405,395,280,125,'Approved action','Record the order or transfer state and reconcile receipt.')
    f.arrow(405,458,327,458)
    f.node(48,395,277,125,'Pilot measurement','Compare prospectively recorded item-days and write-offs.')
    return f.finish('The prototype demonstrates event handling with synthetic records. The final measurement stage requires an approved pilot.')

def policy():
    f=Figure('F06','Reorder review follows the data',
             'A recommendation depends on dated demand, supplier assumptions and inventory position.',
             'SYNTHETIC_DEMO','Decision rule from the execution directive, section 7. Parameters require branch validation.')
    f.node(48,184,280,120,'History available?','Check dated units, observed days and coverage.',True)
    f.node(411,184,270,120,'Estimate usage','Compare rolling-origin baselines and retain dated errors.')
    f.node(761,184,270,120,'Compute threshold','Lead-time demand plus a disclosed safety buffer.')
    f.arrow(328,245,411,245)
    f.arrow(681,245,761,245)
    f.arrow(188,305,188,366,GOLD)
    f.node(48,369,280,145,'Insufficient history','Show a manual review or configured fallback. Leave shortage probability unavailable.')
    f.arrow(896,305,896,366)
    f.node(761,369,270,145,'Position at threshold?','Above threshold: monitor. At or below: size to target, pack and MOQ.',True)
    f.arrow(761,441,682,441)
    f.node(411,369,270,145,'Review order','Inspect expiry, capacity and delivery timing before approval.')
    f.para(48,565,'Inventory position includes usable available stock and eligible inbound quantities counted once.',980,18,24)
    return f.finish('The order candidate targets a disclosed stock level. Actual purchasing requires authorized review.')

def transfers():
    f=Figure('F07','Who holds the stock during a transfer?',
             'A request reserves source stock. Dispatch and receipt move the same quantity through transit.',
             'SYNTHETIC_DEMO','Prototype transfer design. Inspect the audit trail for the actor and time of each transition.')
    data=[('Draft','No stock effect'),('Requested','Reserve origin'),('Approved','Keep reservation'),('Dispatched','Move to transit'),('Received','Post destination')]
    for i,(s,desc) in enumerate(data):
        x=48+i*200
        f.node(x,215,176,104,s,desc,i in (1,3))
        if i<4:f.arrow(x+176,265,x+198,265)
    f.arrow(335,319,335,362,GOLD)
    f.node(223,365,224,115,'Rejected / cancelled','Release reserved units where the transition permits.')
    f.node(555,365,458,115,'At dispatch and receipt','Recheck lot validity and permissions. Block duplicate posting. Retain the source lot identity.')
    f.para(48,544,'Conservation check: origin physical units + in-transit units + destination physical units stays constant for a transfer.',990,20,25)
    return f.finish('Proposals use valid, eligible lots and remaining shelf life. Approved movements preserve units once dispatch and receipt have posted.')

def pilot():
    f=Figure('F08','A one-branch measurement design',
             'Proposed Riyadh pilot. Actual outcome fields remain unmeasured until an authorized import.',
             'SCENARIO',GUIDE+' See the pilot protocol and T03.')
    for i,(name,detail) in enumerate([('Baseline','Freeze the tracked SKU list and count eligible days. Record stockouts, write-offs and staff time.'),('Silent review','Reconcile counts, compare baseline forecasts and review the completeness of dated observations.'),('Intervention','Enable reviewed alerts. Keep definitions stable and record adherence, overrides and supplier delays.')]):
        x=48+i*330
        f.line(x+6,223,x+315,223,TEAL,3)
        f.dot(x+6,223,8)
        f.txt(x,282,name,29,'Times-Bold',NAVY)
        f.para(x,327,detail,295,20,28)
    f.box(48,464,984,102,PALE)
    f.txt(66,495,'Interpretation',19,'Helvetica-Bold',TEAL)
    f.para(66,527,'Compare non-overlapping windows with matching SKU scope. Check season, staffing and lead times. A matched comparison branch would strengthen attribution.',945,19,25)
    return f.finish('This is a prospective before/after plan. The pilot sponsor should pre-register exposure, outcomes and decision thresholds.')

def roadmap():
    f=Figure('F09','Three decisions before wider rollout',
             'Each year is a planning window. A missed condition can pause or redirect the next phase.',
             'SCENARIO',GUIDE+' Expansion is conditional on measured operational and commercial evidence.')
    for i,(year,place,work,gate) in enumerate([('2027','Riyadh','Run a one-branch trial. Record eligible item-days and the cost of onboarding.','Proceed after usable data, safe reconciliation and an agreed KPI review.'),('2028','Makkah and Eastern','Replicate the workflow with a second operator. Test the full cost of branch support.','Proceed after partner permission, repeatable onboarding and credible unit economics.'),('2029','Four further regions','Select sites by readiness, demand for the product and support capacity.','Extend only where the sponsor can sustain controls and service delivery.')]):
        y=195+i*135
        f.txt(48,y+32,year,34,'Times-Bold',TEAL)
        f.txt(166,y+28,place,22,'Helvetica-Bold',NAVY)
        f.para(166,y+60,work,390,18,24)
        f.para(596,y+28,gate,412,19,26)
        f.line(48,y+112,1032,y+112)
    return f.finish('The region sequence follows the supplied strategic guide. Funding, signed partners, staff capacity and measured results are future decisions.')

def evidence():
    f=Figure('F10','Which claim can each record support?',
             'Read the evidence label together with its source, scope and observation period.',
             'DERIVED','Evidence taxonomy from the execution directive, section 1. Current pilot results: not measured.')
    mat=[('OBSERVED_PUBLIC','Reported facility count','Workbook cell and year'),('DERIVED','Regional share or density','Numerator, denominator and years'),('VENDOR_CLAIM','Advertised product capability','Dated vendor source'),('SCENARIO','Assumed price or conversion','Editable assumption and range'),('SYNTHETIC_DEMO','Simulated ledger or backtest','Generator, seed and cutoff'),('PILOT_MEASURED','Authorized branch outcome','Evidence metadata, scope and audit'),('UNKNOWN','Unreported price or missing day','Retain the reason for missingness')]
    for i,(kind,meaning,need) in enumerate(mat):
        y=207+54*i
        f.txt(48,y,kind,17,'Helvetica-Bold',TEAL)
        f.txt(319,y,meaning,20)
        f.txt(704,y,need,17,color=MUTED)
        f.line(48,y+15,1032,y+15)
    return f.finish('The record type limits the scope of each claim. Synthetic events cannot establish measured pilot effects.')

def benchmark(bench):
    pts=bench['points']
    if not pts:
        raise ValueError('Synthetic benchmark must contain out-of-time predictions.')
    f=Figure('F11','SIMULATED — NOT VALIDATED ON CLINIC DATA',
             'Rolling-origin predictions and synthetic issued units. Each prediction uses earlier history.',
             'SYNTHETIC_DEMO','Source: data/demo/backtest.json and T05. Synthetic performance does not establish field accuracy.')
    vals=[float(p[k]) for p in pts for k in ('actual','prediction')]
    upper=max(4,math.ceil(max(vals)/4)*4)
    left,top,width,height=106,223,852,251
    for i in range(5):
        y=top+height*(1-i/4)
        f.line(left,y,left+width,y)
        f.txt(left-13,y+5,f'{upper*i/4:g}',16,color=MUTED,anchor='end')
    for i,p in enumerate(pts):
        x=left+i*width/max(1,len(pts)-1)
        f.txt(x,508,p['date'][-5:],16,color=MUTED,anchor='middle')
    for k,col,dash in [('actual',TEAL,None),('prediction',BLUE,[6,4])]:
        prev=None
        for i,p in enumerate(pts):
            x=left+i*width/max(1,len(pts)-1)
            y=top+height*(1-float(p[k])/upper)
            if prev:f.line(*prev,x,y,col,3,dash)
            f.dot(x,y,4 if k=='prediction' else 6,col)
            prev=x,y
    f.txt(106,193,'Base units per day',16,'Helvetica-Bold',MUTED)
    f.line(110,552,155,552,TEAL,4)
    f.txt(169,558,'Synthetic issues',18)
    f.line(404,552,449,552,BLUE,3,[6,4])
    f.txt(462,558,'Prediction: '+str(bench['chosen']),18)
    return f.finish('Prediction-versus-actual comparison for the seeded branch/SKU. Held-out model errors measure behavior on generated records only.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--without-benchmark',action='store_true',help='Build F01-F10 while a synthetic run is unavailable.')
    args=parser.parse_args()
    FIG.mkdir(exist_ok=True)
    rows=json.loads((ROOT/'data/processed/regions.json').read_text(encoding='utf-8-sig'))
    rows=sorted(rows,key=lambda r:r['rank'])
    figures=[ranking(rows),pareto(rows),stage(rows),provenance(),architecture(),policy(),transfers(),pilot(),roadmap(),evidence()]
    if not args.without_benchmark:
        bench=json.loads((ROOT/'data/demo/backtest.json').read_text(encoding='utf-8-sig'))
        figures.append(benchmark(bench))
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)
        pdf=path/'figures.pdf'
        canvas=Canvas(str(pdf),pagesize=(W,H))
        for drawing in figures:
            renderPDF.draw(drawing,canvas,0,0)
            canvas.showPage()
        canvas.save()
        subprocess.run(['pdftoppm','-png','-scale-to','1620',str(pdf),str(path/'figure')],check=True)
        for item,file in zip(CAT,sorted(path.glob('figure-*.png')),strict=True):
            (FIG/item['png']).write_bytes(file.read_bytes())
    (FIG/'catalog.json').write_text(json.dumps(CAT,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Rendered {len(figures)} SVG and PNG pairs.')


if __name__=='__main__':
    main()

