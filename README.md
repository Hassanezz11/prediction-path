# CS Student Career Platform

This repository now contains a full web platform around the existing career prediction model:

- `backend/` contains the FastAPI backend, database models, auth, admin routes, and static SPA frontend
- `app.py` remains as the original Streamlit prototype
- the existing model files and scraper logic are reused by the new backend services

## Product Capabilities

- student login with persistent history
- admin login with student directory and student detail view
- grade-based branch prediction stored in the database
- CV upload with optional Ollama-powered analysis
- internship and scholarship search history
- polished landing page and role-based dashboards

## Stack

- FastAPI
- SQLAlchemy
- SQLite by default for local development, PostgreSQL-compatible via `DATABASE_URL`
- Static frontend served by FastAPI
- Existing scikit-learn model artifacts for branch prediction

## Run Locally

1. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Seed an initial admin account.

```bash
python -m backend.seed
```

Default seeded admin credentials:

- email: `admin@example.com`
- password: `Admin12345!`

4. Start the platform.

```bash
uvicorn backend.main:app --reload
.\myenv\Scripts\python.exe -m backend.seed
.\myenv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

5. Open `http://127.0.0.1:8000`

## Environment Variables

- `DATABASE_URL`: optional SQLAlchemy connection string
- `SECRET_KEY`: token signing secret
- `UPLOAD_DIR`: directory for stored CV files
- `OLLAMA_URL`: CV analysis endpoint, default `http://localhost:11434/api/generate`
- `DEFAULT_OLLAMA_MODEL`: default CV analysis model

## Tests

```bash
pytest
```

The tests stub the model, CV analysis, and opportunity search flows so auth, persistence, and admin aggregation can be verified without external services.

## Notes

- The new frontend is served from `backend/static/`.
- The old Streamlit prototype in `app.py` was left in place as a legacy reference.
- For production, point `DATABASE_URL` at PostgreSQL and replace the default `SECRET_KEY`.
