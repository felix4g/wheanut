"""Convert BARC GPKG labels to frontend GeoJSON. Does not train or predict.
Run in the team's geospatial Python environment, not in the browser.
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Path to BARC_Corn.2021-2023.gpkg')
    parser.add_argument('--output', default='barc-field-years.geojson')
    parser.add_argument('--repair-invalid', action='store_true', help='Apply Shapely make_valid to invalid geometries and record repairs in provenance')
    args = parser.parse_args()
    import geopandas as gpd
    from shapely.geometry import mapping
    gdf = gpd.read_file(args.input)
    if gdf.crs is None:
        raise ValueError('Input CRS is missing; confirm its actual CRS before conversion.')
    gdf = gdf.to_crs('EPSG:4326')
    columns = {str(c).lower(): c for c in gdf.columns}
    required = [f'corn_{year}' for year in (2021, 2022, 2023)]
    if any(c not in columns for c in required):
        raise ValueError(f'Expected Corn_2021/2022/2023 labels; found {list(gdf.columns)}')
    features = []
    counts = {}
    repaired = []
    for index, row in gdf.iterrows():
        geometry = row.geometry
        labeled = any(str(row[columns[f'corn_{year}']]).strip().capitalize() in ('Grain', 'Silage') for year in (2021, 2022, 2023))
        if not labeled:
            continue
        was_repaired = False
        if geometry is None or geometry.is_empty:
            raise ValueError(f'Labeled field {index} has missing geometry.')
        if not geometry.is_valid:
            if not args.repair_invalid:
                raise ValueError(f'Labeled field {index} has invalid geometry; inspect it or use --repair-invalid.')
            from shapely.validation import make_valid
            geometry = make_valid(geometry)
            if geometry.geom_type == 'GeometryCollection':
                from shapely.ops import unary_union
                geometry = unary_union([g for g in geometry.geoms if g.geom_type in ('Polygon', 'MultiPolygon')])
            if geometry.is_empty or not geometry.is_valid:
                raise ValueError(f'Could not repair labeled field {index}.')
            was_repaired = True
            repaired.append(str(index))
        if geometry.geom_type not in ('Polygon', 'MultiPolygon'):
            raise ValueError(f'Unexpected geometry type: {geometry.geom_type}')
        for year in (2021, 2022, 2023):
            value = row[columns[f'corn_{year}']]
            if value is None or str(value).strip().lower() in ('', 'nan', 'none', '<na>'):
                continue  # Unlabeled records are not negative examples.
            label = str(value).strip().capitalize()
            if label not in ('Grain', 'Silage'):
                raise ValueError(f'Unknown reference label {value!r} for field {index}, year {year}')
            counts[f'{year}-{label}'] = counts.get(f'{year}-{label}', 0) + 1
            features.append({'type': 'Feature', 'geometry': mapping(geometry), 'properties': {
                'id': f'BARC-{index}-{year}', 'name': f'BARC field {index}',
                'region': 'Beltsville, Maryland', 'season': year,
                'prediction': 'Pending', 'confidence': None, 'referenceLabel': label,
                'ndvi': [], 'dates': [], 'demo': False,
                'provenance': {
                    'sourceName': 'Provided BARC field polygons and reference labels',
                    'sourceURLs': ['https://doi.org/10.1002/agg2.20474',
                                   'https://doi.org/10.3390/s23208595',
                                   'https://doi.org/10.5281/zenodo.8087301'],
                    'sourceFile': Path(args.input).name,
                    'processing': 'Reprojected to WGS84; reshaped labeled field-years; blank labels excluded',
                    'geometryRepair': 'Shapely make_valid; original input unchanged' if was_repaired else 'None',
                    'acquisitionDates': f'Reference crop year {year}; no satellite imagery loaded'
                }
            }})
    output = Path(args.output)
    output.write_text(json.dumps({'type': 'FeatureCollection', 'features': features}), encoding='utf-8')
    print(f'Wrote {len(features)} labeled field-years to {output}')
    print(json.dumps(counts, indent=2))
    print('Repaired field indices:', repaired)
    print('Reference labels are not predictions. No evaluation or inference has been run.')


if __name__ == '__main__':
    main()
