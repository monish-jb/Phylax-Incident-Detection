from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.all_models import User, EmergencyContact
from backend.app.schemas.all_schemas import OnboardingStep1, UserOut
from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


@router.get("/status")
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()
    verified_contacts = [c for c in contacts if c.verified]

    # Calculate step (1..5)
    # Step 1: Account Created (done)
    # Step 2: Location Type
    # Step 3: Add Emergency Contacts
    # Step 4: OTP Verification
    # Step 5: Optional First Source Setup / Done
    current_step = 2
    if current_user.location_type:
        current_step = 3
    if len(contacts) > 0:
        current_step = 4
    if len(verified_contacts) > 0:
        current_step = 5

    return {
        "onboarding_completed": current_user.onboarding_completed,
        "location_type": current_user.location_type or "HOME",
        "contacts_count": len(contacts),
        "verified_contacts_count": len(verified_contacts),
        "current_step": current_step
    }


@router.post("/location", response_model=UserOut)
def set_onboarding_location(
    data: OnboardingStep1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.location_type = data.location_type
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/complete")
def complete_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verified_count = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == current_user.id,
        EmergencyContact.verified == True
    ).count()

    if verified_count < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding Protection Guard: At least 1 verified emergency contact is required before proceeding."
        )

    current_user.onboarding_completed = True
    db.commit()

    return {
        "message": "Onboarding completed successfully!",
        "onboarding_completed": True
    }
