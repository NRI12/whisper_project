from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime,Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Float

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    lock_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    password_reset_otps = relationship("PasswordResetOTP", back_populates="user")
    transcription_histories = relationship("TranscriptionHistory", back_populates="user")

class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="password_reset_otps")

class TranscriptionHistory(Base):
    __tablename__ = "transcription_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_name = Column(String, nullable=False)
    text = Column(Text, nullable=True)  # Changed from subtitles/JSON to text/Text
    processing = Column(Boolean, default=True)  # Trạng thái xử lý
    created_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=False)
    file_size = Column(Float, nullable=False)  
    video_duration = Column(Float, nullable=True)
    user = relationship("User", back_populates="transcription_histories")