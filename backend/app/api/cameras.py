from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import User, Camera, Zone, Schedule, DetectorSetting
from backend.app.schemas.all_schemas import (
    CameraCreate, CameraOut, ZoneCreate, ZoneOut, ScheduleCreate, ScheduleOut
)
from backend.app.api.auth import require_verified_onboarding
from detectors.registry import DetectorRegistry
from profiles import LOCATION_PROFILES

router = APIRouter(prefix="/api/cameras", tags=["Cameras & Zones"])


@router.get("", response_model=List[CameraOut])
def list_cameras(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    cameras = db.query(Camera).filter(Camera.user_id == current_user.id).order_by(Camera.created_at.desc()).all()
    return cameras


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(
    cam_in: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    camera = Camera(
        user_id=current_user.id,
        name=cam_in.name,
        location_profile=cam_in.location_profile or current_user.location_type or "HOME",
        source_type=cam_in.source_type or "upload",
        stream_url=cam_in.stream_url
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)

    # Initialize default detector settings for camera based on profile
    prof_data = LOCATION_PROFILES.get(camera.location_profile, LOCATION_PROFILES["HOME"])
    active_dets = prof_data.get("active_detectors", [])
    default_threshs = prof_data.get("default_thresholds", {})

    for det_id in DetectorRegistry.get_all().keys():
        is_enabled = det_id in active_dets
        config_override = default_threshs.get(det_id, {})
        ds = DetectorSetting(
            user_id=current_user.id,
            camera_id=camera.id,
            detector_type=det_id,
            enabled=is_enabled,
            config_json=config_override
        )
        db.add(ds)

    db.commit()
    return camera


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    camera = db.query(Camera).filter(Camera.id == camera_id, Camera.user_id == current_user.id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    camera = db.query(Camera).filter(Camera.id == camera_id, Camera.user_id == current_user.id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    db.delete(camera)
    db.commit()
    return None


# Zone Endpoints
@router.get("/{camera_id}/zones", response_model=List[ZoneOut])
def list_camera_zones(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    zones = db.query(Zone).join(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user.id
    ).all()
    return zones


@router.post("/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone_in: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    camera = db.query(Camera).filter(Camera.id == zone_in.camera_id, Camera.user_id == current_user.id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    zone = Zone(
        camera_id=zone_in.camera_id,
        name=zone_in.name,
        polygon_coords=zone_in.polygon_coords,
        detector_types=zone_in.detector_types or ["intrusion", "loitering"]
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    zone = db.query(Zone).join(Camera).filter(
        Zone.id == zone_id,
        Camera.user_id == current_user.id
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    db.delete(zone)
    db.commit()
    return None


# Schedule Endpoints
@router.get("/{camera_id}/schedules", response_model=List[ScheduleOut])
def list_camera_schedules(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    schedules = db.query(Schedule).join(Camera).filter(
        Camera.id == camera_id,
        Camera.user_id == current_user.id
    ).all()
    return schedules


@router.post("/schedules", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    sched_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_onboarding)
):
    camera = db.query(Camera).filter(Camera.id == sched_in.camera_id, Camera.user_id == current_user.id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    sched = Schedule(
        camera_id=sched_in.camera_id,
        name=sched_in.name,
        start_time=sched_in.start_time,
        end_time=sched_in.end_time,
        days_of_week=sched_in.days_of_week,
        active_detectors=sched_in.active_detectors or ["intrusion", "theft"]
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched
