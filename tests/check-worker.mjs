import worker from '../cloudflare/worker.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const rows=JSON.parse(fs.readFileSync(new URL('../frontend/data/model_results.json',import.meta.url)));const row=rows[0];
const env={NVIDIA_API_KEY:'TEST_ONLY_NOT_REAL',WHEANUT_API_TOKEN:'TEST_BACKEND_ACCESS',NVIDIA_MODEL:'nvidia/test'};
const originalFetch=globalThis.fetch;let upstreamBody;
globalThis.fetch=async(url,options)=>{
 if(String(url).endsWith('/data/model_results.json'))return Response.json(rows);
 assert.equal(String(url),'https://integrate.api.nvidia.com/v1/chat/completions');upstreamBody=JSON.parse(options.body);return Response.json({choices:[{message:{content:'Observed greenness changed. Verify imagery and field records.'}}]});
};
const request=(body,extra={})=>new Request('https://backend.example/api/explain',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer TEST_BACKEND_ACCESS','Origin':'https://wheanut.pages.dev','CF-Connecting-IP':String(Math.random()),...extra},body:JSON.stringify(body)});
try{
 assert.equal((await worker.fetch(request({}),{})).status,503);
 assert.equal((await worker.fetch(request({},{Authorization:'Bearer wrong'}),env)).status,401);
 const input={fieldId:row.id,season:row.season,geometry:row.geometry,question:'What changed?',prediction:'FORGED',referenceLabel:'NEVER_SEND_THIS'};
 const response=await worker.fetch(request(input),env);assert.equal(response.status,200);const result=await response.json();assert.equal(result.prediction,row.prediction);assert.match(result.explanationMode,/live NVIDIA/);assert.equal('NVIDIA_API_KEY' in result,false);
 assert.equal(upstreamBody.chat_template_kwargs.enable_thinking,false);assert.equal(upstreamBody.max_tokens,1024);
 const prompt=JSON.stringify(upstreamBody.messages);assert.equal(prompt.includes('referenceLabel'),false);assert.equal(prompt.includes('NEVER_SEND_THIS'),false);assert.equal(prompt.includes('FORGED'),false);
 assert.equal((await worker.fetch(request({...input,season:2025}),env)).status,422);
 assert.equal((await worker.fetch(request(input,{Origin:'https://untrusted.example'}),env)).status,403);
 console.log('PASS: hosted Worker disabled without secrets, bearer auth, trusted server evidence, reference-label exclusion, changed-season rejection and CORS. No real API requests.');
}finally{globalThis.fetch=originalFetch}
