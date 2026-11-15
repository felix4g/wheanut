# Verification — 2026-11-14

Passed `python src/verify_results.py`: 44 unique field-year records, chronological matching observations, physical NDVI bounds, reproduced confusion matrix, nonoverlapping train/test field IDs, labels excluded from feature columns, and complete Nemotron outputs.

Passed frontend checks: `node tests/check-map.cjs`, `node tests/check-ai.cjs`, `node tests/check-trained.cjs`. Checks cover malformed imports, crossing polygons, duplicate IDs, invalid confidence, real geometry loading, agent failures/recovery, exclusion of reference labels from requests, cached report labeling, and rejection of cached output after a boundary changes.

Browser verified: real BARC map, seasonal selection, map-to-report navigation, model report and Nemotron text, measured evaluation tables, and responsive layout at the available viewport. Existing boundary drawing/persistence was verified in the prior frontend pass. Date positions in the NDVI chart now use actual acquisition intervals.

EVALUATION.ipynb was executed in Keeboh and saved with genuine outputs. Cloudflare reported a successful Production deployment; the public website was opened and a real Nemotron report was verified.

Remaining limits: no live arbitrary-field GPU inference on the public website; no calibrated confidence; no validated transfer beyond this small Maryland dataset. Keeboh final submission and teammate merge are pending.
