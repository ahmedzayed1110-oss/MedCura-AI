"""Build the standalone research report with reportlab from canonical JSON and figure PNGs."""
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

ROOT=Path(__file__).resolve().parents[1]
W,H=A4
NAVY='#10263E'
TEAL='#006D70'
MUTED='#475F68'
PALE='#E5F1EA'
INK='#243742'
RULE='#C0D1CC'


class Page:
    def __init__(self,c,number,section,title):
        self.c=c
        self.number=number
        self.txt(42,38,'MEDCURA AI   /   RESEARCH REPORT',9,'Helvetica-Bold',TEAL)
        self.txt(W-42,38,'19 NOVEMBER 2026',9,'Helvetica',MUTED,'right')
        self.rule(51)
        self.txt(42,84,section.upper(),10,'Helvetica-Bold',TEAL)
        self.txt(42,126,title,self.fit(title,31,W-84,'Times-Bold'),'Times-Bold',NAVY)
    def fit(self,text,size,width,font):
        return min(size,size*width/max(1,stringWidth(text,font,size)))
    def txt(self,x,y,s,size=11,font='Helvetica',color=INK,align='left'):
        self.c.setFillColor(HexColor(color))
        self.c.setFont(font,size)
        (self.c.drawRightString if align=='right' else self.c.drawString)(x,H-y,s)
    def rule(self,y,x1=42,x2=None):
        self.c.setStrokeColor(HexColor(RULE))
        self.c.setLineWidth(.6)
        self.c.line(x1,H-y,W-42 if x2 is None else x2,H-y)
    def para(self,txt,y,x=42,width=None,size=12,lead=17,font='Helvetica',color=INK):
        width=width or W-84
        line=''
        for word in txt.split():
            joined=(line+' '+word).strip()
            if line and stringWidth(joined,font,size)>width:
                self.txt(x,y,line,size,font,color)
                line=word
                y+=lead
            else: line=joined
        if line:
            self.txt(x,y,line,size,font,color)
        return y+lead
    def heading(self,text,y):
        self.txt(42,y,text,17,'Times-Bold',NAVY)
        return y+25
    def block(self,title,body,y):
        return self.para(body,self.heading(title,y))+20
    def panel(self,label,body,y,height=88):
        self.c.setFillColor(HexColor(PALE))
        self.c.rect(42,H-y-height,W-84,height,stroke=0,fill=1)
        self.txt(55,y+23,label,11,'Helvetica-Bold',TEAL)
        last=self.para(body,y+45,55,W-110,size=11,lead=15)
        if last-15>y+height-4:raise ValueError('Panel overflow: '+label)
    def done(self,source):
        self.rule(773)
        self.para(source,790,42,W-130,9,12,color=MUTED)
        self.txt(W-42,804,str(self.number).zfill(2),11,'Helvetica-Bold',TEAL,'right')
        self.c.showPage()


def main():
    data=json.loads((ROOT/'data/processed/regions.json').read_text(encoding='utf-8'))
    bench=json.loads((ROOT/'data/demo/backtest.json').read_text(encoding='utf-8'))
    rows=sorted(data,key=lambda r:r['rank'])
    total=sum(r['complexes'] for r in rows)
    top3=sum(r['complexes'] for r in rows[:3])
    top7=sum(r['complexes'] for r in rows[:7])
    out=ROOT/'presentation/MedCura_AI_Research_Report.pdf'
    out.parent.mkdir(exist_ok=True)
    c=Canvas(str(out),pagesize=A4)
    c.setTitle('MedCura AI | Research evidence and pilot design')
    c.setAuthor('MedCura AI project')
    p=Page(c,1,'Executive brief','Inventory decisions for private medical complexes')
    y=p.para('An evidence review and proposed one-branch pilot in Riyadh',158,size=17,lead=21,font='Times-Italic',color=TEAL)
    y=p.para('A stockkeeper deciding whether to issue or transfer a box of dressings needs its usable quantity, remaining shelf life and expected use. A regional facility count answers a different question: where to look for a potential pilot partner.',y+20,size=13,lead=19)
    y=p.block('The geographic case',f'The two supplied workbooks agree on {total:,} private medical complexes across 13 Saudi administrative regions in 2024. Riyadh, Makkah and Eastern Province account for {top3:,}, or {100*top3/total:.1f}%. The workbooks do not identify corporate ownership, purchasing authority or branch consumption.',y+30)
    y=p.block('The operational question','Could lot-aware records and human-reviewed recommendations improve availability or reduce waste? The local system demonstrates receipts, issues and review using synthetic records. Its forecast benchmark evaluates generated time series only.',y+5)
    y=p.block('The field decision','Seek one authorized Riyadh partner. Agree on eligible SKUs, access roles, data quality gates and pre/post dates before enabling alerts. Measure stockout episodes, unavailable hours, actual write-offs and comparable staff effort.',y+5)
    p.panel('Evidence status','Market counts: workbook-cross-checked. Derived shares: reproducible arithmetic. Branch operations: synthetic demonstration. Commercial forecasts: editable scenarios. Actual clinic outcomes: not measured.',y+10,98)
    p.done('Sources: Workbook A, 01 Facilities!F5:F18. Arabic presentation guide, slides 1, 4 and 7. Research blueprint, pages 5, 8 and 9.')

    p=Page(c,2,'Market evidence','Thirteen regions, one dated footprint')
    p.para('Ranked by 2024 private medical complexes. Density is complexes per 100,000 residents using the 2022 census denominator.',158,size=12)
    ys=221
    p.txt(42,ys,'Administrative region',9,'Helvetica-Bold',TEAL)
    for x,t in [(269,'Complexes'),(350,'Share'),(455,'2022 residents'),(551,'Density')]:p.txt(x,ys,t,9,'Helvetica-Bold',TEAL,'right')
    p.rule(232)
    for i,r in enumerate(rows):
        y=253+i*24
        p.txt(42,y,r['region'],11,'Helvetica-Bold' if i<3 else 'Helvetica')
        for x,t in [(269,f"{r['complexes']:,}"),(350,f"{r['share_pct']:.1f}%"),(455,f"{r['population']:,}"),(551,f"{r['density']:.2f}")]:
            p.txt(x,y,t,11,align='right')
        p.rule(y+8)
    y=577
    p.txt(42,y,'Saudi Arabia',12,'Helvetica-Bold',NAVY)
    pop=sum(r['population'] for r in rows)
    for x,t in [(269,f'{total:,}'),(350,'100.0%'),(455,f'{pop:,}'),(551,f'{100000*total/pop:.2f}')]:
        p.txt(x,y,t,11,'Helvetica-Bold',NAVY,'right')
    y=p.para(f'The top seven regions account for {top7:,} complexes ({100*top7/total:.1f}%). Among categories reported separately in 2024 were {sum(r["private_hospitals"] for r in rows):,} private hospitals and {sum(r["phcs"] for r in rows):,} government primary care centers.',621)
    p.para('Makkah denotes the administrative region. The mixed-year density is descriptive. It cannot establish visits, workload, stockout risk or consumable use. Regional shares may sum differently after rounding.',y+12)
    p.done('Sources: Workbook A, 01 Facilities!A5:H18 and 02 Population!A2:F14. Workbook B cross-check. Canonical T01 and cell-level lineage provide the regional calculation trail.')

    p=Page(c,3,'Source quality','What survives reconciliation')
    y=p.para('Start with original files, hashes and exact cells. Keep definitions and reporting periods beside the observed value. Preserve both sides of a disagreement even when the public dashboard uses only one.',162,size=12.5,lead=18)
    topics=[
        ('Regional insurance','Workbook B allocates beneficiaries using 65% private-facility share and 35% population share. This yields a scenario. Workbook A has no complete dated regional series; the rounded Riyadh value lacks a reference period. Keep the dated observed regional field empty.'),
        ('National insurance','Workbook A reports 14.5 million insured beneficiaries in Q1 2026. The Insurance Authority published its Q1 report on 8 September 2026. Workbook B cites 13 million for 2024. Different periods cannot be combined into a single observed regional estimate.'),
        ('Definitions and periods','The 56 single-doctor clinics in Workbook A form a narrow category. The total number of standalone clinics remains unknown. One-year growth in 2021-2022 and compound growth over 2010-2022 measure different changes.'),
        ('Competitor claims','The competitor sheet records vendor descriptions and source links. An advertised feature does not independently establish a deployment. Keep healthcare prices blank when unpublished. General warehouse software tariffs describe a different offer.'),
        ('Guide versus workbook','The Arabic guide lists 9 private hospitals in Madinah and 4 in Jazan. Workbook A reports 10 and 3, respectively. The two entries offset in the national sum. Regional comparisons in this project use the traceable workbook cells.')]
    for head,body in topics:y=p.block(head,body,y+9)
    p.done('Sources: A and B, 03 Insurance by Region, 04 Insurance National, 06 Competitors and 01 Facilities!D8/D13. Arabic guide, page 3. Insurance Authority Q1 2026 publication (ia.gov.sa/en/media-center/news/128).')

    p=Page(c,4,'Decision science','A forecast test on synthetic issues')
    y=p.para('SIMULATED - NOT VALIDATED ON CLINIC DATA',160,size=13,font='Helvetica-Bold',color=TEAL)
    p.para(f"The deterministic demo represents {bench['sku'].lower()} at {bench['branch']}. The selection window precedes the held-out predictions. Each forecast uses only prior dated, closed observations. The comparison covers {len(bench['points'])} one-day evaluation origins ending {bench['cutoff']}.",y+13)
    p.txt(42,278,'Baseline',10,'Helvetica-Bold',TEAL)
    for x,v in [(332,'MAE (units)'),(412,'WAPE'),(481,'sMAPE'),(551,'Bias (units)')]:p.txt(x,278,v,9,'Helvetica-Bold',TEAL,'right')
    p.rule(289)
    for i,r in enumerate(bench['scores']):
        y=313+i*28
        p.txt(42,y,r['model'].capitalize(),11,'Helvetica-Bold' if r['model']==bench['chosen'] else 'Helvetica')
        for x,val in [(332,f"{r['mae']:.2f}"),(412,f"{r['wape']:.1%}" if r['wape'] is not None else 'undefined'),(481,f"{r['smape']:.1%}"),(551,f"{r['bias']:+.2f}")]:
            p.txt(x,y,val,11,align='right')
        p.rule(y+9)
    y=p.para(f"Earlier validation selected {bench['chosen']}. MAE is absolute error per day. WAPE divides total absolute error by total observed issues. Bias is prediction minus actual. The small held-out set provides no calibrated interval or empirical clinic accuracy.",477)
    y=p.block('Replenishment review','Compare available-to-promise stock and eligible inbound with expected lead-time usage and the disclosed safety buffer. Round a candidate to pack size and minimum order quantity; check capacity and shelf life. An authorized manager reviews the order.',y+26)
    p.para('A transfer requires an eligible lot, sufficient origin cover, destination demand and time to consume the units after arrival. Record the shipment in transit until receipt. Proposed avoided waste remains an estimate until write-offs are observed.',y+4)
    p.done('Source: data/demo/backtest.json, data/demo/T05.csv and apps/api/science.py. Scores apply to the seeded history only. See F06, F07 and F11.')

    p=Page(c,5,'Evaluation and strategy','From a signed protocol to a rollout decision')
    y=p.para('The partner and research lead should agree on a one-branch pilot before collecting outcomes. A proposed configuration follows three SKUs across 28 eligible days per period, or 84 planned SKU-days. Report missing days separately.',161)
    y=p.block('Measurement and comparison','Use non-overlapping windows and a stable item list. Count stockout starts per 1,000 eligible SKU-days, unavailable hours, expired units and write-off value, staff counting hours for equal scope, and scans per eligible movement. Align supplier lead times and flag seasonal changes, staffing or shortages that censor consumption.',y+20)
    y=p.block('Progression rules','Pre-register data completeness, scan adoption, minimum duration and an agreed operating KPI. Proceed only after safety, integration, access and evidence checks pass. Adjust the workflow and repeat when adoption or coverage falls short. Stop or defer if reconciliation or safety fails. Compare a matched branch where feasible.',y+4)
    y=p.block('Commercial scenario','In the base illustration, 12 reachable chains and successive 50% qualification, pilot and payment rates yield one paying chain after rounding down at each stage. Two branches at SAR 600 per month yield SAR 1,200 exit MRR and SAR 14,400 annualized recurring revenue. These are assumed inputs and modeled values.',y+4)
    y=p.block('2027 to 2029','Start with a proposed Riyadh partner in 2027. If there is measured improvement, acceptable cost and partner approval, test replication toward Makkah and Eastern Province in 2028. In 2029 consider Asir, Madinah, Qassim and Jazan after repeatable onboarding and evidence of support capacity.',y+4)
    p.para('Next evidence request: approved inventory extract, SKU/base-unit dictionary, lot and expiry applicability, dated receipts and issues, stockout windows, write-offs, lead times and comparable staff counting effort. Exclude patient data.',y+6,size=11.5,color=TEAL)
    p.done('Sources: supplied guide, slides 6-10; blueprint, pages 9-12. Base economics is a scenario. Measurement thresholds require partner agreement. Regulatory and deployment review remain open.')
    c.save()
    print(out)


if __name__=='__main__':
    main()

