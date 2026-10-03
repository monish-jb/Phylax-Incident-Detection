# PHYLAX — GENERAL-PURPOSE AI CAMERA SURVEILLANCE PLATFORM
> **Tagline:** *Detect. Alert. Protect.*

Phylax ("guardian") is an enterprise-grade, full-stack **General-Purpose AI Camera Surveillance & Emergency Dispatch Platform** built with **FastAPI**, **React + Vite**, **SQLAlchemy**, **YOLOv8**, and **DeepSORT**.

---

## 🛡️ Modular Detector Plugin Architecture

Phylax features a clean, extensible plugin system supporting 9 specialized detector plugins:

1. **Accident & Collision Detector** (`detectors/accident.py`): Vehicle impact IoU overlap, sudden deceleration, and erratic spin-outs.
2. **Theft & Shoplifting Detector** (`detectors/theft.py`): Lingering near restricted counters and item concealment behavior.
3. **Perimeter Intrusion Detector** (`detectors/intrusion.py`): Polygon boundary crossing during monitored hours.
4. **Suspicious Loitering Detector** (`detectors/loitering.py`): Stationarity timer in sensitive target zones.
5. **Fire & Smoke Detector** (`detectors/fire_smoke.py`): HSV flame dynamics & smoke mask accumulation.
6. **Crowd Density & Overcrowding Detector** (`detectors/crowd_density.py`): Real-time human capacity tracking.
7. **Fall Detection Plugin** (`detectors/fall.py`): Posture aspect ratio & post-fall immobility verification.
8. **Fight & Physical Violence Detector** (`detectors/fight.py`): Rapid kinetic velocity interaction spikes between tracks.
9. **Abandoned Object Detector** (`detectors/abandoned_object.py`): Stationary luggage/bag detection with no nearby owner.

---

## 🏛️ Location Surveillance Profiles

Select from 6 location presets or configure custom thresholds:
- **Home / Residential**: Intrusion, Fall, Fire/Smoke, Loitering.
- **Shop / Retail Store**: Theft, Loitering, Intrusion, Crowd Density, Fire/Smoke.
- **Shopping Mall**: Crowd Density, Abandoned Object, Theft, Fight, Fire/Smoke.
- **Cinema / Theatre**: Crowd Density, Abandoned Object, Fight, Fire/Smoke, Fall.
- **Office / Warehouse Facility**: Intrusion, After-Hours Movement, Fire/Smoke, Fall.
- **Roadway / Parking Lot**: Vehicle Collisions, Loitering, Fire/Smoke.

---

## 🚨 Emergency Contacts & Alert Escalation

- **Mandatory Onboarding Guard**: Users must add and verify at least one emergency contact before accessing dashboard features.
- **Multi-Channel Dispatch**: SMS, WhatsApp, Email, and Voice Call notification logging.
- **Token-Based Acknowledgment**: Signed JWT token links allow contacts to acknowledge alert dispatches.
- **Operator Review Workflow**: All detections are labeled `"FLAGGED_FOR_REVIEW"` for human verification before status is updated to `CONFIRMED` or `FALSE_ALARM`.

---

## 📄 Audit & Report Exporting

- **JSON Report Export**: Download complete incident timeline audit logs.
- **PDF/HTML Printable Report**: Download styled surveillance executive summary.

---

## 🚀 Quick Start Guide

### 1. Database Setup & Seeding
Populate demo user accounts and default emergency contacts:
```bash
python seed_demo_data.py
```
- **Demo Account**: Username `demo` | Password `demo123`
- **Command Account**: Username `command` | Password `control123`

### 2. Run Backend API Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`

### 3. Run Frontend Console
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:3000`