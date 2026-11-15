# BARC conversion check

Verified against the actual team GPKG in Keeboh.

| Year | Grain | Silage |
| --- | ---: | ---: |
| 2021 | 14 | 4 |
| 2022 | 3 | 4 |
| 2023 | 15 | 4 |
| Total | 32 | 12 |

44 labeled field-years, 43 MultiPolygon features; maximum ring size 381. Predictions remain Pending. Field index 81 required Shapely make_valid after reprojection; the repair is recorded in feature provenance and the original input was unchanged. Generated GeoJSON is in the team workspace at Wheanut-Frontend/submission/barc-field-years.geojson. It is not included in the local source ZIP. This was a format check, not model training or evaluation.
