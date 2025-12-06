#!/usr/bin/env python3
"""
Auto-ingest script to generate and send sample air quality data.
Usage:
  python auto_ingest.py                    - Ingest 24 sample readings (populate database)
  python auto_ingest.py continuous         - Continuous ingestion every 60 seconds
  python auto_ingest.py continuous 30      - Continuous ingestion every 30 seconds
"""
import requests
import time
import random
from datetime import datetime
import json
import sys

API_URL = "http://127.0.0.1:8000/api/ingest"
BULK_API_URL = "http://127.0.0.1:8000/api/ingest_bulk"

DEVICES = ["SENSOR_01", "SENSOR_02", "SENSOR_03"]

def generate_reading(device_id=None):
    """Generate realistic air quality reading."""
    if device_id is None:
        device_id = random.choice(DEVICES)
    
    pm2_5 = random.uniform(15, 85)
    pm10 = pm2_5 * random.uniform(1.2, 1.8)
    co = random.uniform(0.2, 1.5)
    no2 = random.uniform(10, 60)
    o3 = random.uniform(20, 80)
    so2 = random.uniform(5, 40)
    temperature = random.uniform(15, 35)
    humidity = random.uniform(30, 80)
    
    return {
        "device_id": device_id,
        "pm2_5": round(pm2_5, 2),
        "pm10": round(pm10, 2),
        "co": round(co, 2),
        "no2": round(no2, 2),
        "o3": round(o3, 2),
        "so2": round(so2, 2),
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
    }


def ingest_single(reading):
    """Ingest single reading."""
    try:
        response = requests.post(API_URL, json=reading, timeout=5)
        if response.status_code in (200, 201):
            data = response.json()
            print(f"✓ [{datetime.now().strftime('%H:%M:%S')}] AQI={data.get('aqi', 0):.1f} | "
                  f"{data.get('aqi_category', 'N/A')} | {data.get('device_id', 'N/A')}")
            return True
        else:
            print(f"✗ HTTP {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def ingest_bulk(count=24):
    """Ingest multiple readings."""
    readings = [generate_reading() for _ in range(count)]
    try:
        response = requests.post(BULK_API_URL, json=readings, timeout=10)
        if response.status_code in (200, 201):
            data = response.json()
            print(f"✓ Bulk ingested {len(data)} readings")
            print(f"  Sample: AQI={data[0].get('aqi', 0):.1f}, "
                  f"Category={data[0].get('aqi_category', 'N/A')}")
            return True
        else:
            print(f"✗ Bulk failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def continuous_ingest(interval=60):
    """Continuously ingest data."""
    print(f"Starting continuous ingestion (every {interval}s)...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            reading = generate_reading()
            ingest_single(reading)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n✓ Stopped")


if __name__ == "__main__":
    print("=" * 60)
    print("Air Quality Monitor - Data Ingest Tool")
    print("=" * 60 + "\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        continuous_ingest(interval)
    else:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 24
        print(f"Ingesting {count} readings...\n")
        ingest_bulk(count)
        print("\n✓ Done! Visit http://127.0.0.1:8000 to see data")

