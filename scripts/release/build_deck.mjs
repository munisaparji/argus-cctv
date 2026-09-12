import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const root=path.resolve(import.meta.dirname,'../..');
const runtime=process.env.ARGUS_ARTIFACT_RUNTIME;
const skill=process.env.ARGUS_PRESENTATION_SKILL;
process.env.RUNTIME_NODE_MODULES=path.join(runtime||'', 'node/node_modules');
if(!runtime||!skill)throw new Error('Set ARGUS_ARTIFACT_RUNTIME and ARGUS_PRESENTATION_SKILL to the installed bundled paths.');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')));
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const out=path.join(root,'deliverables'),qa=path.join(root,'artifacts/qa/deck');
await fs.mkdir(out,{recursive:true});await fs.mkdir(qa,{recursive:true});
const metrics=JSON.parse(await fs.readFile(path.join(root,'artifacts/metrics.json'),'utf8')).sample;
const refs=JSON.parse(await fs.readFile(path.join(root,'docs/literature/verified.json'),'utf8'));
const slides=[
 ['ARGUS CCTV evidence verification','Offline research project review',['Munis Aparji V S, Mithin Sagar S and Janit B','Guide: Dr. Premanand V','BCSE497J, SCOPE, Vellore Institute of Technology'], 'title'],
 ['Domain and problem statement','What an operator needs to review',['An anomaly score locates a candidate interval but does not explain it.','Generated descriptions can introduce unsupported objects or intent.','ARGUS records claims, independent evidence and review decisions.']],
 ['Four research questions','Detection, verification, calibration and response',['P1: How can a candidate anomaly window be explained?','P2: Which generated claims have supporting evidence?','P3: How well do interpretable severity factors agree with humans?','P4: Can every recommendation remain inside a closed vocabulary?']],
 ['Literature foundations','The project builds on established research',['Surveillance video-language understanding defines the task family.','PEL4VAD supplies a reproducible weak-supervision comparator.','Video Violence Rating establishes a precedent for graded severity.','StrongSORT provides context for tracking quality and association.']],
 ['Literature and design choices','Fifteen journal DOI records verified through Crossref',['Normalization and snippet attention inform the detector design.','Temporal, graph and feature-modeling work expands the comparison set.','Language-guided detection already exists. ARGUS does not claim it as novel.','Metadata verification supports attribution; full-text replication remains separate.']],
 ['System architecture','One versioned record connects seven bounded modules',['M1 features, M2 temporal detection and M3 independent evidence','M4 structured language and M5 conservative verification','M6 inspectable severity and M7 validated recommendations','The automatic terminal state awaits a human decision.']],
 ['Data plan','Each dataset has a distinct role',['UCF-Crime: WHEN, using weak video labels and pre-released features.','UCA: WHAT TO SAY, for temporal language alignment.','XD-Violence: GENERALISE, held out and evaluated with AP.','SIRB: HOW SERIOUS AND DO WHAT, requiring new human annotations.']],
 ['The offline demonstration','Original synthetic scenes exercise the complete workflow',['Eight generated clips contain coloured person, bag and vehicle sprites.','Pixel segmentation and geometric tracking produce actual sample evidence.','A motion baseline and authored language cache keep the demo independent of GPUs.','Sample labels and reference severity are explicitly identified.']],
 ['Feature cache and temporal detector','Frozen research features feed a trainable transformer',['Resample to 25 fps and aggregate 16-frame snippets, each spanning 0.64 seconds.','Four temporal transformer layers use LayerNorm and positional encoding.','MIL top-k pooling, attention and erasing losses train from video-level labels.','Independent validation selects checkpoints; test labels remain held out.']],
 ['Independent evidence extraction','Object evidence is separate from language generation',['A frozen DETR adapter supports research clips.','A geometric IoU tracker uses clip-local IDs without biometric embeddings.','Counts use simultaneous detections rather than fragmented track totals.','Keyframes combine detection density and motion with temporal spacing.']],
 ['Structured language and cache','The VLM has no severity or response fields',['The optional Qwen batch constrains output to the claim JSON schema.','Each clip saves independently, allowing interrupted notebook jobs to resume.','Generation has at most three parsing attempts and one explicit critic retry.','The default CPU console consumes validated cached outputs.']],
 ['The rejected knife claim','A visible example of missing supporting evidence',['Authored output says a person is holding a knife.','The synthetic detector evidence supports people and a bag.','The critic rejects the knife claim and leaves it visible in the ledger.','A detector miss still means missing support, not proof of absence.']],
 ['Verification rules','Conservative semantics limit unsupported certainty',['Inspect sentence text as well as declared entities.','Check object support, simultaneous counts and the claimed interval.','Use curated aliases and one-way hypernym matching.','Downgrade intent and unsupported interactions; never add new claims.']],
 ['Interpretable severity','Thirteen factors with nonnegative contributions',['Only VERIFIED OBSERVATION claims contribute automatic factors.','Seven context or event factors remain unavailable without independent support.','A constrained ordinal fitting tool learns weights from independent human ratings.','Reference weights are uncalibrated until fitting and held-out evaluation.']],
 ['Policy and human review','Exactly twelve recommendation tokens',['The policy table proposes actions from category and severity.','A validator strips unknown tokens and counts every invalid proposal.','Confirm and dismiss create transactional append-only audit entries.','No code dispatches responders, sends messages or performs enforcement.']],
 ['SIRB annotation workflow','Independent review precedes adjudication',['A deterministic sampling manifest assigns 20 percent overlap.','Operators enter factors, overall score, action labels and evidence spans.','Independent sessions remain separate until a third review resolves disagreements.','Annotation-only export excludes synthetic practice labels and source footage.']],
 ['Executed software checks','Synthetic fixtures only',['All eight clips pass through the seven-stage pipeline.','Backend tests cover rejection, retry bounds, severity isolation and audit transactions.','Browser checks exercise playback, all screens and WebSocket runs.','The accompanying artifacts record actual results and their scope.'],'chart'],
 ['Research evaluation status','Real experiments remain pending',['UCF frame AUC and UCA temporal overlap need real labels and model outputs.','XD AP requires held-out cross-dataset inference.','Severity kappa, rho and MAE need human ratings and held-out predictions.','7B/3B and evidence-conditioning ablations require paired model runs.']],
 ['Ethics and limitations','The delivery is local academic software',['No facial recognition, identity inference or cross-camera re-identification.','No live streaming or automatic external action.','Detector misses, ID switches and restricted language coverage remain limitations.','Local sessions are not authenticated accounts; public deployment needs a separate design.']],
 ['Project delivery and next experiments','A runnable implementation with reproducible study tools',['Run start.ps1 and open the local console.','Read the project guide for schemas, commands and annotation procedures.','Obtain licensed data, run the research adapters and collect independent ratings.','Replace pending findings only with results produced by the evaluation scripts.']],
];
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const family='Arial';
function text(slide,content,x,y,w,h,size,color='#152435',bold=false){const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});shape.text=content;shape.text.style={typeface:family,fontSize:size,color,bold,autoFit:'none'};return shape;}
for(let i=0;i<slides.length;i++){
 const [title,subtitle,body,type]=slides[i],slide=presentation.slides.add();
 slide.background.fill=i===0?'#0A1018':'#FFFFFF';
 const ink=i===0?'#E6EDF5':'#152435',dim=i===0?'#A5B5C8':'#516173';
 text(slide,title,70,i===0?100:52,1140,i===0?150:100,i===0?62:43,ink,true);
 text(slide,subtitle,72,i===0?280:162,1136,54,i===0?30:24,i===0?'#43D7EB':'#087D90');
 if(type==='chart'){
   const chart=slide.charts.add('bar',{position:{left:75,top:245,width:680,height:355},categories:['Claims','Rejected','Invalid actions stripped'],series:[{name:'Synthetic counts',values:[metrics.claims,metrics.rejected_claims,metrics.adversarial_stripped],fill:'#087D90'}],barOptions:{direction:'column',grouping:'clustered'},hasLegend:false,dataLabels:{showValue:true,position:'outEnd'}});
   applyPresentationChartFont(chart,{fontFamily:family});
   text(slide,`${metrics.incidents} synthetic scenes\n\n${metrics.constraint_violations} normal-run policy violations\n\n${metrics.adversarial_stripped} of ${metrics.adversarial_injected} injected invalid actions stripped`,800,280,380,280,28,ink);
 }else{
   body.forEach((line,j)=>text(slide,line,74,(i===0?400:252)+j*(i===0?58:88),1120,i===0?55:76,i===0?23:27,i===0?dim:ink));
 }
 text(slide,`${String(i+1).padStart(2,'0')} / 20`,1120,665,100,25,15,dim);
 let notes='ARGUS implementation review. The sample is synthetic and the severity model is uncalibrated. Research results remain pending.\n';
 if(i===3||i===4)notes+=refs.map(r=>`${r.title}. ${r.url}`).join('\n');
 if(i===16)notes+='Source: artifacts/metrics.json; generated directly from the delivered sample records.\n';
 notes+='Speaker notes: '+body.join(' ');
 slide.speakerNotes.textFrame.setText(notes);
 const preview=await presentation.export({slide,format:'png',scale:1});
 await fs.writeFile(path.join(qa,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const candidatePath=path.join(qa,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const finalPath=path.join(out,'ARGUS_Review_Deck.pptx');
await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:path.join(runtime,'python/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],explicitTotalSlideCount:20,materializeLiteralChartWorkbooks:true,requiredNativeChartOwnerSlides:[17],requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,receiptPath:path.join(qa,'validation.json')});
console.log(finalPath);
