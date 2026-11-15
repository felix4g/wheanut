# Wheanut live backend

This addition does not change the public website until a reachable backend is deliberately configured. It supports two real operations:

- `action: explain`: takes an existing field ID, loads the trusted saved classifier result on the server, and asks Nemotron to answer the new user question. Browser-supplied reference labels or predictions are ignored.
- `action: analyze`: validates a new field polygon and completed season, queries public Sentinel-2 observations, derives the same features, runs the final trained classifier, and generates a real explanation. Cache directories are isolated by normalized geometry and season. This is deployment inference, not a held-out evaluation result.

## Environment
Use the existing isolated Python environment; do not upgrade the shared team environment:

    cd /workspace/Wheanut-Live-Final
    /workspace/Wheanut-Independent/.venv/bin/python src/server.py --port 8767

By default the service binds only 127.0.0.1. It is not reachable from the public Cloudflare website. It does not open firewall ports, create a tunnel, or start paid compute. An approved HTTPS deployment or authenticated proxy is still needed for public integration. The team Jupyter environment currently has no jupyter-server-proxy extension; do not restart the shared notebook server just to add one.

## NVIDIA hosted inference
Privately create `.env` in the backend root:

    NVIDIA_API_KEY=
    NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
    WHEANUT_EXPLAINER=nvidia

Fill the key yourself; never put it in the frontend or send it in chat. The model must be available to this API Catalog account. Official endpoint: https://integrate.api.nvidia.com/v1/chat/completions. If a different Nemotron is enabled, set its exact model ID. API quotas and permissions require a real request to verify; do not assume unlimited free availability.

With `WHEANUT_EXPLAINER=local`, no NVIDIA API key is required; a suitable GPU and the pinned public Nemotron weights are required. The two provider paths never silently fall back to fabricated text.

## API
GET `/api/health` returns readiness and provider, never secrets. All job requests and results require a separate backend access token (not the NVIDIA key). At startup this token is generated into `/tmp/wheanut-live-runtime/.api-token` with owner-only permissions, unless `WHEANUT_API_TOKEN` is supplied as a server secret. Do not upload that token file.

POST `/api/jobs` with Authorization Bearer and JSON `{action, fieldId, fieldName, geometry, season, question}` returns HTTP 202 and a job ID. Poll GET `/api/jobs/{jobId}` for queued/running/complete/error. Classification result schema matches the existing frontend integration contract. One worker at a time; maximum four queued jobs, 20 requests/hour, 128 KiB body, eight-minute worker timeout. Allowed browser origin: https://wheanut.pages.dev, plus documented local previews. No wildcard CORS.

Research limits: completed 2021–2025 seasons only; valid WGS84 polygons near Beltsville, Maryland; bounded geometry and crop size; at least six usable dates. Training-field overlap is explicitly flagged. No California/general-purpose validation is claimed. Failed collection, insufficient evidence or failed explanation remains an error, not a synthetic prediction.

## Credentials and archives
`.env`, runtime jobs, tokens, virtual environments, model weights and generated server logs must stay out of deliverable ZIPs and version control. Use the existing model-results JSON for a credential-free public fallback. Public API deployment should use HTTPS, rate limits and a server-side secret store; the separate demo access token must not be hard-coded in public JS.
