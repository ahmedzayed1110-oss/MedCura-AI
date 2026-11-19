"use strict";
const $=(s,root=document)=>root.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num=(v,n=0)=>v==null?"Unavailable":Number(v).toLocaleString("en",{maximumFractionDigits:n});
const iconPaths={overview:"M3 3h7v7H3z M14 3h7v5h-7z M3 14h7v7H3z M14 12h7v9h-7z",market:"M3 19V9h4v10z M10 19V4h4v15z M17 19v-7h4v7z",audit:"M5 3h10l4 4v14H5z M8 10h8 M8 14h8 M8 18h5",stock:"M3 7l9-4 9 4v10l-9 4-9-4z M3 7l9 4 9-4 M12 11v10",ledger:"M4 5h16v14H4z M8 9h9 M8 12h9 M8 15h6",forecast:"M3 4v16h18 M5 16l5-7 4 4 6-8",decisions:"M5 4h14v17H5z M8 12l3 3 6-7",transfers:"M3 7h17l-4-4 M21 17H4l4 4",pilot:"M9 3h6 M10 3v7l-6 9q-1 2 2 2h12q3 0 2-2l-6-9V3 M8 15h8",economics:"M3 19h18 M5 16v-5 M10 16V8 M15 16v-5 M20 16V4",presentation:"M3 4h18v12H3z M12 16v5 M8 21l4-3 4 3",settings:"M4 7h16 M4 17h16 M8 4v6 M16 14v6",menu:"M3 5h18 M3 12h18 M3 19h18"};
const icon=n=>`<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linejoin="round" stroke-linecap="round"><path d="${iconPaths[n]||iconPaths.overview}"/></svg>`;
const brand=`<div class="brand"><svg aria-hidden="true" viewBox="0 0 40 40"><rect width="40" height="40" rx="7" fill="#c1e4c4"/><path d="M7 29V10l11 13L30 6v23h-5V20l-7 11-6-8v6z" fill="#13433e"/></svg><span>MedCura <em>AI</em></span></div>`;
const groups=[["Workspace",{overview:"Overview",market:"Saudi market",audit:"Source audit"}],["Branch operations",{stock:"Branches & stock",ledger:"Activity ledger",forecast:"Forecast studio",decisions:"Decision center",transfers:"Transfers & expiry"}],["Research & strategy",{pilot:"Pilot evaluation",economics:"Economics & strategy",presentation:"Presentation",settings:"Settings"}]];
const labels=Object.assign({},...groups.map(g=>g[1]));
const desc={overview:"Saudi market evidence and branch decisions at a glance.",market:"Compare Saudi administrative regions using the supplied facility and census tables.",audit:"Trace reported values to source cells and review conflicts between inputs.",stock:"Receive, issue and reconcile consumables in the simulated branch chain.",ledger:"Inspect dated physical and reservation movements by lot.",forecast:"Evaluate closed-day usage and inspect the assumptions behind a reorder.",decisions:"Review proposed quantities before creating local purchase orders.",transfers:"Review shelf life, recipient demand and every movement in transit.",pilot:"Define the prospective Riyadh field evaluation.",economics:"Explore hypothetical chain acquisition and branch economics.",presentation:"Explore the datathon narrative, figures and research report.",settings:"Inspect the signed-in account, clock and local API."};
const badge=(s,c="")=>`<span class="badge ${c}">${esc(s)}</span>`;
const table=(h,r)=>`<div class="table-wrap"><table><thead><tr>${h.map(v=>`<th scope="col">${esc(v)}</th>`).join("")}</tr></thead><tbody>${r.map(row=>`<tr>${row.map(v=>`<td>${v}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const fld=(name,input)=>`<label>${esc(name)}${input}</label>`;
const inp=(name,v="",type="text",extra="")=>`<input name="${name}" type="${type}" value="${esc(v)}" ${extra}>`;
const sel=(name,opts,v)=>`<select name="${name}">${opts.map(([k,title])=>`<option value="${esc(k)}" ${k===v?"selected":""}>${esc(title)}</option>`).join("")}</select>`;
const link=(path,text)=>`<a class="btn secondary" href="${esc(path)}">${esc(text)}</a>`;
const section=(title,content,tag="")=>`<section class="panel"><div class="pair"><h2>${esc(title)}</h2>${tag}</div>${content}</section>`;
const empty=t=>`<p class="empty">${esc(t)}</p>`;
const navbtn=(page,text)=>link("#"+page,text);
let user,state,metrics,regions,page,activeBranch="east",activeSku="gloves",serial=0;
const editable=()=>["owner","manager","storekeeper"].includes(user.role);
const approver=()=>["owner","manager"].includes(user.role);
const data=form=>Object.fromEntries(new FormData(form));
const branchOpts=()=>Object.entries(state.branches);
const skuOpts=()=>state.skus.map(s=>[s.id,s.name]);
const branchName=b=>state.branches[b]||({"north":"Riyadh North","east":"Riyadh East"}[b])||b;
function toast(msg){$("#toast").textContent=msg;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$("#toast").textContent="",5500)}
async function api(path,options={}){
 const headers={...options.headers};
 if(options.method==="POST"){headers["Content-Type"]="application/json";headers["Idempotency-Key"]=options.key||crypto.randomUUID()}
 const res=await fetch(path,{...options,headers});
 const val=await res.json();
 if(res.status===401 && user){user=null;login()}
 if(!res.ok)throw Error(val.error||`Request failed (${res.status})`);
 return val;
}
const post=(path,body)=>api(path,{method:"POST",body:JSON.stringify(body)});
function listen(root,event,selector,fn){
 const pending=new WeakSet();
 root.addEventListener(event,async e=>{
  const el=e.target.closest(selector);
  if(!el||!root.contains(el))return;
  if(event==="submit")e.preventDefault();
  if(pending.has(el))return;
  pending.add(el);
  try{await fn(el,e)}
  catch(err){toast(err.message);const out=root.querySelector(".form-error");if(out)out.textContent=err.message}
  finally{pending.delete(el)}
 });
}
function dialog(title,body){$("#dialog-title").textContent=title;$("#dialog-body").innerHTML=body;if(!$("#dialog").open)$("#dialog").showModal()}
function info(obj){return `<dl class="source">${Object.entries(obj).filter(([k,v])=>v!=null).map(([k,v])=>`<dt>${esc(k.replaceAll("_"," "))}</dt><dd>${esc(typeof v==="object"?JSON.stringify(v):v)}</dd>`).join("")}</dl>`}
function login(){
 $("#shell").innerHTML=`<div class="login"><section class="login-intro">${brand}<div><div class="eyebrow">Saudi private medical complexes</div><h1>From inventory records to explainable supply decisions.</h1><p>Inspect regional evidence, reconcile branch stock and review the reasons behind each proposed action.</p></div><footer>MedCura AI · Local research workspace</footer></section><main id="main" class="sign"><form><h2>Workspace sign-in</h2><p class="muted">Use the local account created by the launcher.</p>${fld("Username",inp("username","director","text",'required autocomplete="username"'))}${fld("Password",inp("password","","password",'required autocomplete="current-password"'))}<button>Sign in</button><p role="alert" class="form-error error"></p><p class="caption">For a one-time director session, start the app with <code>python run.py --open</code>.</p></form></main></div>`;
 listen($("#shell form"),"submit","form",async el=>{await post("/api/login",data(el));await start()});
}
async function start(){
 try{user=await api("/api/session")}catch{login();return}
 [metrics,regions]=await Promise.all([api("/api/market/metrics"),api("/api/market/regions")]);
 await route();
}
function shell(){
 const nav=groups.map(([name,items])=>`<div class="group-title">${name}</div>${Object.entries(items).map(([key,label])=>`<a class="nav ${key===page?"active":""}" ${key===page?'aria-current="page"':""} href="#${key}">${icon(key)}${label}</a>`).join("")}`).join("");
 $("#shell").innerHTML=`<div class="layout"><aside class="sidebar">${brand}<nav aria-label="Workspace">${nav}</nav><div class="userbox"><span class="avatar">${esc(user.name[0].toUpperCase())}</span><div>${esc(user.name)}<small>${esc(user.role)}</small></div><button id="logout" aria-label="Sign out">↪</button></div></aside><div class="workspace"><header class="top"><button class="menu quiet" aria-label="Toggle navigation">${icon("menu")}</button><span class="crumb">Workspace &nbsp; /</span><b>${esc(labels[page])}</b><span class="meta">Local workspace · Asia/Riyadh</span></header><main id="main" class="main"><div class="page-head"><div><h1>${esc(labels[page])}</h1><p>${esc(desc[page])}</p></div></div><div id="view" class="stack" aria-live="polite">Loading…</div></main></div></div>`;
 $(".menu").onclick=()=>$(".layout").classList.toggle("show-menu");
 $("#logout").onclick=async()=>{await post("/api/logout",{});user=null;login()};
}
async function route(){
 const seq=++serial;page=location.hash.slice(1);if(!labels[page])page="overview";shell();
 const root=$("#view");
 try{
 const st=await api("/api/state");if(seq!==serial)return;state=st;if(!state.branches[activeBranch])activeBranch=branchOpts()[0][0];
 if(["pilot","economics"].includes(page)){await window.renderStudy(page,root,api);return}
 await ({overview,market,audit,stock,ledger,forecast:forecastView,decisions,transfers,presentation,settings}[page])(root);
 }catch(e){root.innerHTML=`<p role="alert" class="panel error">${esc(e.message)}</p>`}
}
function bars(records,dark=false){
 const max=Math.max(...records.map(r=>r.complexes),1);const step=30,w=500,h=records.length*step+29;
 return `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img" aria-label="Private medical complexes by administrative region in 2024"><title>Private medical complexes, 2024</title>${records.map((r,i)=>`<g><title>${esc(r.source_ref)} · ${num(r.complexes)} locations</title><text x="0" y="${i*step+20}" font-size="14" fill="${dark?"#e2f0e6":"#213e3b"}">${esc(r.region)}</text><rect x="148" y="${i*step+8}" width="${Math.max(2,280*r.complexes/max)}" height="13" rx="2" fill="${dark?["#c4eabd","#8bc5ad","#68a993"][i%3]:i<3?"#267c70":"#a3c2b5"}"/><text x="493" y="${i*step+20}" text-anchor="end" font-size="14" fill="${dark?"#e2f0e6":"#213e3b"}">${num(r.complexes)}</text></g>`).join("")}<text x="148" y="${h-2}" fill="${dark?"#c3d8c8":"#50665c"}" font-size="12">Facility locations · 2024</text></svg>`
}
const row=(title,detail,end)=>`<div class="item"><div><strong>${esc(title)}</strong><small>${esc(detail)}</small></div>${end}</div>`;
function auditLink(root){listen(root,"click","[data-metric]",async el=>{const m=await api("/api/evidence/lineage/"+encodeURIComponent(el.dataset.metric));dialog("Evidence lineage",info(m))})}
async function overview(root){
 const scenarios=await api("/api/scenarios");
 root.innerHTML=`<section class="hero"><div class="left"><p class="eyebrow">Saudi market footprint · 2024</p><div class="big">${num(metrics.complexes.value)}</div><h2>Private medical complexes</h2><p class="caption">Workbook-derived total across ${regions.length} administrative regions.</p><button class="link" data-metric="complexes">Inspect source cells</button></div><div><p class="eyebrow">Largest regional footprints</p>${bars(regions.slice(0,3),true)}</div></section><div class="statrow">${[["Top-three share",num(metrics.top3_share.value,1)+"%","top3_share"],["Top-seven locations",num(metrics.top7.value),"top7"],["Private hospitals",num(metrics.private_hospitals.value),"private_hospitals"]].map(([t,v,k])=>`<div class="stat"><div><span>${t} · 2024</span><strong>${v}</strong></div><button class="link" data-metric="${k}">Lineage</button></div>`).join("")}</div><div class="grid">${section("Branch decision queue",state.queue.slice(0,3).map(q=>row(q.name,branchName(q.branch)+" · proposed order",`<b class="qty">${num(q.quantity)} units</b>`)).join("")+navbtn("decisions","Review decisions"),badge("Synthetic demo","demo"))}${section("Lot alerts",state.alerts.map(a=>row(a.kind,branchName(a.branch)+" · "+a.detail,badge(a.sku,"warn"))).join("")+navbtn("transfers","Review transfers"),badge("Synthetic demo","demo"))}</div><div class="grid">${section("Data integrity",`<p>${regions.length} distinct regions. Regional insurance estimates remain scenarios. Each featured total links to its source cells.</p><div class="actions">${navbtn("audit","Open source audit")}</div>`)}${section("Next pilot step",`<p>Register the Riyadh branch, SKU scope and baseline window before collecting observations.</p><div class="actions">${navbtn("pilot","Open pilot evaluation")}</div>`,badge("Not measured"))}</div>${section("Saved economic assumptions",`<p>${esc((scenarios.saved||scenarios.scenarios||[]).length)} saved scenarios in this workspace.</p>${navbtn("economics","View assumptions")}`,badge("Scenario"))}`;
 auditLink(root)
}
async function market(root){
 const fields=[
  ["rank","Rank"],["complexes","Private complexes"],["share_pct","National share (%)"],
  ["cumulative_pct","Cumulative share (%)"],["population","Residents (2022)"],["density","Complexes / 100k"],
  ["hospitals","All hospitals"],["government_hospitals","Government hospitals"],["private_hospitals","Private hospitals"],
  ["phcs","Government PHCs"],["clinics","Single-doctor clinics"]
 ];
 const rankOrder=[...regions].sort((a,b)=>a.rank-b.rank);
 const axisMax=Math.ceil(Math.max(...regions.map(r=>r.complexes))/200)*200;
 function pareto(matches){
  const width=840,height=280,left=55,right=778,top=37,bottom=219;
  const step=(right-left)/rankOrder.length;
  const x=i=>left+step*(i+.5);
  const y=v=>bottom-(bottom-top)*v;
  const axes=[0,.25,.5,.75,1].map(v=>
   `<path d="M${left} ${y(v)}H${right}" stroke="#d9e1d9"/><text x="${left-7}" y="${y(v)+4}" text-anchor="end">${num(axisMax*v)}</text><text x="${right+8}" y="${y(v)+4}" fill="#285b8e">${v*100}%</text>`).join("");
  const bars=rankOrder.map((r,i)=>{
   const active=matches.has(r.id),fill=active?(i<3?"#10685e":"#84a99d"):"#d9dfdc";
   return `<g><title>${esc(r.region)} · ${num(r.complexes)} facilities · cumulative ${num(r.cumulative_pct,1)}% · ${esc(r.source_ref)}</title><rect x="${x(i)-step*.29}" y="${y(r.complexes/axisMax)}" width="${step*.58}" height="${bottom-y(r.complexes/axisMax)}" fill="${fill}"/><text x="${x(i)}" y="${bottom+20}" text-anchor="middle">${r.rank}</text></g>`;
  }).join("");
  const line=rankOrder.map((r,i)=>`${x(i)},${y(r.cumulative_pct/100)}`).join(" ");
  const points=rankOrder.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.cumulative_pct/100)}" r="3.7" fill="#fff" stroke="#285b8e" stroke-width="2"><title>${esc(r.region)} · ${num(r.cumulative_pct,1)}% cumulative</title></circle>`).join("");
  return `<div class="table-wrap"><svg id="market-pareto" class="chart" style="min-width:570px" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="pareto-title pareto-description" font-size="13" fill="#29443f"><title id="pareto-title">National private medical complex Pareto, 2024</title><desc id="pareto-description">Bars give locations by descending regional rank. The line is the cumulative percentage of all ${num(metrics.complexes.value)} locations.</desc><text x="${left}" y="19">Facilities</text><text x="${right}" y="19" text-anchor="end" fill="#285b8e">Cumulative share</text>${axes}${bars}<polyline points="${line}" fill="none" stroke="#285b8e" stroke-width="2.7"/>${points}<text x="${(left+right)/2}" y="268" text-anchor="middle">Administrative region rank · 2024</text></svg></div>`;
 }
 root.innerHTML=`<div class="tools">${fld("Filter region",inp("search","","search",'id="market-filter" placeholder="All 13 regions"'))}${fld("Order",sel("sort",[["rank","National rank"],["region","Region name"],...fields.slice(1)],"rank"))}${fld("Direction",sel("direction",[["default","Default order"],["reverse","Reverse order"]],"default"))}${link("/assets/data/processed/T01_regions.csv","Download sourced CSV")}</div><div id="market-content" class="stack"></div>`;
 function render(){
  const query=$("[name=search]",root).value.toLowerCase().trim(),key=$("[name=sort]",root).value;
  const direction=$("[name=direction]",root).value==="reverse"?-1:1;
  const subset=regions.filter(r=>r.region.toLowerCase().includes(query)).sort((a,b)=>{
   if(key==="region")return direction*a.region.localeCompare(b.region,"en");
   const delta=key==="rank"?a.rank-b.rank:b[key]-a[key];
   return direction*delta||a.region.localeCompare(b.region,"en");
  });
  const display=(r,k)=>`<button class="link" data-inspect-metric="${esc(r.id+"."+k)}" aria-label="${esc(r.region+" "+(fields.find(f=>f[0]===k)?.[1]||k)+" source")}">${num(r[k],["density","share_pct","cumulative_pct"].includes(k)?2:0)}</button>`;
  const tableRows=subset.map(r=>[`<strong>${esc(r.region)}</strong>`,...fields.map(([k])=>display(r,k))]);
  const shares=rankOrder.filter(r=>[3,7].includes(r.rank)).map(r=>`Rank ${r.rank} · ${num(r.cumulative_pct,1)}%`).join(" &nbsp; / &nbsp; ");
  $("#market-content",root).innerHTML=section("Regional concentration",pareto(new Set(subset.map(r=>r.id)))+
   `<p class="caption">Teal bars show the number of facilities. The blue line uses the national total. ${shares}. Filtering highlights matching bars.</p><div class="actions">${link("/assets/figures/F02.svg","Export SVG")}${link("/assets/figures/F02.png","Export PNG")}</div>`,badge("Derived · 2024"))+
   section("Regional evidence",`<p class="caption">Showing ${subset.length} of ${regions.length} regions. Select a number to inspect its inputs.</p>`+
    (subset.length?table(["Administrative region",...fields.map(f=>f[1])],tableRows):empty("No regions match this search."))+
    `<details><summary>Definitions, reference periods and source coverage</summary><p>Facilities are 2024 locations. Residents come from the 2022 Census. Density is private complexes per 100,000 census residents. National and cumulative shares use the full Saudi facility count even when the table is filtered.</p><p>Makkah is the administrative region. The clinic column counts the single-doctor category. Each facility class has its own definition and purchasing accounts require separate evidence.</p>${link("/assets/docs/SOURCE_REGISTER.md","Source register")}</details>`,badge("Workbook observations & derived values"));
 }
 root.oninput=render;render();
 listen(root,"click","[data-inspect-metric]",async el=>{
  const key=el.dataset.inspectMetric;
  const record=await api("/api/evidence/lineage/"+encodeURIComponent(key));
  const refs=[...new Set(record.source_ref.split(/, | \/ /))];
  const sourceButtons=refs.map(r=>`<button class="link" data-locate="${esc(r)}">${esc(r)}</button>`).join(" · ");
  const {source_ref, ...metadata}=record;
  dialog("Evidence lineage",`<h3>${esc(key)}</h3>${info(metadata)}<p class="caption">Workbook cells</p><div>${sourceButtons}</div>`);
  $("#dialog-body").onclick=e=>{
   const target=e.target.closest("[data-locate]");if(!target)return;
   sessionStorage.setItem("marketAuditCell",target.dataset.locate);$("#dialog").close();location.hash="audit";
  };
 });
}

async function audit(root){
 const [sources,conflicts,lineage,competitors,aCells,bCells]=await Promise.all([
  "/api/sources","/api/evidence/conflicts","/api/evidence/lineage","/api/competitors",
  "/assets/data/processed/cells_A.json","/assets/data/processed/cells_B.json"].map(path=>api(path)));
 const books={A:aCells,B:bCells};
 const indexed=new Map([...aCells,...bCells].map(c=>[c.source_ref,c]));
 const pages={raw:0,conf:0,lin:0,comp:0};
 const observedInsured=Object.entries(lineage).filter(([id])=>id.endsWith(".insured"));
 const missing=observedInsured.filter(([,r])=>r.value==null).length;
 const comparablePrices=competitors.filter(c=>c.price_sar==null).length;
 function sourceLink(text){
  if(!text)return "";
  const urls=String(text).match(/https?:\/\/[^\s|]+/g)||[];
  return [...new Set(urls)].map(u=>`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(new URL(u).hostname)}</a>`).join(" · ");
 }
 function locateButton(ref){
  return indexed.has(ref)?`<button class="link" data-source-cell="${esc(ref)}">${esc(ref)}</button>`:esc(ref);
 }
 function refs(text){
  return [...new Set(String(text||"").split(/, | \/ /))].map(locateButton).join(" · ");
 }
 function pager(key){
  return `<div class="pager"><button class="quiet" id="${key}-previous" data-list="${key}" data-step="-1" aria-label="Previous ${key} page">Previous</button><span id="${key}-range"></span><button class="quiet" id="${key}-next" data-list="${key}" data-step="1" aria-label="Next ${key} page">Next</button></div>`;
 }
 function drawPage(key,items,renderer,size=8){
  const last=Math.max(0,Math.ceil(items.length/size)-1);
  pages[key]=Math.min(Math.max(pages[key],0),last);
  const start=pages[key]*size;
  $("#"+key+"-rows",root).innerHTML=items.length?renderer(items.slice(start,start+size)):empty("No matching records.");
  $("#"+key+"-range",root).textContent=items.length?`${start+1}–${Math.min(start+size,items.length)} of ${items.length}`:"0 records";
  $("#"+key+"-previous",root).disabled=pages[key]===0;$("#"+key+"-next",root).disabled=pages[key]===last;
 }
 function sheetTable(f){
  return f.sheets?.length?table(["Worksheet","Used range","Header row","Blank cells¹","Formulas","URL cells"],
   f.sheets.map(s=>[esc(s.name),esc(s.populated_range),num(s.header_row),num(s.blank_cells_in_dimensions),num(s.formula_count),num(s.url_cells)]))+
   `<p class="caption">¹ Counts all unused cells inside the sheet dimensions, including layout spacing.</p>`:"";
 }
 const registry=sources.files.map(f=>`<details><summary>${esc(f.id)} · ${esc(f.name)}</summary>${info({sha256:f.sha256,bytes:f.size,
  parsing_status:f.parsing_status,format:f.format,pages:f.pages,extracted_utc:sources.extracted_utc,issues:f.issues?.join(" ")})}${sheetTable(f)}</details>`).join("");
 const check=section("Coverage and missing observations",table(["Measure","Available","Interpretation"],[
  ["Private complexes, 2024",`${regions.filter(r=>r.complexes!=null).length} / ${regions.length} regions`,"Both workbooks agree on regional facility counts."],
  ["Dated regional insured counts",`${observedInsured.length-missing} / ${observedInsured.length} regions`,"A gives an undated Riyadh claim. B distributes a national total using weights."],
  ["Comparable healthcare-specific prices",`${competitors.length-comparablePrices} / ${competitors.length} source listings`,"Raw commercial wording is retained for review."]
 ]),badge("Source audit"));
 const rawPanel=section("Workbook cell explorer",`<div class="tools">${fld("Workbook",sel("book",[["A","A · completed dataset"],["B","B · second workbook"]],"A"))}${fld("Worksheet",'<select name="sheet" id="audit-sheet"></select>')}${fld("Cell or value",inp("cellSearch","","search",'id="audit-cell-search" placeholder="F5 or reported value"'))}</div><div id="raw-rows"></div>${pager("raw")}`);
 const confPanel=section("Conflicting inputs",`<div class="tools">${fld("Filter conflict evidence",sel("ev",[["","All evidence"],...[...new Set(conflicts.map(c=>c.evidence_level))].map(v=>[v,v])],""))}${fld("Search conflict",inp("conflictSearch","","search",'placeholder="Region, source or issue"'))}${link("/assets/data/processed/T02_conflicts.csv","Export sourced conflicts")}</div><div id="conf-rows"></div>${pager("conf")}`);
 const linPanel=section("Metric lineage",`<div class="tools">${fld("Find a metric",inp("find","","search",'placeholder="e.g. riyadh.population"'))}${fld("Metric evidence",sel("label",[["","All evidence"],...[...new Set(Object.values(lineage).map(v=>v.evidence_level))].map(v=>[v,v])],""))}${link("/assets/data/processed/lineage.csv","Export lineage")}</div><div id="lin-rows"></div>${pager("lin")}`);
 const compPanel=section("Competitor observations",`<div class="tools">${fld("Search vendors",inp("vendor","","search",'placeholder="Name or market segment"'))}</div><div id="comp-rows"></div>${pager("comp")}`);
 root.innerHTML=check+rawPanel+confPanel+linPanel+compPanel+section("Source register",registry);
 function val(name){return $(`[name="${name}"]`,root).value}
 function sheets(book,sheet){
  const list=[...new Set(books[book].map(c=>c.sheet))];
  $("[name=sheet]",root).innerHTML=list.map(s=>`<option value="${esc(s)}" ${s===(sheet||"01 Facilities")?"selected":""}>${esc(s)}</option>`).join("");
 }
 function drawRaw(){
  const book=val("book"),sheet=val("sheet"),q=val("cellSearch").trim().toLowerCase();
  const address=/^[a-z]{1,3}[1-9]\d*$/.test(q);
  const found=books[book].filter(c=>c.sheet===sheet&&(address?c.cell.toLowerCase()===q:
   [c.cell,c.value,c.formula].some(v=>String(v??"").toLowerCase().includes(q))));
  drawPage("raw",found,entries=>table(["Cell","Raw value / cached result","Formula","Source URL"],entries.map(c=>[
   `<button class="link" data-inspect-cell="${esc(c.source_ref)}">${esc(c.cell)}</button>`,esc(c.value??"Unavailable"),esc(c.formula||"—"),sourceLink(c.urls.join(" "))||"—"])));
 }
 function drawConf(){
  const query=val("conflictSearch").trim().toLowerCase(),filter=val("ev");
  const list=conflicts.filter(c=>(!filter||c.evidence_level===filter)&&[c.topic,c.source_a,c.source_b,c.decision].some(v=>v.toLowerCase().includes(query)));
  drawPage("conf",list,entries=>entries.map(c=>`<details><summary>${esc(c.topic)} · ${esc(c.evidence_level)}</summary>${table(["Source locator","Recorded value"],[[locateButton(c.source_a),esc(c.value_a??"Unavailable")],[locateButton(c.source_b),esc(c.value_b??"Unavailable")]])}<p>${esc(c.decision)}</p><p class="caption">Reference period · ${esc(c.reference_year)}</p></details>`).join(""));
 }
 function drawLineage(){
  const q=val("find").trim().toLowerCase(),filter=val("label");
  const list=Object.entries(lineage).filter(([k,v])=>(!filter||v.evidence_level===filter)&&(k.includes(q)||v.source_ref.toLowerCase().includes(q)));
  drawPage("lin",list,entries=>entries.map(([k,v])=>`<details><summary>${esc(k)} · ${esc(v.value??"Unavailable")} ${esc(v.unit)}</summary>${info({evidence_level:v.evidence_level,reference_year:v.reference_year??"Undated",notes:v.notes,calculation:v.calculation_id,numerator:v.numerator,denominator:v.denominator,reported_value:v.reported_value})}<p>${refs(v.source_ref)}</p><p>${sourceLink(v.citation_url)}</p></details>`).join(""));
 }
 function drawCompetitors(){
  const q=val("vendor").toLowerCase().trim();
  drawPage("comp",competitors.filter(c=>[c.name,c.segment].some(v=>String(v).toLowerCase().includes(q))),entries=>
   table(["Source listing","Attributed capability","Evidence and verification","Comparable price","Workbook"],entries.map(c=>[
    `<strong>${esc(c.name)}</strong><br>${sourceLink(c.citation_url)}`,esc(c.product),badge(c.evidence_level)+`<br><small>${esc(c.verification_status)}</small>`,
    `Unavailable<details><summary>Source wording</summary>${esc(c.reported_price)}</details>`,locateButton(c.source_ref)])));
 }
 const draws={raw:drawRaw,conf:drawConf,lin:drawLineage,comp:drawCompetitors};
 function showCell(ref,scroll){
  const c=indexed.get(ref);if(!c)return;
  $("[name=book]",root).value=c.book;sheets(c.book,c.sheet);$("[name=cellSearch]",root).value=c.cell;pages.raw=0;drawRaw();
  if(scroll){$("#audit-cell-search",root).focus({preventScroll:true});$("#audit-cell-search",root).scrollIntoView({block:"center"})}
 }
 function cellDetail(ref){
  const c=indexed.get(ref);
  const other=indexed.get((c.book==="A"?"B":"A")+" · "+c.sheet+"!"+c.cell);
  const rawValue=r=>r?esc(r.value??"Missing cached value"):"Blank or outside used range";
  dialog("Workbook cell comparison",`<h3>${esc(c.sheet)} · ${esc(c.cell)}</h3>${table(["Workbook","Value","Formula","Linked source"],[c,other].map((r,i)=>[
   r?esc(r.book):esc(i===0?c.book:(c.book==="A"?"B":"A")),rawValue(r),esc(r?.formula||"—"),sourceLink(r?.urls?.join(" "))||"—"]))}<p class="caption">Values at the same address can describe different entities or periods. Check the headers and the conflict decisions before combining values.</p>`);
 }
 listen(root,"click","[data-list]",el=>{const key=el.dataset.list;pages[key]+=Number(el.dataset.step);draws[key]()});
 listen(root,"click","[data-source-cell]",el=>showCell(el.dataset.sourceCell,true));
 listen(root,"click","[data-inspect-cell]",el=>cellDetail(el.dataset.inspectCell));
 const changed=(name,key)=>{const el=$("[name="+name+"]",root);el.addEventListener(el.tagName==="SELECT"?"change":"input",()=>{
  if(name==="book"){sheets(val("book"));$("[name=cellSearch]",root).value=""}
  if(name==="sheet")$("[name=cellSearch]",root).value="";
  pages[key]=0;draws[key]();
 })};
 for(const n of ["book","sheet","cellSearch"])changed(n,"raw");
 for(const n of ["ev","conflictSearch"])changed(n,"conf");
 for(const n of ["find","label"])changed(n,"lin");
 changed("vendor","comp");
 sheets("A");Object.values(draws).forEach(draw=>draw());
 const target=sessionStorage.getItem("marketAuditCell");if(target){sessionStorage.removeItem("marketAuditCell");showCell(target,true)}
}


const stockTable=lots=>table(["Branch","SKU / lot","Expiry","Physical","Reserved","Available","Base unit"],lots.map(x=>[esc(branchName(x.branch)),`<b>${esc(x.name)}</b><br><small>${esc(x.code)}${x.quarantine?" · Quarantine":""}</small>`,esc(x.expiry||"Not applicable"),num(x.physical),num(x.reserved),num(x.available),esc(x.unit)]));
async function stock(root){
 root.innerHTML=`<div class="tools">${fld("Branch",sel("branchFilter",[["","All assigned branches"],...branchOpts()],""))}${badge("Synthetic demo · "+state.day,"demo")}</div>`+section("Stock by lot",`<div id="stock-table"></div>`)+(editable()?section("Record a movement",`<form id="scan-form" class="tools">${fld("Scan SKU or lot code",inp("scan","","text",'autocomplete="off" maxlength="80" placeholder="Keyboard scanner or typed code"'))}<button class="quiet">Apply scan</button></form><form id="move"><div class="fields">${fld("Action",sel("kind",["receive","issue","return","reserve","unreserve",...(approver()?["adjust","count"]:[])].map(x=>[x,x.charAt(0).toUpperCase()+x.slice(1)]),"receive"))}${fld("Branch",sel("branch",branchOpts(),activeBranch))}${fld("SKU",sel("sku",skuOpts(),activeSku))}<span id="lot-inputs" style="display:contents"></span>${fld("Quantity",inp("qty",1,"number",'required step="1"'))}${fld("Unit",sel("unit",[["base","Base units"],["pack","Packs"]],"base"))}${fld("Reason",inp("reason","","text",'required maxlength="180" placeholder="Reason for movement"'))}</div><div class="actions"><button>Record movement</button></div></form>`):"")+(approver()?section("SKU catalog",`<details><summary>Create or edit a SKU</summary><form id="catalog"><div class="fields">${fld("SKU code",inp("id","","text","required"))}${fld("Name",inp("name","","text","required"))}${fld("Base unit",inp("unit","piece","text","required"))}${fld("Units per pack",inp("pack",10,"number","min=1 required"))}${fld("Cost per base unit (halalas)",inp("cost_minor",100,"number","min=0 required"))}${fld("Expiry tracking",sel("expiry",[["yes","Applicable"],["no","Not applicable"]],"yes"))}</div><div class="actions"><button>Save SKU</button></div></form></details>`):"");
 function refresh(){const val=$("[name=branchFilter]",root).value;$("#stock-table").innerHTML=stockTable(state.stock.filter(b=>!val||val===b.branch))}
 refresh();$("[name=branchFilter]",root).onchange=refresh;
 const form=$("#move");if(form){function fields(){const {sku,branch,kind}=data(form),s=state.skus.find(x=>x.id===sku);
 $("#lot-inputs").innerHTML=["receive","return"].includes(kind)?fld("Lot code",inp("code","","text",'required placeholder="Batch identifier"'))+(s.expiry?fld("Expiry date",inp("expiry","","date","required")):"")+fld("Disposition",sel("disposition",kind==="return"?[["quarantine","Quarantine pending review"]]:[["usable","Usable"],["quarantine","Quarantine"]],"usable")):fld("Lot",sel("lot",[...(["issue","reserve"].includes(kind)?[["","Automatic FEFO"]]:[]),...state.stock.filter(b=>b.branch===branch&&b.sku===sku).map(b=>[b.id,b.code+" · "+b.available+" available"])],""))}
 fields();
 listen($("#scan-form"),"submit","form",async el=>{
   const code=data(el).scan.trim();
   if(!code)throw Error("Scan a SKU or lot code.");
   const selected=state.skus.find(s=>s.id===code),branch=form.elements.branch.value;
   const matches=state.stock.filter(l=>l.branch===branch&&l.code===code);
   if(!selected&&matches.length!==1)throw Error(matches.length?"Lot code matches multiple SKUs. Select the SKU and lot manually.":"No matching SKU or lot at this branch.");
   const lot=selected?null:matches[0];form.elements.sku.value=selected?selected.id:lot.sku;fields();
   if(lot){if(form.elements.lot)form.elements.lot.value=lot.id;if(form.elements.code)form.elements.code.value=lot.code;if(form.elements.expiry)form.elements.expiry.value=lot.expiry||""}
   form.elements.qty.focus();toast("Scan applied. Review quantity and record the movement.");
 });
 form.onchange=e=>{if(["kind","branch","sku"].includes(e.target.name))fields()};listen(form,"submit","form",async el=>{const p=data(el);p.qty=Number(p.qty);p.quarantine=p.disposition==="quarantine";const result=await post("/api/inventory/"+p.kind,p);activeBranch=p.branch;activeSku=p.sku;toast(`Recorded ${p.kind} · ${result.units} base units`);await route()})}
 const catalog=$("#catalog");if(catalog)listen(catalog,"submit","form",async el=>{const p=data(el);p.pack=+p.pack;p.cost_minor=+p.cost_minor;p.expiry=p.expiry==="yes";await post("/api/skus",p);toast("Saved SKU "+p.id);await route()});
}
async function ledger(root){
 const entries=await api("/api/ledger");let index=0;
 root.innerHTML=section("Immutable movements",`<div class="tools">${fld("Filter transactions",inp("q","","search",'placeholder="Branch, lot, reason or actor"'))}${link("/api/exports/ledger.csv","Export ledger")}</div><div id="events"></div><div class="pager"><button class="quiet" id="prev">Previous</button><span id="range"></span><button class="quiet" id="next">Next</button></div>`,badge("Synthetic demo","demo"));
 function draw(){const q=$("[name=q]",root).value.toLowerCase(),list=entries.filter(x=>[x.branch,x.sku,x.code,x.actor,x.reason,x.kind].some(v=>v.toLowerCase().includes(q)));
 const start=index*20;$("#events").innerHTML=list.length?table(["Business date","Branch","SKU / lot","Movement","Physical Δ","Held Δ","Actor / reason"],list.slice(start,start+20).map(x=>[esc(x.day),esc(branchName(x.branch)),esc(x.sku+" / "+x.code),esc(x.kind),x.delta,x.held,esc(x.actor)+"<br><small>"+esc(x.reason)+"</small>"])):empty("No matching movements.");$("#range").textContent=list.length?`${start+1}–${Math.min(start+20,list.length)} of ${list.length}`:"0 records";$("#prev").disabled=!index;$("#next").disabled=start+20>=list.length}
 root.oninput=()=>{index=0;draw()};$("#prev").onclick=()=>{index--;draw()};$("#next").onclick=()=>{index++;draw()};draw()
}
function plot(fc){
 const values=fc.history.slice(-28),w=650,h=160,pad=28,obs=values.map(x=>x.qty),f=fc.future.slice(0,30),all=[...obs,...f];if(!all.length)return empty("No closed demand days.");
 const max=Math.max(1,...all),x=i=>pad+(w-pad-8)*i/(all.length-1||1),y=q=>h-25-(h-47)*q/max;
 const path=(a,off)=>a.map((v,i)=>`${i?"L":"M"}${x(off+i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
 return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Historical issued units and projected daily demand"><title>Daily usage and projected units</title><path d="M${pad} 12V${h-25}H${w-5}" fill="none" stroke="#a3b5aa"/><text x="0" y="25" font-size="12">${num(max)}</text><text x="6" y="${h-23}" font-size="12">0</text><path d="${path(obs,0)}" fill="none" stroke="#126f65" stroke-width="2.7"/><path d="${path([obs.at(-1),...f],obs.length-1)}" fill="none" stroke="#356cb1" stroke-width="2.7" stroke-dasharray="6 3"/><text x="${pad}" y="${h-4}" font-size="12">${values[0]?.date||""}</text><text x="${w-8}" y="${h-4}" text-anchor="end" font-size="12">Forecast · ${f.length} days shown</text></svg>`
}
async function forecastView(root){
 const d=await api(`/api/decisions/reorder?branch=${activeBranch}&sku=${encodeURIComponent(activeSku)}`),fc=d.forecast,r=d.reorder,p=d.policy;
 root.innerHTML=`<div class="tools">${fld("Branch",sel("branch",branchOpts(),activeBranch))}${fld("SKU",sel("sku",skuOpts(),activeSku))}${badge("Synthetic demo","demo")}</div>`+section("Issued units and forecast",plot(fc)+`<p class="caption">Solid teal = closed daily issues. Dashed blue = projected units. ${fc.coverage} consecutive closed days through ${esc(fc.cutoff)}. Model: ${esc(fc.chosen||"manual review")}.</p>`)+`<div class="grid">${section("Reorder calculation",info({available_to_promise:d.atp,confirmed_orders:d.orders,scheduled_transfers:d.incoming,inventory_position:r.position,lead_time_demand:r.lead_demand,safety_buffer:r.safety,reorder_point:r.point,target_units:r.target,proposed_units:r.quantity,arrival:d.eta})+`<p>${esc(r.reason)}</p>${navbtn("decisions","Review orders")}`)}${section("Policy assumptions",`<form id="policy"><div class="fields">${Object.entries({lead:"Lead time (days)",review:"Review interval (days)",service:"Buffer quantile (%)",moq:"Minimum order (units)",capacity:"Capacity (units)"}).map(([k,t])=>fld(t,inp(k,p[k],"number","required"))).join("")}</div><p class="caption">The buffer uses positive one-day holdout errors scaled by lead time. Shortage probability is unavailable.</p>${approver()?'<div class="actions"><button>Save policy</button></div>':""}</form>`)}</div>`+section("Rolling-origin evaluation",fc.chosen?table(["Baseline","MAE (units)","WAPE","sMAPE","Bias (units)","Shortage units"],fc.scores.map(v=>[esc(v.model),num(v.mae,3),v.wape==null?"Unavailable":num(100*v.wape,2)+"%",num(v.smape*100,2)+"%",num(v.bias,3),num(v.shortage_units,2)]))+`<p class="caption">Selection ends ${esc(fc.selection_end)}. Seven later origins start ${esc(fc.holdout_start)}. ${esc(fc.reason)} Run ${esc(d.run)}.</p><details><summary>Prediction versus actual</summary>${table(["Origin target day","Prediction","Simulated actual"],fc.points.map(v=>[v.date,num(v.prediction,2),v.actual]))}</details>`:empty(fc.reason),badge("Simulation"));
 root.insertAdjacentHTML("beforeend",section("Simulation test bench",`<p>A fixed-order policy and a rolling-demand policy face the same 14 simulated days. The comparison reports unmet units and unit-days held. Changes in delay, returns, scan coverage and shelf life are evaluated separately.</p><div class="actions">${approver()?'<button id="backtest">Save current backtest run</button>':""}${link("/assets/data/demo/stress.json","Stress results")}${link("/assets/data/demo/T05.csv","Baseline results CSV")}</div>`,badge("Synthetic demo","demo")));
 listen(root,"click","#backtest",async()=>{const saved=await post("/api/forecast/backtest",{branch:activeBranch,sku:activeSku});toast("Saved forecast run "+saved.run)});
 for(const key of ["branch","sku"])$(`[name=${key}]`,root).onchange=e=>{if(key==="sku")activeSku=e.target.value;else activeBranch=e.target.value;route()};
 if(approver())listen($("#policy"),"submit","form",async el=>{const params=Object.fromEntries(Object.entries(data(el)).map(([k,v])=>[k,+v]));await post("/api/policy",{branch:activeBranch,sku:activeSku,...params});toast("Policy saved and decision recalculated");await route()});
}
async function decisions(root){
 root.innerHTML=section("Order review",state.queue.length?state.queue.map((q,i)=>row(q.name,`${branchName(q.branch)} · position ${q.position} ≤ reorder point ${q.point} · target ${q.target} · pack ${q.pack}`,`<div class="actions"><b>${q.quantity} units</b>${approver()?`<button data-order="${i}">Approve order</button>`:""}</div>`)).join(""):empty("No orders currently meet the policy threshold."),badge("Synthetic demo","demo"))+section("Local purchase orders",state.orders.length?table(["Branch","SKU","Units","Expected receipt","Approver","Status","Action"],state.orders.map(o=>[esc(branchName(o.branch)),esc(o.sku),o.qty,esc(o.eta),esc(o.approver),esc(o.status),o.status==="confirmed"&&editable()?`<button data-po="${esc(o.id)}">Receive order</button>`:"—"])):empty("Approved orders will appear here."))+`<p class="caption">Approval adds confirmed incoming units to inventory position. Physical stock changes when a receipt is recorded.</p>`;
 listen(root,"click","[data-order]",async el=>{const q=state.queue[+el.dataset.order];await post("/api/decisions/reorder",{branch:q.branch,sku:q.sku,run:q.run});toast("Order approved locally");await route()});
 listen(root,"click","[data-po]",async el=>{const o=state.orders.find(o=>o.id===el.dataset.po);dialog("Receive approved order",`<form id="po-form"><p>${esc(o.qty)} units · ${esc(o.sku)}</p><div class="fields">${fld("Lot code",inp("code","","text","required"))}${state.skus.find(s=>s.id===o.sku).expiry?fld("Expiry",inp("expiry","","date","required")):""}</div><div class="actions"><button>Confirm receipt</button></div><p class="form-error error"></p></form>`);listen($("#po-form"),"submit","form",async f=>{await post("/api/orders/receive",{...data(f),id:o.id});$("#dialog").close();toast("Receipt posted to stock");await route()})})
}
async function transfers(root){
 const actionMap={DRAFT:["request","cancel"],REQUESTED:["approve","reject","cancel"],APPROVED:["dispatch","cancel"],DISPATCHED:["receive"]};
 function actions(t){return (actionMap[t.status]||[]).filter(a=>editable()&&(approver()||!["approve","reject"].includes(a))&&(!user.branch||user.branch===(a==="receive"?t.destination:t.branch))).map(a=>`<button data-step="${a}" data-id="${esc(t.id)}" class="${["reject","cancel"].includes(a)?"quiet":""}">${a[0].toUpperCase()+a.slice(1)}</button>`).join(" ")}
 root.innerHTML=section("Expiry watch",state.alerts.length?state.alerts.map(a=>row(a.detail,branchName(a.branch)+" · "+a.sku,badge("Review","warn"))).join(""):empty("No near-expiry lots."),badge("Synthetic demo","demo"))+section("Transfer candidates",state.candidates.length?state.candidates.map((c,i)=>`<div class="item"><div><h3>${esc(c.code)} · ${esc(c.sku)}</h3><p>${esc(branchName(c.source_branch))} to ${esc(branchName(c.destination))}</p><small>Origin exposure ${c.origin_excess} units · recipient need ${c.destination_deficit} · remaining life ${c.life_days} days</small><small>Up to ${c.limit} units · estimated net SAR ${num(c.net_minor/100,2)} at maximum quantity, including SAR 12 transport.</small></div>${editable()?`<button data-draft="${i}">Draft transfer</button>`:""}</div>`).join(""):empty("No inter-branch movement meets current demand, shelf-life and value gates."))+section("Transfer register",state.transfers.length?table(["Lot","Route","Units","State","Approver","Next step"],state.transfers.map(t=>[esc(t.code),esc(branchName(t.branch)+" → "+branchName(t.destination)),t.qty,badge(t.status),esc(t.approver||"Pending"),actions(t)||"—"])):empty("Drafts, reservations, in-transit stock and completed receipts will appear here."));
 listen(root,"click","[data-draft]",async el=>{const c=state.candidates[+el.dataset.draft];dialog("Draft transfer",`<p>${esc(c.code)} · ${esc(branchName(c.source_branch))} to ${esc(branchName(c.destination))}</p><form id="draft-form"><div class="fields">${fld("Base units",inp("qty",Math.min(25,c.limit),"number",`min=1 max=${c.limit} required`))}${fld("Transit days",inp("days",1,"number","min=1 max=30 required"))}${fld("All-in freight (SAR)",inp("freight",12,"number",'min=0 step=".01" required'))}</div><p class="caption">Two extra days of remaining shelf life are required. Origin safety stock and destination consumption are rechecked at dispatch.</p><div class="actions"><button>Create draft</button></div><p class="form-error error"></p></form>`);listen($("#draft-form"),"submit","form",async f=>{const v=data(f);await post("/api/transfers",{action:"draft",lot:c.lot,destination:c.destination,qty:+v.qty,days:+v.days,freight:Math.round(+v.freight*100)});$("#dialog").close();toast("Transfer drafted");await route()})});
 listen(root,"click","[data-step]",async el=>{await post("/api/transfers",{action:el.dataset.step,id:el.dataset.id});toast("Transfer updated");await route()})
}
async function presentation(root){
 const [slides,cat]=await Promise.all([api("/api/presentation"),api("/assets/figures/catalog.json")]);let idx=0;
 root.innerHTML=`<div class="actions">${link("/assets/presentation/MedCura_AI_Datathon.pptx","Download deck")}${link("/assets/presentation/MedCura_AI_Research_Report.pdf","Research report")}${link("/assets/docs/JUDGE_QA.md","Judge Q&A")}</div><section class="panel"><div class="story-nav">${slides.map((s,i)=>`<button class="quiet" aria-label="Slide ${i+1}" data-slide="${i}">${i+1}</button>`).join("")}</div><div id="slide"></div></section>`+section("Figure library",cat.map(c=>row(c.title,c.caption,`<div class="actions">${link("/assets/figures/"+c.svg,"SVG")}${link("/assets/figures/"+c.png,"PNG")}</div>`)).join(""));
 function draw(){const s=slides[idx];$("#slide").innerHTML=`<p class="eyebrow">Slide ${idx+1} of ${slides.length}</p><h2>${esc(s.title)}</h2><p>${esc(s.body)}</p>${(s.items||[]).map(v=>`<p>${esc(typeof v==="object"?Object.values(v).join(" · "):v)}</p>`).join("")}<p class="caption">${esc(s.notes)}</p>${badge(s.evidence_level)}`;root.querySelectorAll("[data-slide]").forEach(b=>b.className=+b.dataset.slide===idx?"":"quiet")}
 listen(root,"click","[data-slide]",el=>{idx=+el.dataset.slide;draw()});draw()
}
async function settings(root){
 root.innerHTML=section("Workspace settings",info({account:user.name,role:user.role,tenant:user.tenant,branch:user.branch||"Assigned chain",timezone:"Asia/Riyadh (UTC+03:00)",simulation_date:state.day,location:"Main storeroom per branch",session_lifetime:"8 hours"})+link("/openapi.json","OpenAPI contract"))+section("Access and evidence",`<p>Role and branch scope are assigned by the local server. Ledger movements are append-only. Opening stock, issues and transfer opportunities in this workspace are simulated.</p>`);
 if(["owner","auditor"].includes(user.role)){const log=await api("/api/audit");root.innerHTML+=section("Mutation audit",log.length?table(["Time in Riyadh","Actor","API action","Details"],log.map(r=>[esc(new Date(r.stamp).toLocaleString("en-GB",{timeZone:"Asia/Riyadh"})),esc(r.actor),esc(r.path),esc(r.detail)])):empty("No user mutations recorded."))}
}
$("#close-dialog").onclick=()=>$("#dialog").close();
window.addEventListener("hashchange",()=>{if(user)route()});
(async()=>{try{if(location.hash.startsWith("#ticket=")){const ticket=location.hash.slice(8);history.replaceState(null,"",location.pathname);await post("/api/login",{ticket})}await start()}catch(e){login();toast(e.message)}})();
