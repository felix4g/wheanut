'use strict';
// Optional live adapter. A separate backend access token is held in memory only.
// NVIDIA API keys are never accepted, saved, or sent by this browser adapter.
(function(){
 const card=document.createElement('article');card.className='paper';card.innerHTML='<p class="eyebrow">OPTIONAL LIVE CONNECTION</p><h2>Ask a new question.</h2><p>Connect your team’s HTTPS backend for live Nemotron answers and new-field analysis. Saved reports remain available without a connection.</p><button class="secondary" id="live-connect-open">Connect team backend ↗</button><p id="live-connection-status" class="fine" role="status">No live backend configured.</p>';
 document.querySelector('#data-view .data-grid').prepend(card);
 const dialog=document.createElement('dialog');dialog.id='live-connect-dialog';dialog.innerHTML='<form id="live-connect-form"><div class="dialog-heading"><h2>Connect the team backend</h2><button class="icon-button" type="button" id="live-connect-close" aria-label="Close live connection">×</button></div><p>Use an approved backend URL and its separate access token. Never paste an NVIDIA API key here.</p><label>Backend HTTPS URL<input id="live-backend-url" type="url" required value="https://wheanut-api.maqichao0203.workers.dev" placeholder="https://your-approved-backend.example"></label><label>Backend access token<input id="live-backend-token" type="password" autocomplete="off" required></label><p class="fine">Token stays in memory for this page only. Reloading disconnects the backend.</p><p id="live-connect-error" role="alert"></p><button class="primary" id="live-connect-submit">Verify and connect</button></form>';
 document.body.append(dialog);const shortcut=document.createElement('button');shortcut.className='preview-link';shortcut.textContent='Connect live Nemotron ↗';shortcut.id='live-connect-shortcut';shortcut.onclick=()=>dialog.showModal();$('#ai-run-status').after(shortcut);$('#live-connect-open').onclick=()=>dialog.showModal();$('#live-connect-close').onclick=()=>dialog.close();
 $('#live-connect-form').onsubmit=async event=>{
  event.preventDefault();$('#live-connect-error').textContent='';const submit=$('#live-connect-submit');submit.disabled=true;
  try{
   const url=new URL($('#live-backend-url').value);if(url.protocol!=='https:'&&!(url.protocol==='http:'&&['127.0.0.1','localhost'].includes(url.hostname)))throw Error('Use HTTPS, or a local loopback preview.');
   if(url.username||url.password||url.search||url.hash)throw Error('Use a clean backend URL without credentials or query parameters.');
   let token=$('#live-backend-token').value.trim();if(token.startsWith('nvapi-'))throw Error('This looks like an NVIDIA key. Keep it on the backend; use the separate backend access token here.');
   const base=url.href.replace(/\/$/,'');const headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'};
   const health=await fetch(base+'/api/health',{headers,signal:AbortSignal.timeout(15000)});if(!health.ok)throw Error('Backend health check failed. Check the separate backend access token.');const capabilities=await health.json();if(capabilities.status!=='ready')throw Error('The backend still needs its private configuration.');
   const known=await fetch('data/model_results.json').then(r=>{if(!r.ok)throw Error('Saved report index unavailable.');return r.json()});
   window.Wheanut.connectAgent(async(request,{signal})=>{
    const saved=known.find(r=>r.id===request.fieldId&&r.season===request.season&&JSON.stringify(r.geometry)===JSON.stringify(request.geometry));
    if(capabilities.kind==='hosted-explainer'){
     const response=await fetch(base+'/api/explain',{method:'POST',headers,body:JSON.stringify(request),signal});const output=await response.json();if(!response.ok)throw Error(output.error||'Hosted explanation failed.');return output;
    }
    const started=await fetch(base+'/api/jobs',{method:'POST',headers,body:JSON.stringify({...request,action:saved?'explain':'analyze'}),signal});
    const job=await started.json();if(!started.ok)throw Error(job.error||'Could not start analysis.');
    const deadline=Date.now()+500000;
    while(Date.now()<deadline){
     if(signal.aborted)throw Error('Analysis was cancelled.');
     const response=await fetch(base+'/api/jobs/'+encodeURIComponent(job.jobId),{headers,signal});const current=await response.json();if(!response.ok)throw Error(current.error||'Could not read analysis status.');
     if(current.status==='complete')return current.result;
     if(current.status==='error')throw Error(current.error||'Analysis failed without a prediction.');
     setAIStatus(current.status==='queued'?'Queued on the team backend.':'Running real satellite/model analysis on the team backend.','loading');
     await new Promise((resolve,reject)=>{const timer=setTimeout(resolve,2000);signal.addEventListener('abort',()=>{clearTimeout(timer);reject(Error('Analysis was cancelled.'))},{once:true})});
    }
    throw Error('Analysis exceeded its time limit.');
   },{timeoutMs:510000});
   $('#ai-question').value='';$('#ai-question').placeholder='Ask about the evidence, uncertainty or what changed during the season.';$('#start-analysis').innerHTML=`${icon('sparkles')}Start live analysis${icon('arrow')}`;
   $('#live-backend-token').value='';$('#live-connection-status').textContent='Live backend connected for this page session.';dialog.close();toast('Live backend connected. Choose a field in AI Analysis.');
  }catch(error){$('#live-connect-error').textContent=error.message||'Connection failed.'}finally{submit.disabled=false}
 };
})();
