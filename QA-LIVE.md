# Live-backend verification

Passed locally without any real API credentials:
- Existing map, model-import and cached-report checks.
- Hosted request construction, reference-label exclusion and explicit quota failure.
- Cloudflare Worker disabled without secrets; bearer authentication; trusted server-side evidence; rejected changed season; restricted CORS. Fetches were mocked, with no NVIDIA calls.
- Browser connection dialog rejects NVIDIA-shaped keys before sending any request.

Passed in the actual team environment:
- Four geometry/cache tests: boundary validation, completed-season restriction, research-region restriction and isolation by normalized geometry + year.
- HTTP access controls reject missing/wrong access tokens and source/secret-file paths.
- Real live request: inset research polygon, season 2023, 21 usable observed dates, Grain classification, local NVIDIA Nemotron-Mini-4B-Instruct explanation; 27.8 seconds end to end. This is a deployment smoke test, not an independent test-score improvement.

Public deployment checks:
- Cloudflare reported the frontend Production deployment succeeded.
- The deployed Worker health endpoint returned configuration_required before user secrets and ready afterwards.
- Authenticated website verification completed successfully: the rendered UI reported Analysis received and displayed actual live NVIDIA hosted inference text from Nemotron 3.5 Lightning 30B A3B. Health alone was not used to claim inference success.

The hosted API initially failed because the Nano 9B v2 free endpoint was Deprecated; the active catalog model was changed to Nemotron 3.5 Lightning 30B A3B. A subsequent empty-text response was fixed by disabling thinking and setting max_tokens=1024. A final authenticated browser request returned a real explanation successfully. Credential values were not inspected or included in artifacts.
