# Integration for the team's AI Agent

The frontend serves real, pre-generated classifier results and Nemotron explanations through trained-data.js. That adapter can be replaced without changing the map or report UI. It does not call a live model service yet. Keep API credentials on a backend, never in these static files.

## Selected field

```js
const field = window.Wheanut.getSelectedField();
const all = window.Wheanut.getFields();
const geojson = window.Wheanut.getGeoJSON();
```

A field contains:
- `id`, `name`, `region`, `season`
- `geometry`: GeoJSON Polygon or MultiPolygon in WGS84 [longitude, latitude] order (closed rings; up to 500 corners per ring)
- `prediction`: `Pending`, `Silage` or `Grain`
- `confidence`: 0–1, or null while Pending
- `ndvi`: values from -1 to 1; `dates`: matching string labels
- `demo`, `checked`, `note`

The frontend dispatches `wheanut:field-selected` when a selection changes or a new boundary is saved. `event.detail` is a copy of the selected field. The initial selection is available from `getSelectedField()`.

## Return results

```js
window.Wheanut.applyResults([
  {
    id: 'WH-001',
    prediction: 'Silage',
    confidence: 0.84,
    season: 2026,
    dates: ['2026-07-01', '2026-08-01', '2026-09-01'],
    ndvi: [0.78, 0.72, 0.23]
  }
]);
```

IDs must match existing fields. applyResults validates all updates before changing the dataset, preserves an existing geometry when one is not supplied, marks updates as real (demo=false), refreshes the interface and persists locally. Only use real model output here; a confidence number is not a measured evaluation score. Call getSelectedField again if the user changed selection while a request was running.

## File handoff

Import predictions as a JSON array in Data & reports. Import boundaries as a GeoJSON FeatureCollection with the same keys in each feature's properties. Missing predictions default to Pending. Matching IDs are replaced; other fields stay in the workspace. Export before replacing fields if prior notes must be retained. Limits: 2 MB per file and 200 workspace fields. The downloadable sample.json shows a boundary without invented predictions.

## Future backend

The teammate should own endpoint selection, authentication, loading/error/retry behavior and model evaluation. Assistant chat remains visibly disconnected until that work is completed. Public geospatial data and dates should accompany the actual model outputs. No live satellite retrieval is implemented by this frontend.

## Competition compatibility
Use one unique ID per field-year, e.g. BARC-12-2021. Set season to the actual crop year. Keep referenceLabel (Grain/Silage) separate from prediction; a reference label must never be copied into prediction to simulate inference. Optional provenance metadata is retained in reports and exports. See submission/KEEBOH-CHECKLIST.md for actual evaluation and archive requirements.

## Prominent AI Analysis homepage

The default view is now AI Analysis. The homepage includes field selection, a question box, analysis submission, a result panel, and clearly labeled sample preview. Map and field details link back to this central flow.

To connect the teammate's backend without editing the UI code:

```js
window.Wheanut.connectAgent(async (request, { signal }) => {
  // Call your own backend here. Keep secrets on the server.
  // Return the JSON response matching the schema below.
  const response = await fetch('/YOUR_BACKEND_ENDPOINT', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal
  });
  if (!response.ok) throw new Error('Analysis service unavailable');
  return response.json();
});
```

A cached adapter is configured by trained-data.js. Register your live handler after it has finished loading, or omit trained-data.js when deploying your own backend. No live endpoint is called by default. Configure your actual endpoint, CORS and server-side credentials in the teammate's integration file. Do not deploy the placeholder path as a working endpoint.

Request: `fieldId`, `fieldName`, WGS84 `geometry`, `season`, `region`, `isSampleBoundary`, `question`. Ground-truth reference labels are deliberately excluded.

Required response: `prediction` (`Grain` or `Silage`), `confidence` (0–1).
Optional response: `summary` (string), `evidence` (string array), `uncertainty` (string), `ndvi`/`dates` (matching arrays), `provenance` (object).

The UI handles pending connection, loading, success, invalid response and service error states. Requests time out after 90 seconds. A failed request does not write a result. Successful results preserve the field boundary, validate model values and refresh field views. Sample NDVI curves are not carried into actual model results when the backend returns no observations.

`window.Wheanut.disconnectAgent()` returns the interface to its disconnected state. `window.Wheanut.openAnalysis()` opens and focuses the analysis workspace.

## Current cached reports

`connectAgent(handler, {mode: 'cached'})` labels outputs as saved reports, makes the question area read-only and hides example prompts. Plain `connectAgent(handler)` restores the live interaction mode. Register the live handler after the cached adapter loads, or remove the `trained-data.js` script reference.

Cached reports are matched by ID, exact geometry and season; changing a boundary cannot silently reuse another field's result. Reference labels are never included in the request. No live arbitrary-field inference, weather API or yield prediction is implemented.
