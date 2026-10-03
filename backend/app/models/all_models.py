import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship as sql_relationship

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    location_type = Column(String, default="HOME")  # HOME, SHOP_RETAIL, MALL, CINEMA_THEATRE, OFFICE_WAREHOUSE, ROAD_PARKING, OTHER
    onboarding_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    videos = sql_relationship("Video", back_populates="user", cascade="all, delete-orphan")
    cameras = sql_relationship("Camera", back_populates="user", cascade="all, delete-orphan")
    emergency_contacts = sql_relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    detector_settings = sql_relationship("DetectorSetting", back_populates="user", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)  # e.g., "Front Door", "Cash Counter", "Screen 2 Hall"
    location_profile = Column(String, default="HOME")  # HOME, SHOP_RETAIL, MALL, CINEMA_THEATRE, OFFICE_WAREHOUSE, ROAD_PARKING, CUSTOM
    source_type = Column(String, default="upload")  # upload, webcam, rtsp, phone
    stream_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = sql_relationship("User", back_populates="cameras")
    videos = sql_relationship("Video", back_populates="camera")
    zones = sql_relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    schedules = sql_relationship("Schedule", back_populates="camera", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), index=True, nullable=False)
    name = Column(String, nullable=False)  # e.g., "Restricted Counter", "Main Entrance"
    polygon_coords = Column(JSON, nullable=False)  # List of [x, y] normalized coordinates (0.0 to 1.0)
    detector_types = Column(JSON, nullable=True)  # List of detector IDs tied to this zone
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    camera = sql_relationship("Camera", back_populates="zones")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), index=True, nullable=False)
    name = Column(String, nullable=False)  # e.g., "After-hours Monitoring"
    start_time = Column(String, nullable=False)  # "22:00"
    end_time = Column(String, nullable=False)    # "08:00"
    days_of_week = Column(JSON, nullable=True)   # [0, 1, 2, 3, 4, 5, 6] (0 = Mon)
    active_detectors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    camera = sql_relationship("Camera", back_populates="schedules")


class DetectorSetting(Base):
    __tablename__ = "detector_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), index=True, nullable=True)
    detector_type = Column(String, nullable=False)  # e.g. "accident", "theft", "intrusion"
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, nullable=True)  # Thresholds, cooldowns, parameters

    user = sql_relationship("User", back_populates="detector_settings")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), index=True, nullable=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    profile = Column(String, default="ROAD_PARKING")
    source_type = Column(String, default="upload")
    duration_sec = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    poster_path = Column(String, nullable=True)
    has_accident = Column(Boolean, default=False)
    max_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = sql_relationship("User", back_populates="videos")
    camera = sql_relationship("Camera", back_populates="videos")
    analysis_job = sql_relationship("AnalysisJob", back_populates="video", uselist=False, cascade="all, delete-orphan")
    incidents = sql_relationship("Incident", back_populates="video", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True, index=True, nullable=False)
    status = Column(String, default="queued", index=True)  # queued, processing, completed, failed
    progress = Column(Integer, default=0)  # 0 to 100
    error_message = Column(Text, nullable=True)
    annotated_video_path = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    video = sql_relationship("Video", back_populates="analysis_job")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True, nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), index=True, nullable=True)
    type = Column(String, default="ACCIDENT")  # ACCIDENT, THEFT, INTRUSION, LOITERING, FIRE, CROWD_DENSITY, FALL, FIGHT, ABANDONED_OBJECT
    timestamp_sec = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    confidence = Column(Float, default=0.85)
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    accident_score = Column(Integer, default=0)
    bbox = Column(JSON, nullable=True)
    keyframe_thumbnail_path = Column(String, nullable=True)
    involved_tracks_json = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    reviewed_status = Column(String, default="FLAGGED_FOR_REVIEW")  # FLAGGED_FOR_REVIEW, CONFIRMED, FALSE_ALARM
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    video = sql_relationship("Video", back_populates="incidents")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    full_name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)  # Owner, Family, Manager, Security Guard, Neighbour, Police, Other
    phone = Column(String, nullable=False)
    whatsapp = Column(String, nullable=True)
    email = Column(String, nullable=True)
    channels = Column(JSON, nullable=False)  # ["SMS", "WhatsApp", "Email", "Call"]
    priority = Column(Integer, default=1)     # 1 = first, 2 = backup...
    available_hours = Column(JSON, nullable=True)  # {"type": "24x7"} or {"start": "08:00", "end": "20:00"}
    incident_filter = Column(JSON, nullable=True)  # ["ALL"] or ["HIGH", "CRITICAL"]
    camera_scope = Column(JSON, nullable=True)     # ["ALL"] or list of camera IDs
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    opted_out = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = sql_relationship("User", back_populates="emergency_contacts")
    verifications = sql_relationship("ContactVerification", back_populates="contact", cascade="all, delete-orphan")
    alert_logs = sql_relationship("AlertLog", back_populates="contact", cascade="all, delete-orphan")


class ContactVerification(Base):
    __tablename__ = "contact_verifications"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("emergency_contacts.id"), index=True, nullable=False)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contact = sql_relationship("EmergencyContact", back_populates="verifications")


class AlertLog(Base):
    __tablename__ = "alert_log"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), index=True, nullable=True)
    contact_id = Column(Integer, ForeignKey("emergency_contacts.id"), index=True, nullable=False)
    channel = Column(String, nullable=False)  # SMS, WhatsApp, Email, Phone Call
    status = Column(String, default="SENT")    # SENT, DELIVERED, FAILED, ACKNOWLEDGED
    ack_token = Column(String, nullable=True, index=True)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)

    contact = sql_relationship("EmergencyContact", back_populates="alert_logs")
