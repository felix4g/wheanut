"""Single isolated field analysis. Each job gets its own geometry/season cache."""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def validate_request(request):
    from shapely.geometry import shape,mapping
    if not isinstance(request,dict):raise ValueError('Request must be an object.')
    year=request.get('season')
    if type(year) is not int or year not in range(2021,2026):raise ValueError('Use a completed June–November season from 2021 to 2025.')
    geometry=request.get('geometry')
    if not isinstance(geometry,dict) or geometry.get('type') not in ['Polygon','MultiPolygon']:raise ValueError('A WGS84 Polygon or MultiPolygon is required.')
    # Bound work before geometry construction, including nested coordinate counts.
    flat=[]
    def coordinates(value):
        if not isinstance(value,list):raise ValueError('Coordinates must be arrays.')
        if len(value)>=2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in value[:2]):
            if len(value)!=2 or not all(math.isfinite(v) for v in value):raise ValueError('Coordinates must be finite [longitude, latitude] pairs.')
            flat.append(value)
            if len(flat)>2500:raise ValueError('Boundary is too detailed; simplify it first.')
        else:
            if len(value)>501:raise ValueError('Use at most 500 corners per ring.')
            for child in value:coordinates(child)
    coordinates(geometry.get('coordinates'))
    geom=shape(geometry)
    if geom.is_empty or not geom.is_valid:raise ValueError('Boundary must be nonempty and valid, without crossing edges.')
    west,south,east,north=geom.bounds
    if not (-77.1<=west<east<=-76.6 and 38.8<=south<north<=39.2):raise ValueError('This research model supports the Beltsville, Maryland area only; transfer elsewhere is not validated.')
    if east-west>.08 or north-south>.08 or geom.area<1e-8:raise ValueError('Use one field boundary with a bounding box smaller than 0.08 degrees.')
    fingerprint=hashlib.sha256((geom.normalize().wkb_hex+str(year)).encode()).hexdigest()[:24]
    return {'fieldId':str(request.get('fieldId','NEW-FIELD'))[:100],'fieldName':str(request.get('fieldName','New field'))[:80],'season':year,'geometry':mapping(geom),'question':str(request.get('question',''))[:1000],'fingerprint':fingerprint}

def analyze(request,job_dir,progress=lambda message:None):
    import pandas as pd,joblib
    import pipeline
    from shapely.geometry import shape
    from explainer import explain
    req=validate_request(request);started=time.perf_counter();job_dir=Path(job_dir)
    # pipeline caches normally index scene/year only. Isolate by boundary+season so
    # observations from another polygon can never be reused for a new field.
    pipeline.DATA=job_dir/req['fingerprint'];pipeline.OUT=pipeline.DATA/'artifacts'
    (pipeline.DATA/'cache').mkdir(parents=True,exist_ok=True);pipeline.OUT.mkdir(exist_ok=True)
    pipeline.CFG={**pipeline.CFG,'years':[req['season']]}
    record={'id':req['fieldId'],'field_id':req['fingerprint'],'year':req['season'],'geometry':req['geometry']}
    progress('Searching public Sentinel-2 scenes and collecting cloud-masked observations')
    observations=pipeline.collect([record]);observations=observations.drop_duplicates('date').sort_values('date')
    features=pipeline.features_for(observations,req['season'])
    if features is None:raise ValueError('Not enough valid observations to classify this field. Try another season or verify the boundary.')
    bundle=joblib.load(ROOT/'artifacts/classifier.joblib')
    values=pd.DataFrame([{k:features.get(k,float('nan')) for k in bundle['features']}])
    probabilities=bundle['model'].predict_proba(values)[0];classes=list(bundle['model'].classes_);best=int(probabilities.argmax())
    training=json.loads((ROOT/'data/field_years.json').read_text());geom=shape(req['geometry'])
    overlaps=any(geom.intersection(shape(r['geometry'])).area/geom.area>.1 for r in training)
    result={'id':req['fieldId'],'name':req['fieldName'],'region':'Beltsville, Maryland','season':req['season'],'prediction':classes[best],'confidence':float(probabilities[best]),'geometry':req['geometry'],'dates':observations.date.astype(str).tolist(),'ndvi':observations.ndvi.astype(float).tolist(),'demo':False,'evidence':[f'Actual cloud-masked Sentinel-2 observations: {len(observations)} dates.','Prediction from the final trained classifier; this is not a held-out evaluation result.'],'uncertainty':'Uncalibrated score; small Maryland dataset. Verify imagery and field records.','provenance':{'sourceName':'Sentinel-2 L2A / Planetary Computer','sourceURLs':['https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a'],'acquisitionDates':f"{req['season']}-06-01 through {req['season']}-11-30",'classification_model':'Final balanced logistic regression fitted on 44 BARC records','training_area_overlap':overlaps,'validation':'New deployment inference, not an independent test score','cache_scope':'normalized geometry + season'}}
    if overlaps:result['uncertainty']+=' This boundary overlaps a training field; do not count this inference as independent validation.'
    progress('Generating a real Nemotron explanation')
    result.update(explain(result,req['question']))
    result['responseTimeSeconds']=time.perf_counter()-started
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--output',required=True);parser.add_argument('--cache',required=True);args=parser.parse_args()
    def progress(message):print(message,flush=True)
    try:
        result=analyze(json.loads(Path(args.request).read_text()),args.cache,progress)
        Path(args.output).write_text(json.dumps({'status':'complete','result':result},indent=2,allow_nan=False))
    except Exception as error:
        # Record safe failures; never turn them into invented predictions.
        Path(args.output).write_text(json.dumps({'status':'error','error':str(error)[:400]},indent=2));sys.exit(1)
