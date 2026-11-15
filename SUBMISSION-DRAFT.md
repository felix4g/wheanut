# Wheanut

## One-line description
A map-based corn harvest classifier that pairs real satellite observations with locally generated NVIDIA Nemotron explanations.

## Problem and approach
Silage and grain harvests have different seasonal vegetation patterns, but those patterns are ambiguous. Our hypothesis is that seasonal NDVI features can help distinguish them while keeping uncertainty visible to the reviewer.

We use official BARC field-year reference labels, cloud-masked Sentinel-2 L2A observations from Planetary Computer, and balanced logistic regression. Features include monthly NDVI medians, peak greenness, seasonal decline and post-peak change. NVIDIA Nemotron-Mini-4B-Instruct generates plain-English interpretations locally on the team GPU without receiving reference labels. The website presents actual held-out predictions, cached Nemotron explanations, seasonal curves and review notes.

## Measured validation
44 labeled field-years across 34 unique Maryland fields, 2021–2023 (32 Grain, 12 Silage). Blank labels excluded. Each test year is held out, and all test fields are excluded from other training years too.

Confusion matrix (rows actual, columns predicted; Grain, Silage): [[21,11],[3,9]]. Accuracy 68.2%; balanced accuracy 70.3%. Grain precision/recall 87.5%/65.6%; Silage precision/recall 45.0%/75.0%. FPR: Grain 25.0%; Silage 34.4%. Always-Grain baseline: 72.7% accuracy, 50.0% balanced accuracy. Our model does not outperform that baseline on overall accuracy.

## What works
Interactive georeferenced map; field/year selection; 44 real reports; measured NDVI; Nemotron explanations; notes and review flags; custom boundary drawing; JSON/GeoJSON import; CSV/GeoJSON export; model evaluation and source links. Free static Cloudflare Pages hosting: https://wheanut.pages.dev.

## Limitations
Small Maryland dataset; uncalibrated probabilities; substantial false positives; no validated transfer to California; no harvest timing, yield or weather recommendations. Photos are illustrative. The public website serves cached reports, not live arbitrary-field inference or chat. New boundaries require imported observations/results or a teammate backend. Nemotron explanations are generated text, not additional measurements.

## Reproducibility and citations
See README.md, src/pipeline.py, src/local_nemotron.py, data/, artifacts/ and EVALUATION.ipynb. Satellite catalog queries, scenes, physical reflectance scaling and cloud masking are recorded in artifacts/provenance.json.

BARC publications: https://doi.org/10.1002/agg2.20474 and https://doi.org/10.3390/s23208595. Dataset: https://doi.org/10.5281/zenodo.8087301 and the USDA BARC Gridded Yield Data Archive, version 1. Satellite catalog: https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a. Model: https://huggingface.co/nvidia/Nemotron-Mini-4B-Instruct. Leaflet and OSM attribution included in the frontend; photo credits bundled.

## Team lead must complete before final submission
Confirm teammate names and contributions; merge any accepted teammate modules; inspect Keeboh's actual submission manifest and size exclusions; confirm deadline and required links; capture final demo/video if requested; have every teammate save their work before submitting. Final submission has not been performed.
