"""Generate real, cached explanations without an NVIDIA API key."""
import json, os, time
from pathlib import Path
os.environ.setdefault('HF_HOME','/tmp/wheanut-nemotron-cache')
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config/project.json').read_text())
MODEL=CFG.get('local_nemotron_model','nvidia/Nemotron-Mini-4B-Instruct')
REVISION=CFG.get('local_nemotron_revision')
p=ROOT/'artifacts/model_results.json'
rows=json.loads(p.read_text())
started=time.time()
tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,torch_dtype=torch.bfloat16,device_map='auto')
model.eval()
raw=[]
for row in rows:
    facts={k:row[k] for k in ['id','region','season','prediction','confidence','dates','ndvi']}
    prompt='Write exactly 3 short sentences for a farmer, at most 70 words. Sentence 1 must begin "The classifier suggests" and mention the predicted class and uncalibrated percentage below. Sentence 2 should explain that NDVI measures greenness and cannot confirm harvest type. Sentence 3 should recommend checking field records and imagery. Never say the satellite proves or shows actual harvest, never call confidence high or low, never invent harvest dates, weather or yield. This is a saved model interpretation. Facts: '+json.dumps({'prediction':row['prediction'],'uncalibrated_percentage':round(row['confidence']*100),'observation_dates':len(row['dates'])})
    messages=[{'role':'system','content':'You explain satellite crop classification evidence carefully and accurately.'},{'role':'user','content':prompt}]
    inputs=tokenizer.apply_chat_template(messages,add_generation_prompt=True,return_tensors='pt',return_dict=True).to(model.device)
    with torch.inference_mode():
        out=model.generate(**inputs,max_new_tokens=180,do_sample=False,pad_token_id=tokenizer.eos_token_id)
    answer=tokenizer.decode(out[0,inputs['input_ids'].shape[-1]:],skip_special_tokens=True).strip()
    row['summary']=answer
    row['explainerModel']=MODEL
    row['explanationMode']='cached local inference'
    row['uncertainty']='Uncalibrated model probability; small Maryland dataset; verify in the field.'
    raw.append({'id':row['id'],'model':MODEL,'text':answer})
    p.write_text(json.dumps(rows,indent=2))
    (ROOT/'artifacts/nemotron_generations.json').write_text(json.dumps(raw,indent=2))
    print('Explained',row['id'],flush=True)
(ROOT/'artifacts/nemotron_status.json').write_text(json.dumps({'status':'complete','model':MODEL,'mode':'local GPU inference, cached explanations','count':len(raw),'elapsed_seconds':time.time()-started,'revision':REVISION or getattr(model.config,'_commit_hash',None),'ground_truth_in_prompts':False},indent=2))
