"""Validate exported evidence independently against the OOXML source archives."""
import csv
import hashlib
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/processed'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
spec=importlib.util.spec_from_file_location('source_ingest',ROOT/'scripts/ingest.py')
ingest=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)

def read(file):
    return json.loads(file.read_text(encoding='utf-8'))

def direct_cells(file,sheet):
    """Independent source read; do not reuse the ETL parser or snapshot JSON."""
    with ZipFile(file) as archive:
        book=ET.fromstring(archive.read('xl/workbook.xml'))
        rid=next(s for s in book.findall('.//s:sheet',NS) if s.attrib['name']==sheet).attrib['{'+NS['r']+'}id']
        relations=ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        path=next(r.attrib['Target'] for r in relations if r.attrib['Id']==rid)
        if path.startswith('/'):path=path.lstrip('/')
        else:path='xl/'+path
        sheetxml=ET.fromstring(archive.read(path))
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings=[''.join(t.itertext()) for t in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        result={}
        for c in sheetxml.findall('.//s:c',NS):
            value=c.findtext('s:v',namespaces=NS)
            if c.get('t')=='s':value=strings[int(value)]
            if c.get('t')=='inlineStr':value=''.join(c.itertext())
            result[c.get('r')]=value
        return result

class MarketEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read(ROOT/'data/source_manifest.json')
        cls.rows=read(DATA/'regions.json')
        cls.metrics=read(DATA/'metrics.json')
        cls.lineage=read(DATA/'lineage.json')
        cls.sources={x['id']:x for x in cls.manifest['files']}
        cls.conflicts=read(DATA/'conflicts.json')

    def test_hashes_and_document_extraction(self):
        if not (ROOT/'data/raw').is_dir():
            self.skipTest('Authorized raw inputs are required for source extraction verification')
        for source in self.sources.values():
            raw=ROOT/source['source_path']
            self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),source['sha256'])
        self.assertEqual([self.sources[b]['pages'] for b in ['guide','blueprint']],[6,17])
        self.assertTrue(all(p['text'] for id_ in ('guide','blueprint') for p in read(DATA/self.sources[id_]['extraction'])))

    def test_regions_and_years_against_both_original_workbooks(self):
        if not (ROOT/'data/raw').is_dir():
            self.skipTest('Authorized raw workbooks are required for direct cell comparison')
        self.assertEqual(len(self.rows),13)
        self.assertEqual({r['region'] for r in self.rows},ingest.REGIONS)
        for source in ('A','B'):
            file=ROOT/self.sources[source]['source_path']
            fac=direct_cells(file,ingest.FAC)
            pop=direct_cells(file,ingest.POP)
            rows={r['region']:r for r in self.rows}
            for n in range(5,18):
                row=rows[fac['A'+str(n)]]
                for col,field in [('B','hospitals'),('C','government_hospitals'),('D','private_hospitals'),('E','phcs'),('F','complexes'),('H','reference_year')]:
                    self.assertEqual(row[field],int(fac[f'{col}{n}']))
            for n in range(2,15):
                row=rows[pop['A'+str(n)]]
                self.assertEqual(row['population'],int(pop[f'B{n}']))
                self.assertEqual(row['population_year'],int(pop[f'C{n}']))

    def test_canonical_sums_pareto_and_density(self):
        counts=[r['complexes'] for r in self.rows]
        self.assertEqual(counts,sorted(counts,reverse=True))
        self.assertEqual((sum(counts),sum(counts[:3]),sum(counts[:7])),(3607,2527,3238))
        self.assertEqual([round(100*sum(counts[:n])/sum(counts),1) for n in (3,7)],[70.1,89.8])
        self.assertEqual(sum(r['population'] for r in self.rows),32175224)
        self.assertEqual(sum(r['private_hospitals'] for r in self.rows),166)
        for i,row in enumerate(self.rows,1):
            self.assertAlmostEqual(row['cumulative_pct'],100*sum(counts[:i])/sum(counts))
            self.assertAlmostEqual(row['density'],100000*row['complexes']/row['population'])
        self.assertEqual(self.rows[-1]['cumulative_pct'],100)

    def test_lineage_points_to_snapshot_cells_and_preserves_units(self):
        cells={c['source_ref'] for k in ('A','B') for c in read(DATA/f'cells_{k}.json')}
        for obs in self.lineage.values():
            self.assertTrue({'value','evidence_level','reference_year','source_ref','unit','notes','calculation_id'}<=set(obs))
            for point in re.split(', | / ',obs['source_ref']):
                self.assertIn(point,cells)
        self.assertEqual(self.lineage['riyadh.density']['denominator'],8591748)
        self.assertEqual(self.metrics['top3_share']['denominator'],sum(r['complexes'] for r in self.rows))

    def test_regional_allocation_and_missing_observations(self):
        for row in self.rows:
            self.assertIsNone(row['insured'])
            self.assertEqual(self.lineage[row['id']+'.insured']['evidence_level'],'UNKNOWN')
            self.assertEqual(self.lineage[row['id']+'.allocated_insured']['evidence_level'],'SCENARIO')
        self.assertEqual(self.lineage['riyadh.insured']['reported_value'],9700000)
        self.assertEqual(self.metrics['insured_q1_2026']['value'],14500000)
        self.assertEqual(self.lineage['insured_2024']['value'],13000000)
        self.assertEqual(self.lineage['insured_2024']['reference_year'],2024)
        self.assertEqual(self.lineage['al-baha.private_hospitals']['value'],0)

    def test_period_definition_and_pdf_conflicts(self):
        keyed={c['topic']:c for c in self.conflicts}
        self.assertEqual(keyed['Madinah guide discrepancy']['value_b'],9)
        self.assertEqual(keyed['Jazan guide discrepancy']['value_a'],3)
        self.assertEqual(keyed['Clinic definition']['value_a'],56)
        self.assertEqual(self.lineage['riyadh.growth_A']['reference_year'],'2021–2022')
        self.assertEqual(self.lineage['riyadh.growth_B']['reference_year'],'2010–2022')
        self.assertEqual(keyed['Riyadh physicians']['evidence_level'],'SCENARIO')

    def test_competitor_price_and_no_deployments_as_facts(self):
        competitors=read(DATA/'competitors.json')
        self.assertEqual(len(competitors),24)
        self.assertTrue(all(row['price_sar'] is None for row in competitors))
        self.assertTrue(all(row['evidence_level'] in ('VENDOR_CLAIM','UNKNOWN') for row in competitors))
        self.assertIn('700',next(r['reported_price'] for r in competitors if r['name'].startswith('Stokvera')))

    def test_renamed_duplicate_and_missing_region_rejected(self):
        class Sheet(list):
            title='Test regions'
        def parse(names):
            title=SimpleNamespace(row=1,column=1,value='Region')
            sheet=Sheet([[title]]+[[SimpleNamespace(row=i,column=1,value=n,coordinate='A'+str(i))]
                                        for i,n in enumerate(names,2)])
            return ingest.region_rows(sheet)[0]
        names=sorted(ingest.REGIONS)
        self.assertEqual(set(parse(names)),ingest.REGIONS)
        for invalid in (names[:-1],names+[names[0]],['Makkah City']+names[1:]):
            with self.assertRaises(ValueError):parse(invalid)

    def test_blank_and_fractional_counts_rejected(self):
        for val in [None,'N/A','',3.5,-2,True]:
            cell=SimpleNamespace(value=val,coordinate='F5',parent=SimpleNamespace(title='Facilities'))
            with self.assertRaises(ValueError):ingest.whole(cell)

    def test_csv_export_and_source_comparator(self):
        with (DATA/'T01_regions.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),13)
        self.assertEqual(rows[0]['density_unit'],'complexes per 100,000 residents')
        self.assertEqual(rows[0]['density_evidence'],'DERIVED')
        self.assertEqual(rows[0]['insured'],'')
        audit_time=self.manifest['extracted_utc']
        self.assertTrue(audit_time.endswith('+00:00'))
        self.assertEqual(self.manifest['integrity'],'passed')

if __name__=='__main__':
    unittest.main()
