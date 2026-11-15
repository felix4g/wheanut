# Keeboh submission audit — Wheanut

Checked against the team's visible Keeboh starter kit on 2026-11-14:
- 02 - Submitting your work.md
- 03 - Read me.md
- README.md
- 01_Challenge/challenge_statement.md

## Overall status
The frontend now includes 44 genuine held-out classifier results and actual locally generated Nemotron explanations. Source, data, metrics, provenance and scripts are bundled in Wheanut-Release. Final team merge and submission-manifest review remain required; final submission has not been performed.

## Done in the frontend
- Map selection and drawing, saved notes and field review, JSON/GeoJSON imports, reports.
- Distinguishes sample predictions from actual results and Pending fields.
- Early vegetation decline is described as a clue, not ground truth.
- Polygon and MultiPolygon imports; season selector for field-year records.
- Reference labels are kept separate from model prediction and confidence.
- Provenance metadata survives JSON import / GeoJSON export and appears in CSV reports.
- No API credentials in frontend source.
- Local source, README and Agent handoff included in this package.

## Must do before the team lead submits
1. Upload AND extract this source package into the team GPU workspace, in a new directory such as `Wheanut_Frontend`. Keeboh copies saved workspace files; it never follows links. A public URL by itself does not archive the source. Confirm the extracted folder is present and listed by the submission manifest.
2. Keep https://wheanut.pages.dev as the demo URL in the submission answers, alongside actual source files in the workspace.
3. Model teammate: state a hypothesis; obtain public geospatial observations; record source URLs, acquisition dates, query parameters, resolution, processing level, cloud filters, preprocessing and feature definitions.
4. Use the provided BARC data in `04_Evaluation`. README reports 83 fields, 34 unique labeled fields, and 44 labeled field-years (32 Grain / 12 Silage) for 2021–2023. Recompute these counts from the actual file and explain any differences. Blank labels must be excluded, not labeled negative.
5. Validate on held-out year(s) or spatial groups when possible. Avoid using a purely random neighboring-field split as the only validation.
6. Save a confusion matrix, precision and recall for EACH class, evaluated counts by year/class, validation split design, errors, uncertainty and transfer limits. The event rubric also asks about false positive rate and response time. Frontend confidence values are not a substitute for these metrics.
7. Cite BARC publications/datasets if used or redistributed. DATA-SOURCES.md provides source pointers; complete real acquisition/provenance records.
8. Save all notebooks WITH outputs. Record runtime dependencies and reproducible commands; Keeboh does not copy the team's Python environment.
9. Keep keys in `.env`; do not paste secrets into saved notebooks or source.
10. Team lead: inspect the actual submission-page file list and size exclusions, stop running jobs, then submit by Nov 15 at 9:00 a.m. Pacific. Submission closes notebooks and ends the team's workspace access. Do not submit until everyone is finished.

## Unknown until the submission page is available
The project overview currently shows submission as Upcoming. Exact per-file and total submission-copy size limits were not shown in the pages inspected. The workspace guide says 10 GB workspace capacity; that is NOT evidence of the submission archive limit. Inspect the actual submission manifest later.

## BARC conversion helper
In an environment with geopandas and shapely installed:

    python Wheanut_Frontend/submission/prepare_barc.py \
      --input 04_Evaluation/BARC_Corn.2021-2023.gpkg \
      --output barc-field-years.geojson

Import that GeoJSON through Data & reports. Geometry and reference labels are real input; model predictions remain Pending. The helper was run against the actual team GPKG with --repair-invalid. It produced 44 labeled field-years (32 Grain / 12 Silage); 43 are MultiPolygon features, maximum ring size 381. Field index 81 was repaired with Shapely make_valid after reprojection, and this is recorded in provenance. The original GPKG was not modified. The converted file is in the team workspace under Wheanut-Frontend/submission/barc-field-years.geojson. No model was trained or evaluated by this check.

## Current implementation update
The independent pipeline has completed real Sentinel-2 collection, balanced logistic regression training, strict year-and-field evaluation, FPR and classifier timing, and 44 local Nemotron explanations. The public frontend adapter uses saved reports and explicitly does not claim live arbitrary-field inference. See SUBMISSION-DRAFT.md and artifacts/metrics.json in the release for measured results and limitations.
