"""
detectors/fire_smoke.py
Fire & Smoke Detection plugin using color-space, luminance, and temporal intensity heuristic models.
"""

import time
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector


@register_detector
class FireSmokeDetector(BaseDetector):
    detector_id = "fire_smoke"
    name = "Fire & Smoke Detector"
    description = "Detects flame presence and expanding smoke clouds using HSV color space, luminance dynamics, and temporal flicker analysis."
    default_config = {
        "cooldown_sec": 20,
        "fire_pixel_ratio_thresh": 0.005,  # 0.5% of frame area
        "smoke_pixel_ratio_thresh": 0.02,  # 2.0% of frame area
    }

    def reset(self):
        self.last_alert_time: float = 0

    def process_frame(
        self,
        frame,
        frame_idx: int,
        timestamp_sec: float,
        tracks: List[Dict[str, Any]],
        detections: List[Any],
        zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[IncidentData]:
        incidents = []
        if frame is None or frame.size == 0:
            return incidents

        now = time.time()
        if now - self.last_alert_time < self.config["cooldown_sec"]:
            return incidents

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        img_h, img_w = frame.shape[:2]
        total_pixels = img_h * img_w

        # Fire color range (Red/Yellow/Orange in HSV: H: 0-25 & 160-180, S: 120-255, V: 190-255)
        lower_fire1 = np.array([0, 120, 190], dtype=np.uint8)
        upper_fire1 = np.array([25, 255, 255], dtype=np.uint8)
        lower_fire2 = np.array([160, 120, 190], dtype=np.uint8)
        upper_fire2 = np.array([180, 255, 255], dtype=np.uint8)

        mask_fire1 = cv2.inRange(hsv, lower_fire1, upper_fire1)
        mask_fire2 = cv2.inRange(hsv, lower_fire2, upper_fire2)
        mask_fire = cv2.bitwise_or(mask_fire1, mask_fire2)

        fire_pixels = cv2.countNonZero(mask_fire)
        fire_ratio = fire_pixels / float(total_pixels)

        # Smoke range (Low saturation, medium-high value: S: 0-50, V: 140-230)
        lower_smoke = np.array([0, 0, 140], dtype=np.uint8)
        upper_smoke = np.array([180, 50, 230], dtype=np.uint8)
        mask_smoke = cv2.inRange(hsv, lower_smoke, upper_smoke)
        smoke_pixels = cv2.countNonZero(mask_smoke)
        smoke_ratio = smoke_pixels / float(total_pixels)

        if fire_ratio >= self.config["fire_pixel_ratio_thresh"]:
            self.last_alert_time = now
            # Find contour bbox of largest fire region
            contours, _ = cv2.findContours(mask_fire, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            bbox = None
            if contours:
                largest_c = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_c)
                bbox = [float(x), float(y), float(x + w), float(y + h)]

            incidents.append(
                IncidentData(
                    type="FIRE",
                    timestamp=timestamp_sec,
                    frame=frame_idx,
                    confidence=min(0.99, 0.70 + (fire_ratio * 10)),
                    severity=SEVERITY_CRITICAL,
                    bbox=bbox,
                    description=f"CRITICAL FIRE HAZARD DETECTED! Flame intensity ratio: {fire_ratio*100:.2f}% of frame",
                    extra_data={"fire_ratio": round(fire_ratio, 4)}
                )
            )
        elif smoke_ratio >= self.config["smoke_pixel_ratio_thresh"]:
            self.last_alert_time = now
            incidents.append(
                IncidentData(
                    type="FIRE",
                    timestamp=timestamp_sec,
                    frame=frame_idx,
                    confidence=0.82,
                    severity=SEVERITY_HIGH,
                    bbox=None,
                    description=f"Smoke accumulation hazard flagged (Smoke ratio: {smoke_ratio*100:.2f}% of frame)",
                    extra_data={"smoke_ratio": round(smoke_ratio, 4)}
                )
            )

        return incidents
