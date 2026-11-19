"""Build the narrative and source notes shared by the presentation, report and app."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
A = 'Workbook A (Datathon Dataset - MedCuraAI - Completed.xlsx)'
F = A + ', 01 Facilities!A4:H18.'
P = A + ', 02 Population!A2:F14.'
G = 'Supplied Arabic presentation guide, slide '
B = 'MedCura AI Visual Research and Codex Blueprint'
LEVELS = ['SCENARIO','UNKNOWN','SCENARIO','DERIVED','SYNTHETIC_DEMO','SCENARIO','SCENARIO','SCENARIO','SCENARIO','SCENARIO']


def build(rows):
    rows=sorted(rows,key=lambda row:row['rank'])
    counts=[row['complexes'] for row in rows]
    total=sum(counts)
    three,seven=sum(counts[:3]),sum(counts[:7])
    a,b,c=counts[:3]
    pct=100*three/total
    p7=100*seven/total
    fields=[
        ('Executive thesis','Inventory decisions for Saudi private medical complexes','A branch manager needs to know what can be issued today, what may expire and what needs approval before the next delivery.',
         [('Start in Riyadh','A proposed single-branch pilot tracks gloves, masks and dressings.'),('Make decisions traceable','Every reorder or transfer should explain its quantity, timing and evidence.')],
         'Use the prototype to show how an inventory record becomes a reviewable supply decision. State at the outset that the Saudi market counts come from dated statistics and branch transactions in the demo are synthetic. The operational value of this proposal remains a pilot question.',G+'1; '+B+', pages 2 and 5.','F05'),
        ('The operating question','What can the branch safely issue today?','A carton on a shelf may already be reserved. A lot can expire before the next inventory count. Staff need both quantities before promising supply.',
         [('Usable units','Separate physical stock from reservations, quarantine and expired lots.'),('Evidence gap','The supplied workbooks contain no dated branch issues, write-offs or counting shifts.')],
         'Use a concrete stocked-but-unavailable example. Stockout events, expiry losses and staff time are outcomes to measure. The guide describes the operating problem, but it does not quantify its prevalence across Saudi complexes.',G+'2; '+B+', pages 5 and 8.','F07'),
        ('Source governance','The regional insurance figures are estimates','A workbook status cell cannot establish that a value was observed. Keep the source, definition and time window beside the number.',
         [('Workbook A','A complete dated regional series is missing. The Q1 2026 figure covers the whole country.'),('Workbook B','Regional estimates allocate a national pool using facility and population weights of 65% and 35%.')],
         'Separate an observation with incomplete primary verification from a derived number and a scenario. Workbook B labels some allocated values verified; the allocation still depends on assumptions. Avoid merging national estimates across different reporting windows.',G+'3; workbooks A and B, 03 Insurance by Region!A2:E14 and 04 Insurance National.','F04'),
        ('Market evidence',f'Three regions account for {pct:.1f}% of private complexes',f'{three:,} of {total:,} private medical complexes were in Riyadh, Makkah and Eastern Province in the 2024 workbook.',
         [(rows[i]['region'],f'{counts[i]:,} locations') for i in range(3)],
         f'The national count reconciles across all 13 administrative regions. Makkah refers to the region. The facility count gives a geographic footprint. There is no chain ownership or buyer identifier. The top seven total {seven:,}, or {p7:.1f}%. Population denominators refer to the 2022 census.',G+'4; '+F+' '+P,'F02'),
        ('Decision mechanism','From one receipt to a reviewed transfer','A dated receipt enters stock in base units. A lot-level issue changes the balance. The next review compares usable stock with demand and expiry.',
         [('Ledger','Record and validate each lot movement.'),('Policy','Compare inventory position with lead-time demand and a safety buffer.'),('Review','A named approver checks the lot, quantity and route before dispatch.')],
         'Demonstrate this sequence with the synthetic branch workspace. Explain why an order cannot increase physical stock before receipt, and why a transfer leaves the source once, then reaches its destination on receipt. Actual adoption and outcomes depend on future field data.',G+'5; '+B+', pages 6–8; prototype ledger and transfer controls.','F06'),
        ('Commercial choices','A chain signs. Its branches use the service.','Facility locations provide a search area. Contracting and revenue require separate assumptions about the number of reachable chains, paid conversion and enabled branches.',
         [('Partner discovery','Identify the buyer and how many branches that buyer controls.'),('Unit economics','Price per paid branch and month. Model onboarding, recurring support, hosting and churn.')],
         'Test willingness to pay and implementation effort with potential buyers. Other vendors advertise inventory or forecasting capabilities. Position reviewable recommendations and light integration as hypotheses for buyer interviews. Healthcare-specific competitor prices remain unknown where the evidence gives no public rate.',G+'6; '+A+', 06 Competitors!A2:H13; '+B+', page 11.','F03'),
        ('Pilot design','One branch, comparable observation windows','Track the same non-pharmaceutical SKUs in a Riyadh branch before and after reviewed alerts begin.',
         [('Baseline','Record eligible SKU-days, stockout starts and hours, write-offs and staff counting time.'),('Silent review','Reconcile scans and compare simple forecasts without changing purchasing.'),('Intervention','Turn on human-reviewed alerts. Log actions, missed scans, staffing and lead-time changes.')],
         'Pre-register the eligible SKU list, windows, main outcome, thresholds and censoring rules with the site. Add a comparison branch or staggered start where feasible. A single-site pre/post difference is an association and seasonality can affect it. Actual pilot outcomes are not measured.',G+'7; '+B+', page 9.','F08'),
        ('Conditional strategy','A pilot in 2027 precedes regional expansion','Each step requires evidence from the preceding stage and permission from the next participating operator.',
         [('2027   Riyadh',f'Seek one branch in a region with {a:,} private complexes. Review baseline quality and adherence.'),('2028   Makkah and Eastern',f'Test replication across the three-region footprint of {three:,} locations.'),('2029   Four further regions',f'Consider Asir, Madinah, Qassim and Jazan. Seven regions total {seven:,} locations.')],
         'The geographic counts come from 2024. The years describe proposed commercial decisions. They do not establish new contracts, integrations or installations. Pause an expansion if support capacity, reconciliation or economics fail the agreed review.',G+'8; '+F+' '+B+', page 12.','F09'),
        ('Measures and risks','The pilot must measure both benefit and failure','Pair each operating measure with a denominator and record events that can bias it.',
         [('Availability','Stockout starts per 1,000 eligible SKU-days and unavailable hours per eligible observation window.'),('Waste and effort','Write-off quantity and cost, tracked inventory value, and counting hours for the same scope.'),('Reliability','Missing scans, reconciliation corrections and lead-time shifts can change the apparent result.')],
         'Agree a go, pivot or no-go rule before observing post-period results. Inspect adverse changes in availability or recording quality alongside any apparent benefit. Count episodes separately from affected SKU-days. Do not replace actual write-offs with estimated risk.',G+'9; '+B+', page 9; T03 measurement protocol.','F08'),
        ('Next decision','What a Riyadh pilot partner can test','Bring a branch owner, a stockkeeper and an authorized operational extract to the same pilot review.',
         [('The data request','A SKU and unit dictionary, dated receipts and issues, lot attributes, lead times and physical counts.'),('The decision','Agree how to measure availability, expiry, effort and adoption before the first alert goes live.')],
         'Close with a request for an authorized operational pilot, rather than a promise of savings. Source-linked statistics support the geographic case, the local prototype demonstrates a workflow, and a measured trial is the next evidence gate.',G+'10; '+F+' '+B+', pages 9 and 12.','F10')
    ]
    return [dict(number=i+1,section=section,title=title,body=body,items=[dict(label=l,text=t) for l,t in items],
                 notes=notes,source_ref=ref,figure=fig,evidence_level=LEVELS[i])
            for i,(section,title,body,items,notes,ref,fig) in enumerate(fields)]


QA=[
('Why Riyadh first?','The 2024 workbook ranks Riyadh first by private complexes. A single-site pilot also gives the team a bounded place to reconcile records and compare the workflow with a baseline.'),
('How many buyers are reachable?','Unknown. The facility data omit parent chain and purchasing authority. Obtain permission to map branches to decision-makers and validate qualified leads independently.'),
('Can the forecast use regional population?','The operational model requires dated branch and SKU usage. A facility-to-population ratio can describe geography, while unknown visits, case mix and consumption prevent it from estimating item demand.'),
('Why compare simple forecasting methods?','A repeatable seasonal or trailing baseline establishes whether complexity adds value on earlier unseen periods. Report the coverage, horizon, sample and error on later observed dates.'),
('What happens to missing observations?','Keep them missing. A genuine zero requires a recorded observation with zero usage. Stockouts can censor demand even when recorded usage is low.'),
('Does the system order automatically?','Purchase and transfer proposals require authorized review. A confirmed order affects expected inbound stock until the goods are physically received.'),
('How do transfers conserve units?','Reserve at request, deduct at dispatch and track goods in transit. Post the destination lot at receipt exactly once. Check remaining shelf life and how fast the receiving site can use it.'),
('How much money does this save?','There is no measured savings estimate. Enter assumed costs and conversion in the scenario model. A field estimate requires comparable operating windows and the full implementation cost.'),
('How does the product differ from existing tools?','The hypotheses are lightweight integration, visible evidence and reviewable inter-branch decisions. Compare these in buyer interviews and trials. Vendor advertising alone cannot establish local deployment or relative superiority.'),
('Can we call a pre/post difference an intervention effect?','A single-branch comparison is vulnerable to season, staffing and supplier changes. Record these factors and use a comparable branch or staggered rollout when feasible.'),
('Has a regulator endorsed the product?','The supplied guide describes a strategic interpretation. Any pilot must undergo its own privacy, cybersecurity, supplier, hosting and classification reviews.')
]


def main():
    rows=json.loads((ROOT/'data/processed/regions.json').read_text(encoding='utf-8-sig'))
    slides=build(rows)
    deck=ROOT/'presentation'
    deck.mkdir(exist_ok=True)
    (deck/'story.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2),encoding='utf-8')
    docs=ROOT/'docs'
    md=['# MedCura AI datathon story','', 'Ten-slide speaking guide for a panel evaluating a proposed Saudi inventory pilot.']
    for s in slides:
        md += ['',f"## {s['number']}. {s['title']}",'',s['body'],'']
        md += [f"- **{it['label']}.** {it['text']}" for it in s['items']]
        md += ['',s['notes'],'',f"Figure {s['figure']}. Evidence class {s['evidence_level']}. Source: {s['source_ref']}"]
    (docs/'DATATHON_10_SLIDE_STORY.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    (docs/'JUDGE_QA.md').write_text('# Questions from the judging panel\n\n'+'\n\n'.join('## '+q+'\n\n'+a for q,a in QA)+'\n',encoding='utf-8')
    n=sum(r['complexes'] for r in rows)
    p=sum(r['population'] for r in rows)
    facts=['# Presentation fact sheet','','Facility figures are workbook observations for 2024. Population describes 2022. The regional administrative unit includes cities and their surrounding areas.','','| Claim | Calculation or source | Evidence |','| --- | --- | --- |',f'| {n:,} private medical complexes | Sum of 13 regions, A 01 Facilities!F5:F17. National check F18. | OBSERVED_PUBLIC |']
    for k in (3,7):
        s=sum(r['complexes'] for r in rows[:k])
        facts.append(f'| Top {k}: {s:,} ({s/n:.1%}) | Rank by F5:F17, sum top {k}, divide by {n:,}. | DERIVED |')
    facts.extend([f'| {p:,} residents | A 02 Population!B2:B14. Census year 2022. | OBSERVED_PUBLIC |',
       '| 166 private hospitals | A 01 Facilities!D18. A distinct entity class. | OBSERVED_PUBLIC |',
       '| Missing regional insurance | A 03 Insurance by Region. B allocates its national total using 65/35 weights. | UNKNOWN / SCENARIO |',
       '| Forecast benchmark | data/demo/backtest.json. Dated synthetic issues only. | SYNTHETIC_DEMO |',
       '| Prospective branch outcomes | No authorized pilot observations supplied. | UNKNOWN |','',
       'The Arabic guide is a narrative reference. Where a guide cell and workbook disagree, cite the workbook-level lineage and the relevant conflict decision. Unobserved willingness to pay, adoption and operating gains require field research.'])
    (docs/'PRESENTATION_FACTS.md').write_text('\n'.join(facts)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

