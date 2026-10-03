from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.all_models import User, AlertLog, EmergencyContact
from backend.app.schemas.all_schemas import AlertLogOut
from backend.app.api.auth import get_current_user
from alert_engine.engine import AlertEngine

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/log", response_model=List[AlertLogOut])
def get_alert_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logs = db.query(AlertLog).join(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id
    ).order_by(desc(AlertLog.sent_at)).limit(100).all()
    return logs


@router.get("/acknowledge")
def acknowledge_alert_get(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    engine = AlertEngine(db)
    log_entry = engine.acknowledge_alert(token)
    if not log_entry:
        raise HTTPException(status_code=400, detail="Invalid, expired, or previously processed acknowledgment token")

    return {
        "status": "SUCCESS",
        "message": "Incident alert acknowledged successfully. Escalation chain stopped.",
        "log_id": log_entry.id,
        "acknowledged_at": log_entry.acknowledged_at
    }


@router.post("/acknowledge")
def acknowledge_alert_post(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    return acknowledge_alert_get(token=token, db=db)
