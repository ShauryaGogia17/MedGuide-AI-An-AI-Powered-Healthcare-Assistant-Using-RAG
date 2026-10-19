# MedGuide AI

An educational aid for understanding medical reports and preparing for conversations with a qualified healthcare professional. It does not diagnose, prescribe, or give dosages.

The existing React → Express → FastAPI structure is retained. Reports and verified lab measurements live in MongoDB; page-aware evidence lives in persistent, separate personal and medical-knowledge Chroma collections.

## Requirements

- Node.js 22.12+ (tested with 22.17.1), npm, Python 3.11+ (tested with 3.13.2).
- MongoDB: an existing local/server installation, Docker, or the optional development runner below.
- An OpenAI API key with access to your configured answer and embedding models. A ChatGPT subscription does not supply an API key.
- Tesseract for scanned-PDF OCR. On macOS: `brew install tesseract`; on Debian/Ubuntu: `sudo apt-get install tesseract-ocr`. English is the default; install the relevant language pack for other languages.

## First-time setup

Run from the repository root:

```bash
python3 scripts/setup_env.py
cd backend
npm ci
cd ../frontend
npm ci
cd ../ai-service
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Edit the **root `.env`**, set `OPENAI_API_KEY`, and check `MONGODB_URI`. `setup_env.py` generates separate strong JWT and internal-service secrets and never overwrites an existing file. Keep secrets out of frontend environment variables and version control.

`OPENAI_MODEL=gpt-5.6-luna` was checked against the [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna) on 2026-10-10; it supports Responses and structured outputs. Both `OPENAI_MODEL` and `OPENAI_EMBEDDING_MODEL` are configurable. Structured extraction uses the [documented Pydantic Responses parser](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Run locally

From the repository root, start the full development stack with:

```bash
npm run dev
```

This starts MongoDB when a local database is needed, then FastAPI, Express, and React. Services that are already running are reused. Press Ctrl+C to stop only services started by this command. Complete the first-time dependency/environment setup above before using it.

To start each service separately, use separate terminals:

```bash
# Terminal 1: choose ONE MongoDB option
# Existing MongoDB: start your normal server.
# Docker, from the repository root:
docker compose up -d mongodb
# OR local development runner, from backend/:
cd backend
npm run db:dev
```

The development runner downloads a local MongoDB binary on its first run and keeps data in `.local-data/mongo` across restarts. It binds to localhost and is not a production database deployment.

```bash
# Terminal 2, from the repository root:
cd ai-service
source .venv/bin/activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Terminal 3, from the repository root:
cd backend
npm run dev
```

```bash
# Terminal 4, from the repository root:
cd frontend
npm run dev
```

Open **http://localhost:5173**. Use `localhost` consistently: `FRONTEND_ORIGIN` is exact, and session cookies belong to that hostname. Register an account, upload a PDF, optionally supply its printed report date, and ask a question. Use **Health timeline** for dated readings and **Doctor visit brief** for the summary/PDF.

After a successful upload, **Diet Guide** shows Indian food suggestions with **Eat More**, **Limit**, and **Avoid** lists. Each personalized reason cites a verified report reading and page. It includes **Day 1 to Day 7**, with early morning, breakfast, snack, lunch, evening snack, and dinner, plus **Download PDF**. Reopen a saved report to view its guide again. Suggestions are educational food ideas, not diagnoses or prescriptions; verify extracted readings and discuss food allergies, pregnancy, existing conditions, and individual dietary requirements with your clinician. Critical readings and kidney-related concerns pause automated meal planning and show review guidance instead.

The **Overview** has a **Diet Guide** card with an **Open Diet Guide** button. You can also open it from the sidebar, choose a saved report, and see **Simple food swaps** that compare **Instead of** with **Choose**, with reasons tied to report values. The same page includes the complete seven-day meal plan, Hindi listening controls, and PDF download. Food swaps are included in the PDF and are paused when the report requires clinical review.

**Blood Guide** is available from **Overview → Open Blood Guide** and the sidebar. Choose a saved blood report for CBC explanations, printed reference-interval comparisons, original values/pages, questions to ask your doctor, and critical-value warnings. English and Hindi text and Hindi play/pause/stop are included. It uses verified saved measurements without another provider call.

The same page accepts a **PNG/JPEG blood-smear microscope image** and shows a segmentation overlay, a color map, and pixel coverage from the linked [blood-cell segmentation project](https://github.com/abhanjac/blood_cell_image_segmentation). Its trained checkpoint runs in a separate optional TensorFlow environment. Set it up once with `python3 scripts/setup_blood_model.py`; see [model setup and provenance](docs/blood-model.md). The main React/Express/FastAPI dependencies remain compatible. Research labels and pixel percentages cannot establish blood cell counts, CBC values, infection, malaria, or health. A laboratory professional must review the original smear. Uploading a photo of a report is not this image workflow; use the existing PDF upload for report readings.

Use **English / हिन्दी** in the workspace or sign-in screen to change language. Interface text and Diet Guide use bundled Hindi translations; dynamic report explanations, chat answers, and timeline/brief observations are translated through the existing configured AI service, with numeric values, units, and citations preserved. The original report evidence stays available. Translation failures are shown with a retry control. **Listen in Hindi** uses browser speech synthesis with a Hindi voice and `hi-IN`, with play/pause/stop controls. Audio stops when navigating or switching results. If the device has no Hindi voice, install one in the device's speech settings. Both diet and doctor-brief PDF downloads follow the selected language.

Every result includes: **General awareness only, not a substitute for a doctor's advice.** Diet generation and diet PDFs work from saved report values without an additional AI call. Dynamic Hindi translation requires the configured AI provider.

Health checks:

```bash
curl --fail http://localhost:5173/health
curl --fail http://localhost:5000/health
curl --fail http://localhost:8000/health
curl --fail http://localhost:5173/api/health
```

The combined check reports Express, FastAPI, and MongoDB readiness. It is not an OpenAI account-access or billing check. With a blank key, health checks, authentication, emergency responses, and analysis of saved readings work; new embeddings and lab extraction require provider access.

Save `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_EMBEDDING_MODEL` in the root `.env`. The AI service picks up saved provider settings on the next request, including key changes, without a restart. Explicit settings exported by your shell retain precedence. Other environment settings still require restarting the services. Upload and chat errors identify rejected keys, unavailable models, quota limits, and timeouts without exposing credentials.

## Medical knowledge ingestion

Two short, attributed MedlinePlus educational summaries are included under `knowledge-base/sources/government/`. Add reviewed `.txt`, `.md`, or `.pdf` resources inside `knowledge-base/`, then register their relative path, title, and public HTTPS attribution URL in `knowledge-base/metadata/sources.json`.

```bash
# From the repository root, after setting the OpenAI key:
ai-service/.venv/bin/python scripts/ingest_documents.py
```

Run ingestion explicitly when sources change. Unchanged files are skipped using content/metadata hashes; no restart triggers re-embedding. Changing the embedding model requires a deliberate rebuild into a fresh vector directory, followed by re-ingestion/re-upload; never mix incompatible vectors in an existing collection.

## Behavior and data boundaries

- Uploads are limited to 10 MB by default and 100 PDF pages. Both services verify the PDF signature/type; FastAPI also enforces the size limit. Node stores randomly named files under `uploads/reports/`; temporary AI files are removed.
- pypdf preserves page numbers; pages without text use local Tesseract OCR. OCR quality varies. Verify all extracted values against the report.
- Lab extraction uses a strict schema and Pydantic validation. Values, units, reference bounds, pages, and evidence snippets must match report text. Unverifiable pages produce warnings, not fabricated values. Dates are never inferred from upload time. Supply the printed date during upload when extraction is ambiguous.
- Lab values are embedded in the MongoDB report document, so values and their report are persisted atomically. Reports and queries are scoped to the authenticated user. Browser sessions use HTTP-only JWT cookies; FastAPI requires a separate service secret plus user context from Express.
- Old unowned `medguide_documents` vectors are retained but excluded from retrieval. Re-upload legacy reports after signing in to associate them with your account. There is no automatic guess at legacy ownership.
- Chat returns only citations referenced in the validated answer. Report and knowledge claims are separated; unsupported source IDs, category mismatches, and unsupported numeric claims are rejected. Prompts forbid diagnosis, prescriptions, and dosages. Rule-based emergency handling occurs before retrieval.
- Reports without dates remain available for chat and reference-range checks but do not appear in time-based charts. Units are grouped separately; values without units receive no trend label. Changing laboratory methods can still affect comparability.
- Regression uses actual elapsed days. A 1% fitted-change tolerance labels descriptive stability; it is not a medical threshold. Percent change is unavailable when the first value is zero. Z-scores require at least eight earlier readings and nonzero historical variance.
- PDF briefs fit one page, show up to five changes and five out-of-range results, and state omitted counts. The UI shows the complete summary. No disease inference is produced by the ML engine.
- Original report passages and extracted pages are sent to the configured OpenAI API for embeddings/extraction/answers. Files are not served publicly. Local MongoDB, Chroma, and uploaded files are not encrypted by this application; deployment needs protected storage and transport.

## Tests and build

To verify a real PDF upload and cited answer through the browser with your configured OpenAI account, run `node scripts/smoke_live_ai.cjs` while the app is running. This opt-in check makes real API calls using a synthetic report and removes its temporary account, uploaded file, and vectors afterward.

```bash
# From the repository root:
ai-service/.venv/bin/python -m pytest tests -q
npm --prefix backend test
npm --prefix frontend test
npm --prefix frontend run build
```

Python tests exercise chunk overlap, page extraction, indexing, batching, user isolation, evidence validation, emergency/dosage handling, the `/ask` API, lab schemas, trends, range boundaries, and the full PDF → index → question path. Provider calls are mocked; real Chroma is used in isolation. Backend tests use disposable MongoDB and mock the AI transport. Frontend tests verify citations, readings, errors, and upload validation.

With all services running and Google Chrome installed, an optional browser smoke test creates and removes a synthetic account and synthetic report rows:

```bash
node scripts/smoke_browser.cjs
```

It checks registration, report lists, real timeline/reference-band rendering, PDF download, emergency responses, mobile overflow, and logout. QA screenshots/PDFs are written to the OS temporary folder. This is not a paid-provider integration test.

The Diet Guide and Hindi UI smoke check uses synthetic report readings, a mocked translation transport, and a mocked Hindi browser voice, while exercising the real diet API and PDF renderer:

```bash
node scripts/smoke_diet.cjs
```

With the optional blood model installed, `node scripts/smoke_blood.cjs` checks Blood Guide navigation, saved CBC explanations, Hindi listening controls, mobile layout, and an actual upstream sample-image inference. Synthetic accounts and report rows are removed afterward. The optional real-model Python check is documented in [blood-model.md](docs/blood-model.md).

For a production frontend build, serve `frontend/dist` behind a same-origin `/api` reverse proxy. `VITE_API_BASE_URL` can override the API path; prefer the same origin for HTTP-only cookies. Production HTTPS is required with `NODE_ENV=production`. Restrict `FRONTEND_ORIGIN` to the deployed frontend. Express currently binds to localhost; use a local reverse proxy. Do not expose FastAPI directly.

See [the API contract](docs/api.md), [architecture](docs/architecture.md), and [phase-by-phase implementation notes](docs/implementation.md) for changed files, code excerpts, commands, and manual verification.
