import json,sys
from pathlib import Path
from run_analysis import analyze,validate_request
from explainer import explain
ROOT=Path(__file__).resolve().parents[1]
folder=Path(sys.argv[1]);request=json.loads((folder/'request.json').read_text())
try:
    if request.get('action')=='explain':
        rows=json.loads((ROOT/'artifacts/model_results.json').read_text());result=next((r.copy() for r in rows if r['id']==request.get('fieldId')),None)
        if result is None:raise ValueError('No saved report matches that field ID.')
        from shapely.geometry import shape
        if request.get('season')!=result['season'] or not shape(request.get('geometry',{})).equals(shape(result['geometry'])):raise ValueError('Field geometry or season changed; run a new analysis instead.')
        # Do not accept browser-supplied predictions, NDVI, confidence or labels.
        result.update(explain(result,request.get('question','')))
    else:
        validate_request(request)
        result=analyze(request,folder/'cache',lambda text:print(text,flush=True))
    output={'status':'complete','result':result}
except Exception as error:
    # Upstream request bodies/headers and local secrets are not included.
    output={'status':'error','error':str(error)[:400]}
(folder/'output.json').write_text(json.dumps(output,indent=2,allow_nan=False))
