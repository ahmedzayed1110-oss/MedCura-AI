"""Rebuild workbook observations and source audit. Run from any directory.

Install the optional packages in scripts/requirements-evidence.txt to regenerate.
The running application reads only the exported UTF-8 JSON/CSV files.
"""
import argparse
import csv
import hashlib
import json
import logging
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC, POP, INS, NAT, WORK, COMP, ANALYSIS, SOURCES = (
    '01 Facilities', '02 Population', '03 Insurance by Region', '04 Insurance National',
    '05 Workforce', '06 Competitors', '07 Regional Analysis', '08 Sources')
REGIONS = {'Riyadh','Makkah','Eastern Province','Madinah','Qassim','Asir','Tabuk',
           'Hail','Jazan','Najran','Al-Baha','Al-Jouf','Northern Borders'}
KEYS = {'hospitals':'Hospitals total','government_hospitals':'Hospitals government',
        'private_hospitals':'Hospitals private','phcs':'Primary care centers (govt)',
        'complexes':'Medical complexes (private)','clinics':'Single-doctor private clinics'}
MOH = 'https://www.moh.gov.sa/en/Ministry/Statistics/book/Documents/Statistical-Yearbook-2024.xlsx'
IA = 'https://www.ia.gov.sa/en/media-center/news/128'
CAVEAT = 'Workbook transcription. Administrative region. Facility locations only.'
EXPECTED = {'complexes':3607, 'top3':2527, 'top7':3238,'private_hospitals':166,
            'regions':13,'population':32175224}

def as_json(value):
    return json.dumps(value,ensure_ascii=False,indent=2,default=str,allow_nan=False) + '\n'

def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(as_json(value),encoding='utf-8')

def write_csv(file, rows):
    def clean(v):
        if isinstance(v,(list,dict)):
            return json.dumps(v,ensure_ascii=False)
        if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')):
            return "'" + v
        return v
    with file.open('w',encoding='utf-8-sig',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader()
        writer.writerows([{k:clean(v) for k,v in row.items()} for row in rows])

def record(value,ref,year,level,unit,notes,calc=None,url=None,**extra):
    return dict(value=value,source_ref=ref,reference_year=year,evidence_level=level,
                unit=unit,notes=notes,calculation_id=calc,citation_url=url,**extra)

def ref(book, sheet, cell):
    return f'{book} · {sheet}!{cell.coordinate}'

def header(ws, first):
    for row in ws:
        if row[0].value==first:
            return row[0].row, {c.value:c.column for c in row if c.value is not None}
    raise ValueError(f'Missing "{first}" header in {ws.title}')

def region_rows(ws):
    start,cols=header(ws,'Region')
    found={}
    for row in list(ws)[start:]:
        name=row[0].value
        if name is None or str(name).startswith(('SAUDI ARABIA','https:','Source:','2024 MOH',
                'PHC =','Standalone clinics','Hospital total')):
            continue
        if name not in REGIONS or name in found:
            raise ValueError(f'{ws.title}!{row[0].coordinate}: unexpected or duplicated region {name!r}')
        found[name]=row[0].row
    if set(found)!=REGIONS:
        raise ValueError(f'{ws.title}: missing regions {sorted(REGIONS-set(found))}')
    return found,cols

def whole(cell, allow_zero=True):
    if type(cell.value) is not int or cell.value<0 or (not allow_zero and cell.value==0):
        raise ValueError(f'{cell.parent.title}!{cell.coordinate}: expected integer count, got {cell.value!r}')
    return cell.value

def workbook_audit(path, book, out):
    import openpyxl
    wb=openpyxl.load_workbook(path,data_only=True)
    formulas=openpyxl.load_workbook(path,data_only=False)
    metadata={k:getattr(wb.properties,k) for k in ['creator','title','description','created','modified','lastModifiedBy']}
    sheets=[]; cells=[]
    for ws in wb:
        fws=formulas[ws.title]
        formulas_found=[]; filled=[]; url_count=0; fingerprints=[]
        for row in ws:
            if any(c.value is not None for c in row):
                fingerprints.append(tuple(str(c.value) for c in row))
            for c in row:
                fc=fws[c.coordinate]
                if c.value is None and fc.value is None:
                    continue
                filled.append(c)
                formula=fc.value if fc.data_type=='f' else None
                url=re.findall(r'https?://[^\s|]+',str(c.value))
                if fc.hyperlink and fc.hyperlink.target:
                    url.append(fc.hyperlink.target)
                cells.append(dict(book=book,sheet=ws.title,cell=c.coordinate,
                    source_ref=ref(book,ws.title,c),value=c.value,formula=formula,
                    cached_value=c.value if formula else None,urls=list(dict.fromkeys(url))))
                url_count+=bool(url)
                if formula: formulas_found.append([c.coordinate,formula,c.value])
        start=next((c.row for c in filled if c.column==1 and c.value in ('Region','Metric','Competitor','Field','Section','MEDCURA AI DATATHON | WORKBOOK GUIDE')),None)
        bounds=None
        if filled:
            from openpyxl.utils import get_column_letter as col
            bounds=f'{col(min(c.column for c in filled))}{min(c.row for c in filled)}:{col(max(c.column for c in filled))}{max(c.row for c in filled)}'
        sheets.append(dict(name=ws.title,dimension=ws.calculate_dimension(),rows=ws.max_row,
            columns=ws.max_column,populated_range=bounds,header_row=start,
            populated_cells=len(filled),blank_cells_in_dimensions=ws.max_row*ws.max_column-len(filled),
            hidden=ws.sheet_state!='visible',merged_ranges=sorted(map(str,ws.merged_cells.ranges)),
            url_cells=url_count,formula_count=len(formulas_found),formulas=formulas_found,
            duplicate_nonempty_rows=sum(n-1 for n in Counter(fingerprints).values() if n>1)))
    save(out/f'cells_{book}.json',cells)
    formulas.close()
    return wb,dict(metadata=metadata,sheets=sheets,format='OOXML XLSX',cell_snapshot=f'cells_{book}.json')

def canonical(books):
    a,b=books['A'],books['B']
    index={k:{s:region_rows(w[s]) for s in (FAC,POP,INS,WORK,ANALYSIS)} for k,w in books.items()}
    def get(k,s,name,field):
        rows,cols=index[k][s]
        return books[k][s].cell(rows[name],cols[field])
    observations={}; metrics={}; conflicts=[]; rows=[]
    def conflict(topic,ac,bc,decision,level,year,**extras):
        conflicts.append(dict(id=f'C{len(conflicts)+1:03}',topic=topic,
            source_a=ref('A',ac.parent.title,ac),value_a=ac.value,
            source_b=ref('B',bc.parent.title,bc),value_b=bc.value,
            decision=decision,evidence_level=level,reference_year=year,
            calculation_id=None,source_ref=f'{ref("A",ac.parent.title,ac)} / {ref("B",bc.parent.title,bc)}',
            notes=decision,**extras))
    def shared(s,name,field):
        ac,bc=[get(k,s,name,field) for k in ('A','B')]
        if ac.value!=bc.value:
            raise ValueError(f'Source mismatch: {ref("A",s,ac)}={ac.value!r}; {ref("B",s,bc)}={bc.value!r}')
        return ac
    for name in sorted(REGIONS):
        ident=name.lower().replace(' ','-')
        rr=dict(id=ident,region=name)
        for key,field in KEYS.items():
            ac=get('A',FAC,name,field) if key=='clinics' else shared(FAC,name,field)
            val=whole(ac)
            yr=whole(shared(FAC,name,'Year'))
            if yr!=2024:raise ValueError(f'{FAC}!{ac.coordinate}: unexpected facility year {yr}')
            note=CAVEAT if key!='clinics' else 'Only the MOH single-doctor category. Broader standalone clinic count unavailable.'
            obs=record(val,ref('A',FAC,ac),yr,'OBSERVED_PUBLIC','locations',note,url=MOH,
                       verification_status='workbook transcription',entity=key)
            if key!='clinics':obs['corroborating_cell']=ref('B',FAC,get('B',FAC,name,field))
            observations[f'{ident}.{key}']=obs
            rr[key]=val
        if rr['hospitals']!=rr['government_hospitals']+rr['private_hospitals']:
            raise ValueError(f'Hospital subtotal mismatch: {name}, {FAC} row {index["A"][FAC][0][name]}')
        pc=shared(POP,name,'Population')
        pyear=whole(shared(POP,name,'Population year'))
        if pyear!=2022:raise ValueError(f'{POP}!{pc.coordinate}: unexpected census year {pyear}')
        rr['population']=whole(pc,False)
        observations[f'{ident}.population']=record(rr['population'],ref('A',POP,pc),pyear,
            'OBSERVED_PUBLIC','residents','2022 Census as transcribed in the two workbooks.',
            url=get('A',POP,name,'Source URL').value,corroborating_cell=ref('B',POP,get('B',POP,name,'Population')))
        ac,bc=[get(k,INS,name,'Insured beneficiaries') for k in ('A','B')]
        rr['insured']=None
        if type(ac.value) is int and type(get('A',INS,name,'Year').value) is int:
            rr['insured']=whole(ac)
        decision=('A cites a rounded 9.7M dashboard value without a reference date. Exclude it from year-specific totals. '
                  if type(ac.value) is int else 'Leave the observed field null. ') + 'B allocates a national figure using 65% facility share and 35% population share.'
        conflict(f'{name} insurance',ac,bc,decision,'SCENARIO',get('B',INS,name,'Year').value)
        observations[f'{ident}.insured']=record(rr['insured'],ref('A',INS,ac),None,'UNKNOWN','beneficiaries',
            decision,url=get('A',INS,name,'Source URL').value,reported_value=ac.value)
        observations[f'{ident}.allocated_insured']=record(whole(bc),ref('B',INS,bc),2024,'SCENARIO','beneficiaries',
            get('B',INS,name,'Verification status').value,'B-weighted-regional-allocation',get('B',INS,name,'Source URL').value)
        for field in ('Physicians','Hospital beds'):
            ac,bc=[get(k,WORK,name,field) for k in ('A','B')]
            conflict(f'{name} {field.lower()}',ac,bc,'A cites MOH branch aggregation. B uses weights. Keep B as a scenario.','SCENARIO',2024)
            observations[f'{ident}.{field.lower().replace(" ","_")}']=record(whole(ac),ref('A',WORK,ac),2024,'OBSERVED_PUBLIC',
                field.lower(),get('A',WORK,name,'Verification status').value,url=get('A',WORK,name,'Source URL').value)
        ac,bc=[get(k,POP,name,'Growth rate %') for k in ('A','B')]
        conflict(f'{name} population growth',ac,bc,'Separate 2021–2022 change in A and 2010–2022 CAGR in B. Historical denominator series were not supplied.','DERIVED','different periods')
        for book,c,period,method in [('A',ac,'2021–2022','one-year change'),('B',bc,'2010–2022','compound annual growth')]:
            observations[f'{ident}.growth_{book}']=record(c.value,ref(book,POP,c),period,'DERIVED','fraction',
                'As reported. Individual historical inputs unavailable. Treat as provisional.',method,get(book,POP,name,'Source URL').value)
        rr.update(source_ref=observations[f'{ident}.complexes']['source_ref'],reference_year=2024,population_year=2022,
                  evidence_level='OBSERVED_PUBLIC',notes=CAVEAT,calculation_id=None)
        rows.append(rr)
    rows.sort(key=lambda r:(-r['complexes'],r['region']))
    def refs(items,field):
        return ', '.join(observations[f'{r["id"]}.{field}']['source_ref'] for r in items)
    def summed(items,field):return sum(r[field] for r in items)
    def add_total(key,field,items,year,unit,url):
        metrics[key]=record(summed(items,field),refs(items,field),year,'DERIVED',unit,
                           'Sum of distinct administrative regions.',f'sum-{key}-v1',url)
    for key,items in [('complexes',rows),('top3',rows[:3]),('top7',rows[:7])]:
        add_total(key,'complexes',items,2024,'private medical complexes',MOH)
    add_total('population','population',rows,2022,'residents',observations['riyadh.population']['citation_url'])
    add_total('private_hospitals','private_hospitals',rows,2024,'hospitals',MOH)
    metrics['regions']=record(len(rows),refs(rows,'complexes'),2024,'DERIVED','regions','Distinct region identifiers.','count-distinct-regions',MOH)
    total=metrics['complexes']['value']
    for key in ('top3','top7'):
        n=metrics[key]['value']
        metrics[key+'_share']=record(100*n/total,metrics[key]['source_ref']+' / '+metrics['complexes']['source_ref'],2024,
            'DERIVED','%','Share of all 2024 private medical complexes.',f'{key}/national*100',MOH,numerator=n,denominator=total)
    for key,expected in EXPECTED.items():
        if metrics[key]['value']!=expected:
            raise ValueError(f'Anchor {key}: {metrics[key]["value"]} != {expected}; inspect {metrics[key]["source_ref"]}')
    for area,n in [('Riyadh',1171),('Makkah',880),('Eastern Province',476),('Asir',255),('Madinah',182),('Qassim',146),('Jazan',128)]:
        obs=observations[area.lower().replace(' ','-')+'.complexes']
        if obs['value']!=n:raise ValueError(f'Anchor {area}: {obs["source_ref"]}={obs["value"]}; expected {n}')
    for key,field in KEYS.items():
        for book,wb in books.items():
            if key=='clinics' and book=='B':continue
            ws=wb[FAC]
            totals=next(row for row in ws if row[0].value=='SAUDI ARABIA')
            cell=totals[index[book][FAC][1][field]-1]
            if summed(rows,key)!=whole(cell):raise ValueError(f'National subtotal mismatch: {ref(book,FAC,cell)}')
    cumulative=0
    for ix,r in enumerate(rows,1):
        cumulative+=r['complexes']
        r.update(rank=ix,share_pct=100*r['complexes']/total,cumulative_pct=100*cumulative/total,
                 density=100000*r['complexes']/r['population'])
        for field,num,den,factor,src,yr,unit in (
            ('share_pct',r['complexes'],total,100,r['source_ref']+' / '+metrics['complexes']['source_ref'],2024,'%'),
            ('cumulative_pct',cumulative,total,100,refs(rows[:ix],'complexes')+' / '+metrics['complexes']['source_ref'],2024,'%'),
            ('density',r['complexes'],r['population'],100000,r['source_ref']+' / '+observations[r['id']+'.population']['source_ref'],'2024 / 2022','complexes per 100,000 residents')):
            observations[r['id']+'.'+field]=record(r[field],src,yr,'DERIVED',unit,
                'Facility geography only. No consumption or patient-traffic inference.',
                f'{field}-v1',MOH,numerator=num,denominator=den,factor=factor)
        observations[r['id']+'.rank']=record(ix,metrics['complexes']['source_ref'],2024,'DERIVED',
            'ordinal','Descending facility count, ties ordered by region name.','rank-complexes-v1',MOH)
    conflict('National insured periods',a[NAT]['B5'],b[INS]['B15'],
             'Separate Q1 2026 and 2024. IA reports 14.5M on 8 September 2026. B cites 13M for 2024.','OBSERVED_PUBLIC','Q1 2026 / 2024')
    conflict('Clinic definition',a[FAC]['G18'],b[FAC]['G18'],'56 represents single-doctor clinics only. Broader standalone clinic total unknown.','UNKNOWN',2024)
    conflict('Density and throughput',a[ANALYSIS]['I3'],b[ANALYSIS]['I3'],'Density describes geography. Patient throughput, replenishment need and consumption require branch records.','UNKNOWN','2024 / 2022')
    conflict('Market-entry timeline',a[ANALYSIS]['I3'],b[ANALYSIS]['I3'],'B suggests 2027 Makkah expansion. The adopted guide proposes conditional expansion in 2028.','SCENARIO','2027–2029')
    conflict('Competitor comparison scope',a[COMP]['E13'],b[COMP]['E13'],'Generic WMS tiers and bundled ERP ranges lack comparable scope. Leave healthcare-specific normalized prices null.','UNKNOWN','2025–2026')
    metrics['insured_q1_2026']=record(whole(a[NAT]['B5']),ref('A',NAT,a[NAT]['B5']),'Q1 2026','OBSERVED_PUBLIC',
        'beneficiaries','National health insurance beneficiaries, publication date 2026-09-08.',url=IA,verification_status='primary corroborated')
    for sheet,field,coord in [(POP,'Population','B15'),(INS,'Insured beneficiaries','B15'),
                               (WORK,'Physicians','B15'),(WORK,'Hospital beds','C15')]:
        total_b=sum(whole(get('B',sheet,name,field)) for name in REGIONS)
        if total_b!=whole(b[sheet][coord]):
            raise ValueError(f'Workbook B {sheet}!{coord}: cached subtotal disagrees with regional rows')
    observations['insured_2024']=record(whole(b[INS]['B15']),ref('B',INS,b[INS]['B15']),2024,
        'OBSERVED_PUBLIC','beneficiaries','Workbook-reported national value; primary table unconfirmed.',
        url=b[INS]['D15'].value,verification_status='provisional national transcription')
    competitors=[]
    for book,wb in books.items():
        ws=wb[COMP]
        start,cols=header(ws,'Competitor')
        for row in list(ws)[start:]:
            def fld(key):return row[cols[key]-1].value
            competitors.append(dict(name=fld('Competitor'),product=fld('Product / service'),segment=fld('Target segment'),
                reported_price=fld('Published price SAR'),price_sar=None,
                evidence_level='VENDOR_CLAIM' if book=='A' else 'UNKNOWN',
                source_ref=ref(book,COMP,row[0]),price_source_ref=ref(book,COMP,row[4]),reference_year=fld('Evidence date'),
                notes='Workbook-attributed description. Comparable healthcare price and deployment require separate verification.',
                citation_url=fld('Source URL'),calculation_id=None,
                verification_status='Vendor page corroborates advertised seasonal forecasting and supply tracking. Independent deployment unknown.'
                  if book=='A' and fld('Competitor')=='Medlog' else 'workbook attribution only'))
    return rows,metrics,observations|metrics,conflicts,competitors

def pdf_audit(path,out,code):
    import pdfplumber
    logging.getLogger('pdfminer').setLevel(logging.ERROR)
    with pdfplumber.open(path) as doc:
        pages=[]
        for pg in doc.pages:
            text=pg.extract_text() or ''
            pages.append(dict(page=pg.page_number,text=text,tables=pg.extract_tables(),
                              width=pg.width,height=pg.height))
        save(out/f'pages_{code}.json',pages)
        return dict(format='PDF',pages=len(pages),metadata=doc.metadata,
                    extraction=f'pages_{code}.json',tables_detected=sum(len(p['tables']) for p in pages),
                    issues=['Arabic PDF uses presentation forms and mixed visual order. Consult the original page for precise reading.']
                    if code=='guide' else [])

def compare_guide(out,rows,lineage,conflicts):
    pages=json.loads((out/'pages_guide.json').read_text(encoding='utf-8'))
    table=pages[2]['tables'][0]
    for data in rows:
        for entry in table[1:]:
            english='Eastern' if data['region']=='Eastern Province' else data['region']
            if '('+english+')' not in str(entry[-1]):
                continue
            private=re.fullmatch(r'[\d,]+\s*\(([\d,]+)\)',entry[3] or '')
            if not private:
                raise ValueError(f'Cannot parse guide p.3 hospital cell for {english}')
            n=int(private.group(1).replace(',',''))
            if n!=data['private_hospitals']:
                ref_a=lineage[data['id']+'.private_hospitals']['source_ref']
                ref_b=f'Guide · p.3 market table · {english} · private hospitals'
                decision='The two source workbooks agree. Use their count and flag the guide for editorial correction.'
                conflicts.append(dict(id=f'C{len(conflicts)+1:03}',topic=f'{english} guide discrepancy',
                    source_a=ref_a,value_a=data['private_hospitals'],source_b=ref_b,value_b=n,decision=decision,
                    evidence_level='OBSERVED_PUBLIC',reference_year=2024,calculation_id=None,
                    source_ref=ref_a+' / '+ref_b,notes=decision))
    
def ingest(project=ROOT):
    import openpyxl
    raw=project/'data/raw'; processed=project/'data/processed'
    processed.mkdir(parents=True,exist_ok=True)
    audit_time=datetime.now(timezone.utc).isoformat()
    manifest=dict(extracted_utc=audit_time,files=[],unavailable_optional=['MedCura_AI_Codex_Master_Blueprint.md'])
    books={}; files=sorted(raw.iterdir()); contract=project/'MedCura_AI_ONE_SHOT_CODEX_MASTER_PROMPT.md'
    if contract.exists(): files.append(contract)
    with tempfile.TemporaryDirectory(dir=processed.parent) as staged:
        out=Path(staged)
        for path in files:
            if not path.is_file():continue
            ext=path.suffix.lower()
            details={}
            if ext=='.xlsx':
                with path.open('rb') as stream:
                    if stream.read(2)!=b'PK': raise ValueError(f'Invalid workbook container: {path.name}')
                check=openpyxl.load_workbook(path,read_only=True,data_only=True)
                try:
                    _,fields=header(check[FAC],'Region')
                    code='A' if 'Single-doctor private clinics' in fields else 'B' if 'Standalone clinics' in fields else None
                    if code is None or code in books:raise ValueError(f'Unknown or duplicate facility schema: {path.name}')
                finally:check.close()
                wb,details=workbook_audit(path,code,out)
                books[code]=wb
            elif ext=='.pdf':
                with path.open('rb') as stream:
                    if stream.read(5)!=b'%PDF-':raise ValueError(f'Invalid PDF signature: {path.name}')
                import pypdf
                first=pypdf.PdfReader(path).pages[0].extract_text() or ''
                code='blueprint' if 'EVIDENCE-LED' in first.upper() else 'guide'
                details=pdf_audit(path,out,code)
            elif path==contract:
                code='contract'; details=dict(format='UTF-8 text',description='User-adopted execution directive; pasted attachment originally named نص ملصق.txt.')
            else:raise ValueError(f'Unexpected source {path.name}')
            manifest['files'].append(dict(id=code,name=path.name,size=path.stat().st_size,sha256=digest(path),
                parsing_status='parsed',source_path=str(path.relative_to(project)).replace('\\','/'),issues=details.pop('issues',[]),**details))
        if set(books)!={'A','B'}:raise ValueError('Both workbook schemas are required.')
        rows,metrics,lineage,conflicts,competitors=canonical(books)
        if (out/'pages_guide.json').exists(): compare_guide(out,rows,lineage,conflicts)
        version=hashlib.sha256(''.join(sorted(f['sha256'] for f in manifest['files'] if f['id'] in books)).encode()).hexdigest()
        manifest['canonical_version']='regional-v1-'+version[:16]
        manifest['integrity']='passed'
        for filename,obj in [('regions',rows),('metrics',metrics),('lineage',lineage),('conflicts',conflicts),('competitors',competitors)]:
            save(out/(filename+'.json'),obj)
        sourced=[]
        for row in rows:
            item=row.copy()
            for key in ('complexes','hospitals','government_hospitals','private_hospitals','phcs','clinics',
                        'population','insured','share_pct','cumulative_pct','density','rank'):
                obs=lineage[row['id']+'.'+key]
                item[key+'_source_ref']=obs['source_ref']
                item[key+'_evidence']=obs['evidence_level']
                item[key+'_unit']=obs['unit']
            sourced.append(item)
        write_csv(out/'T01_regions.csv',sourced)
        write_csv(out/'T02_conflicts.csv',conflicts)
        write_csv(out/'lineage.csv',[dict(metric=k,**v) for k,v in lineage.items()])
        for p in out.iterdir():p.replace(processed/p.name)
        save(project/'data/source_manifest.json',manifest)
        for w in books.values():w.close()
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=ROOT)
    args=parser.parse_args()
    try:
        result=ingest(args.project)
        print('Reconciled 13 regions. Published',result['canonical_version'])
    except (ValueError,KeyError,StopIteration) as err:
        raise SystemExit(f'Integrity check failed. Previous processed data retained. {err}') from err

