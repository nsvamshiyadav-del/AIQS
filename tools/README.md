CSV importer for Airquality

Files:
- `csv_ingest.py` : small script to post rows to `/api/ingest`
- `sample_readings.csv` : example CSV

Usage:

Python (requires `requests`):

```bash
python tools/csv_ingest.py tools/sample_readings.csv
```

Dry-run (validate only):

```bash
python tools/csv_ingest.py tools/sample_readings.csv --dry-run
```

Custom URL or timeout:

```bash
python tools/csv_ingest.py tools/sample_readings.csv --url http://127.0.0.1:8000/api/ingest --timeout 10
```

Notes:
- The backend must be running and accessible at the provided URL.
- Script expects header row matching the required fields.
