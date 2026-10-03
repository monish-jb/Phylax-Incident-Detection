from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.all_models import User, Incident, Video
from backend.app.schemas.all_schemas import IncidentOut, IncidentReviewUpdate
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    incident_type: Optional[str] = Query(None, alias="type"),
    severity: Optional[str] = None,
    reviewed_status: Optional[str] = None,
    camera_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Incident).join(Video).filter(Video.user_id == current_user.id)

    if incident_type:
        query = query.filter(Incident.type.ilike(f"%{incident_type}%"))
    if severity:
        query = query.filter(Incident.severity == severity.upper())
    if reviewed_status:
        query = query.filter(Incident.reviewed_status == reviewed_status.upper())
    if camera_id:
        query = query.filter(Video.camera_id == camera_id)

    incidents = query.order_by(desc(Incident.created_at)).limit(100).all()
    return incidents


@router.post("/{incident_id}/review", response_model=IncidentOut)
def review_incident(
    incident_id: int,
    review_in: IncidentReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).join(Video).filter(
        Incident.id == incident_id,
        Video.user_id == current_user.id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found or access denied")

    target_status = review_in.status.upper()
    if target_status not in ["CONFIRMED", "FALSE_ALARM", "FLAGGED_FOR_REVIEW"]:
        raise HTTPException(status_code=400, detail="Invalid review status. Allowed values: CONFIRMED, FALSE_ALARM, FLAGGED_FOR_REVIEW")

    incident.reviewed_status = target_status
    db.commit()
    db.refresh(incident)
    return incident
