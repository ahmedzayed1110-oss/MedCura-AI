/**
 * Build an editable deck from the verified presentation story and source data.
 * Requires @oai/artifact-tool. Pass the path to the package entry using
 * ARTIFACT_TOOL_ENTRY if the package is outside standard module resolution.
 * The optional second argument selects a private rendering/build directory.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const build = process.argv[3] || await fs.mkdtemp(path.join(os.tmpdir(), 'medcura-slides-'));
await fs.mkdir(build, { recursive: true });
const { Presentation, PresentationFile } = await import(process.env.ARTIFACT_TOOL_ENTRY ?
  pathToFileURL(process.env.ARTIFACT_TOOL_ENTRY).href : '@oai/artifact-tool');
const pres = Presentation.create({slideSize:{width:1280,height:720}});
const story = JSON.parse(await fs.readFile(path.join(root,'presentation/story.json'),'utf8'));
const regions = JSON.parse(await fs.readFile(path.join(root,'data/processed/regions.json'),'utf8'));
const total = regions.reduce((a,r)=>a+r.complexes,0);
const fmt = n=>n.toLocaleString('en-US');
const C = {paper:'#F7F7F1',ink:'#10263E',teal:'#006E71',dim:'#405B68',soft:'#D8E6E2',
  dark:'#0E3F3C',bright:'#A7E2C9',white:'#FFFFFF',pale:'#D1E6DF',blue:'#356CB1'};
const hidden = {fill:'none',width:0};
const sans='Segoe UI', serif='Georgia';
const pos=(left,top,width,height)=>({left,top,width,height});
function rect(s,x,y,w,h,fill) {
  s.shapes.add({geometry:'rect',position:pos(x,y,w,h),fill,line:hidden});
}
function txt(s,text,x,y,w,h,size,options={}) {
  const sh=s.shapes.add({geometry:'textbox',name:options.name || text.slice(0,50),
    position:pos(x,y,w,h),fill:'none',line:hidden});
  sh.text=text;
  sh.text.style={typeface:options.serif?serif:sans,fontSize:size,color:options.color||C.ink,
    bold:options.bold||false,wrap:'wrap',verticalAlignment:'top',
    insets:{top:0,bottom:0,left:0,right:0},alignment:options.align||'left'};
  return sh;
}
function chrome(s,rec,dark=false) {
  s.background.fill=dark?C.dark:C.paper;
  const color=dark?C.pale:C.dim;
  txt(s,'MEDCURA AI',66,34,240,26,18,{bold:true,color:dark?C.bright:C.teal});
  txt(s,rec.section.toUpperCase(),365,34,600,26,16,{color,align:'center'});
  txt(s,rec.number.toString().padStart(2,'0')+' / 10',1090,34,125,26,16,{color,align:'right'});
  rect(s,66,72,1149,1,dark?'#54807B':'#B9CAC7');
  rect(s,66,653,1149,1,dark?'#54807B':'#B9CAC7');
  txt(s,rec.evidence_level.replaceAll('_',' '),66,671,255,21,14,{bold:true,color:dark?C.bright:C.teal});
  const src = rec.number===4?'Workbook A, 01 Facilities!A5:H18. Administrative regions, 2024.':
    rec.number===3?'Workbooks A and B, 03 Insurance by Region and 04 Insurance National.':
    rec.number===5?'Synthetic branch transactions. Pilot outcomes have yet to be measured.':
    rec.number===8?'2024 workbook footprint. Expansion requires pilot evidence and partner agreement.':
    'Datathon presentation guide, slide '+rec.number+'. Source details in speaker notes.';
  txt(s,src,337,670,878,26,14,{color,align:'right'});
  s.speakerNotes.text=rec.notes+'\n\nSources: '+rec.source_ref+'\nRelated export: figures/'+rec.figure+'.svg';
}
function title(s,t,dark=false) {
  txt(s,t,66,103,1140,108,t.length>61?43:49,{serif:true,color:dark?C.white:C.ink});
}
function cols(s,rec,y,colors={}) {
  const gap=35, col=(1149-gap*(rec.items.length-1))/rec.items.length;
  rec.items.forEach((it,i)=>{
    const x=66+i*(col+gap);
    rect(s,x,y,col,5,colors.rule||C.teal);
    txt(s,it.label,x,y+23,col,62,27,{bold:true,color:colors.head||C.ink});
    txt(s,it.text,x,y+95,col,195,25,{color:colors.body||C.dim});
  });
}
function lines(s,rec,y=305) {
  rec.items.forEach((it,i)=>{
    const yy=y+101*i;
    rect(s,66,yy,1149,1,'#BECFCA');
    txt(s,it.label,67,yy+18,275,75,25,{bold:true,color:C.teal});
    txt(s,it.text,364,yy+16,847,78,26);
  });
}
for(const rec of story) {
  const s=pres.slides.add();
  const dark=[1,7,10].includes(rec.number);
  chrome(s,rec,dark);
  if(rec.number===1) {
    txt(s,'MedCura AI',65,123,1090,104,85,{serif:true,color:C.white});
    txt(s,rec.title,69,235,1010,130,47,{color:C.bright});
    txt(s,rec.body,69,414,1075,106,31,{color:C.white});
    txt(s,'Proposed field study    /    One Riyadh branch    /    Non-pharmaceutical consumables',69,582,1139,40,21,{color:C.pale});
  } else if(rec.number===4) {
    title(s,rec.title);
    txt(s,rec.body,66,225,1070,72,24,{color:C.dim});
    const best=regions.slice(0,3);
    s.charts.add('bar',{title:'Private medical complexes, 2024',titleTextStyle:{typeface:sans,fontSize:19,color:C.ink,bold:true},
      position:pos(69,319,761,292),categories:best.map(r=>r.region),
      series:[{name:'Complexes',values:best.map(r=>r.complexes),fill:C.teal}],
      barOptions:{direction:'column',grouping:'clustered',gapWidth:100},hasLegend:false,chartFill:C.paper,plotAreaFill:C.paper,
      xAxis:{textStyle:{typeface:sans,fontSize:16,color:C.dim}},yAxis:{minimumScale:0,numberFormatCode:'#,##0',majorGridlines:{fill:'#D6DFDA',width:1},textStyle:{typeface:sans,fontSize:14,color:C.dim}},
      dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:sans,fontSize:16,bold:true,color:C.ink}}});
    rect(s,866,329,2,258,C.soft);
    txt(s,fmt(total),900,363,315,84,59,{serif:true,color:C.teal});
    txt(s,'private complexes nationally across 13 administrative regions',902,451,302,130,26);
  } else if(rec.number===10) {
    title(s,rec.title,true);
    txt(s,rec.body,68,221,1115,101,31,{color:C.pale});
    cols(s,rec,362,{rule:C.bright,head:C.white,body:C.pale});
  } else if(rec.number===7) {
    title(s,rec.title,true);
    txt(s,rec.body,68,230,1100,73,27,{color:C.pale});
    cols(s,rec,350,{rule:C.bright,head:C.white,body:C.pale});
  } else if([2,3,6].includes(rec.number)) {
    // An editorial opening at left, followed by two short working definitions.
    txt(s,rec.title,66,119,660,255,55,{serif:true});
    txt(s,rec.body,68,402,636,185,27,{color:C.dim});
    rect(s,751,122,2,470,C.soft);
    rec.items.forEach((it,i)=>{
      const y=138+226*i;
      txt(s,it.label,796,y,411,54,26,{bold:true,color:C.teal});
      txt(s,it.text,796,y+60,410,152,25);
    });
  } else {
    title(s,rec.title);
    txt(s,rec.body,68,221,1130,85,25,{color:C.dim});
    if(rec.number===8)cols(s,rec,343);
    else lines(s,rec,321);
  }
}
for(const [i,s] of pres.slides.items.entries()) {
  const b=await pres.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(build,'slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await b.arrayBuffer()));
}
const target=process.argv[2] || path.join(root,'presentation','MedCura_AI_Datathon.pptx');
await (await PresentationFile.exportPptx(pres)).save(target);
console.log('Exported '+pres.slides.items.length+' slides to '+target);

