# Pravdalist Private Website

Private website at **https://private.pravdalist.ai** and API at **https://api.pravdalist.ai**.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Jinja2, SQLAlchemy 2 (async), Alembic, PostgreSQL/asyncpg
- **Auth**: python-jose (JWT), passlib (bcrypt)
- **Frontend**: Bootstrap 5 (CDN), Vue.js 3 (CDN islands)
- **Locale Editor**: PyQt6, deep-translator

## Quickstart

```bash
cp .env.example .env
# start postgres
docker compose up -d db

# backend
cd backend
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

## Locale Editor

```bash
cd locale-editor
pip install -e .
python -m locale_editor
```

## Project Structure

```
backend/          FastAPI application
locale-editor/    PyQt6 locale editing desktop app
```

## DNS / Host Guard

DNS A-records for `private.pravdalist.ai` and `api.pravdalist.ai` are already configured.
The host guard middleware enforces these hostnames — any request with a different `Host` header
gets `421 Misdirected Request`.
