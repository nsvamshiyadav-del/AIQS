# backend/main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Local/package imports: try to support both running from project root (as package)
# and running inside the `backend/` folder directly.
try:
    # when run as package (recommended): `uvicorn backend.main:app`
    from backend.database import SessionLocal, engine, Base
    from backend.models import Reading
    from backend.aqi_logic import calculate_aqi, classify_aqi, risk_level_from_aqi
    from backend.user_models import User
    from backend.auth import hash_password, verify_password, create_access_token, get_current_user
    from backend.user_models import UserCreate, UserLogin, UserResponse, TokenResponse
    from backend.email_service import send_notification_email, send_welcome_email
    _UVICORN_TARGET = "backend.main:app"
except Exception:
    # fallback when running inside backend/: `uvicorn main:app`
    from database import SessionLocal, engine, Base
    from models import Reading
    from aqi_logic import calculate_aqi, classify_aqi, risk_level_from_aqi
    from user_models import User
    from auth import hash_password, verify_password, create_access_token, get_current_user
    from user_models import UserCreate, UserLogin, UserResponse, TokenResponse
    from email_service import send_notification_email, send_welcome_email
    _UVICORN_TARGET = "main:app"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Initialize App
app = FastAPI(title="AI Air Quality API")

# Store for notification data
notification_store = {"latest": None, "notifications": []}
scheduler = None

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

class ReadingIn(BaseModel):
    device_id: str
    pm2_5: float 
    pm10: float
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


class NotificationMessage(BaseModel):
    timestamp: str
    message: str
    aqi: float
    category: str
    risk_level: str


# --- Hourly Data Collection & Notification ---
def collect_and_notify():
    """Collect data hourly and generate notifications."""
    try:
        db = SessionLocal()
        
        # Get latest reading
        latest = db.query(Reading).order_by(Reading.timestamp.desc()).first()
        
        if latest:
            # Generate notification message
            msg = f"🌍 Hourly Air Quality Report: AQI is {latest.aqi:.1f} ({latest.aqi_category}). Risk Level: {latest.risk_level}"
            
            notification = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": msg,
                "aqi": latest.aqi,
                "category": latest.aqi_category,
                "risk_level": latest.risk_level,
                "device_id": latest.device_id
            }
            
            # Store notification (keep last 24 hours worth)
            notification_store["latest"] = notification
            notification_store["notifications"].append(notification)
            
            # Keep only last 100 notifications (roughly 4 days at hourly)
            if len(notification_store["notifications"]) > 100:
                notification_store["notifications"] = notification_store["notifications"][-100:]
            
            logger.info(f"Hourly notification sent: {msg}")
            
            # Send emails to users with notifications enabled
            try:
                users = db.query(User).filter(User.is_active == True, User.email_notifications == True).all()
                for user in users:
                    send_notification_email(
                        user.email,
                        latest.aqi,
                        latest.aqi_category,
                        latest.risk_level
                    )
                    user.last_notified = datetime.utcnow()
                db.commit()
                logger.info(f"Sent email notifications to {len(users)} users")
            except Exception as e:
                logger.error(f"Error sending emails: {e}")
        
        db.close()
    except Exception as e:
        logger.error(f"Error in collect_and_notify: {e}")


def start_scheduler():
    """Start background scheduler for hourly tasks."""
    global scheduler
    try:
        scheduler = BackgroundScheduler()
        # Schedule hourly collection and notification at minute 0 of each hour
        scheduler.add_job(collect_and_notify, 'interval', hours=1, id='hourly_collect')
        scheduler.start()
        logger.info("Scheduler started: hourly data collection enabled")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")


# --- Pydantic Models ---

# --- Routes ---
@app.on_event("startup")
async def startup_event():
    """Start scheduler on app startup."""
    start_scheduler()
    logger.info("App started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on app shutdown."""
    global scheduler
    if scheduler:
        scheduler.shutdown()
    logger.info("App shut down")


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
    
    # Trigger immediate notification on data ingest
    collect_and_notify()
    
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

    # Trigger notification after bulk ingest
    collect_and_notify()

    return objs


# --- User Authentication Endpoints ---
@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        email_notifications=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email
    send_welcome_email(new_user.email, new_user.username)
    
    # Create token
    access_token = create_access_token(data={"sub": new_user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user)
    }


@app.post("/api/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user."""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@app.put("/api/auth/notifications/{enabled}")
def toggle_notifications(enabled: bool, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggle email notifications for user."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.email_notifications = enabled
    db.commit()
    return {"email_notifications": user.email_notifications}


# --- Notification Endpoints ---
@app.get("/api/notifications")
def get_notifications(limit: int = 10):
    """Get recent notifications."""
    notifications = notification_store["notifications"][-limit:]
    return {"notifications": notifications, "latest": notification_store["latest"]}


@app.get("/api/latest-notification")
def get_latest_notification() -> Optional[dict]:
    """Get the latest notification."""
    return notification_store["latest"]


@app.post("/api/trigger-notification")
def trigger_notification_manual(db: Session = Depends(get_db)):
    """Manual trigger for testing notifications."""
    collect_and_notify()
    return {"status": "Notification triggered", "latest": notification_store["latest"]}


if __name__ == "__main__":
    uvicorn.run(_UVICORN_TARGET, host="127.0.0.1", port=8000, reload=True)