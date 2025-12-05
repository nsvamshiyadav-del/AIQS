"""
Simple CSV -> API importer for the Airquality app.
Usage:
    python tools/csv_ingest.py sample.csv

CSV format (header required):
device_id,pm2_5,pm10,co,no2,o3,so2,temperature,humidity

The script will POST each row to http://127.0.0.1:8000/api/ingest by default.
"""
import sys
import csv
import argparse
import requests
from typing import Dict

API_BASE = "http://127.0.0.1:8000/api/ingest"

REQUIRED_FIELDS = [
    "device_id",
    "pm2_5",
    "pm10",
    "co",
    "no2",
    "o3",
    "so2",
    "temperature",
    "humidity",
]


def parse_args():
    p = argparse.ArgumentParser(description="Import CSV rows to Airquality /api/ingest")
    p.add_argument("csvfile", help="Path to CSV file")
    p.add_argument("--url", default=API_BASE, help="Full ingest URL (default: %(default)s)")
    p.add_argument("--dry-run", action="store_true", help="Don't POST; just validate and print payloads")
    p.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    return p.parse_args()


def row_to_payload(row: Dict[str,str]):
    payload = {}
    for f in REQUIRED_FIELDS:
        if f not in row:
            raise ValueError(f"Missing required column: {f}")
        # numeric fields -> convert to float where applicable
        if f == "device_id":
            payload[f] = row[f]
        else:
            val = row[f]
            if val == "":
                payload[f] = None
            else:
                try:
                    payload[f] = float(val)
                except ValueError:
                    raise ValueError(f"Invalid number for {f}: '{val}'")
    return payload


def import_csv(path: str, url: str, dry_run: bool, timeout: float):
    successes = 0
    failures = 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=1):
            try:
                payload = row_to_payload(row)
            except Exception as e:
                print(f"Row {i}: validation error: {e}")
                failures += 1
                continue

            print(f"Row {i}: payload: {payload}")
            if dry_run:
                successes += 1
                continue

            try:
                r = requests.post(url, json=payload, timeout=timeout)
                if r.status_code in (200, 201):
                    print(f"Row {i}: OK -> {r.json()}")
                    successes += 1
                else:
                    print(f"Row {i}: HTTP {r.status_code} -> {r.text}")
                    failures += 1
            except requests.RequestException as e:
                print(f"Row {i}: Request error: {e}")
                failures += 1

    print(f"Done. Successes: {successes}, Failures: {failures}")


if __name__ == "__main__":
    args = parse_args()
    import_csv(args.csvfile, args.url, args.dry_run, args.timeout)
