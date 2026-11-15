# Hosted Nemotron on Cloudflare Workers

The default handler is disabled until two server-side secrets exist:

- NVIDIA_API_KEY: create a fresh API Catalog key; enter it directly in Cloudflare's Secret field, never in chat or frontend code.
- WHEANUT_API_TOKEN: a separate strong random access code for this demo backend. This is the only code the frontend connection dialog accepts. Do not reuse the NVIDIA key.

Optional plain variable NVIDIA_MODEL overrides the default official catalog model ID. A real NVIDIA request must verify account permission and quota. No inference occurs merely by deploying this source or checking /api/health.

This service can answer new questions about the 44 trusted BARC reports without running a GPU VM. It loads prediction and NDVI from the existing website, excludes reference labels, and calls NVIDIA's official hosted endpoint. It cannot collect or classify arbitrary new satellite polygons; use the Python backend for that.

CORS allows the existing website only. Bearer authentication is required. Best-effort per-instance limits (3 requests/minute per IP, 2 concurrent) help with a small demo; they are not a global cost guarantee. Keep the access code private, use account quotas, and do not assume unlimited free API use. No credentials are returned in errors or health checks.

The deployed model was verified on the official NVIDIA catalog with Free Endpoint: Available. Earlier Nano 9B v2 endpoints are deprecated. Requests disable thinking to prevent reasoning-only responses within the output budget. See artifacts/hosted_inference_verification.json for the successful visible website check.
