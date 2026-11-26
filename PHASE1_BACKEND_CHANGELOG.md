# EduPilot AI — Phase 1 Backend API Changes

## Implemented in this phase

Added authenticated API routers for:

- Materials: PDF upload, text extraction/chunking, list/search, detail, delete.
- Quizzes: mock generation (MCQ, short-answer and mixed), list/detail, scoring and persisted attempts.
- Tutor: mock chat replies, persisted conversation history and session listing.
- Performance: overview, topic scores and weak-topic/misconception summaries derived from saved attempts.
- Roadmap: rule-based generation from weak topics, task status updates and retrieval.

All learning data is scoped to the authenticated user. Quiz submission rejects a second completed submission for the same quiz (HTTP 409). Invalid file type, oversized files, unreadable PDFs, unknown resources and invalid payloads return explicit HTTP errors.

## Mock mode

`AI_MODE=mock` is the default. No Gemini subscription or API key is required. `/health` reports the configured mode. The newly added learning routes intentionally use deterministic mock/rule-based behavior; they are not presented as live Gemini responses. Real provider integration remains a later task.

PDF upload supports text-extractable PDFs only. Image-only/scanned PDFs are rejected with HTTP 422 because OCR is not included in this phase.

## API paths

All paths are under `/api/v1`:

- `POST /materials/upload`
- `GET /materials/` (supports `page`, `per_page`, `search`)
- `GET /materials/{material_id}`
- `DELETE /materials/{material_id}`
- `POST /quiz/generate`
- `GET /quiz/`
- `GET /quiz/history` (completed attempts for the signed-in user)
- `GET /quiz/{quiz_id}`
- `POST /quiz/{quiz_id}/submit`
- `POST /tutor/chat`
- `GET /tutor/history`
- `GET /tutor/sessions`
- `GET /performance/overview`
- `GET /performance/topics`
- `GET /performance/misconceptions`
- `GET /roadmap/`
- `POST /roadmap/generate`
- `PATCH /roadmap/tasks/{task_id}`

## Follow-up integration and verification

The verification and next-step notes in the original handoff below predate the frontend integration. Student learning screens now use the authenticated backend APIs. Tutor replies and quiz generation are deterministic mock behavior; the roadmap is rule-based. The UI identifies these limits, and study-time visualization remains sample data.

The quiz API also exposes `GET /api/v1/quiz/history`, returning only the signed-in user's completed attempts for the saved practice history.

Current checks:

- Backend pytest: 12 tests passed, using in-memory SQLite and a temporary PDF folder.
- FastAPI app import/startup check with temporary test-only SQLite settings: passed; 27 routes loaded.
- Frontend production build: passed.
- Docker Compose config validation: passed with temporary process-only placeholder values; no containers started and no project secrets read.
- Alembic migration against a disposable PostgreSQL+pgvector container: passed; `0001_safe_baseline` reached head.
- Persistence against the configured developer/production database: not verified or touched.
- Docker image build: passed for backend and frontend; Nginx `/health` proxy returned 200 and protected API proxy returned 401 as expected in an isolated temporary network.
- Live Render/Vercel deployment: not run.
- Render upload persistence: not configured. The current free web plan uses ephemeral local storage; durable PDF files need a paid service with a persistent disk and `UPLOAD_DIR` configured.

These checks do not require a Gemini key. They did not create, reset, or modify PostgreSQL data.
