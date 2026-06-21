# Shurer Dhara — Backend API

FastAPI backend powering the notice board (and future features) for both the `fe-website` and `dashboard`.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/notices` | List all notices. Add `?active=true` for public feed. |
| `POST` | `/api/notices` | Create a notice |
| `GET` | `/api/notices/{id}` | Get a single notice |
| `PUT` | `/api/notices/{id}` | Full update |
| `PATCH` | `/api/notices/{id}` | Partial update (toggle active/pinned etc.) |
| `DELETE` | `/api/notices/{id}` | Delete |
| `GET` | `/health` | Health check |

Interactive docs: **http://localhost:8000/docs**

## Environment

| Variable | Default | Used by |
|----------|---------|---------|
| `BACKEND_API_URL` | `http://localhost:8000` | `dashboard`, `fe-website` |

Set in `dashboard/.env.local` and `fe-website/.env.local`:
```
BACKEND_API_URL=http://localhost:8000
```

## Data

Notices are persisted in `backend/data/notices.json` (auto-created on first run).
