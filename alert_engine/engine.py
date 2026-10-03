"""
alert_engine/engine.py
Alert Engine dispatcher, token signer, escalation manager, and cooldown control.
"""

import time
import datetime
from typing import List, Dict, Any, Optional
import jwt
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.all_models import Incident, EmergencyContact, AlertLog, Video, Camera, User
from alert_engine.providers import MockConsoleProvider, TwilioSMSProvider, EmailSMTPProvider

_last_alert_timestamps: Dict[str, float] = {}  # key -> timestamp


def generate_ack_token(incident_id: int, contact_id: int) -> str:
    """Generate signed JWT token valid for 2 hours for single-click incident acknowledgment."""
    payload = {
        "inc_id": incident_id,
        "cnt_id": contact_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_ack_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None


class AlertEngine:
    def __init__(self, db: Session):
        self.db = db
        self.mock_provider = MockConsoleProvider()
        self.sms_provider = TwilioSMSProvider()
        self.email_provider = EmailSMTPProvider()

    def _is_cooldown_active(self, key: str, cooldown_sec: int = 30) -> bool:
        now = time.time()
        last_t = _last_alert_timestamps.get(key, 0)
        if now - last_t < cooldown_sec:
            return True
        _last_alert_timestamps[key] = now
        return False

    def _check_contact_available(self, contact: EmergencyContact, severity: str) -> bool:
        if contact.opted_out:
            return False

        # Incident filter check
        filters = contact.incident_filter or ["ALL"]
        if "ALL" not in filters:
            if severity.upper() not in [f.upper() for f in filters]:
                return False

        # Hours check
        hours = contact.available_hours or {"type": "24x7"}
        if hours.get("type") == "range":
            try:
                now_time = datetime.datetime.utcnow().time()
                start = datetime.datetime.strptime(hours["start"], "%H:%M").time()
                end = datetime.datetime.strptime(hours["end"], "%H:%M").time()
                if start <= end:
                    if not (start <= now_time <= end):
                        return False
                else:
                    if not (now_time >= start or now_time <= end):
                        return False
            except Exception:
                pass

        return True

    def dispatch_incident_alert(self, incident: Incident, video: Video, user: User) -> List[AlertLog]:
        # Cooldown check per video/user
        cooldown_key = f"user_{user.id}_video_{video.id}_{incident.type}"
        if self._is_cooldown_active(cooldown_key, cooldown_sec=30):
            print(f"[ALERT ENGINE] Cooldown active for {cooldown_key}. Suppressing alert.")
            return []

        # Get sorted verified emergency contacts by priority
        contacts = self.db.query(EmergencyContact).filter(
            EmergencyContact.user_id == user.id,
            EmergencyContact.verified == True
        ).order_by(EmergencyContact.priority.asc()).all()

        if not contacts:
            print(f"[ALERT ENGINE] No verified emergency contacts for User #{user.id}. Alert not dispatched.")
            return []

        # Target Contact #1 initially (escalation targets next if unacknowledged)
        target_contact = None
        for c in contacts:
            if self._check_contact_available(c, incident.severity):
                target_contact = c
                break

        if not target_contact:
            target_contact = contacts[0]

        logs = []
        camera_name = video.camera.name if video.camera else f"Source #{video.id} ({video.original_filename})"
        title = f"[PHYLAX SECURITY ALERT] {incident.type} Flagged on {camera_name}"
        
        for channel in target_contact.channels:
            token = generate_ack_token(incident.id, target_contact.id)
            ack_url = f"http://localhost:8000/api/alerts/acknowledge?token={token}"

            message = (
                f"Incident: {incident.type}\n"
                f"Severity: {incident.severity.upper()}\n"
                f"Location / Camera: {camera_name}\n"
                f"Time: {incident.timestamp_sec:.1f}s (Frame #{incident.frame_number})\n"
                f"Description: {incident.description or 'Event flagged for human review'}\n\n"
                f"Note: Phylax alerts contacts chosen by user; it does NOT auto-call emergency services."
            )

            metadata = {"ack_url": ack_url, "incident_id": incident.id}

            # Select channel provider
            success = False
            if channel == "SMS":
                success = self.sms_provider.send(target_contact.phone, title, message, metadata)
            elif channel == "Email" and target_contact.email:
                success = self.email_provider.send(target_contact.email, title, message, metadata)
            else:
                success = self.mock_provider.send(target_contact.phone, title, message, metadata)

            log_entry = AlertLog(
                incident_id=incident.id,
                contact_id=target_contact.id,
                channel=channel,
                status="SENT" if success else "FAILED",
                ack_token=token,
                sent_at=datetime.datetime.utcnow()
            )
            self.db.add(log_entry)
            logs.append(log_entry)

        self.db.commit()
        return logs

    def acknowledge_alert(self, token: str) -> Optional[AlertLog]:
        payload = verify_ack_token(token)
        if not payload:
            return None

        inc_id = payload.get("inc_id")
        cnt_id = payload.get("cnt_id")

        log_entry = self.db.query(AlertLog).filter(
            AlertLog.incident_id == inc_id,
            AlertLog.contact_id == cnt_id
        ).order_by(AlertLog.sent_at.desc()).first()

        if log_entry:
            log_entry.status = "ACKNOWLEDGED"
            log_entry.acknowledged_at = datetime.datetime.utcnow()
            self.db.commit()
            return log_entry

        return None
