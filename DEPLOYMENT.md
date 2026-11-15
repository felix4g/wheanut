# Deployment status — 2026-11-14

- Public frontend: https://wheanut.pages.dev — updated with the optional live connection dialog, existing research reports, map and measured evaluation.
- Hosted explainer: https://wheanut-api.maqichao0203.workers.dev — deployed on the existing Cloudflare account's free Workers plan. `/api/health` reports ready after the user configured backend secrets. Readiness confirms configuration presence; a separate real website request subsequently verified inference.
- Hosted secrets: entered by the user directly in Cloudflare. No actual NVIDIA key or backend access code is in this source package. The browser accepts only the separate backend access code and retains it in page memory. Reloading disconnects the session.
- Hosted model default: NVIDIA Nemotron 3.5 Lightning 30B A3B. It explains trusted existing BARC predictions and answers new questions. It does not fetch imagery for arbitrary new boundaries.
- Satellite/classifier backend: `/workspace/Wheanut-Live`, listening on loopback port 8767 in the team GPU workspace. Not publicly exposed. Real end-to-end test obtained 21 observation dates for an inset research boundary, ran the trained classifier and local Nemotron-Mini-4B-Instruct, and completed in 27.8 seconds. This test boundary overlaps the training area and is not independent validation.

## Live website use
1. Open AI Analysis → Connect live Nemotron.
2. Keep the prefilled approved backend URL. Enter the separate WHEANUT_API_TOKEN access code, never the NVIDIA_API_KEY.
3. Verify and connect; choose a known BARC field and ask about evidence or uncertainty.
4. Review generated text with observed NDVI and field records. A model failure remains an error; it is not replaced with fabricated output.

## What is still required
An authenticated website request was successfully completed with the hosted model and rendered with the label live NVIDIA hosted inference. New-field satellite inference is tested in the private workspace, but still needs an approved reachable deployment to be used from the public website. Team merge, final submission review and team-lead submission remain separate.

## Billing and scope
No Brev VM was started and no plan upgrade was made. Cloudflare hosting remains on the existing free plan. NVIDIA API quotas/availability are account dependent; this project does not promise unlimited free inference. The Worker requires an access code and has best-effort per-instance limits, not a global cost guarantee. Keep that code private and use account quotas.

The old Nano 9B v2 free endpoint was found Deprecated in the live NVIDIA catalog and replaced. The currently selected model page showed Free Endpoint: Available. User accepted NVIDIA trial terms themselves. Hosted requests explicitly disable thinking via chat_template_kwargs.enable_thinking=false and allow 1024 tokens for a concise answer.

The final credential-free source is archived as Wheanut-Live-Final in the team workspace, leaving earlier versions untouched. The private loopback smoke-test server originally ran from Wheanut-Live; do not start another server on its occupied port without coordinating with the team.
