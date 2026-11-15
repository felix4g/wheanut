import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_analysis import validate_request
ROOT=Path(__file__).resolve().parents[1]
class BoundaryTests(unittest.TestCase):
    def setUp(self):
        row=json.loads((ROOT/'data/field_years.json').read_text())[0]
        self.request={'fieldId':'NEW-TEST','season':2023,'geometry':row['geometry']}
    def test_valid_boundary_and_geometry_scoped_cache(self):
        from shapely.geometry import shape,mapping
        from shapely.affinity import scale
        one=validate_request(self.request);two=validate_request({**self.request,'geometry':json.loads(json.dumps(mapping(scale(shape(self.request['geometry']),.9,.9))))})
        self.assertNotEqual(one['fingerprint'],two['fingerprint'])
        self.assertNotEqual(one['fingerprint'],validate_request({**self.request,'season':2022})['fingerprint'])
    def test_incomplete_current_season(self):
        with self.assertRaisesRegex(ValueError,'completed'):validate_request({**self.request,'season':2026})
    def test_outside_training_region(self):
        with self.assertRaisesRegex(ValueError,'Beltsville'):validate_request({**self.request,'geometry':{'type':'Polygon','coordinates':[[[-121,38],[-120.99,38],[-120.99,38.01],[-121,38.01],[-121,38]]]}})
    def test_crossing_boundary(self):
        with self.assertRaises(ValueError):validate_request({**self.request,'geometry':{'type':'Polygon','coordinates':[[[-76.9,39],[-76.89,39.01],[-76.89,39],[-76.9,39.01],[-76.9,39]]]}})
if __name__=='__main__':unittest.main()
