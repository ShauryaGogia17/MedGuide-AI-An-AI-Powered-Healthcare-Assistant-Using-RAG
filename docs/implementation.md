# Implementation and verification by phase

These changes extend the existing project. Source files are the full implementation; excerpts below highlight each phase's behavior. Run test commands from the repository root unless a command explicitly changes directory. Setup is in the README.

## 1. Service communication and health

Edited `backend/server.js`, `backend/src/config/env.js`, `frontend/vite.config.js`, `frontend/src/services/api.js`, `frontend/package.json`, `ai-service/main.py`, `ai-service/llm/openai_client.py`, and `.env.example`. Added `ai-service/config.py`, missing package `__init__.py` files, and frontend health output. Fixed the original relative-import mismatch and the frontend build script.

```python
@app.get('/health')
def health():return {'status':'ok','service':'ai-service'}
```

```bash
curl --fail http://localhost:5173/health
curl --fail http://localhost:5000/health
curl --fail http://localhost:8000/health
curl --fail http://localhost:5173/api/health
npm --prefix frontend run build
```

Verify that all three liveness endpoints return `status: ok`, and combined readiness includes MongoDB and FastAPI. Missing provider credentials do not prevent startup.

## 2. PDF upload

Implemented `backend/src/middleware/uploadMiddleware.js` and `errorMiddleware.js`; edited report routes/controllers, AI transport, and `ai-service/api/routes/document_routes.py`. Node retains randomly named PDFs in `uploads/reports/`; FastAPI processes bounded temporary files.

```js
if (header.toString() !== '%PDF-') throw Object.assign(new Error('The uploaded file is not a valid PDF'), { status: 415 });
```

```bash
ai-service/.venv/bin/python -m pytest tests/rag/test_upload.py -q
npm --prefix backend test
```

Register an account and upload a PDF. Try a JPG renamed to PDF and a file over 10 MB: both must fail clearly. Failed files are removed. Both old `/api/reports/upload` and the `/upload` alias are supported, with authentication required.

## 3. Extraction, chunks, embeddings, and persistent Chroma

Edited `ai-service/extraction/pdf_extractor.py`, `extraction/ocr.py`, `rag/chunker.py`, `rag/embeddings.py`, `rag/vector_store.py`, and the document router. Implemented `scripts/ingest_documents.py`; added two attributed resources and populated `knowledge-base/metadata/sources.json`.

```python
ids=[f'{user_id}:{report_id}:{chunk["chunk_index"]}' for chunk in chunks]
```

```bash
ai-service/.venv/bin/python -m pytest tests/rag/test_chunking.py tests/rag/test_indexing.py tests/rag/test_extraction.py -q
ai-service/.venv/bin/python scripts/ingest_documents.py
```

Upload a selectable-text PDF and a scanned PDF. Sources retain original page numbers. Upload two different reports with the same filename; they remain distinct. Run knowledge ingestion twice: unchanged files are skipped. Restarting services does not re-embed. OCR was additionally verified using a real generated scanned PDF and installed Tesseract.

## 4. Retrieval and grounded answers

Edited `rag/retriever.py` and `rag/generator.py`; implemented `rag/prompt_builder.py`, `rag/citation_manager.py`, `llm/prompts.py`, `llm/response_parser.py`, `llm/safety.py`, and `api/routes/rag_routes.py`. Updated the Express chat controller and AI transport.

```python
response = get_client().responses.parse(model=get_model(), instructions=SAFETY_PROMPT, input=build_prompt(question,sources), text_format=GroundedAnswer)
```

```bash
ai-service/.venv/bin/python -m pytest tests/rag/test_ask.py tests/rag/test_pipeline.py -q
```

Ask about an indexed report. Responses contain `answer` and `sources`, with personal/general sections. Ask from a second account: the first account's passages must not appear. Ask a dosage question or describe chest pain: the answer is handled without generation. Ask without indexed evidence: the system acknowledges insufficient evidence. Provider-backed tests use mock responses; actual provider access needs the root `.env` key.

## 5. Citations in chat

Implemented `frontend/src/components/SourceCitation.jsx`; edited `ChatBox.jsx` and the API client. Added frontend test configuration and citation tests.

```jsx
{!!message.sources?.length && <div className="sources"><h4>Evidence used</h4>{message.sources.map(source=><SourceCitation key={source.id} source={source}/>)}</div>}
```

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Expand a source beneath an answer. Confirm its filename, page, and exact retrieved passage. General sources also link to the registered public attribution URL. Only IDs used by validated claims are shown.

## 6. Verified labs, database, and authentication

Implemented the existing backend database/auth/model placeholders: `config/db.js`, `models/User.js`, `models/Report.js`, `models/LabResult.js`, auth routes/controller/middleware, and report persistence. Lab values are embedded in the report document. Added a persistent local development database runner and MongoDB Docker configuration. Implemented `extraction/lab_parser.py`; edited the document router. Implemented the frontend auth context and sign-in/register screen.

```python
for lab in parsed.labs: validate_evidence(lab,page)
```

```js
const payload = jwt.verify(token, jwtSecret(), { algorithms: ['HS256'], issuer: 'medguide', audience: 'medguide-web' });
```

```bash
ai-service/.venv/bin/python -m pytest tests/rag/test_labs.py -q
npm --prefix backend test
```

Create two accounts. Each sees only its own reports; guessed report IDs return 404. Unauthenticated and expired sessions fail. Confirm that password hashes and stored paths are not returned. Expand a report to see extracted rows/evidence and warnings. Missing dates remain unknown. Provider errors during lab parsing do not fabricate rows.

## 7. Trends and anomaly detection

Edited `ml/trend_detector.py`; implemented `ml/anomaly_detector.py`, `ml/predict.py`, `api/routes/ml_routes.py`, `backend/src/services/mlService.js`, and new `backend/src/routes/timelineRoutes.js`.

```python
slope=float(LinearRegression().fit(x.reshape(-1,1),y).coef_[0])
```

```bash
ai-service/.venv/bin/python -m pytest tests/ml -q
```

Use two or more dated reports with the same test and unit. Directions and percent change reflect actual elapsed days. Bounds use the report's own reference range. Undated values still receive range comparisons, but are not charted. Z-scores remain unavailable until eight prior values exist. The ML output contains no disease inference.

## 8. Health timeline and workspace

Implemented `TrendChart.jsx`, `ReportCard.jsx`, sidebar/loading/disclaimer components, `pages/HealthTimeline.jsx`, `pages/Reports.jsx`, `pages/Dashboard.jsx`, format helpers, and the app shell. Added Recharts and responsive styles.

```jsx
{hasBand&&<Area dataKey="band" type="linear" stroke="none" fill="#d9eae0" fillOpacity={0.7} connectNulls={false} isAnimationActive={false}/>}
```

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Open Health timeline: printed two-sided intervals are shaded; points outside their own intervals are highlighted. Tooltips and individual readings show file/page references. Different units use separate series. Unknown dates and missing reference intervals are explicitly described.

## 9. Doctor visit brief and PDF

Added `backend/src/services/briefService.js`, `briefPdf.js`, `routes/briefRoutes.js`, and an openly licensed embedded font. Implemented `frontend/src/pages/DoctorBrief.jsx`; connected app navigation. Briefs are derived deterministically from stored numeric observations.

```js
const count=doc.bufferedPageRange().count;
if(count!==1){doc.end();reject(new Error('Brief unexpectedly exceeded one page'));return;}
```

```bash
npm --prefix backend test
```

Open Doctor visit brief and export its PDF. Check changes, dates, values, reference ranges, source files/pages, and clinician questions. The PDF stays one page and explicitly counts omitted entries; the UI includes all summarized entries. Tests cover 20 long measurement names; the exported page was rendered and visually inspected.

## 10. Polish, errors, setup, and regression checks

Edited responsive styles, upload/chat/loading flows, API error handling, environment examples, README, architecture/API/RAG/ML docs, and dependency manifests/lockfiles. Added `scripts/setup_env.py`, `scripts/smoke_browser.cjs`, UI error/timeline tests, and a PDF-to-index-to-answer test. Timeline and brief code are loaded on demand to reduce the initial bundle.

```js
xhr.upload.onprogress=event=>{if(event.lengthComputable){const next=Math.round(event.loaded/event.total*100);setProgress(next);if(next===100)setStatus('Reading, indexing, and extracting lab values…');}};
```

```bash
ai-service/.venv/bin/python -m pytest tests -q
npm --prefix backend test
npm --prefix frontend test
npm --prefix frontend run build
# With local services and Chrome running:
node scripts/smoke_browser.cjs
```

Verify desktop and phone-sized navigation, file validation, progress/loading states, failed-request retry, disclaimers, account registration/logout, actual SVG reference shading, and PDF download. The browser smoke test removes its synthetic account and rows. Actual OpenAI billing/account access is separate from mocked provider tests and was not tested because no API key was provided.

## Completed verification

- Python: 44 tests passed, including real Chroma persistence and the PDF-to-index-to-answer path with mocked provider calls.
- Express/MongoDB/PDF: 7 tests passed using disposable MongoDB.
- Frontend: 6 tests passed; production build passed with separate timeline/brief bundles.
- Browser smoke: passed registration, report lists, SVG reference bands, PDF download, emergency response, mobile layout, and logout; its synthetic account and rows were removed.
- OCR: a real scanned PDF was read successfully using local Tesseract.
- PDF: rendered and visually inspected the stress-case one-page export; live HTTP export also verified as one page with expected values and sources.
- Dependency checks: Python pip check passed; npm production audits reported no vulnerabilities.
- Frontend, Express, FastAPI, and combined database/service health checks passed.
- Live OpenAI calls and actual knowledge-source embedding are pending a configured API key. No real medical report was provided; provider-backed logic was tested with deterministic mocks.
