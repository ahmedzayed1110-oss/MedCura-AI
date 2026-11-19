/* Functional browser checks on an isolated database. --pipe uses the real HTTP handler over stdio.
   Default: start the launcher in a temporary folder and exercise the TCP listener. */
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const readline = require("node:readline");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname,"..");
const python = process.env.PYTHON || "python";
const pipe = process.argv.includes("--pipe");
const base = "http://127.0.0.1:8765";
const shot = process.env.MEDCURA_SCREENSHOTS;
const sleep = ms => new Promise(resolve => setTimeout(resolve,ms));

async function main(){
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(),"medcura-ui-"));
  let child,browser,passed=0;
  const errors=[];
  try{
    let credentials,channel;
    if(pipe){
      child=spawn(python,["-u","tests/http_transport.py"],{cwd:root,stdio:["pipe","pipe","inherit"],windowsHide:true});
      const messages=readline.createInterface({input:child.stdout})[Symbol.asyncIterator]();
      credentials=JSON.parse((await messages.next()).value).password;
      let chain=Promise.resolve(),id=0;
      channel=route=>{
        const run=async()=>{
          const req=route.request(),url=new URL(req.url());
          const message={id:++id,method:req.method(),path:url.pathname+url.search,headers:await req.allHeaders(),body:(req.postDataBuffer()||Buffer.alloc(0)).toString("base64")};
          child.stdin.write(JSON.stringify(message)+"\n");
          const res=JSON.parse((await messages.next()).value);
          assert.equal(res.id,message.id);
          await route.fulfill({status:res.status,headers:res.headers,body:Buffer.from(res.body,"base64")});
        };
        chain=chain.then(run);
        return chain;
      };
    } else {
      child=spawn(python,["-u","run.py","--port","0","--data-dir",tmp],{cwd:root,stdio:["ignore","pipe","inherit"],windowsHide:true});
      const lines=readline.createInterface({input:child.stdout})[Symbol.asyncIterator]();
      const first=(await lines.next()).value;
      process.env.MEDCURA_E2E_URL=first.match(/http:\/\/127\.0\.0\.1:\d+/)[0];
      credentials=JSON.parse(fs.readFileSync(path.join(tmp,"local-accounts.json"))).director;
    }
    const url=pipe?base:process.env.MEDCURA_E2E_URL;
    const executablePath=process.env.CHROME_PATH;
    browser=await chromium.launch({headless:true,...(executablePath?{executablePath}:{})});
    const context=await browser.newContext({viewport:{width:1440,height:1024},acceptDownloads:true});
    if(channel)await context.route(base+"/**",channel);
    const page=await context.newPage();
    page.setDefaultTimeout(10000);
    page.on("pageerror",e=>errors.push(e.message));
    const by=(name)=>page.getByRole("button",{name,exact:true});
    const nav=async (key)=>{await page.locator('nav a[href="#'+key+'"]').click();await page.locator("#view > .panel,#view .hero,#view .study-space,#view > .tools,#view > .actions").first().waitFor()};
    const snap=async n=>{if(shot){fs.mkdirSync(shot,{recursive:true});await page.screenshot({path:path.join(shot,n+".png")})}};
    const ok=s=>{passed++;console.log("PASS "+s)};
    await page.goto(url);await page.getByLabel("Username").fill("director");await page.getByLabel("Password").fill(credentials);
    await by("Sign in").click();await page.locator(".hero").waitFor();
    assert.match(await page.locator(".hero").innerText(),/3,607/);
    await by("Inspect source cells").click();await page.locator("dialog[open]").waitFor();assert.match(await page.locator("dialog").innerText(),/01 Facilities!F5/);
    await by("Close dialog").click();await snap("overview");ok("Sign-in and cell-level KPI lineage");
    await nav("stock");const move=page.locator("#move");
    await move.locator("[name=branch]").selectOption("north");await page.getByLabel("Scan SKU or lot code").fill("masks");await by("Apply scan").click();assert.equal(await move.locator("[name=sku]").inputValue(),"masks");
    await move.locator("[name=code]").fill("QA-BATCH");await move.locator("[name=qty]").fill("2");await move.locator("[name=unit]").selectOption("pack");
    await move.locator("[name=reason]").fill("Two simulated packs");await by("Record movement").click();
    await page.getByText("QA-BATCH",{exact:true}).waitFor();await move.locator("[name=kind]").selectOption("issue");
    await move.locator("[name=qty]").fill("3");const lot=await move.locator("[name=lot] option").filter({hasText:"QA-BATCH"}).getAttribute("value");
    await move.locator("[name=lot]").selectOption(lot);await move.locator("[name=reason]").fill("Three simulated issues");await by("Record movement").click();
    await page.waitForFunction(()=>[...document.querySelectorAll("#stock-table tr")].some(r=>r.textContent.includes("QA-BATCH")&&r.textContent.includes("47")));
    await nav("ledger");await page.getByLabel("Filter transactions").fill("QA-BATCH");
    assert.equal(await page.locator("#events tbody tr").count(),2);ok("Pack receipt, lot issue and ledger reconciliation");
    await nav("forecast");await page.locator('#view select[name=branch]').selectOption("east");await page.locator('#view select[name=sku]').waitFor();
    await page.locator('#view select[name=sku]').selectOption("gloves");
    await page.getByRole("heading",{name:"Rolling-origin evaluation"}).waitFor();
    await page.waitForFunction(()=>document.querySelector("#view")?.textContent.includes("weekly naive"));
    await snap("forecast");ok("Forecast and reorder explanation");
    await nav("transfers");await by("Draft transfer").first().click();await by("Create draft").click();
    for(const action of ["Request","Approve","Dispatch","Receive"])await by(action).click();
    await page.getByText("RECEIVED",{exact:true}).waitFor();await snap("transfer-received");ok("Transfer draft, approval, dispatch and receipt");
    await nav("decisions");await by("Approve order").first().click();await by("Receive order").first().click();
    await page.locator("#po-form [name=code]").fill("QA-PO");const expiry=page.locator("#po-form [name=expiry]");
    if(await expiry.count())await expiry.fill("2028-10-01");await by("Confirm receipt").click();
    await page.getByText("received",{exact:true}).waitFor();ok("Order approval and physical receipt");
    await nav("economics");await page.locator(".study-fin [name=name]").fill("Browser case");await by("Save scenario").click();
    await page.waitForFunction(()=>document.querySelector(".study-fin select")?.textContent.includes("Browser case")||document.querySelector(".study-status")?.textContent.toLowerCase().includes("saved"));
    await nav("pilot");assert.match(await page.locator("#view").innerText(),/not measured/i);ok("Saved scenario and empty prospective pilot");
    await page.locator(".study-import input[type=file]").setInputFiles({name:"observations.csv",mimeType:"text/csv",buffer:Buffer.from("unapproved_column\nexample\n")});
    await by("Validate file").click();
    await page.waitForFunction(()=>[...document.querySelectorAll(".study-status")].some(e=>/header|template|columns/i.test(e.textContent)));
    ok("Pilot upload rejects a nonconforming schema");
    await nav("market");await page.locator("#market-filter").fill("Makkah");
    assert.match(await page.locator("#market-content table").innerText(),/880/);
    assert.equal(await page.locator("#market-content table tbody tr").count(),1);
    await nav("audit");await page.locator("#audit-cell-search").fill("F5");
    assert.match(await page.locator("#raw-rows").innerText(),/1171|1,171/);
    ok("Regional filtering and raw workbook cell lookup");
    for(const name of ["presentation","settings"]) {await nav(name);assert.doesNotMatch(await page.locator("#view").innerText(),/Internal error|File unavailable/);}
    await nav("overview");await page.setViewportSize({width:390,height:844});await by("Toggle navigation").waitFor();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await snap("mobile-overview");
    await by("Toggle navigation").click();await nav("stock");await page.locator("#stock-table").waitFor();
    assert.match(await page.locator("#stock-table").innerText(),/QA-BATCH/);ok("Mobile navigation and persistent state");
    assert.deepEqual(errors,[]);console.log(passed+" browser workflows passed; 0 failed; transport "+(pipe?"stdio HTTP":"TCP HTTP"));
  }finally{
    if(browser)await browser.close();
    if(child){child.stdin?.end();child.kill()}
    await sleep(200);
    fs.rmSync(tmp,{recursive:true,force:true});
  }
}
main().catch(err=>{console.error(err);process.exitCode=1});

