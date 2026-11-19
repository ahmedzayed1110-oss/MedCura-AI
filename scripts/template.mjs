import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL, fileURLToPath } from "node:url";
import os from "node:os";
const nodeRoot = path.resolve(path.dirname(process.execPath), "..", "node_modules");
const fromBundle = createRequire(path.join(nodeRoot, "resolve.cjs"));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(fromBundle.resolve("@oai/artifact-tool")).href);
const outDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../data/templates");
const scratch = await fs.mkdtemp(path.join(os.tmpdir(),"medcura-template-"));
const header = (await fs.readFile(path.join(outDir, "pilot_observations.csv"), "utf8")).trimEnd().split(",");
const workbook = Workbook.create();
const observations = workbook.worksheets.add("Observations");
const guide = workbook.worksheets.add("Field guide");
const row = observations.getRange("A1:W1");
row.values = [header];
row.format = {fill:"#0E3F3C",font:{name:"Aptos",bold:true,size:11,color:"#FFFFFF"},rowHeight:28};
observations.getRange("A1:W30").format.columnWidth = 22;
observations.getRange("L1:L30").format.columnWidth = 29;
observations.getRange("A2:C1201").setNumberFormat("@");
observations.getRange("D2:D1201").setNumberFormat("yyyy-mm-dd");
observations.freezePanes.freezeRows(1);
guide.getRange("A1:B1").merge();
guide.getRange("A1").values=[["MedCura AI   /   Pilot observation template"]];
guide.getRange("A1:B1").format={fill:"#0E3F3C",font:{name:"Aptos",bold:true,color:"#FFFFFF",size:16},rowHeight:36};
const guideRows=[
  ["Scope","Record one row per registered branch, SKU and Riyadh calendar day. Aggregate lots within each SKU-day."],
  ["Identifiers","Use approved local codes. Leave lot blank if multiple lots contribute. Exclude patient and staff identifiers."],
  ["Quantities","Enter whole base units. issued and received are daily flows. on_hand is the end-of-day physical snapshot."],
  ["Stockouts","Enter total hours and new episode starts. Count a continuing episode once across days. Maximum 24 hours/day."],
  ["Costs","Use actual weighted disposal unit cost in SAR. Count opening inventory value once, then only new receipts in tracked_value_added_sar."],
  ["Counting","Keep the count scope fixed. Allocate shared staff hours once across standardized SKU sessions."],
  ["Event counts","Supply numerator and denominator together. A numerator cannot exceed the matching denominator."],
  ["Forecast","Use the frozen estimate from before the day began. Blank means unavailable."],
  ["Missing values","Leave unknown numerical fields blank. Enter 0 only for an observed zero."],
  ["Upload","Save the Observations sheet as UTF-8 CSV with the unchanged header. Limit each file to 180 KB and 1,200 rows."],
  ["Evidence status","Validation in training writes no measured outcomes. A custodian-approved field tenant is required for actual imports."]
];
guide.getRange("A3:B13").values=guideRows;
guide.getRange("A3:A13").format={fill:"#E3F0EB",font:{name:"Aptos",bold:true,size:11,color:"#0E3F3C"}};
guide.getRange("B3:B13").format={font:{name:"Aptos",size:11,color:"#10263E"},wrapText:true,verticalAlignment:"center"};
guide.getRange("A1:A13").format.columnWidth=22;
guide.getRange("B1:B13").format.columnWidth=90;
guide.getRange("A3:B13").format.rowHeight=42;
workbook.recalculate();
if(observations.getRange("A1:W1").values[0].join(",")!==header.join(",")){throw new Error("Header mismatch");}
for(const [name,range,file] of [["Observations","A1:J4","headers"],["Field guide","A1:B13","guide"]]){
  const preview=await workbook.render({sheetName:name,range,scale:1,format:"png"});
  await fs.writeFile(path.join(scratch,file+".png"),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(workbook)).save(path.join(outDir,"pilot_observations.xlsx"));
