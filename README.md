# EduPilot AI 🎓

> **Personalized AI-Powered Learning Platform** — Hackathon 2026

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-336791.svg)](https://postgresql.org)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Setup](#manual-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Hackathon Tracks](#hackathon-tracks)

---

## Overview

**EduPilot AI** is a hackathon MVP with a React frontend and FastAPI backend. Authentication, admin user management, PDF materials, mock tutor chat, quiz scoring, progress summaries, and rule-based study roadmaps use authenticated backend APIs and PostgreSQL persistence.

Learning assistance runs in deterministic `AI_MODE=mock`; no Gemini account or key is needed. Mock tutor and quiz responses are labeled in the UI. PDF text extraction and chunk storage are implemented, but vector embeddings and retrieval-based LLM answers are not. Study-time charts are sample data; quiz-derived statistics are real saved records. Render's current free web plan does not preserve uploaded files after restarts; see [DEPLOYMENT.md](DEPLOYMENT.md) for the paid-disk option and deployment steps.

Logout clears the access token from the current browser. Because access tokens are stateless JWTs, a copied token remains valid until its 30-minute expiry; the MVP does not have a server-side token revocation endpoint.

---

## Screenshots

Screenshots are not included yet. The frontend demo can be previewed locally by following [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Features

### MVP feature status

| Feature | Status | What works now |
|---|---|---|
| Student registration and login | Connected | JWT auth API and current-user lookup |
| Student dashboard | Connected, partial | Saved quiz statistics and PDF list; weekly study-time chart remains sample data |
| AI Tutor | Connected, mock | Deterministic backend replies and account-scoped saved chat; not Gemini or vector RAG |
| Quiz and scoring | Connected, mock | Deterministic generation and backend scoring; saved quiz and attempt history |
| Progress | Connected | Quiz scores, topic summaries, and rule-based weak-topic notes |
| Learning roadmap | Connected, rule-based | Generated from quiz performance and saved task status |
| PDF materials | Connected, partial | Text PDF upload/extraction/chunk storage, search, detail, delete; scanned PDFs unsupported; Render needs paid persistent storage |
| Admin panel | Connected, basic | List users and change user roles |

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.111 | Async web framework |
| SQLAlchemy | 2.0 (async) | ORM |
| PostgreSQL | 16 | Primary database |
| pgvector | 0.3 | Vector similarity search |
| Alembic | 1.13 | Database migrations |
| Google Gemini | Optional future provider | Not called; `AI_MODE=mock` works without a key |
| Embeddings / vector retrieval | Not active | pgvector column is present, but embedding generation and similarity retrieval are not implemented |
| PyMuPDF | 1.24 | PDF text extraction |
| Passlib + bcrypt | — | Password hashing |
| python-jose | — | JWT tokens |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18 | UI framework |
| Vite | 5 | Build tool |
| JavaScript | ES modules | Application code |
| Tailwind CSS | 3 | Styling |
| React Router | 6 | Client-side routing |
| Axios | 1.x | Backend HTTP client |
| Recharts | 2 | Analytics charts |
| Lucide React | — | Icons |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| Docker + Compose | Containerization |
| Nginx | Static file serving + API proxy |
| Vercel + Render | Deployment configuration in this repository |

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│              React 18 / Vite / Tailwind                    │
└───────────────────────┬────────────────────────────────────┘
                        │ HTTPS / REST / JSON
┌───────────────────────▼────────────────────────────────────┐
│                     Backend Layer                           │
│     FastAPI · Auth · Admin · Materials · Learning APIs      │
└──────────┬──────────────────────────────┬──────────────────┘
           │ ORM queries
           ▼
┌────────────────────────┐
│ PostgreSQL + pgvector   │
│ account and learning data│
└────────────────────────┘
```

The MVP does not call an external LLM. Tutor and quiz responses are generated
by deterministic backend mock logic. Database reads and writes remain inside
the backend; the frontend receives only API responses.

The learning cycle:

```
LEARN → PRACTICE → EVALUATE → IMPROVE
 (PDF)   (Quiz)    (Analytics)  (Roadmap)
```

The backend owns all database access. Uploaded files are untrusted input, and the current mock tutor does not pass retrieved database text to an external LLM.

---

## Quick Start (Docker)

### Prerequisites
- Docker Engine 24+
- Docker Compose v2+
- PostgreSQL with pgvector support (or Docker Compose)

### Steps

```bash
# 1. After you create your repository, clone its actual GitHub URL and open that folder.

# 2. Create environment file
cp backend/.env.example backend/.env
# Edit backend/.env — set a random SECRET_KEY and local PostgreSQL values.
# AI_MODE=mock is the default; no Gemini key is required.

# 3. Set POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_URL (using host `postgres`), and SECRET_KEY in backend/.env
# 4. Launch all services
docker compose --env-file backend/.env up --build -d

# 5. Run database migrations
docker compose --env-file backend/.env exec backend alembic upgrade head

# 6. Open the app
# Frontend: http://localhost
# Backend API docs: http://localhost:8000/docs
```

To stop:
```bash
docker compose down
# To also remove volumes (wipes database):
docker compose down -v
```

---

## Manual Setup

### Backend

```bash
cd backend

# Create and activate virtualenv
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your local PostgreSQL URL and a random SECRET_KEY. AI_MODE=mock needs no API key.

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start the development server
pnpm dev
```

App will be available at http://localhost:5173

---

## Environment Variables

All backend environment variables are set in `backend/.env` (copy from `backend/.env.example`).

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) | — | ✅ |
| `SECRET_KEY` | JWT signing secret — change in production! | — | ✅ |
| `ALGORITHM` | JWT algorithm | `HS256` | ✅ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (minutes) | `30` | ✅ |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (days) | `7` | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | empty (mock AI mode) | ❌ |
| `AI_MODE` | AI response mode (`mock` or optional future `gemini`) | `mock` | ❌ |
| `EMBEDDING_MODEL` | Reserved future embedding model setting | `models/text-embedding-004` | ❌ |
| `LLM_MODEL` | Reserved future LLM model setting | `gemini-1.5-flash` | ❌ |
| `MAX_FILE_SIZE_MB` | Maximum upload size in MB | `10` | ❌ |
| `UPLOAD_DIR` | Directory for uploaded PDFs | `app/storage/uploads` | ❌ |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` | ❌ |
| `ENVIRONMENT` | `development` or `production` | `development` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |

---

## API Reference

Protected routes require a Bearer access token. All API routes except `/health`
are prefixed with `/api/v1`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | API process health check |
| `POST` | `/api/v1/auth/register` | No | Create a student account; public role assignment is rejected |
| `POST` | `/api/v1/auth/login` | No | Form fields `username` (email) and `password`; returns an access token |
| `GET` | `/api/v1/auth/me` | Yes | Return the signed-in user |
| `GET` | `/api/v1/admin/users` | Admin | List users |
| `PUT` | `/api/v1/admin/users/{user_id}/role` | Admin | Change a user's role |
| `POST` | `/api/v1/materials/upload` | Yes | Upload text-readable PDF, extract and chunk text |
| `GET` | `/api/v1/materials/` | Yes | List/search the signed-in user's materials |
| `GET` / `DELETE` | `/api/v1/materials/{material_id}` | Yes | Read or delete an owned material |
| `POST` | `/api/v1/tutor/chat` | Yes | Return a mock tutor response and save chat |
| `GET` | `/api/v1/tutor/history` | Yes | Read the signed-in user's chat history |
| `POST` | `/api/v1/quiz/generate` | Yes | Generate a deterministic mock quiz |
| `POST` | `/api/v1/quiz/{quiz_id}/submit` | Yes | Score and save a quiz attempt; rejects duplicates |
| `GET` | `/api/v1/quiz/history` | Yes | List completed saved attempts |
| `GET` | `/api/v1/performance/{overview,topics,misconceptions}` | Yes | Read saved quiz-derived performance |
| `GET` / `POST` | `/api/v1/roadmap/`, `/api/v1/roadmap/generate` | Yes | Read or create a rule-based roadmap |
| `PATCH` | `/api/v1/roadmap/tasks/{task_id}` | Yes | Update an owned roadmap task |

Swagger UI is available at `/docs` outside production; it is disabled when
`ENVIRONMENT=production`.

---

## Testing

```bash
cd backend

# Activate virtualenv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run authentication and learning API integration tests
pytest tests/test_auth.py tests/test_learning_api.py -v
```

The test suite uses SQLite (via `aiosqlite`) in-memory databases so no PostgreSQL is needed to run tests.

---

## Deployment

### Production Checklist

- [ ] Set a strong random `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set `ENVIRONMENT=production`
- [ ] Use a managed PostgreSQL instance with pgvector extension enabled
- [ ] Keep `AI_MODE=mock` unless a real provider is explicitly configured and tested
- [ ] Configure HTTPS via a reverse proxy (Nginx/Caddy/Traefik)
- [ ] Set `CORS_ORIGINS` to your production frontend URL
- [ ] Enable database backups
- [ ] Set resource limits in `docker-compose.yml`

### Docker Production Deploy

```bash
# Build production images
docker compose -f docker-compose.yml build

# Start services
docker compose up -d

# View logs
docker compose logs -f backend

# Scale backend if needed
docker compose up -d --scale backend=3
```

---

## Hackathon Tracks

### A02 and A07 status

The MVP includes rule-based weak-topic summaries and a rule-based saved roadmap.
Advanced adaptive recommendations, misconception diagnosis from free-text
answers, and automated multi-step learning workflows are not implemented.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

This checkout does not include a license file. Choose and add a license before
public distribution.

---

<div align="center">
  Built with ❤️ for Hackathon 2026 · Team EduPilot
</div>
