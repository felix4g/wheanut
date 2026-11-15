"""Independent public-data harvest pipeline. No labels are inferred from NDVI.
Caches scene-level observations. Trains a small model from provided reference labels.
Never sends evaluation labels to Nemotron. No source dataset is modified.
"""
from __future__ import annotations
import argparse, json, os, time, hashlib, traceback, datetime, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config/project.json').read_text())
DATA=ROOT/'data'; OUT=ROOT/'artifacts'
for p in [DATA,OUT,DATA/'cache']: p.mkdir(parents=True,exist_ok=True)
def log(s): print(datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),s,flush=True)
def write_json(path,data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2,allow_nan=False,default=str));temp.replace(path)
def prepare(gpkg):
    import geopandas as gpd
    from shapely.validation import make_valid
    from shapely.geometry import mapping
    import pandas as pd
    fields=gpd.read_file(gpkg).to_crs(4326); records=[]; repairs=[]
    for idx,row in fields.iterrows():
        labels=[(year,str(row.get(f'Corn_{year}','')).strip().capitalize()) for year in CFG['years']]
        labels=[x for x in labels if x[1] in ['Silage','Grain']]
        if not labels: continue
        geom=row.geometry
        if geom is None or geom.is_empty:raise ValueError(f'Labeled field {idx} has no geometry')
        if not geom.is_valid:geom=make_valid(geom);repairs.append(str(idx))
        if geom.geom_type=='GeometryCollection':
            from shapely.ops import unary_union
            geom=unary_union([g for g in geom.geoms if g.geom_type in ['Polygon','MultiPolygon']])
        if geom.geom_type not in ['Polygon','MultiPolygon']:raise ValueError('Nonpolygon repair')
        oid=str(row.get('OBJECTID',idx)); name=str(row.get('FIELD',oid))
        for year,label in labels: records.append({'id':f'BARC-{oid}-{year}','field_id':oid,'name':f'BARC field {name}','year':year,'reference_label':label,'geometry':mapping(geom)})
    write_json(DATA/'field_years.json',records)
    summary={'records':len(records),'unique_fields':len(set(r['field_id'] for r in records)),'counts':pd.DataFrame(records).groupby(['year','reference_label']).size().to_dict(),'geometry_repairs_after_reprojection':repairs}
    summary['counts']={str(k):int(v) for k,v in summary['counts'].items()};write_json(OUT/'data_summary.json',summary);log(summary)
    return records

def select_scenes(records,year):
    from pystac_client import Client
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from collections import Counter
    cache=DATA/'cache'/f'catalog-{year}.json'
    if cache.exists():return json.loads(cache.read_text())
    geoms=unary_union([shape(r['geometry']) for r in records if r['year']==year]);bbox=list(geoms.bounds)
    log(f'Searching catalog {year}, bbox={bbox}')
    items=list(Client.open(CFG['catalog']).search(collections=[CFG['collection']],bbox=bbox,datetime=f'{year}-{CFG["start_month_day"]}/{year}-{CFG["end_month_day"]}',query={'eo:cloud_cover':{'lt':CFG['max_scene_cloud']}},max_items=500).items())
    # Prefer a tile covering the complete AOI; otherwise retain all intersecting tiles.
    covering=[i for i in items if shape(i.geometry).covers(geoms)]
    if covering: items=covering
    best={}
    for item in items:
        d=item.datetime.date().isoformat()
        score=item.properties.get('eo:cloud_cover',100)
        if d not in best or score<best[d].properties.get('eo:cloud_cover',100):best[d]=item
    ordered=sorted(best.values(),key=lambda i:i.datetime)
    if len(ordered)>CFG['max_scenes_per_year']:
        import numpy as np
        ordered=[ordered[i] for i in np.linspace(0,len(ordered)-1,CFG['max_scenes_per_year']).round().astype(int)]
    out=[i.to_dict() for i in ordered];write_json(cache,out);log(f'{year}: selected {len(out)} unique acquisition dates');return out

def scene_observations(item,records):
    import numpy as np,geopandas as gpd,rasterio,planetary_computer
    from rasterio.windows import from_bounds,transform as window_transform
    from rasterio.features import geometry_mask
    from rasterio.warp import reproject,Resampling
    import pystac
    date=item['properties']['datetime'][:10]; key=item['id']; cache=DATA/'cache'/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json')
    if cache.exists():return json.loads(cache.read_text())
    signed=planetary_computer.sign(pystac.Item.from_dict(item))
    # Construct geometry explicitly to avoid index alignment differences across geopandas versions.
    from shapely.geometry import shape
    frame=gpd.GeoDataFrame([{'field_id':r['field_id']} for r in records],geometry=[shape(r['geometry']) for r in records],crs=4326)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT=40,GDAL_HTTP_MAX_RETRY=2):
        with rasterio.open(signed.assets['B04'].href) as redsrc:
            projected=frame.to_crs(redsrc.crs); bounds=projected.total_bounds;win=from_bounds(*bounds,transform=redsrc.transform).round_offsets().round_lengths();
            if win.width*win.height>25000000:raise ValueError('AOI exceeds safe in-memory crop size')
            red=redsrc.read(1,window=win,boundless=True,fill_value=0).astype('float32');trans=window_transform(win,redsrc.transform);crs=redsrc.crs
        arrays={}
        for band in ['B08','SCL']:
            dest=np.zeros(red.shape,dtype='float32' if band=='B08' else 'uint8')
            with rasterio.open(signed.assets[band].href) as src:
                reproject(source=rasterio.band(src,1),destination=dest,src_transform=src.transform,src_crs=src.crs,dst_transform=trans,dst_crs=crs,resampling=Resampling.nearest)
            arrays[band]=dest
    nir=arrays['B08'];scl=arrays['SCL']
    # Read physical reflectance scale/offset from STAC where present. PC data uses quantized DN.
    def reflectance(band,arr):
        meta=item['assets'][band].get('raster:bands',[{}])[0]
        scale=meta.get('scale',0.0001);offset=meta.get('offset')
        if offset is None:
            baseline=float(item['properties'].get('s2:processing_baseline',0))
            offset=-0.1 if baseline>=4 else 0.0
        return arr*scale+offset,{'scale':scale,'offset':offset}
    rr,red_meta=reflectance('B04',red);nn,nir_meta=reflectance('B08',nir)
    valid=np.isin(scl,[4,5,6,7])&(red>0)&(nir>0)&(rr>=0)&(nn>=0)&((rr+nn)>0)
    ndvi=np.divide(nn-rr,nn+rr,out=np.zeros_like(nn),where=(nn+rr)>0)
    result=[]
    for r,geom in zip(records,projected.geometry):
        inside=geometry_mask([geom.__geo_interface__],out_shape=red.shape,transform=trans,invert=True)
        count=int(inside.sum());use=inside&valid;fraction=float(use.sum()/count) if count else 0
        if count>=4 and fraction>=CFG['minimum_valid_fraction']:
            value=float(np.median(ndvi[use]));
            if -1<=value<=1:result.append({'field_id':r['field_id'],'date':date,'ndvi':value,'valid_fraction':fraction,'pixels':int(use.sum()),'scene_id':key})
    payload={'scene_id':key,'date':date,'collection':CFG['collection'],'catalog':CFG['catalog'],'cloud_cover':item['properties'].get('eo:cloud_cover'),'red_transform':red_meta,'nir_transform':nir_meta,'acquired_at':item['properties']['datetime'],'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observations':result}
    write_json(cache,payload);return payload

def collect(records):
    import pandas as pd
    all_obs=[];provenance=[];errors=[]
    for year in CFG['years']:
        group=list({r['field_id']:r for r in records if r['year']==year}.values());items=select_scenes(records,year)
        with ThreadPoolExecutor(max_workers=3) as pool:
            tasks={pool.submit(scene_observations,item,group):item for item in items}
            for done in as_completed(tasks):
                item=tasks[done]
                try:
                    payload=done.result();all_obs.extend(payload['observations']);provenance.append({k:v for k,v in payload.items() if k!='observations'});log(f'{item["id"]}: {len(payload["observations"])} fields')
                except Exception as e:errors.append({'scene':item['id'],'error':str(e)[:300]});log(f'Scene failed {item["id"]}: {str(e)[:150]}')
        pd.DataFrame(all_obs).to_parquet(DATA/'observations.parquet',index=False)
        write_json(OUT/'provenance.json',{'config':CFG,'scenes':provenance,'errors':errors,'spatial_resolution_m':10,'SCL_resampled_from_m':20,'SCL_valid_classes':[4,5,6,7],'processing':'field median of valid surface-reflectance NDVI; no true label used'})
    if not all_obs:raise RuntimeError('No usable satellite observations. Read artifacts/provenance.json; do not train from invented data.')
    return pd.DataFrame(all_obs)

def features_for(frame,year):
    import numpy as np,pandas as pd
    frame=frame.drop_duplicates('date').sort_values('date');t=pd.to_datetime(frame.date);v=frame.ndvi.to_numpy();d=t.dt.dayofyear.to_numpy();months=t.dt.month.to_numpy()
    if len(v)<CFG['minimum_observations']:return None
    f={'n_obs':len(v),'peak_ndvi':float(v.max()),'peak_doy':int(d[v.argmax()]),'ndvi_std':float(v.std())}
    for month in range(6,12):f[f'ndvi_month_{month}']=float(np.median(v[months==month])) if np.any(months==month) else np.nan
    late=v[months>=9];early=v[months<=8]
    f['late_median']=float(np.median(late)) if len(late) else np.nan;f['early_median']=float(np.median(early)) if len(early) else np.nan
    f['early_late_drop']=f['early_median']-f['late_median'];slopes=np.diff(v)/np.maximum(np.diff(d),1);after=(d[1:]>=210)&(d[1:]<=330)
    f['steepest_decline']=float(slopes[after].min()) if after.any() else np.nan
    f['decline_doy']=int(d[1:][after][slopes[after].argmin()]) if after.any() else np.nan
    f['post_peak_drop']=float(v.max()-np.median(late)) if len(late) else np.nan
    return f

def train(records,obs):
    import numpy as np,pandas as pd,joblib
    from sklearn.pipeline import make_pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import confusion_matrix,classification_report
    rows=[];skipped=[]
    obs['date']=pd.to_datetime(obs.date).dt.strftime('%Y-%m-%d')
    for r in records:
        o=obs[(obs.field_id.astype(str)==r['field_id'])&obs.date.str.startswith(str(r['year']))]
        f=features_for(o,r['year'])
        if f is None:skipped.append(r['id']);continue
        rows.append({**{k:r[k] for k in ['id','field_id','year','reference_label']},**f})
    table=pd.DataFrame(rows);table.to_parquet(DATA/'features.parquet',index=False)
    if len(table)<12 or table.reference_label.nunique()<2:raise RuntimeError('Insufficient labeled observations to train honestly.')
    columns=[c for c in table.columns if c not in ['id','field_id','year','reference_label']]
    # Counts are data-quality diagnostics, not predictors; avoid learning availability artifacts.
    columns=[c for c in columns if c!='n_obs'];X=table[columns];y=table.reference_label
    oof=[];folds=[]
    def model():return make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),LogisticRegression(C=0.5,class_weight='balanced',max_iter=2000,random_state=42))
    for year in sorted(table.year.unique()):
        test=table.year==year
        # Strict year AND field holdout: remove all instances of test fields from training.
        hold_fields=set(table.loc[test,'field_id']);train_mask=(~test)&(~table.field_id.isin(hold_fields))
        if train_mask.sum()<6 or y[train_mask].nunique()<2:raise RuntimeError(f'Year {year}: insufficient independent training fields for strict holdout.')
        m=model();m.fit(X[train_mask],y[train_mask]);started=time.perf_counter();prob=m.predict_proba(X[test]);latency=(time.perf_counter()-started)/int(test.sum());classes=list(m.classes_)
        for (_,r),p in zip(table[test].iterrows(),prob):
            idx=int(np.argmax(p));oof.append({'id':r.id,'field_id':r.field_id,'year':int(r.year),'reference_label':r.reference_label,'prediction':classes[idx],'confidence':float(p[idx]),'silage_probability':float(p[classes.index('Silage')]),'response_time_seconds':latency})
        folds.append({'held_out_year':int(year),'train_records':int(train_mask.sum()),'test_records':int(test.sum()),'training_fields':sorted(set(table.loc[train_mask,'field_id'])),'held_out_fields':sorted(hold_fields),'field_overlap':0})
    pred=pd.DataFrame(oof);pred.to_csv(OUT/'heldout_predictions.csv',index=False)
    cm=confusion_matrix(pred.reference_label,pred.prediction,labels=['Grain','Silage']);report=classification_report(pred.reference_label,pred.prediction,labels=['Grain','Silage'],output_dict=True,zero_division=0)
    fpr={}
    for i,label in enumerate(['Grain','Silage']):
        fp=int(cm[:,i].sum()-cm[i,i]);neg=int(cm.sum()-cm[i,:].sum());fpr[label]=fp/neg if neg else None
    metrics={'evaluation':'strict leave-one-year-out with all held-out fields excluded from training in every year','class_order':['Grain','Silage'],'confusion_matrix':cm.tolist(),'classification_report':report,'false_positive_rate':fpr,'folds':folds,'evaluated_counts':{str(k):int(v) for k,v in pred.groupby(['year','reference_label']).size().items()},'skipped_low_observation_ids':skipped,'feature_columns':columns,'limitations':['Small Maryland BARC dataset; not validated for California or other regions.','Satellite gaps and field-level mixed pixels can affect timing features.','Probabilities are uncalibrated model estimates, not guarantees.','Same field never appears on both sides of any evaluation split.','Nemotron explains predictions; it does not supply ground truth or measured classifier metrics.']}
    write_json(OUT/'metrics.json',metrics);final=model().fit(X,y);joblib.dump({'model':final,'features':columns,'config':CFG},OUT/'classifier.joblib')
    results=[]
    lookup={r['id']:r for r in records}
    for p in oof:
        r=lookup[p['id']];o=obs[(obs.field_id.astype(str)==r['field_id'])&obs.date.str.startswith(str(r['year']))].drop_duplicates('date').sort_values('date')
        results.append({'id':r['id'],'name':r['name'],'region':'Beltsville, Maryland','season':r['year'],'geometry':r['geometry'],'prediction':p['prediction'],'confidence':p['confidence'],'referenceLabel':r['reference_label'],'ndvi':o.ndvi.tolist(),'dates':o.date.tolist(),'demo':False,'summary':'Trained harvest classifier result from held-out-year and held-out-field evaluation.','evidence':[f'Actual cloud-masked Sentinel-2 observations: {len(o)} dates.','Prediction produced without this field or this year in training.'],'provenance':{'sourceName':'Sentinel-2 L2A / Planetary Computer + BARC reference labels','sourceURLs':[CFG['catalog'],'https://doi.org/10.1002/agg2.20474'],'acquisitionDates':f'{r["year"]}-06-01 through {r["year"]}-11-30','validation':'held-out year and field; no reference label sent to explainer','classification_model':'balanced logistic regression on seasonal features'}})
    write_json(OUT/'model_results.json',results);log('Training/evaluation complete. '+json.dumps(report));return results

def explain(results,limit=None):
    import requests
    key=os.environ.get('NVIDIA_API_KEY','')
    if not key:
        env=Path('/workspace/.env')
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip().startswith('NVIDIA_API_KEY='):key=line.partition('=')[2].strip().strip('"').strip("'")
    if not key:write_json(OUT/'nemotron_status.json',{'status':'missing_key','model':CFG['nemotron_model'],'note':'Set NVIDIA_API_KEY in /workspace/.env; never source code.'});log('Nemotron key missing; trained results retained without a fabricated explanation.');return
    targets=results[:limit] if limit else results;success=0;errors=[]
    for r in targets:
        cache=DATA/'cache'/('nemotron-'+r['id']+'.json')
        if cache.exists():payload=json.loads(cache.read_text())
        else:
            # Deliberately exclude referenceLabel and geometry; only public observation summary is transmitted.
            evidence={'field_id':r['id'],'season':r['season'],'prediction':r['prediction'],'model_probability':r['confidence'],'observation_dates':r['dates'],'ndvi':r['ndvi'],'method':'held-out year and field logistic regression; uncalibrated; Maryland only'}
            prompt='Explain this trained corn-harvest classifier result for a farmer. Do not change the prediction or invent observations. Return JSON only with summary (max 70 words), evidence (3 short strings), uncertainty (one sentence). Mention alternative causes such as clouds/weather and no harvest-timing advice. Data: '+json.dumps(evidence)
            try:
                response=requests.post('https://integrate.api.nvidia.com/v1/chat/completions',headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},json={'model':CFG['nemotron_model'],'messages':[{'role':'system','content':'You explain real remote-sensing model results faithfully. Output a JSON object only. Do not infer or reveal reference labels.'},{'role':'user','content':prompt}],'temperature':0.2,'max_tokens':700,'stream':False},timeout=90)
                response.raise_for_status();body=response.json();text=body['choices'][0]['message']['content'];text=text[text.find('{'):text.rfind('}')+1];payload=json.loads(text)
                if not isinstance(payload.get('summary'),str) or not isinstance(payload.get('evidence'),list):raise ValueError('Invalid explanation JSON')
                payload['explainer_model']=CFG['nemotron_model'];write_json(cache,payload)
            except Exception as e:errors.append({'id':r['id'],'error':type(e).__name__});log('Nemotron explanation failed for '+r['id']+' ('+type(e).__name__+')');continue
        r.update({k:payload[k] for k in ['summary','evidence','uncertainty'] if k in payload});r['explainerModel']=payload['explainer_model'];success+=1;write_json(OUT/'model_results.json',results)
    write_json(OUT/'nemotron_status.json',{'status':'complete' if success==len(targets) else 'partial','model':CFG['nemotron_model'],'explained':success,'requested':len(targets),'errors':errors});log(f'Nemotron explanations: {success}/{len(targets)}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['all','prepare','collect','train','explain']);ap.add_argument('--gpkg',default='/workspace/04_Evaluation/BARC_Corn.2021-2023.gpkg');ap.add_argument('--explain-limit',type=int);a=ap.parse_args()
    records=prepare(a.gpkg) if a.stage in ['all','prepare'] else json.loads((DATA/'field_years.json').read_text())
    if a.stage=='prepare':return
    if a.stage in ['all','collect']:obs=collect(records)
    if a.stage=='collect':return
    if a.stage in ['all','train']:
        import pandas as pd
        if a.stage=='train':obs=pd.read_parquet(DATA/'observations.parquet')
        results=train(records,obs)
    elif a.stage=='explain':results=json.loads((OUT/'model_results.json').read_text())
    if a.stage in ['all','explain']:explain(results,a.explain_limit)
if __name__=='__main__':
    try:main()
    except Exception:log('PIPELINE FAILED; see traceback, no fabricated fallback.');traceback.print_exc();sys.exit(1)
