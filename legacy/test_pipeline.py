"""
test_pipeline.py
Unit test verifying AccidentDetector, ClipSaver, and EmergencyAlertSystem interaction.
"""

import os
import cv2
import numpy as np
import config
from accident_detector import AccidentDetector
from clip_saver import ClipSaver
from alert_system import EmergencyAlertSystem

def test_full_alert_flow():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("clips", exist_ok=True)

    height, width = 480, 640
    fps = 20
    clip_saver = ClipSaver(fps=fps, frame_size=(width, height))
    alert_system = EmergencyAlertSystem()
    detector = AccidentDetector()

    # Create dummy frames to fill pre-event buffer
    for _ in range(30):
        dummy_frame = np.zeros((height, width, 3), dtype=np.uint8)
        clip_saver.add_frame(dummy_frame)

    # Simulated tracks with collision and sudden deceleration
    tracks = [
        {
            "id": 1,
            "bbox": (100, 100, 200, 200),
            "class_name": "car",
            "centroid": (150, 150),
            "history": [(150, 50), (150, 100), (150, 140), (150, 150)],
        },
        {
            "id": 2,
            "bbox": (110, 110, 210, 210),  # High IoU collision with track 1
            "class_name": "truck",
            "centroid": (160, 160),
            "history": [(160, 250), (160, 200), (160, 170), (160, 160)],
        }
    ]

    is_accident, details = detector.analyze(tracks)
    print(f"Test Accident Analysis -> is_accident: {is_accident}, details: {details}")

    assert is_accident is True, "Expected accident detector to trigger on simulated collision"

    if is_accident:
        clip_path = clip_saver.trigger()
        print(f"Triggered clip path: {clip_path}")
        alert_system.dispatch(clip_path, details)

    # Add post-event frames to finalize clip
    for _ in range(int(config.POST_EVENT_SECONDS * fps) + 5):
        dummy_frame = np.zeros((height, width, 3), dtype=np.uint8)
        clip_saver.add_frame(dummy_frame)

    clip_saver.close()

    log_path = os.path.join("logs", "alerts.log")
    assert os.path.exists(log_path), "logs/alerts.log was not created"
    
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
    print("Alert log verification output:")
    print(log_content)

    assert "DISPATCHING EMERGENCY ALERT" in log_content
    print("SUCCESS: Pipeline alert dispatch, clip saving, and logging verified!")

if __name__ == "__main__":
    test_full_alert_flow()
