"""Attach the new figure series to copies of the original report and speaker notes."""
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from pypdf import PdfReader,PdfWriter

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"results/figures"
OUT=ROOT/"reports"

def main():
    OUT.mkdir(exist_ok=True)
    writer=PdfWriter()
    writer.append(ROOT/"presentation/MedCura_AI_Research_Report.pdf")
    for figure in ("F01","F02","F06","F07","F11","F12"):
        writer.append(ASSETS/(figure+".pdf"), outline_item=f"Publication appendix {figure}")
    target=OUT/"MedCura_AI_Research_Report_with_Appendix.pdf"
    with target.open("wb") as stream:
        writer.write(stream)
    assert len(PdfReader(target).pages)==11
    notes={3:"Release provenance: results/tables/T02.csv and results/figures/F04.svg.",
           4:"Matplotlib data figures: results/figures/F01.svg, F02.svg and F03.svg. See T01 and T03 for provenance.",
           7:"Release pilot design: results/figures/F12.svg and results/tables/T07.csv. Field outcomes remain unmeasured.",
           8:"Release roadmap and scenario sensitivity: results/figures/F10.svg and F11.svg; T06 and T08."}
    original=ROOT/"presentation/MedCura_AI_Datathon.pptx"
    out=ROOT/"presentation/MedCura_AI_Datathon_Research_Edition.pptx"
    with ZipFile(original) as source,ZipFile(out,"w") as revised:
        for item in source.infolist():
            contents=source.read(item)
            for i,note in notes.items():
                if item.filename==f"ppt/notesSlides/notesSlide{i}.xml":
                    import re
                    pattern=rb'(<(?:\w+:)?t(?:\s[^>]*)?>)([^<]+)(</(?:\w+:)?t>)'
                    matches=list(re.finditer(pattern,contents))
                    comment=matches[0]
                    contents=contents[:comment.end(2)]+(" "+note).encode()+contents[comment.end(2):]
                    assert note in "".join(ET.fromstring(contents).itertext())
            revised.writestr(item,contents)
    with ZipFile(original) as source,ZipFile(out) as revised:
        assert revised.testzip() is None
        slides=[x for x in source.namelist() if x.startswith("ppt/slides/slide") and x.endswith(".xml")]
        assert len(slides)==10 and all(source.read(x)==revised.read(x) for x in slides)

if __name__=="__main__":
    main()
