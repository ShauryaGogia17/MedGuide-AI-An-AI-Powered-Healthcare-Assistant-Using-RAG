# API contract

The browser communicates with Express. JSON errors have `{ "message": "..." }`. Authentication uses an HTTP-only `medguide_session` cookie, sent automatically by the same-origin Vite `/api` proxy. Authorization Bearer JWTs are also accepted by Express for programmatic clients.

## Express (port 5000)

- `GET /health`: liveness.
- `GET /api/health`: combined service/database readiness; 503 when a dependency is unavailable.
- `POST /api/auth/register`: `{name,email,password}`; 201 with `{user}` and session cookie. Passwords require at least 10 characters and at most 72 bytes.
- `POST /api/auth/login`: `{email,password}`; returns `{user}` and cookie.
- `GET /api/auth/me`: authenticated `{user}`.
- `POST /api/auth/logout`: clears the cookie.
- `POST /api/reports/upload` (alias `/upload`): authenticated multipart `file`, optional ISO `report_date`; 201 with a saved report containing `report_id`, `filename`, `report_date`, `date_source`, `chunks`, `labs[]`, `warnings[]`, and `status`. `stored_path` is never returned.
- `GET /api/reports`: authenticated `{reports[]}` scoped to the current user.
- `GET /api/reports/:id`: authenticated `{report}`; 404 when nonexistent or not owned.
- `GET /api/reports/:id/diet`: authenticated, user-scoped Diet Guide derived from verified saved lab readings. Returns bilingual `summary`, `eat_more`, `limit`, `avoid`, `warnings`, `days`, `disclaimer`, and guidance `sources`. Each food item includes `food`, `reason`, and report `evidence`; each evidence reference includes the test name, numeric value, unit, and page. `days` contains exactly Day 1 through Day 7 and six named meals per day. `personalized` distinguishes supported report-based guidance from general food ideas; `plan_paused` marks readings requiring clinician review before automated meal planning.
- `GET /api/reports/:id/diet/pdf?language=en|hi`: authenticated diet PDF in the requested language; defaults to English. Includes evidence, safety warnings, and the seven-day chart or paused-plan review guidance.
- `GET /api/reports/:id/blood`: authenticated, scoped to a ready report owned by the user. Returns bilingual `summary`, `readings[]`, `warnings[]`, `disclaimer`, and attributed `sources[]`. Each reading includes a label, description, original numeric/page/reference evidence, `flag` (`within`, `outside`, `unknown`), status, review guidance and a question for a clinician. CBC comparisons use the printed interval; critical alert checks require supported blood units. Missing units/intervals do not generate guessed normal ranges or diagnoses.
- `GET /api/blood/status`: authenticated optional model readiness (`ready`, `code`, `message`, `source_url`, `revision`, `input_size`). Missing/checkpoint integrity/runtime failures keep report explanations and the rest of the workspace available.
- `POST /api/blood/analyze`: authenticated multipart `file`, one PNG/JPEG image up to 5 MB. Returns research-mode segmentation `overlay_image`/`segmentation_image` as PNG data URLs, original/analyzed dimensions, `classes[]` with pixel coverage, `uncertain_pixel_percent`, English/Hindi warnings and model provenance. No image or result is added to MongoDB or Chroma. A separate per-user limit allows six image requests/minute. Blood responses use `Cache-Control: no-store`.
- `POST /api/chat/ask` (alias `/ask`): authenticated `{question}` (1-4000 characters); returns `{answer,sources[],sections?,urgent?}`.
- `GET /api/timeline`: authenticated `{series[],undated_values,undated_readings[],report_count,note}`. Each series has `test_name`, `unit`, `points`, `latest`, and `analysis`.
- `GET /api/brief`: authenticated summary from saved observations.
- `GET /api/brief/pdf?language=en|hi`: authenticated one-page PDF download; defaults to English.
- `POST /api/language/translate`: authenticated `{texts:[...]}`; returns `{translations:[...]}` in the same order. Accepts 1-32 nonempty texts, each up to 4000 characters and up to 32000 characters total. Translates to Hindi through the configured AI provider, protecting printed numeric values, units, and citation identifiers. Invalid or unverifiable output fails instead of silently changing report data.

Diet Guide also returns `swaps[]`: each entry has bilingual `instead_of`, `choose`, and `reason` plus report `evidence[]`. Supported glucose/HbA1c and lipid readings determine targeted swaps. General swaps are labeled as general advice and have no report evidence; `plan_paused` returns an empty swap list.

Citation fields: `id`, `kind` (`personal` or `knowledge`), `filename`, `title`, `page`, `report_id`, `report_date`, `url`, and the retrieved `snippet`. Only sources actually referenced in accepted claims are returned.

## FastAPI (port 8000)

- `GET /health` and `GET /`: public liveness.
- `POST /documents/upload`: multipart `file`, optional `report_id` and `report_date`; indexes page evidence and returns verified labs/warnings.
- `DELETE /documents/:report_id`: deletes only the specified user's report vectors; used for failed-upload compensation.
- `POST /ask`: `{question}`; evidence retrieval, structured generation, and citation validation.
- `POST /ml/analyze`: `{observations[]}`; descriptive analysis of observations supplied by Express.
- `POST /language/translate`: `{texts[]}`; faithful structured Hindi translation with protected clinical values and citation identifiers. Requires gateway and user authentication like other AI routes.
- `GET /blood/status` and `POST /blood/analyze`: optional pinned research model through an isolated local worker, with gateway/user authentication. See [model setup](blood-model.md) for image validation, exact classes, checkpoints and limitations.

Every non-health AI route requires `X-Service-Key` matching `AI_SERVICE_SECRET` and `X-User-ID` populated by Express after JWT validation. These headers must never be assembled from a browser-supplied user ID or exposed to the browser. CORS permits only the configured frontend origin, but browser clients still use Express.

Common statuses: 400 malformed input; 401 missing/expired authentication; 403 disallowed origin; 404 missing/not-owned report; 409 duplicate account; 413 upload/body/dimensions too large; 415 unsupported PDF/image type; 422 invalid PDF/report/image fields; 429 rate limit; 502 upstream AI/model failure or rejected answer; 503 missing service/model configuration/database readiness; 504 model/provider timeout. Optional model errors use fixed `blood_model_unavailable`, `blood_model_failed`, or `blood_model_timeout` codes; framework logs and local paths stay private.
