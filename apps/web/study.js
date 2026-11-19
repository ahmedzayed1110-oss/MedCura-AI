/* Research workspaces share the authenticated host API and shell. */
(() => {
  "use strict";
  const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => (
    {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]
  ));
  const fmt = value => value == null ? "Unavailable" : Number(value).toLocaleString("en", {maximumFractionDigits: 2});
  const post = (api, path, body) => api(path, {method: "POST", body: JSON.stringify(body)});
  const tag = text => '<span class="badge">' + esc(text) + '</span>';
  const field = (title, input) => '<label class="study-field"><span>' + esc(title) + '</span>' + input + '</label>';
  const textInput = (name, value, type = "text", attrs = "") =>
    '<input type="' + type + '" name="' + name + '" value="' + esc(value) + '" ' + attrs + ' required>';
  const table = (labels, rows) => '<div class="table-wrap"><table><thead><tr>' +
    labels.map(s => '<th scope="col">' + esc(s) + '</th>').join("") +
    '</tr></thead><tbody>' + rows.map(row => '<tr>' + row.map(x => '<td>' + esc(x) + '</td>').join("") + '</tr>').join("") + '</tbody></table></div>';
  const style = `<style>
  .study-space{display:grid;gap:1.25rem}.study-space h2,.study-space h3,.study-space p{margin:.2rem 0 .7rem}
  .study-intro,.study-actions,.study-presets{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap}
  .study-space .panel{padding:clamp(1rem,2.4vw,2rem)}
  .study-tiles,.study-fields,.study-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,195px),1fr));gap:1rem}
  .study-tiles{border-block:1px solid #cbd6d0;padding:1rem 0;margin:1rem 0}.study-tiles small,.study-field span{display:block;color:#36534d}
  .study-tiles strong{display:block;color:#0e3f3c;font-size:clamp(1.5rem,3vw,2.3rem);font-variant-numeric:tabular-nums}
  .study-field{display:grid;align-content:end;gap:.35rem;font-size:.9rem}.study-field input,.study-field select{width:100%;box-sizing:border-box}
  .study-space details>summary{cursor:pointer;font-weight:650;padding:.65rem 0}.study-fields{margin:1rem 0}.study-steps article{border-left:3px solid #007f86;padding:0 .85rem}
  .study-steps article strong{font-size:1.2rem}.study-status{color:#0e3f3c;min-height:1.4em;margin:.4rem 0}.study-status[role=alert]{color:#8e2b1b}
  .study-chart{margin:1rem 0}.study-bar{display:grid;grid-template-columns:7rem 1fr minmax(5rem,auto);gap:.7rem;align-items:center;margin:.55rem 0}
  .study-bar i{display:block;background:#007f86;height:.7rem}.study-space fieldset{border:1px solid #cbd6d0;padding:.8rem;margin:.8rem 0}
  .study-space fieldset label,.study-check{display:inline-flex;align-items:center;gap:.4rem;margin:.25rem .7rem .25rem 0}
  .study-check input,.study-space fieldset input{width:auto}.study-status:empty{display:none}.study-space .btn{display:inline-block}
  .study-space .study-filename{max-width:100%}.study-space summary:focus-visible,.study-space button:focus-visible,.study-space input:focus-visible{outline:3px solid #356cb1;outline-offset:2px}
  @media(max-width:540px){.study-bar{grid-template-columns:5.5rem 1fr auto}.study-actions .btn{min-height:2.75rem}.study-space .panel{padding:.85rem}}
  </style>`;
  function feedback(node, text, error = false) {
    node.setAttribute("role", error ? "alert" : "status");
    node.textContent = text;
  }
  function busy(form, active) {
    form.querySelectorAll("button").forEach(btn => { btn.disabled = active; });
  }
  const financeRows = [
    ["Reached chains","reachable"],["Qualified chains","qualified"],["Completed pilots","pilots"],["New contracts","new_contracts"],
    ["Retained contracts","retained"],["Churned contracts","churned"],["Closing contracts","contracts"],["Paying branches","paying_branches"],
    ["Billable branch-months","branch_months"],["Exit MRR · SAR","mrr"],["Exit ARR · SAR","arr"],["Recognized revenue · SAR","revenue"],
    ["COGS · SAR","cogs"],["Gross profit · SAR","gross_profit"],["Gross margin · %","gross_margin_pct"],
    ["Acquisition expense · SAR","acquisition"],["Operating result · SAR","operating_result"],["Recurring break-even · branches","break_even_branches"]
  ];
  function projection(years) {
    const last = years[years.length - 1];
    return '<div class="study-tiles">' + [["2029 paying branches",fmt(last.paying_branches)],["2029 exit ARR",fmt(last.arr) + " SAR"],
      ["2029 operating result",fmt(last.operating_result) + " SAR"]].map(([label,n]) =>
      '<div><small>'+label+'</small><strong>'+n+'</strong></div>').join("") + '</div>' +
      table(["Model output",...years.map(y => y.year)], financeRows.map(([label,key]) => [label,...years.map(y => fmt(y[key]))]));
  }
  async function economics(root, api) {
    const data = await api("/api/scenarios");
    const presets = Object.keys(data.presets);
    root.innerHTML = style + '<div class="study-space"><section class="panel"><div class="study-intro">' + tag("SCENARIO") +
      '<h2>Chain economics</h2></div><p>Set the number of distinct chains the team can reach. Subscription revenue begins when a pilot converts to a paying contract.</p>' +
      '<form class="study-fin"><div class="study-fields">'+ field("Starting assumptions",'<select name="preset">'+presets.map(p=>'<option '+(p==="Base"?"selected":"")+'>'+esc(p)+'</option>').join("")+
      data.saved.map((s,i)=>'<option value="saved-'+i+'">Saved · '+esc(s.name)+'</option>').join("")+'</select>') +
      field("Scenario name",textInput("name","Base projection","text",'maxlength="48"'))+'</div><details><summary>Edit funnel, fees and costs</summary><div class="study-fields">' +
      data.drivers.map(([k,label,unit,min,max])=>field(label + " · " + unit,textInput(k,data.presets.Base[k],"number",'min="'+min+'" max="'+max+'" step="'+(["accounts","branches"].includes(unit)?"1":"0.0001")+'"'))).join("")+
      '</div></details><div class="study-actions"><button class="btn" type="submit" value="preview">Calculate projection</button><button class="btn" type="submit" value="save">Save scenario</button></div></form>' +
      '<p class="study-status" role="status"></p><div class="study-result">'+projection(data.comparison.Base)+'</div></section>' +
      '<section class="panel"><h3>2029 sensitivity</h3><p>Exit ARR by starting case, in SAR. Each case changes reach, conversion, pricing and costs together.</p><div class="study-chart">' +
      presets.map(p=>{const arr=data.comparison[p][2].arr;const max=Math.max(...presets.map(k=>data.comparison[k][2].arr),1);return '<div class="study-bar"><span>'+esc(p)+'</span><i style="width:'+(arr/max*100)+'%"></i><strong>'+fmt(arr)+'</strong></div>';}).join("")+
      '</div></section><section class="panel"><h3>Expansion gates</h3><div class="study-steps">'+data.gates.map((g,i)=>'<article><strong>'+(2027+i)+'</strong><p>'+esc(g)+'</p></article>').join("")+
      '</div></section><details class="panel"><summary>Calculation notes</summary><p>Each year models a fresh pool of reachable chains. Funnel stages round down to whole accounts. Opening contracts churn at the start of each year. New contracts contribute six months of revenue. Exit MRR uses closing paid branches and ARR annualizes that MRR. Recurring break-even divides fixed monthly expense by per-branch contribution and rounds up. It excludes onboarding and acquisition. The number of serviceable chains remains unknown.</p></details></div>';
    const form = root.querySelector(".study-fin"), status = root.querySelector(".study-status"), result = root.querySelector(".study-result");
    const markDirty = () => feedback(status,"Assumptions changed. Calculate to update the projection.");
    form.addEventListener("input",markDirty);
    form.elements.preset.onchange = () => {
      const key=form.elements.preset.value, saved=key.startsWith("saved-") ? data.saved[Number(key.slice(6))] : null;
      const vals=saved ? saved.assumptions : data.presets[key];
      data.drivers.forEach(([k])=>{form.elements[k].value=vals[k];});
      form.elements.namedItem("name").value=saved ? saved.name : key+" projection";
      result.innerHTML=projection(saved?saved.years:data.comparison[key]);
      feedback(status,"Selected assumptions applied.");
    };
    form.onsubmit = async event => {
      event.preventDefault();
      const saving=event.submitter?.value==="save";
      const assumptions=Object.fromEntries(data.drivers.map(([k])=>[k,form.elements[k].value]));
      const body=saving ? {name:form.elements.namedItem("name").value.trim(),assumptions} : {assumptions};
      busy(form,true);
      try {
        const r=await post(api,saving?"/api/scenarios":"/api/scenarios/preview",body);
        result.innerHTML=projection(r.years);
        if(saving){
          const idx=data.saved.push(r)-1, option=new Option("Saved · "+r.name,"saved-"+idx);
          form.elements.preset.add(option); form.elements.preset.value=option.value;
        }
        feedback(status,saving?"Saved to this tenant.":"Projection recalculated.");
      } catch(e){feedback(status,e.message,true);} finally{busy(form,false);}
    };
  }
  const metricLabels = {
    stockout_starts_per_1000_sku_days:"Stockout starts per 1,000 SKU-days",
    stockout_hours_per_sku_day:"Stockout hours per eligible SKU-day",expired_units:"Expired base units",expiry_writeoff_sar:"Expiry write-off · SAR",
    expiry_pct_of_tracked_value:"Write-off / tracked value · %",counting_hours_per_session:"Counting hours per standardized session",barcode_adoption_pct:"Barcode adoption · %",
    correction_pct:"Correction rate · %",discrepancy_pct:"Count lines with discrepancy · %",adherence_pct:"Alerts followed · %",forecast_mae_units:"Prospective forecast MAE · units"
  };
  async function pilot(root,api) {
    const r=await api("/api/pilot/report"), p=r.protocol, measured=r.evidence_level==="PILOT_MEASURED", locked=r.imports.length>0;
    const review=r.reviews[0] || p;
    const periodKeys=[["baseline_start","Baseline begins"],["baseline_end","Baseline ends"],["intervention","Intervention begins"],["post_start","Post window begins"],["post_end","Post window ends"]];
    const thresholdKeys=[["minimum_days","Minimum complete days per SKU"],["completeness_pct","Required complete SKU-days · %"],["scan_pct","Required barcode adoption · %"],["improvement_pct","Target reduction in stockout incidence · %"]];
    const measure=(stage,k)=>stage.metrics[k]==null ? measured?"Insufficient coverage":"Not measured" : fmt(stage.metrics[k]);
    root.innerHTML=style+'<div class="study-space"><section class="panel"><div class="study-intro">'+tag(r.evidence_level)+'<h2>Riyadh pilot evaluation</h2></div>' +
      '<p>Compare the same registered SKUs at one branch before and after scanning and alerts enter routine use.</p><div class="study-steps">'+
      [["Baseline",p.baseline_start+" to "+p.baseline_end],["Introduce scanning",p.intervention],["Post-intervention",p.post_start+" to "+p.post_end]].map(([t,v])=>'<article><strong>'+t+'</strong><p>'+esc(v)+'</p></article>').join("")+'</div>'+
      '<div class="study-tiles"><div><small>Progression decision</small><strong>'+esc(r.decision)+'</strong></div><div><small>Baseline complete SKU-days</small><strong>'+fmt(r.baseline.complete_sku_days)+' / '+fmt(r.baseline.expected_sku_days)+'</strong></div><div><small>Post complete SKU-days</small><strong>'+fmt(r.post.complete_sku_days)+' / '+fmt(r.post.expected_sku_days)+'</strong></div></div>'+
      table(["Operating measure","Baseline","Post","Observed SKU-days (pre / post)"],Object.keys(metricLabels).map(k=>[metricLabels[k],measure(r.baseline,k),measure(r.post,k),r.baseline.observed_days[k]+" / "+r.post.observed_days[k]]))+
      '<p class="muted">'+esc(r.uncertainty)+'</p></section><details class="panel"><summary>Register scope, windows and gates</summary>'+
      '<p>Agree the thresholds with the branch lead before collection. Register only coded branch and SKU identifiers.</p><form class="study-protocol"><fieldset '+(locked?'disabled':'')+'><legend>Pilot scope and eligibility</legend><div class="study-fields">'+
      field("Branch code",textInput("branch",p.branch))+field("Eligible SKU codes, comma-separated",textInput("skus",p.skus.join(", ")))+
      periodKeys.map(([k,l])=>field(l,textInput(k,p[k],"date"))).join("")+thresholdKeys.map(([k,l])=>field(l,textInput(k,p[k],"number",'min="1" step="'+(k==="minimum_days"?"1":"0.01")+'"'))).join("")+'</div>'+
      [["integration_reviewed","Integration reviewed"],["security_reviewed","Safety and security reviewed"]].map(([k,l])=>'<label><input type="checkbox" name="'+k+'" '+(p[k]?'checked':'')+'>'+l+'</label>').join("")+
      '<fieldset><legend>Potential confounding factors</legend>'+r.confounder_options.map(f=>'<label><input type="checkbox" name="flags" value="'+esc(f)+'" '+(p.confounders.includes(f)?'checked':'')+'>'+esc(f)+'</label>').join("")+'</fieldset>'+
      '<button class="btn" type="submit">Save protocol</button></fieldset></form><p class="study-status" role="status"></p></details>'+
      '<details class="panel"><summary>Review comparability and safety</summary><p>Record changes observed during the study. Each review preserves the registered dates, thresholds and previous reviews.</p>'+
      '<form class="study-review"><fieldset><legend>Current review</legend>'+
      [["integration_reviewed","Integration reviewed"],["security_reviewed","Safety and security reviewed"]].map(([k,l])=>'<label><input type="checkbox" name="'+k+'" '+(review[k]?'checked':'')+'>'+l+'</label>').join("")+
      '<fieldset><legend>Unresolved comparability factors</legend>'+r.confounder_options.map(f=>'<label><input type="checkbox" name="flags" value="'+esc(f)+'" '+(review.confounders.includes(f)?'checked':'')+'>'+esc(f)+'</label>').join("")+
      '</fieldset><button class="btn" type="submit">Record governance review</button></fieldset></form><p class="study-status" role="status"></p>'+
      (r.reviews.length?table(["Reviewer","UTC","Unresolved factors"],r.reviews.map(x=>[x.actor,x.saved,x.confounders.join(", ")||"None recorded"])):'')+'</details>'+
      '<section class="panel"><h3>Observation import</h3><p>Use one row per branch, SKU and local calendar day. Leave unknown values blank. The Excel template can be saved as UTF-8 CSV for validation.</p>'+
      '<p class="study-actions"><a href="/assets/data/templates/pilot_observations.csv" download>CSV template</a><a href="/assets/data/templates/pilot_observations.xlsx" download>Excel template</a></p>'+
      '<form class="study-import"><div class="study-fields">'+field("Observation file · CSV, up to 180 KB",'<input class="study-filename" type="file" name="file" accept=".csv,text/csv" required>')+
      (r.field_enabled?field("Custodian source reference",'<input type="text" name="reference">'):'')+'</div>'+
      (r.field_enabled?'<label class="study-check"><input type="checkbox" name="attest_actual">I confirm that the custodian authorized this actual branch extract.</label>':'<p class="muted">Training workspace. Validation checks the schema and leaves actual pilot outcomes empty.</p>')+
      '<div class="study-actions"><button class="btn" type="submit" value="validate">Validate file</button>'+(r.field_enabled?'<button class="btn" type="submit" value="import">Import measured observations</button>':'')+
      '</div></form><p class="study-status" role="status"></p></section>'+
      (r.imports.length?'<section class="panel"><h3>Evidence register</h3>'+table(["Batch","Source reference","Authorization","Imported UTC","Custodian"],r.imports.map(x=>[x.id,x.reference,x.authorization,x.imported_at,x.actor]))+'</section>':'')+'</div>';
    const protocol=root.querySelector(".study-protocol"), csvForm=root.querySelector(".study-import"), reviewForm=root.querySelector(".study-review");
    reviewForm.onsubmit=async event=>{
      event.preventDefault();busy(reviewForm,true);
      const next={integration_reviewed:reviewForm.elements.integration_reviewed.checked,security_reviewed:reviewForm.elements.security_reviewed.checked,
        confounders:Array.from(reviewForm.querySelectorAll('[name="flags"]:checked')).map(x=>x.value)};
      try{await post(api,"/api/pilot/review",next);await pilot(root,api);const updated=root.querySelector(".study-review");updated.closest("details").open=true;feedback(updated.nextElementSibling,"Governance review recorded.");}
      catch(e){feedback(reviewForm.nextElementSibling,e.message,true);}finally{busy(reviewForm,false);}
    };
    protocol.onsubmit=async event=>{
      event.preventDefault();
      const next={branch:protocol.elements.branch.value.trim(),skus:protocol.elements.skus.value.split(",").map(s=>s.trim()),
        integration_reviewed:protocol.elements.integration_reviewed.checked,security_reviewed:protocol.elements.security_reviewed.checked,
        confounders:Array.from(protocol.querySelectorAll('[name="flags"]:checked')).map(x=>x.value)};
      periodKeys.forEach(([k])=>{next[k]=protocol.elements[k].value;});thresholdKeys.forEach(([k])=>{next[k]=Number(protocol.elements[k].value);});
      busy(protocol,true);
      try{await post(api,"/api/pilot/protocol",next);await pilot(root,api);feedback(root.querySelector(".study-protocol").nextElementSibling,"Protocol saved.");root.querySelector("details").open=true;}
      catch(e){feedback(protocol.nextElementSibling,e.message,true);}finally{busy(protocol,false);}
    };
    csvForm.onsubmit=async event=>{
      event.preventDefault();
      const file=csvForm.elements.file.files[0], mode=event.submitter?.value || "validate", status=csvForm.nextElementSibling;
      if(!file || file.size>180000){feedback(status,"Select a CSV up to 180 KB.",true);return;}
      busy(csvForm,true);
      try{
        const payload={filename:file.name,csv:await file.text(),mode};
        if(mode==="import"){payload.reference=csvForm.elements.reference.value.trim();payload.attest_actual=csvForm.elements.attest_actual.checked;}
        const got=await post(api,"/api/pilot/measurements",payload);
        if(mode==="import"){await pilot(root,api);feedback(root.querySelector(".study-import").nextElementSibling,fmt(got.rows)+" measured SKU-days imported.");}
        else{feedback(status,fmt(got.rows)+" SKU-days passed schema validation. Nothing was imported.");}
      }catch(e){feedback(status,e.message,true);}finally{busy(csvForm,false);}
    };
  }
  window.renderStudy=(page,container,api)=>page==="pilot" ? pilot(container,api) : economics(container,api);
})();
