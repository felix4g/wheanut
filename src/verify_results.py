"""Audit persisted evidence without downloading imagery or needing a GPU."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'artifacts/model_results.json').read_text())
m=json.loads((root/'artifacts/metrics.json').read_text())
s=json.loads((root/'artifacts/nemotron_status.json').read_text())
assert len(rows)==44 and len({r['id'] for r in rows})==44
labels=m['class_order'];matrix=[[0,0],[0,0]]
for r in rows:
    assert len(r['dates'])==len(r['ndvi'])>=6
    assert all(-1<=v<=1 for v in r['ndvi'])
    assert r['dates']==sorted(r['dates'])
    assert 0<=r['confidence']<=1
    assert r['explainerModel']=='nvidia/Nemotron-Mini-4B-Instruct'
    matrix[labels.index(r['referenceLabel'])][labels.index(r['prediction'])]+=1
assert matrix==m['confusion_matrix']
for fold in m['folds']:
    assert not set(fold['training_fields']) & set(fold['held_out_fields'])
assert s['status']=='complete' and s['count']==len(rows) and not s['ground_truth_in_prompts']
assert all(x not in m['feature_columns'] for x in ['referenceLabel','reference_label','year','field_id'])
print('PASS: 44 real field-year records; aligned observations; reproduced confusion matrix; disjoint held-out fields; Nemotron completed without ground-truth prompts.')
print('Accuracy:',m['classification_report']['accuracy'],'; majority-class baseline:',32/44)
