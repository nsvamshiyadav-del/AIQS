"""
Read a CSV and POST all rows to /api/ingest_bulk
Usage:
  python tools/bulk_upload.py tools/sample_readings.csv
"""
import csv
import sys
import json
import requests

URL = "http://127.0.0.1:8000/api/ingest_bulk"

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = [r for r in reader]
    return rows

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'tools/sample_readings.csv'
    rows = read_csv(path)
    print(f"Read {len(rows)} rows from {path}")
    if not rows:
        sys.exit(0)
    # Convert numeric fields
    converted = []
    for r in rows:
        obj = {}
        for k,v in r.items():
            if k == 'device_id':
                obj[k] = v
            else:
                obj[k] = float(v) if v != '' else None
        converted.append(obj)
    print('Posting to', URL)
    resp = requests.post(URL, json=converted, timeout=10)
    try:
        print('Status', resp.status_code)
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print('Response text:', resp.text)
    
