# backend/models.py
from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
try:
    # When imported as package (recommended)
    from backend.database import Base
except Exception:
    # Fallback when running inside the backend/ folder directly
    from database import Base

# backend/models.py


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String, index=True)

    pm2_5 = Column(Float)
    pm10 = Column(Float)
    co = Column(Float)
    no2 = Column(Float)
    o3 = Column(Float)
    so2 = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)

    aqi = Column(Float)
    aqi_category = Column(String)
    risk_level = Column(String)
