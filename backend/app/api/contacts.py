import hashlib
import datetime
import random
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import User, EmergencyContact, ContactVerification, AlertLog
from backend.app.schemas.all_schemas import (
    EmergencyContactCreate, EmergencyContactUpdate, EmergencyContactOut,
    SendOTPRequest, VerifyOTPRequest
)
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["Emergency Contacts"])


def validate_phone(phone: str) -> bool:
    """Basic phone validation for standard E.164 formats."""
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.match(r"^\+?[1-9]\d{7,14}$", clean_phone))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


@router.get("", response_model=List[EmergencyContactOut])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id
    ).order_by(EmergencyContact.priority.asc()).all()
    return contacts


@router.post("", response_model=EmergencyContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_in: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce maximum 5 emergency contacts
    existing_count = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).count()
    if existing_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum limit of 5 emergency contacts reached"
        )

    if not validate_phone(contact_in.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Please include country code (e.g. +1234567890)"
        )

    # Duplicate phone check for this user
    duplicate = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id,
        EmergencyContact.phone == contact_in.phone
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An emergency contact with this phone number already exists"
        )

    contact = EmergencyContact(
        user_id=current_user.id,
        full_name=contact_in.full_name,
        relationship=contact_in.relationship,
        phone=contact_in.phone,
        whatsapp=contact_in.whatsapp or (contact_in.phone if "WhatsApp" in contact_in.channels else None),
        email=contact_in.email,
        channels=contact_in.channels,
        priority=contact_in.priority or (existing_count + 1),
        available_hours=contact_in.available_hours,
        incident_filter=contact_in.incident_filter,
        camera_scope=contact_in.camera_scope,
        verified=False
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    # Auto-generate verification OTP
    raw_otp = "123456" if contact.phone.endswith("0000") else f"{random.randint(100000, 999999)}"
    code_hash = hash_otp(raw_otp)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

    verification = ContactVerification(
        contact_id=contact.id,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0
    )
    db.add(verification)
    db.commit()

    print(f"[PHYLAX OTP DISPATCH] Contact #{contact.id} ({contact.full_name}, {contact.phone}) OTP: {raw_otp}")

    return contact


@router.put("/{contact_id}", response_model=EmergencyContactOut)
def update_contact(
    contact_id: int,
    contact_in: EmergencyContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    update_data = contact_in.dict(exclude_unset=True)
    if "phone" in update_data and update_data["phone"]:
        if not validate_phone(update_data["phone"]):
            raise HTTPException(status_code=400, detail="Invalid phone number format")

    for field, val in update_data.items():
        setattr(contact, field, val)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    total_contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).count()
    if total_contacts <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory Protection Policy: You cannot delete your last remaining emergency contact."
        )

    db.delete(contact)
    db.commit()
    return None


@router.post("/send-otp")
def send_contact_otp(
    req: SendOTPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == req.contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    raw_otp = "123456" if contact.phone.endswith("0000") else f"{random.randint(100000, 999999)}"
    code_hash = hash_otp(raw_otp)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

    # Delete existing active verifications
    db.query(ContactVerification).filter(ContactVerification.contact_id == contact.id).delete()

    verification = ContactVerification(
        contact_id=contact.id,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0
    )
    db.add(verification)
    db.commit()

    print(f"[PHYLAX OTP RESEND] Contact #{contact.id} ({contact.full_name}, {contact.phone}) OTP: {raw_otp}")

    return {
        "message": f"Verification code sent via {req.channel}",
        "contact_id": contact.id,
        "dev_code": raw_otp  # Included for seamless local testing
    }


@router.post("/verify-otp")
def verify_contact_otp(
    req: VerifyOTPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == req.contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    verification = db.query(ContactVerification).filter(
        ContactVerification.contact_id == contact.id
    ).order_by(ContactVerification.created_at.desc()).first()

    if not verification:
        raise HTTPException(status_code=400, detail="No active verification request found. Please request a new OTP.")

    if verification.attempts >= 5:
        raise HTTPException(status_code=400, detail="Maximum OTP verification attempts exceeded. Please resend code.")

    if datetime.datetime.utcnow() > verification.expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new OTP.")

    verification.attempts += 1
    db.commit()

    submitted_hash = hash_otp(req.code)
    # Also allow universal dev code "123456" for convenience in testing
    if submitted_hash != verification.code_hash and req.code != "123456":
        raise HTTPException(status_code=400, detail="Invalid verification code")

    contact.verified = True
    contact.verified_at = datetime.datetime.utcnow()
    db.commit()

    # If user has at least one verified contact, mark onboarding as completed!
    verified_contacts_count = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id,
        EmergencyContact.verified == True
    ).count()

    if verified_contacts_count >= 1:
        current_user.onboarding_completed = True
        db.commit()

    return {
        "message": "Emergency contact verified successfully!",
        "contact": EmergencyContactOut.from_orm(contact),
        "onboarding_completed": current_user.onboarding_completed
    }


@router.post("/{contact_id}/test-alert")
def send_test_alert(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found")

    log_entry = AlertLog(
        incident_id=None,
        contact_id=contact.id,
        channel=contact.channels[0] if contact.channels else "SMS",
        status="SENT",
        ack_token="TEST_ACK_TOKEN"
    )
    db.add(log_entry)
    db.commit()

    print(f"[PHYLAX TEST ALERT] Dispatching test notification to {contact.full_name} ({contact.phone}) via {log_entry.channel}")

    return {
        "message": f"Test alert dispatched to {contact.full_name} via {log_entry.channel}",
        "status": "SENT"
    }
