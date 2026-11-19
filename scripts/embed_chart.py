"""Attach editable category/value ranges to the deck's single literal chart."""
import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as ET
from openpyxl import Workbook
C="{http://schemas.openxmlformats.org/drawingml/2006/chart}"
R="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P="{http://schemas.openxmlformats.org/package/2006/relationships}"
T="{http://schemas.openxmlformats.org/package/2006/content-types}"

def update(src,dest):
    with ZipFile(src) as deck:
        parts={n:deck.read(n) for n in deck.namelist()}
    chartname=next(n for n in parts if n.endswith("/charts/chart1.xml"))
    chart=ET.fromstring(parts[chartname])
    if chart.find(C+"externalData") is not None:
        raise ValueError("This chart already has a workbook.")
    series=chart.find(".//"+C+"ser")
    categories=series.find(C+"cat")
    numbers=series.find(C+"val")
    labels=[x.text for x in categories.findall(".//"+C+"v")]
    values=[int(x.text) for x in numbers.findall(".//"+C+"v")]
    wb=Workbook(); sheet=wb.active;sheet.title="Regional footprint"
    sheet.append(["Region","Complexes"])
    for name,count in zip(labels,values,strict=True):sheet.append([name,count])
    stream=BytesIO();wb.save(stream)
    for node,typ,col in [(categories,"str","A"),(numbers,"num","B")]:
        literal=node[0];node.remove(literal)
        ref=ET.SubElement(node,C+typ+"Ref")
        ET.SubElement(ref,C+"f").text=f"'Regional footprint'!${col}$2:${col}${len(labels)+1}"
        literal.tag=C+typ+"Cache";ref.append(literal)
    data=ET.SubElement(chart,C+"externalData",{R+"id":"rIdWorkbook"})
    ET.SubElement(data,C+"autoUpdate",val="0")
    rels=ET.Element(P+"Relationships",nsmap={None:P[1:-1]})
    import posixpath
    book="ppt/embeddings/facilities.xlsx"
    ET.SubElement(rels,P+"Relationship",Id="rIdWorkbook",Type=R[1:-1]+"/package",Target=posixpath.relpath(book,posixpath.dirname(chartname)))
    ct=ET.fromstring(parts["[Content_Types].xml"])
    if not any(r.get("Extension")=="xlsx" for r in ct):
        ET.SubElement(ct,T+"Default",Extension="xlsx",ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    parts[book]=stream.getvalue()
    relpath=posixpath.join(posixpath.dirname(chartname),"_rels",posixpath.basename(chartname)+".rels")
    for key,xml in [(chartname,chart),(relpath,rels),("[Content_Types].xml",ct)]:
        parts[key]=ET.tostring(xml,encoding="UTF-8",xml_declaration=True)
    with ZipFile(dest,"w",ZIP_DEFLATED) as deck:
        for name,body in parts.items():deck.writestr(name,body)

if __name__=="__main__":
    cli=argparse.ArgumentParser();cli.add_argument("input",type=Path);cli.add_argument("output",type=Path)
    args=cli.parse_args()
    if args.input.resolve()==args.output.resolve():cli.error("Supply a distinct output file.")
    update(args.input,args.output)

