# Live extension

See DEPLOYMENT.md and LIVE-BACKEND.md for the live Python backend and protected Cloudflare Nemotron API. The original reproducibility and held-out evaluation below remain applicable.

# Wheanut Independent — real training + Nemotron

This project is independent of teammates' working notebooks. Outputs can later replace or merge with their model and service adapters.

## Run in the team workspace

    cd /workspace/Wheanut-Live-Final
    python -m venv --system-site-packages .venv
    mkdir -p artifacts data/cache
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python src/pipeline.py all --explain-limit 3

Use existing /workspace/04_Evaluation/BARC_Corn.2021-2023.gpkg. No source GPKG or teammate file is changed. Dependencies are installed into the independent venv, without --user or upgrading the team environment.

Stages can also run separately: prepare, collect, train, explain. Use --explain-limit to control the number of hosted Nemotron calls. The existing NVIDIA_API_KEY is read from the environment or /workspace/.env and never printed, copied into source, or included in the browser.

## Pipeline
1. Prepare field-year rows using actual BARC reference labels. Blank labels excluded.
2. Query public Planetary Computer Sentinel-2 L2A scenes, June–November 2021–2023.
3. Crop only the field AOI, mask SCL, calculate per-field median NDVI. Cache each date's observations. Use STAC physical-reflectance scale/offset with a documented processing-baseline fallback.
4. Train balanced logistic regression on seasonal NDVI features. Evaluate held-out years with all testing fields excluded from training in other years too.
5. Save held-out predictions, confusion matrix, both classes' precision/recall, false positive rates, year/class counts, split details and inference timing.
6. Call an actual NVIDIA Nemotron model to explain predictions and uncertainty. Reference labels are excluded from prompts. Failures do not generate fake explanations.

## Artifacts
- data/field_years.json
- data/observations.parquet and data/features.parquet
- artifacts/provenance.json, metrics.json, heldout_predictions.csv
- artifacts/classifier.joblib (model trained on all available labeled observations after honest held-out evaluation)
- artifacts/model_results.json (frontend-format real held-out results)
- artifacts/nemotron_status.json

## Data and limits
BARC dataset references: https://doi.org/10.1002/agg2.20474 and https://doi.org/10.3390/s23208595; dataset https://doi.org/10.5281/zenodo.8087301. Cite the provided starter README's dataset archive too.

Scene count caps, valid-pixel fraction, observation minimum, features and train configuration are recorded. Model probability is uncalibrated. No generalization beyond the small Maryland evaluation dataset is claimed. No fabricated satellite observations or performance values are used. Do not treat a decline in NDVI as ground truth.

## No NVIDIA API key: local Nemotron

The optional `src/local_nemotron.py` runs the official NVIDIA Nemotron-Mini-4B-Instruct model on a CUDA GPU. Install torch, transformers, accelerate and sentencepiece in the independent venv, then run `.venv/bin/python src/local_nemotron.py`. Weights are cached under `/tmp/wheanut-nemotron-cache`, outside the submission workspace. Explanations are generated from classifier predictions and observed NDVI only; reference labels are excluded. These are cached reports, not a public live inference service. Review the status file for actual completion.

## Initial held-out performance

44 field-year records: accuracy 68.2%, balanced accuracy 70.3%; Silage recall 75.0%, precision 45.0%. Always predicting Grain gives 72.7% accuracy and 50.0% balanced accuracy. This initial classifier does not beat the majority baseline on overall accuracy. Its ability to detect Silage comes with substantial false positives; field verification remains necessary.

## Complete release

Frontend: `frontend/`. Run `python3 -m http.server 8766 --bind 127.0.0.1 --directory frontend` and open http://127.0.0.1:8766.

Audit saved evidence: `python src/verify_results.py`. Frontend checks from this folder: `node tests/check-map.cjs`, `node tests/check-ai.cjs`, `node tests/check-trained.cjs`.

Cached observations and features are included as Parquet. `python src/pipeline.py train` can retrain without downloading imagery, but it overwrites result explanations; run `python src/local_nemotron.py` afterwards to regenerate them. The final classifier.joblib is fit on all 44 records for future inference; displayed evaluation predictions are independently held out.

`DEMO-SCRIPT.md` and `SUBMISSION-DRAFT.md` are prepared for team review. No final hackathon submission has been made. Teammate directories are not changed by this release.

The exact installed package versions observed at packaging are in requirements-lock.txt. The local Nemotron model revision is pinned in config/project.json. GPU weights and virtual environments are intentionally excluded; they are not needed to view the bundled static reports.
