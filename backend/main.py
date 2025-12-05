# backend/main.py
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

# Local/package imports: try to support both running from project root (as package)
# and running inside the `backend/` folder directly.
try:
    # when run as package (recommended): `uvicorn backend.main:app`
    from backend.database import SessionLocal, engine, Base
    from backend.models import Reading
    from backend.aqi_logic import calculate_aqi, classify_aqi, risk_level_from_aqi
    _UVICORN_TARGET = "backend.main:app"
except Exception:
    # fallback when running inside backend/: `uvicorn main:app`
    from database import SessionLocal, engine, Base
    from models import Reading
    from aqi_logic import calculate_aqi, classify_aqi, risk_level_from_aqi
    _UVICORN_TARGET = "main:app"

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Initialize App
# Initialize App (use lowercase `app` for uvicorn)
app = FastAPI(title="AI Air Quality API")

# Enable CORS for local frontend access (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files so backend serves the UI using absolute path
# Resolve frontend directory robustly: support running from project root or from backend/
CURRENT_FILE = Path(__file__).resolve()
POSSIBLE_FRONTEND = CURRENT_FILE.parent.parent.joinpath('frontend')
if POSSIBLE_FRONTEND.exists():
    FRONTEND_DIR = str(POSSIBLE_FRONTEND)
    app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='static')
else:
    FRONTEND_DIR = None


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class ReadingIn(BaseModel):
    device_id: str
    pm2_5: float 
    pm10:float
    co: float
    no2: float
    o3: float
    so2: float
    temperature: float
    humidity: float


class ReadingOut(BaseModel):
    timestamp: datetime
    device_id: str
    pm2_5: float
    pm10: float
    aqi: float
    aqi_category: str
    risk_level: str

    class Config:
        orm_mode = True

# --- Routes ---
@app.get("/")
def root():
    # Serve the frontend index if available using absolute path
    if FRONTEND_DIR:
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Air Quality API is running"}


@app.post("/api/ingest", response_model=ReadingOut)
def ingest_data(reading: ReadingIn, db: Session = Depends(get_db)):
    aqi = calculate_aqi(reading.pm2_5, reading.pm10)
    aqi_category = classify_aqi(aqi)
    risk_level = risk_level_from_aqi(aqi)

    db_obj = Reading(
        device_id=reading.device_id,
        pm2_5=reading.pm2_5,
        pm10=reading.pm10,
        co=reading.co,
        no2=reading.no2,
        o3=reading.o3,
        so2=reading.so2,
        temperature=reading.temperature,
        humidity=reading.humidity,
        aqi=aqi,
        aqi_category=aqi_category,
        risk_level=risk_level,
    )

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@app.get("/api/latest", response_model=ReadingOut)
def get_latest_reading(db: Session = Depends(get_db)):
    latest = db.query(Reading).order_by(Reading.timestamp.desc()).first()
    if not latest:
        # Return dummy if empty
        return Reading(
            timestamp=datetime.utcnow(), device_id="none",
            pm2_5=0, pm10=0, co=0, no2=0, o3=0, so2=0,
            temperature=0, humidity=0, aqi=0,
            aqi_category="No Data", risk_level="No Data"
        )
    return latest


@app.get("/api/history", response_model=List[ReadingOut])
def get_history(minutes: int = 60, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return db.query(Reading).filter(Reading.timestamp >= cutoff).all()


@app.get("/api/calculate_aqi", response_model=ReadingOut)
def calculate_aqi_endpoint(pm2_5: float, pm10: float):
    aqi = calculate_aqi(pm2_5, pm10)
    aqi_category = classify_aqi(aqi)
    risk_level = risk_level_from_aqi(aqi)

    return ReadingOut(
        timestamp=datetime.utcnow(),
        device_id="calculation_only",
        pm2_5=pm2_5,
        pm10=pm10,
        aqi=aqi,
        aqi_category=aqi_category,
        risk_level=risk_level
    )


@app.post("/api/ingest_bulk", response_model=List[ReadingOut])
def ingest_bulk(readings: List[ReadingIn], db: Session = Depends(get_db)):
    """Accept an array of readings and insert them in a single transaction.
    Each reading will have AQI, category and risk computed server-side.
    Returns list of created rows.
    """
    if not readings:
        return []

    objs = []
    for r in readings:
        aqi = calculate_aqi(r.pm2_5, r.pm10)
        aqi_category = classify_aqi(aqi)
        risk_level = risk_level_from_aqi(aqi)

        obj = Reading(
            device_id=r.device_id,
            pm2_5=r.pm2_5,
            pm10=r.pm10,
            co=r.co,
            no2=r.no2,
            o3=r.o3,
            so2=r.so2,
            temperature=r.temperature,
            humidity=r.humidity,
            aqi=aqi,
            aqi_category=aqi_category,
            risk_level=risk_level,
        )
        objs.append(obj)

    # Add all and commit in one transaction
    db.add_all(objs)
    db.commit()

    # Refresh to populate defaults like timestamp
    for o in objs:
        db.refresh(o)

    return objs


if __name__ == "__main__":
    uvicorn.run(_UVICORN_TARGET, host="127.0.0.1", port=8000, reload=True)