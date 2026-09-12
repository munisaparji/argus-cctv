import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from '@playwright/test';

const root=path.resolve('../..');
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},recordVideo:{dir:path.join(root,'artifacts/qa/video'),size:{width:1440,height:900}}});
const page=await context.newPage();
await page.goto('http://127.0.0.1:8000/?demo=1');
await page.getByRole('heading',{name:'Incident workspace'}).waitFor();
const started=Date.now();
const captions=[];
async function caption(title,body){
 await page.evaluate(({title,body})=>{
  let el=document.getElementById('walkthrough-caption');
  if(!el){el=document.createElement('div');el.id='walkthrough-caption';document.body.append(el)}
  el.style.cssText='position:fixed;z-index:9999;left:248px;right:24px;bottom:12px;padding:16px 22px;background:#071820f5;color:#e7f1f6;border:1px solid #2aaabd;border-radius:10px;font:17px/1.5 system-ui;pointer-events:none;box-shadow:0 4px 30px #0008';
  el.replaceChildren();const strong=document.createElement('strong');strong.textContent=title;strong.style.cssText='display:block;color:#4bdded;font-size:19px';el.append(strong,document.createTextNode(body));
 },{title,body});
 captions.push({start_s:(Date.now()-started)/1000,title,body});
}
const nav=async name=>{await page.getByRole('navigation').getByRole('button',{name,exact:true}).click();await page.evaluate(()=>window.scrollTo(0,0));};
const slots=[
 async()=>caption('ARGUS: local evidence review','This recorded walkthrough uses eight original synthetic clips. The application runs without a GPU or paid service.'),
 async()=>{await page.getByLabel('Filter incidents').fill('counter');await caption('Triage the evidence','Search clips, compare anomaly curves and inspect severity, claim rejection and review state. Reference severity is uncalibrated.');},
 async()=>{await page.getByRole('button',{name:'Open sample_counter_01',exact:true}).click();await page.locator('video').evaluate(v=>{v.loop=true;return v.play()});await caption('Video and independent evidence','Person and bag detections come from pixel segmentation in this sample. Research clips use the separate DETR adapter.');},
 async()=>{await page.locator('video').evaluate(v=>v.pause());await page.locator('.claim.rejected').scrollIntoViewIfNeeded();await page.locator('.claim.rejected summary').click();await caption('A rejected knife claim','The authored language says a person is holding a knife. Available evidence has no supporting knife detection. Missing support is not proof of absence.');},
 async()=>{await page.getByLabel('Show what an unverified system would have shown').check();await page.locator('.raw-warning').scrollIntoViewIfNeeded();await caption('Raw output versus verified ledger','The comparison exposes unsupported assertions. The normal ledger keeps rejected and downgraded claims clearly labelled.');},
 async()=>{await page.getByLabel('Show what an unverified system would have shown').uncheck();await page.locator('.gauge').scrollIntoViewIfNeeded();await caption('Inspectable severity','Thirteen factors expose raw values, weights and contributions. Unsupported context stays unavailable. Human fitting and held-out validation remain pending.');},
 async()=>{await page.locator('.response-panel').scrollIntoViewIfNeeded();await caption('Recommendations require human review','Exactly twelve permitted action tokens. A confirm or dismiss records an operator decision; ARGUS never dispatches a service. Offline sample writes are disabled.');},
 async()=>{await nav('Pipeline');await caption('Seven stages, one typed record','Features, detection, evidence, structured language, critic, severity and policy each produce inspectable JSON. Research model runs use the supplied CLI tools.');},
 async()=>{await nav('Benchmarks');await caption('Executed synthetic checks','Eight scenes, fifteen authored claims and two unsupported claims rejected. The policy test strips four of four deliberately invalid actions.');},
 async()=>{await page.locator('.research-results').scrollIntoViewIfNeeded();await caption('Research findings remain pending','Real UCF AUC, XD AP, independent severity agreement and VLM ablations need licensed data, model runs and human ratings. No target is presented as an achieved result.');},
 async()=>{await nav('Annotation');await caption('Annotation and adjudication tooling','Record normalized factors, a score, action labels and typed evidence spans. Independent annotators must finish before comparison and adjudication.');},
 async()=>{await nav('Method & ethics');await caption('Delivered source and academic materials','The package includes setup scripts, tests, training and evaluation tools, the project guide, review deck and poster. There is no biometric identification, live surveillance or automated dispatch.');},
];
try{
 for(let i=0;i<slots.length;i++){
  await slots[i]();
  console.log(`Walkthrough segment ${i+1}/${slots.length}`);
  await page.waitForTimeout(Math.max(0,started+(i+1)*15000-Date.now()));
 }
 const video=page.video();
 await context.close();
 await video.saveAs(path.join(root,'deliverables/ARGUS_Demo_Walkthrough.webm'));
 await fs.writeFile(path.join(root,'artifacts/walkthrough-captions.json'),JSON.stringify({audio:'none',captions},null,2));
}finally{await browser.close();}
