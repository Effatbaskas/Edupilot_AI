# Deploying the EduPilot AI MVP

The app uses `AI_MODE=mock` by default and needs no Gemini key. Authentication,
PDF text extraction and storage, mock tutor chats, quiz scoring, performance
summaries, and rule-based roadmaps use the backend. Vector embedding generation,
similarity search, OCR for scanned PDFs, and real LLM responses are not part of
this MVP. The dashboard's study-time chart is sample data; quiz and material
counts come from the signed-in user's saved records.

## Local setup on Windows

1. Install Python 3.12, Node.js, pnpm, Docker Desktop, and Git.
2. Copy `backend/.env.example` to `backend/.env`.
3. Set `DATABASE_URL` to the Compose database URL, for example
   `postgresql+asyncpg://<user>:<password>@postgres:5432/<database>`. Use the
   same database name, username, and password in `POSTGRES_DB`, `POSTGRES_USER`,
   and `POSTGRES_PASSWORD`.
4. Set `SECRET_KEY` to a random value of at least 32 characters. In PowerShell,
   generate one with:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. Keep `AI_MODE=mock`; leave `GEMINI_API_KEY` empty.
6. From the repository root, run:

   ```powershell
   docker compose --env-file backend/.env up --build -d
   docker compose --env-file backend/.env exec backend alembic upgrade head
   ```

   Open the frontend at `http://localhost` and API docs at
   `http://localhost:8000/docs`. To stop the app without deleting its database,
   run `docker compose down` (do not add `-v`).

For local development without Docker, install `backend/requirements.txt`,
configure `backend/.env` with a reachable PostgreSQL server that has pgvector,
run `alembic upgrade head`, then start `uvicorn app.main:app --reload` from
`backend`. In another terminal, run `pnpm install` and `pnpm dev` from `frontend`.
The Vite development proxy forwards `/api` and `/health` to localhost port 8000.

## Vercel frontend

- Import the repository and set **Root Directory** to `frontend`.
- Build command: `pnpm run build` (or `npm run build` if deploying with npm).
- Output directory: `dist`.
- Set `VITE_API_BASE_URL` for Production and Preview to the actual Render API
  origin, with no trailing slash and no `/api/v1` suffix. Do this after Render
  has provided the service URL; do not use an example URL as a real setting.
- `frontend/vercel.json` rewrites app routes to `index.html` for SPA navigation.

## Render backend and PostgreSQL

The root `render.yaml` Blueprint describes the Python API service and managed
PostgreSQL database. Review the plan and database retention details in Render
before creating the resources. Configure the backend environment as follows:

| Variable | Setting |
| --- | --- |
| `DATABASE_URL` | Connected Render PostgreSQL connection string |
| `SECRET_KEY` | Generated secret from the Blueprint; keep private |
| `ENVIRONMENT` | `production` |
| `AI_MODE` | `mock` |
| `CORS_ORIGINS` | Exact deployed Vercel origin(s), comma separated |
| `LOG_LEVEL` | `INFO` |
| `GEMINI_API_KEY` | Not required; leave unset for mock mode |

The production start command in `render.yaml` applies `alembic upgrade head`
before starting Uvicorn. The baseline migration creates missing schema and
enables pgvector; it does not reset tables or records. The service health check
uses `/health`. Once the real Vercel domain exists, add it to `CORS_ORIGINS` and
redeploy the backend. Do not place database URLs or JWT secrets in frontend
variables or source control.

### Uploaded PDF storage needs a plan choice

The current Blueprint uses a Free Render web service and does not attach a
persistent disk. Render Free web services have an ephemeral filesystem and do
not support persistent disks. Uploaded PDF files can disappear after a restart
or redeploy even though the database still has the material record and text
chunks. To keep PDFs durable on Render, approve a paid web service with a disk
mounted at `/var/data`, then set `UPLOAD_DIR=/var/data/uploads` in the service
environment. Do not provision the paid option until you approve the cost in
Render. The local Docker Compose setup already stores uploads in a named volume.

## Verification commands

From `backend`:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

From `frontend`:

```powershell
pnpm run build
```

Compose validation requires the Compose variables in `backend/.env` to be
filled in first:

```powershell
docker compose --env-file backend/.env config --quiet
```

`config --quiet` checks configuration only; it does not start or build the
containers. Never commit `.env` files. Use `.env.example` only as a template.
