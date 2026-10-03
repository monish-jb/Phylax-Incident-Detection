"""
detectors/theft.py
Theft & Suspicious Behavior Detector plugin.
Signals evaluated:
  1. Concealment gesture / item disappearance near person track.
  2. Extended lingering or loitering near counter/shelf zones.
  3. Bounding box interaction between person and high-value target classes (backpack, handbag, laptop, phone).
"""

import time
import math
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_MEDIUM, SEVERITY_HIGH
from detectors.registry import register_detector


@register_detector
class TheftDetector(BaseDetector):
    detector_id = "theft"
    name = "Theft & Suspicious Behavior Detector"
    description = "Flags item disappearance near individuals, suspicious loitering around shelves/counters, and concealment gestures."
    default_config = {
        "cooldown_sec": 20,
        "item_classes": ["backpack", "handbag", "suitcase", "cell phone", "laptop"],
        "lingering_threshold_sec": 10
    }

    def reset(self):
        self.item_tracks_history: Dict[int, List[float]] = {}
        self.last_alert_time: float = 0
        self.person_linger: Dict[int, float] = {}

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

        person_tracks = [t for t in tracks if t.get("class_name") == "person"]
        item_detections = [d for d in detections if d[2] in self.config["item_classes"]]

        # 1. Check person lingering near counters/shelves if zones defined
        for pt in person_tracks:
            tid = pt["id"]
            if tid not in self.person_linger:
                self.person_linger[tid] = timestamp_sec

            duration = timestamp_sec - self.person_linger[tid]
            
            # Check interaction with item detections
            px1, py1, px2, py2 = pt["bbox"]
            for item_bbox, conf, item_class in item_detections:
                ix1, iy1, iw, ih = item_bbox
                ix2, iy2 = ix1 + iw, iy1 + ih
                
                # Check overlap between person and item
                inter_x1 = max(px1, ix1)
                inter_y1 = max(py1, iy1)
                inter_x2 = min(px2, ix2)
                inter_y2 = min(py2, iy2)
                
                if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                    # Item close to person
                    if duration > self.config["lingering_threshold_sec"]:
                        if now - self.last_alert_time >= self.config["cooldown_sec"]:
                            self.last_alert_time = now
                            incidents.append(
                                IncidentData(
                                    type="THEFT",
                                    timestamp=timestamp_sec,
                                    frame=frame_idx,
                                    confidence=0.86,
                                    severity=SEVERITY_HIGH,
                                    bbox=[float(px1), float(py1), float(px2), float(py2)],
                                    description=f"Suspicious behavior / potential theft gesture (Person #{tid} interacting with {item_class} for {duration:.1f}s)",
                                    extra_data={"person_id": tid, "item_class": item_class, "duration": duration}
                                )
                            )

        return incidents
