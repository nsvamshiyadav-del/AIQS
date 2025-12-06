# backend/user_models.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel, EmailStr

Base = declarative_base()


class User(Base):
    """User database model for authentication and notifications."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    email_notifications = Column(Boolean, default=True)
    last_notified = Column(DateTime, nullable=True)


# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    email_notifications: bool
    
    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
