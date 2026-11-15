'use strict';
// Replace this adapter with connectAgent(yourHandler) when the team backend is ready.
(async function loadTrainedReports(){
 try {
  const responses=await Promise.all(['model_results','metrics','nemotron_status'].map(n=>fetch(`data/${n}.json`).then(r=>{if(!r.ok)throw Error(`Cannot load ${n}`);return r.json()})));
  const [reports,metrics,nemotron]=responses;
  if(nemotron.status!=='complete')throw Error('Nemotron reports are incomplete');
  const validated=validateFields(reports), saved=new Map(fields.map(f=>[f.id,f]));
  const restore=()=>{
   const saved=new Map(fields.map(f=>[f.id,f]));
   const custom=fields.filter(f=>!f.demo&&!f.id.startsWith('BARC-'));
   fields=[...validated.map(f=>({...f,checked:saved.get(f.id)?.checked||false,note:saved.get(f.id)?.note||''})),...custom].slice(0,200);
   selected=fields.some(f=>f.id===selected)?selected:fields[0].id;
   seasonFilter=String(getField().season||'all');filter='all';$('#field-search').value='';render();fitAll();persist();
  };
  restore();
  window.Wheanut.connectAgent(async request=>{
   const report=reports.find(r=>r.id===request.fieldId);
   const current=window.Wheanut.getFields().find(f=>f.id===request.fieldId);
   if(!report||!current||JSON.stringify(current.geometry)!==JSON.stringify(report.geometry)||current.season!==report.season)throw Error('This boundary or season has no trained report. Import a real result or connect the team backend.');
   return {...report};
  },{mode:'cached'});
  $('#start-analysis').innerHTML=`${icon('sparkles')}Open Nemotron report${icon('arrow')}`;
  $('#ai-question').value='Read the saved harvest classification, Nemotron interpretation, measured observations and uncertainty. Live questions will be available when the team backend is connected.';
  $('#preview-analysis').hidden=true;
  $('.connection-note').textContent='44 reports · real satellite observations · NVIDIA Nemotron';
  $('.demo-tag').innerHTML='<i></i>BARC evaluation workspace';
  $('#reset-data').onclick=()=>{if(window.confirm('Restore BARC evaluation fields? Your custom boundaries will be kept. Export your current work first.')){restore();toast('Evaluation fields restored. Custom boundaries kept.')}};
  const pct=v=>(v*100).toFixed(1)+'%';
  $('#evaluation-panel').innerHTML=`<div class="evaluation-heading"><div><p class="eyebrow">MEASURED, NOT ASSUMED</p><h2>How well does it work?</h2><p>44 field-years · 34 unique fields · Beltsville, Maryland · 2021–2023</p></div><span class="outline-label">STRICT YEAR + FIELD HOLDOUT</span></div><div class="evaluation-stats"><div><strong>${pct(metrics.classification_report.accuracy)}</strong><span>Overall accuracy</span></div><div><strong>${pct(metrics.classification_report['macro avg'].recall)}</strong><span>Balanced accuracy</span></div><div><strong>${pct(metrics.classification_report.Silage.recall)}</strong><span>Silage recall</span></div><div><strong>${pct(metrics.classification_report.Silage.precision)}</strong><span>Silage precision</span></div></div><p class="evaluation-caution">This initial model misses 3 of 12 Silage cases and incorrectly flags 11 Grain cases as Silage. Always predicting Grain reaches 72.7% accuracy (50% balanced accuracy); this model does not beat that baseline on overall accuracy.</p><div class="evaluation-tables"><div><h3>Confusion matrix</h3><p class="fine">Rows: reference label · Columns: predicted label</p><table><thead><tr><th scope="col">Actual / predicted</th><th scope="col">Grain</th><th scope="col">Silage</th></tr></thead><tbody>${metrics.confusion_matrix.map((r,i)=>`<tr><th scope="row">${metrics.class_order[i]}</th>${r.map(n=>`<td>${n}</td>`).join('')}</tr>`).join('')}</tbody></table></div><div><h3>Both classes, in full</h3><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>FPR</th><th>Count</th></tr></thead><tbody>${metrics.class_order.map(c=>`<tr><th scope="row">${c}</th><td>${pct(metrics.classification_report[c].precision)}</td><td>${pct(metrics.classification_report[c].recall)}</td><td>${pct(metrics.false_positive_rate[c])}</td><td>${metrics.classification_report[c].support}</td></tr>`).join('')}</tbody></table></div></div><details><summary>Validation, timing & limitations</summary><p>Balanced logistic regression with seasonal NDVI features. Each test year is withheld; all test fields are also excluded from every training year. No reference labels enter Nemotron prompts.</p><table><thead><tr><th>Test year</th><th>Train records</th><th>Test records</th><th>Field overlap</th></tr></thead><tbody>${metrics.folds.map(f=>`<tr><td>${f.held_out_year}</td><td>${f.train_records}</td><td>${f.test_records}</td><td>${f.field_overlap}</td></tr>`).join('')}</tbody></table><p>Label counts (Grain / Silage): 2021: 14 / 4 · 2022: 3 / 4 · 2023: 15 / 4.</p><p>Classifier prediction: ${(metrics.response_time.classifier_seconds_per_field_mean*1000).toFixed(3)} ms per field, averaged from batched predictions. Excludes imagery retrieval and AI explanation. Nemotron generated ${nemotron.count} explanations in ${nemotron.elapsed_seconds.toFixed(1)} seconds including model loading. These timings are not public API latency.</p><ul>${metrics.limitations.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></details><div class="source-links"><a href="https://doi.org/10.5281/zenodo.8087301" target="_blank" rel="noopener">BARC dataset ↗</a><a href="https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a" target="_blank" rel="noopener">Sentinel-2 L2A ↗</a><a href="data/metrics.json" download>Download measured metrics ↓</a><a href="data/model_results.json" download>Download real results ↓</a></div>`;
  const initial=reports.find(r=>r.id===selected);
  if(initial)renderAIResult(getField(),initial,false);
 } catch(error) {
  setAIStatus('Saved reports could not load: '+error.message+'. Retry by reloading; importing your own results still works.','error');
  $('#evaluation-panel').textContent='Measured evaluation unavailable. Reload to try again.';
 }
})();
