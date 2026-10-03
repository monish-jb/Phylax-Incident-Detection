"""
seed_demo_data.py
Populates Phylax with demo user, emergency contacts, location profiles, and sample video surveillance feeds.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.core.database import SessionLocal, engine, Base, migrate_db
from backend.app.models.all_models import User, Camera, Zone, EmergencyContact, Video, AnalysisJob, Incident
from backend.app.core.security import get_password_hash
from detectors.registry import DetectorRegistry
import detectors  # ensures all plugins are registered

def seed():
    Base.metadata.create_all(bind=engine)
    migrate_db()
    db = SessionLocal()

    try:
        # 1. Create or get Demo User
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            demo_user = User(
                email="demo@phylax.ai",
                username="demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Phylax Security Officer",
                location_type="SHOP_RETAIL",
                onboarding_completed=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print("Created demo user: demo / demo123")

        # Create or update command user
        cmd_user = db.query(User).filter(User.username == "command").first()
        if not cmd_user:
            cmd_user = User(
                email="command@control.gov",
                username="command",
                hashed_password=get_password_hash("control123"),
                full_name="Incident Command Officer",
                location_type="ROAD_PARKING",
                onboarding_completed=True
            )
            db.add(cmd_user)
            db.commit()
            db.refresh(cmd_user)
            print("Created command user: command / control123")

        # 2. Add verified emergency contact for demo user
        contact = db.query(EmergencyContact).filter(EmergencyContact.user_id == demo_user.id).first()
        if not contact:
            contact = EmergencyContact(
                user_id=demo_user.id,
                full_name="Chief Security Officer",
                relationship="Manager",
                phone="+15550192834",
                whatsapp="+15550192834",
                email="security@store.com",
                channels=["SMS", "WhatsApp", "Email"],
                priority=1,
                verified=True
            )
            db.add(contact)
            db.commit()

        # Add contact for command user as well
        cmd_contact = db.query(EmergencyContact).filter(EmergencyContact.user_id == cmd_user.id).first()
        if not cmd_contact:
            cmd_contact = EmergencyContact(
                user_id=cmd_user.id,
                full_name="Dispatch Control Room",
                relationship="Owner",
                phone="+15559876543",
                whatsapp="+15559876543",
                email="dispatch@control.gov",
                channels=["SMS", "Email"],
                priority=1,
                verified=True
            )
            db.add(cmd_contact)
            db.commit()

        print("Seeded verified emergency contacts for demo and command accounts.")

        # 3. Create sample Cameras
        cam1 = db.query(Camera).filter(Camera.user_id == demo_user.id, Camera.name == "Retail Entrance Cam").first()
        if not cam1:
            cam1 = Camera(
                user_id=demo_user.id,
                name="Retail Entrance Cam",
                location_profile="SHOP_RETAIL",
                source_type="upload"
            )
            db.add(cam1)
            db.commit()
            db.refresh(cam1)

        cam2 = db.query(Camera).filter(Camera.user_id == cmd_user.id, Camera.name == "Main Intersection Cam").first()
        if not cam2:
            cam2 = Camera(
                user_id=cmd_user.id,
                name="Main Intersection Cam",
                location_profile="ROAD_PARKING",
                source_type="upload"
            )
            db.add(cam2)
            db.commit()

        print("Seeded camera profiles.")
        print("Demo database seeding complete!")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
