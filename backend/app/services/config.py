"""
config.py
Central place for all tunable parameters and credentials.
Fill in the ALERT/TWILIO/EMAIL section with real credentials before going live.
For a hackathon demo, leave DRY_RUN = True so alerts just print to console/log
instead of actually calling Twilio / SMTP (no real numbers get called).
"""

# ---------------- Video / Detection ----------------
VIDEO_SOURCE = 0                  # 0 = webcam, or path to a video file e.g. "test_videos/crash1.mp4"
YOLO_MODEL_PATH = "yolov8n.pt"    # nano model = fastest, good for demo. Use yolov8s.pt for more accuracy
VEHICLE_CLASSES = ["car", "motorcycle", "bus", "truck"]  # COCO class names we care about
CONF_THRESHOLD = 0.35
IOU_NMS_THRESHOLD = 0.45

# ---------------- Tracking ----------------
MAX_TRACK_AGE = 30                # frames a track can go undetected before being dropped
TRACK_HISTORY_LEN = 15            # how many past centroids we keep per track for speed calc

# ---------------- Accident Heuristics ----------------
SPEED_DROP_RATIO = 0.6            # e.g. 0.6 = speed must fall by 60%+ to count as "sudden stop"
MIN_SPEED_TO_CONSIDER = 4.0       # px/frame -- ignore vehicles that were basically stationary anyway
COLLISION_IOU_THRESHOLD = 0.15    # bounding box overlap ratio that counts as "possible collision"
ACCIDENT_SCORE_THRESHOLD = 2      # combined heuristic score needed to trigger an alert
ALERT_COOLDOWN_SECONDS = 30       # don't re-alert for the same incident within this window

# ---------------- Clip Saving ----------------
PRE_EVENT_SECONDS = 5             # seconds of footage to keep BEFORE the accident (rolling buffer)
POST_EVENT_SECONDS = 5            # seconds to keep recording AFTER the accident is flagged
CLIP_OUTPUT_DIR = "clips"
CLIP_FPS_FALLBACK = 20            # used if the video source doesn't report FPS correctly

# ---------------- Alerts ----------------
DRY_RUN = True                    # True = simulate alerts (safe for demo). Set False for real dispatch.

# Twilio (SMS + voice call) -- https://www.twilio.com/console
TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_FROM_NUMBER = "+10000000000"

EMERGENCY_CONTACTS = {
    "police":    {"phone": "+10000000001", "email": "police@example.com"},
    "ambulance": {"phone": "+10000000002", "email": "ambulance@example.com"},
    "fire":      {"phone": "+10000000003", "email": "fire@example.com"},
}

# Email (SMTP)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"   # use an app password, not your real password

# Location metadata attached to alerts (replace with GPS module / fixed camera location)
CAMERA_LOCATION = "Camera-01, MG Road Junction, Sample City"
CAMERA_GPS = (11.0, 77.0)   # (lat, lon) placeholder
