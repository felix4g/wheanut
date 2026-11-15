"""End-to-end private-loopback test. Reads only the separate backend token."""
import json,time,sys
from pathlib import Path
import requests
from shapely.geometry import shape,mapping
from shapely.affinity import scale
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8767'
token=Path('/tmp/wheanut-live-runtime/.api-token').read_text().strip()
headers={'Authorization':'Bearer '+token}
assert requests.get(BASE+'/api/jobs/nope',timeout=10).status_code==401
assert requests.get(BASE+'/api/health',headers={'Authorization':'Bearer invalid'},timeout=10).status_code==401
assert requests.get(BASE+'/src/server.py',timeout=10).status_code==404
assert requests.get(BASE+'/.env',timeout=10).status_code==404
print('PASS: unauthenticated API, wrong tokens and source/secret paths rejected.',flush=True)
row=json.loads((ROOT/'data/field_years.json').read_text())[0]
geometry=mapping(scale(shape(row['geometry']),.85,.85,origin='centroid'))
request={'action':'analyze','fieldId':'LIVE-INSET-QA-2023','fieldName':'Research boundary inset (live QA)','season':2023,'geometry':geometry,'question':'What do the observations support, and what should I verify?'}
response=requests.post(BASE+'/api/jobs',headers=headers,json=request,timeout=10);assert response.status_code==202,response.status_code
job=response.json();deadline=time.time()+500
while time.time()<deadline:
    status=requests.get(BASE+'/api/jobs/'+job['jobId'],headers=headers,timeout=10).json()
    if status['status']=='complete':
        result=status['result'];assert result['prediction'] in ['Grain','Silage'];assert len(result['ndvi'])==len(result['dates'])>=6;assert result['explanationMode'].startswith('live');assert result['summary'];assert 'held-out evaluation result' in result['evidence'][1]
        (ROOT/'artifacts/live_smoke_result.json').write_text(json.dumps(result,indent=2))
        print('PASS: actual new-boundary satellite collection, classifier inference and real Nemotron explanation.',flush=True)
        print('Observation dates:',len(result['dates']),'Prediction:',result['prediction'],'Seconds:',round(result['responseTimeSeconds'],1),'Explainer:',result['explainerModel'],flush=True)
        break
    if status['status']=='error':raise RuntimeError(status['error'])
    time.sleep(2)
else:raise TimeoutError('Live smoke test exceeded eight minutes')
