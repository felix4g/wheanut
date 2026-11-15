"""Tests evidence boundaries and hosted API failures without an API key or spend."""
import json,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import explainer
class ExplainTests(unittest.TestCase):
    def setUp(self):self.result={'prediction':'Silage','confidence':.7,'season':2023,'ndvi':[.7,.3],'dates':['2023-08-01','2023-10-01'],'referenceLabel':'SECRET_LABEL'}
    def test_prompt_excludes_reference_label(self):
        text=json.dumps(explainer.messages_for(self.result,'What changed?'))
        self.assertNotIn('referenceLabel',text);self.assertNotIn('SECRET_LABEL',text);self.assertIn('What changed?',text)
    def test_hosted_call_has_fixed_destination(self):
        response=SimpleNamespace(status_code=200,ok=True,json=lambda:{'choices':[{'message':{'content':'Measured greenness declined; verify records.'}}]})
        calls=[]
        def post(*args,**kwargs):calls.append((args,kwargs));return response
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'TEST_ONLY_NOT_A_REAL_KEY','NVIDIA_MODEL':'nvidia/test'}),patch.dict(sys.modules,{'requests':SimpleNamespace(post=post)}):
            result=explainer.explain(self.result,'What changed?',provider='nvidia')
        self.assertEqual(calls[0][0][0],'https://integrate.api.nvidia.com/v1/chat/completions');self.assertNotIn('SECRET_LABEL',json.dumps(calls[0][1]['json']));self.assertIn('live NVIDIA',result['explanationMode'])
    def test_quota_is_explicit_error(self):
        with patch.dict(os.environ,{'NVIDIA_API_KEY':'TEST_ONLY_NOT_A_REAL_KEY','NVIDIA_MODEL':'nvidia/test'}),patch.dict(sys.modules,{'requests':SimpleNamespace(post=lambda *a,**k:SimpleNamespace(status_code=429,ok=False))}):
            with self.assertRaisesRegex(RuntimeError,'quota'):explainer.explain(self.result,provider='nvidia')
if __name__=='__main__':unittest.main()
