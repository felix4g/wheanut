# Sources and reproducibility record

## Public map basemap
- Provider: OpenStreetMap contributors, https://www.openstreetmap.org/copyright
- Tiles: https://tile.openstreetmap.org/{z}/{x}/{y}.png
- This is a navigation basemap, NOT satellite imagery or harvest ground truth.
- Client library: Leaflet 1.9.4; license bundled under dist/vendor/.

## Current dataset
- 44 actual BARC field-year records, 34 unique labeled Maryland fields, 2021–2023.
- Real Sentinel-2 L2A cloud-masked field median NDVI, accessed through Planetary Computer.
- Complete query, scene and scale/offset records are in artifacts/provenance.json of the independent pipeline.
- Legacy sample data exist only as an explicitly labeled offline UI fallback.

## BARC references from the provided starter README
Publications:
- Dulaney et al. (2024), Development of a gridded yield data archive for farm management and research at the USDA Beltsville Agricultural Research Center. https://doi.org/10.1002/agg2.20474
- Kraatz et al. (2023), Comparing NISAR (Using Sentinel-1), USDA/NASS CDL, and Ground Truth Crop/Non-Crop Areas in an Urban Agricultural Region. https://doi.org/10.3390/s23208595
Datasets:
- USDA BARC Gridded Yield Data Archive, version 1. https://agdatacommons.nal.usda.gov/articles/dataset/USDA_Beltsville_Agricultural_Research_Center_BARC_Gridded_Yield_Data_Archive_version_1/28950746
- Kraatz (2023), Validating NISAR's cropland mapping approach and the USDA/NASS Cropland Data Layer against ground truth data in a fragmented urban agricultural region, v1.0.0. https://doi.org/10.5281/zenodo.8087301

## To complete for each ACTUAL imagery/weather source
Source name and URL:
Acquisition dates and AOI:
Download/access date and query parameters:
Spatial/temporal resolution and processing level:
Cloud/quality filters:
Preprocessing and derived features:
Dependencies and command/notebook:
Known limitations and license/citation:

Do not fill these fields with invented values. Store real records in the modeling workflow and optional frontend `provenance` metadata.
