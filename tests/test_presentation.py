"""Delivery checks on actual exported assets. Uses standard library only."""
import json
import re
import struct
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]


class PresentationAssets(unittest.TestCase):
    def test_complete_paired_figures(self):
        records=json.loads((ROOT/'figures/catalog.json').read_text(encoding='utf-8'))
        self.assertEqual([row['id'] for row in records],[f'F{i:02d}' for i in range(1,12)])
        for row in records:
            with self.subTest(row=row['id']):
                svg=ET.parse(ROOT/'figures'/row['svg']).getroot()
                self.assertEqual(svg.attrib['role'],'img')
                self.assertIn(row['title'],''.join(svg.itertext()))
                png=(ROOT/'figures'/row['png']).read_bytes()
                self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
                self.assertGreaterEqual(struct.unpack('>I',png[16:20])[0],1080)
        self.assertEqual(records[-1]['evidence_level'],'SYNTHETIC_DEMO')
        self.assertIn('NOT VALIDATED ON CLINIC DATA',records[-1]['title'])

    def test_deck_source_and_notes(self):
        story=json.loads((ROOT/'presentation/story.json').read_text(encoding='utf-8'))
        self.assertEqual(len(story),10)
        with ZipFile(ROOT/'presentation/MedCura_AI_Datathon.pptx') as deck:
            self.assertIsNone(deck.testzip())
            slides=[p for p in deck.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',p)]
            self.assertEqual(len(slides),10)
            for row in story:
                part=f"ppt/notesSlides/notesSlide{row['number']}.xml"
                self.assertIn(row['source_ref'],''.join(ET.fromstring(deck.read(part)).itertext()))
            chartparts=[p for p in deck.namelist() if re.search(r'/charts/chart\d+\.xml$',p)]
            self.assertEqual(len(chartparts),1)
            chart=''.join(ET.fromstring(deck.read(chartparts[0])).itertext())
            observations=json.loads((ROOT/'data/processed/regions.json').read_text(encoding='utf-8'))
            for row in observations[:3]:
                self.assertIn(row['region'],chart)
                self.assertIn(str(row['complexes']),chart)
            self.assertTrue(any(p.startswith('ppt/embeddings/') and p.endswith('.xlsx') for p in deck.namelist()))

    def test_report_has_five_pages(self):
        body=(ROOT/'presentation/MedCura_AI_Research_Report.pdf').read_bytes()
        self.assertTrue(body.startswith(b'%PDF'))
        self.assertIn(b'%%EOF',body)
        self.assertEqual(len(re.findall(rb'/Type\s*/Page\b',body)),5)


if __name__=='__main__':
    unittest.main()

