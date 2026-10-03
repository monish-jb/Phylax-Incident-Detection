"""
detectors/intrusion.py
Intrusion & Restricted Zone Violation Detector plugin.
"""

import time
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector


def point_in_polygon(x: float, y: float, polygon: List[List[float]], img_w: int, img_h: int) -> bool:
    """Check if normalized or pixel point (x, y) lies inside polygon using OpenCV."""
    pts = []
    for pt in polygon:
        px = int(pt[0] * img_w) if pt[0] <= 1.0 else int(pt[0])
        py = int(pt[1] * img_h) if pt[1] <= 1.0 else int(pt[1])
        pts.append([px, py])
    poly_np = np.array(pts, dtype=np.int32)
    res = cv2.pointPolygonTest(poly_np, (float(x), float(y)), False)
    return res >= 0


@register_detector
class IntrusionDetector(BaseDetector):
    detector_id = "intrusion"
    name = "Intrusion & Restricted Zone Detector"
    description = "Detects unauthorized human presence within designated restricted polygon zones or during off-hours."
    default_config = {
        "cooldown_sec": 15,
        "target_classes": ["person"],
        "after_hours_mode": False
    }

    def reset(self):
        self.last_alert_time: float = 0
        self.alerted_tracks = set()

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
        now = time.time()
        img_h, img_w = frame.shape[:2] if frame is not None else (720, 1280)

        person_tracks = [t for t in tracks if t.get("class_name") in self.config["target_classes"]]

        # Check zone intrusion if zones provided
        for pt in person_tracks:
            tid = pt["id"]
            cx, cy = pt["centroid"]
            x1, y1, x2, y2 = pt["bbox"]

            if zones:
                for zone in zones:
                    poly = zone.get("polygon_coords", [])
                    if poly and point_in_polygon(cx, cy, poly, img_w, img_h):
                        if tid not in self.alerted_tracks and (now - self.last_alert_time >= self.config["cooldown_sec"]):
                            self.last_alert_time = now
                            self.alerted_tracks.add(tid)
                            incidents.append(
                                IncidentData(
                                    type="INTRUSION",
                                    timestamp=timestamp_sec,
                                    frame=frame_idx,
                                    confidence=0.95,
                                    severity=SEVERITY_CRITICAL if self.config.get("after_hours_mode") else SEVERITY_HIGH,
                                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                                    zone_id=zone.get("id"),
                                    description=f"Intrusion detected in zone '{zone.get('name', 'Restricted')}' by Person #{tid}",
                                    extra_data={"track_id": tid, "zone_name": zone.get("name")}
                                )
                            )
            elif self.config.get("after_hours_mode") and len(person_tracks) > 0:
                # After hours intrusion anywhere in camera frame
                if tid not in self.alerted_tracks and (now - self.last_alert_time >= self.config["cooldown_sec"]):
                    self.last_alert_time = now
                    self.alerted_tracks.add(tid)
                    incidents.append(
                        IncidentData(
                            type="INTRUSION",
                            timestamp=timestamp_sec,
                            frame=frame_idx,
                            confidence=0.91,
                            severity=SEVERITY_CRITICAL,
                            bbox=[float(x1), float(y1), float(x2), float(y2)],
                            description=f"After-hours security breach: Person #{tid} detected in monitored area",
                            extra_data={"track_id": tid}
                        )
                    )

        return incidents
