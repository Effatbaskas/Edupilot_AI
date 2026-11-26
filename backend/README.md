# Backend foundation

## Configure

Use Python 3.12 and PostgreSQL with the `vector` extension for the full app.
Copy `.env.example` to `.env`, then fill in `DATABASE_URL`, `SECRET_KEY`, and
the `POSTGRES_*` values used by Docker Compose. Keep `.env` private. Generate a
new signing key locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

For a local server, `DATABASE_URL` must use `postgresql+asyncpg://` and the
database host should be `localhost`. For Docker Compose, use host `postgres`.
If the database password contains reserved URL characters, URL-encode it in
`DATABASE_URL`.

Install the dependencies already listed in this project and apply the safe
baseline migration from this directory:

```powershell
python -m pip install -r requirements.txt
alembic upgrade head
```

The first migration creates only missing tables and does not drop or recreate
existing tables. App startup does not change the schema. Future schema changes
should use new Alembic revisions.

Create an administrator from a trusted local terminal (public signup cannot
assign teacher or admin roles):

```powershell
python scripts/create_admin.py
```

## Run and test

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

Tests use a temporary in-memory SQLite users table and do not connect to the
configured PostgreSQL database:

```powershell
python -m pytest -q
```

Authentication endpoints:

- `POST /api/v1/auth/register` — JSON registration; creates a student account.
- `POST /api/v1/auth/login` — form fields `username` (email) and `password`.
- `GET /api/v1/auth/me` — current active account; requires a Bearer access token.
- `GET /api/v1/admin/users` — administrator only.

The API issues short-lived access tokens. It does not issue refresh tokens or
claim to support server-side logout/revocation yet.


## Backend API development (mock mode)

The backend exposes authenticated learning APIs under `/api/v1`:

- `POST /materials/upload`, `GET /materials/`, `GET /materials/{id}`, `DELETE /materials/{id}`
- `POST /quiz/generate`, `GET /quiz/`, `GET /quiz/{id}`, `POST /quiz/{id}/submit`
- `POST /tutor/chat`, `GET /tutor/history`, `GET /tutor/sessions`
- `GET /performance/overview`, `/topics`, `/misconceptions`
- `GET /roadmap/`, `POST /roadmap/generate`, `PATCH /roadmap/tasks/{task_id}`

### AI mode

`AI_MODE=mock` is the default and does not require a Gemini subscription or API key. Tutor replies and quiz generation use deterministic local mock logic; they are for development and workflow testing, not equivalent to a real LLM. Real-provider wiring for these learning endpoints is intentionally deferred to a later phase. Never commit a real key.

### Material upload

Mock mode currently supports text-extractable PDF files up to `MAX_FILE_SIZE_MB`. Scanned/image-only PDFs are rejected with HTTP 422; OCR is not part of this phase. Uploaded files and extracted text chunks are stored under the configured upload directory and database.
