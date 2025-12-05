# AIQS — Air Quality Sensor (Local)

A small FastAPI-based backend and static frontend for recording and viewing air quality readings. This README covers setup, running the app locally, and using the provided CSV import tool.

**Project layout**
- `backend/` — FastAPI app, models and database (SQLite).
- `frontend/` — Static UI files (HTML/CSS/JS). Mounted by the backend when running.
- `tools/` — Utility scripts (CSV ingest, bulk upload samples).

**Prerequisites**
- Python 3.10+ installed and available on `PATH`.
- Recommended: create a virtual environment for isolation.

**Quick setup (Windows PowerShell)**
- Create and activate a venv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Install Python dependencies:

```powershell
pip install -r backend/requirements.txt
```

**Run the backend (development)**
From the project root you can run uvicorn to start the FastAPI app. Two common options:

- Use uvicorn target (recommended):

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- Or run the package entrypoint which also falls back when executed inside `backend/`:

```powershell
python -m uvicorn backend.main:app --reload
```

When running, the backend will serve the static frontend (if `frontend/` exists) and expose the API at `http://127.0.0.1:8000`.

**Main API endpoints**
- `GET /` — serves `frontend/index.html` if available, otherwise a simple status JSON.
- `POST /api/ingest` — ingest a single reading (JSON body matching fields in `tools/csv_ingest.py`).
- `POST /api/ingest_bulk` — ingest an array of readings in one request.
- `GET /api/latest` — returns the most recent stored reading.
- `GET /api/history?minutes=60` — returns readings from the last N minutes (default 60).
- `GET /api/calculate_aqi?pm2_5=...&pm10=...` — calculate and return AQI without persisting.

Refer to `backend/main.py` for full request/response models.

**CSV import tool**
A simple helper to POST rows from a CSV into `/api/ingest`.

CSV header (required):
```
device_id,pm2_5,pm10,co,no2,o3,so2,temperature,humidity
```

Dry-run validation and actual import:

```powershell
# Validate and print payloads
python tools/csv_ingest.py tools/sample_readings.csv --dry-run

# Import into a running local API
python tools/csv_ingest.py tools/sample_readings.csv
```

If your API is not at the default URL, pass `--url` with the full ingest endpoint.

**Database**
- The app uses a SQLite DB at `backend/airquality.db` by default.
- That file is created automatically when the app first runs.

**Git / hygiene notes**
- It's recommended to add a `.gitignore` to exclude `__pycache__/`, virtual envs, and `backend/airquality.db`.
- Note: the current repository may already include the DB and some `__pycache__` files. If you want, I can help add a `.gitignore`, remove those files from the index, and (optionally) purge them from history.

**Next steps / Helpful commands**
- Set global git identity if you want commits attributed to you:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

- Create a `.gitignore` (example):
```
__pycache__/
*.pyc
.venv/
backend/airquality.db
```

- Add and commit changes (from project root):

```powershell
git add README.md
git commit -m "Add project README"
git push
```

If you'd like, I can:
- add a `.gitignore` and remove `backend/airquality.db` and `__pycache__` from the repo index;
- amend the README with contributor, license, or deployment instructions;
- open the repo in your browser.

Enjoy — let me know which next step you want me to take.