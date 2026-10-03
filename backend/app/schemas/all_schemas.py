from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    location_type: Optional[str] = "HOME"
    onboarding_completed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# Onboarding Schemas
class OnboardingStep1(BaseModel):
    location_type: str  # HOME, SHOP_RETAIL, MALL, CINEMA_THEATRE, OFFICE_WAREHOUSE, ROAD_PARKING, OTHER


# Emergency Contact Schemas
class EmergencyContactCreate(BaseModel):
    full_name: str
    relationship: str  # Owner, Family, Manager, Security Guard, Neighbour, Police, Other
    phone: str
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    channels: List[str] = ["SMS"]  # SMS, WhatsApp, Email, Phone Call
    priority: int = 1
    available_hours: Optional[Dict[str, Any]] = {"type": "24x7"}
    incident_filter: Optional[List[str]] = ["ALL"]
    camera_scope: Optional[List[str]] = ["ALL"]


class EmergencyContactUpdate(BaseModel):
    full_name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    channels: Optional[List[str]] = None
    priority: Optional[int] = None
    available_hours: Optional[Dict[str, Any]] = None
    incident_filter: Optional[List[str]] = None
    camera_scope: Optional[List[str]] = None


class EmergencyContactOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    relationship: str
    phone: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    channels: List[str]
    priority: int
    available_hours: Optional[Dict[str, Any]] = None
    incident_filter: Optional[List[str]] = None
    camera_scope: Optional[List[str]] = None
    verified: bool
    verified_at: Optional[datetime] = None
    opted_out: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SendOTPRequest(BaseModel):
    contact_id: int
    channel: str = "SMS"  # SMS or Email


class VerifyOTPRequest(BaseModel):
    contact_id: int
    code: str


# Camera Schemas
class CameraCreate(BaseModel):
    name: str
    location_profile: str = "HOME"
    source_type: str = "upload"
    stream_url: Optional[str] = None


class CameraOut(BaseModel):
    id: int
    user_id: int
    name: str
    location_profile: str
    source_type: str
    stream_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Zone Schemas
class ZoneCreate(BaseModel):
    camera_id: int
    name: str
    polygon_coords: List[List[float]]  # list of [x, y]
    detector_types: Optional[List[str]] = None


class ZoneOut(BaseModel):
    id: int
    camera_id: int
    name: str
    polygon_coords: List[List[float]]
    detector_types: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Schedule Schemas
class ScheduleCreate(BaseModel):
    camera_id: int
    name: str
    start_time: str
    end_time: str
    days_of_week: Optional[List[int]] = [0, 1, 2, 3, 4, 5, 6]
    active_detectors: Optional[List[str]] = None


class ScheduleOut(BaseModel):
    id: int
    camera_id: int
    name: str
    start_time: str
    end_time: str
    days_of_week: Optional[List[int]] = None
    active_detectors: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Incident Schemas
class IncidentOut(BaseModel):
    id: int
    video_id: int
    zone_id: Optional[int] = None
    type: str = "ACCIDENT"
    timestamp_sec: float
    frame_number: int
    confidence: float
    severity: str
    accident_score: int
    bbox: Optional[Any] = None
    keyframe_thumbnail_path: Optional[str] = None
    involved_tracks_json: Optional[Any] = None
    description: Optional[str] = None
    reviewed_status: str = "FLAGGED_FOR_REVIEW"
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentReviewUpdate(BaseModel):
    status: str  # CONFIRMED or FALSE_ALARM


# AnalysisJob Schemas
class JobOut(BaseModel):
    id: int
    video_id: int
    status: str
    progress: int
    error_message: Optional[str] = None
    annotated_video_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Video Schemas
class VideoOut(BaseModel):
    id: int
    user_id: int
    camera_id: Optional[int] = None
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    profile: Optional[str] = "ROAD_PARKING"
    source_type: Optional[str] = "upload"
    duration_sec: float
    width: int
    height: int
    fps: float
    poster_path: Optional[str] = None
    has_accident: bool
    max_score: int
    created_at: datetime
    analysis_job: Optional[JobOut] = None
    incidents: List[IncidentOut] = []

    class Config:
        from_attributes = True


class VideoListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[VideoOut]


# Alert Log Schemas
class AlertLogOut(BaseModel):
    id: int
    incident_id: Optional[int] = None
    contact_id: int
    channel: str
    status: str
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_videos: int
    total_accidents: int
    total_incidents: int
    avg_confidence: float
    active_jobs: int
    activity_grid: List[dict]
