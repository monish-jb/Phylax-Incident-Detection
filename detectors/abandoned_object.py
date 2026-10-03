"""
detectors/abandoned_object.py
Abandoned Object Detector plugin.
"""

import time
import math
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_MEDIUM, SEVERITY_HIGH
from detectors.registry import register_detector


@register_detector
class AbandonedObjectDetector(BaseDetector):
    detector_id = "abandoned_object"
    name = "Abandoned Object Detector"
    description = "Detects stationary luggage, bags, or items left unattended without any nearby owner for extended durations."
    default_config = {
        "cooldown_sec": 20,
        "object_classes": ["backpack", "handbag", "suitcase"],
        "abandoned_sec_threshold": 10.0,
        "owner_proximity_px": 150.0
    }

    def reset(self):
        self.item_timestamps: Dict[str, float] = {}
        self.last_alert_time: float = 0
        self.alerted_items = set()

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
        
        item_dets = [d for d in detections if d[2] in self.config["object_classes"]]
        person_tracks = [t for t in tracks if t.get("class_name") == "person"]

        for item_bbox, conf, item_cls in item_dets:
            ix1, iy1, iw, ih = item_bbox
            icx, icy = ix1 + (iw / 2.0), iy1 + (ih / 2.0)
            item_key = f"{item_cls}_{int(icx/20)}_{int(icy/20)}"

            # Check if any person is within proximity radius
            near_person = False
            for pt in person_tracks:
                pcx, pcy = pt["centroid"]
                if math.hypot(icx - pcx, icy - pcy) <= self.config["owner_proximity_px"]:
                    near_person = True
                    break

            if not near_person:
                if item_key not in self.item_timestamps:
                    self.item_timestamps[item_key] = timestamp_sec

                duration = timestamp_sec - self.item_timestamps[item_key]
                if duration >= self.config["abandoned_sec_threshold"]:
                    if item_key not in self.alerted_items and (now - self.last_alert_time >= self.config["cooldown_sec"]):
                        self.last_alert_time = now
                        self.alerted_items.add(item_key)
                        incidents.append(
                            IncidentData(
                                type="ABANDONED_OBJECT",
                                timestamp=timestamp_sec,
                                frame=frame_idx,
                                confidence=0.90,
                                severity=SEVERITY_HIGH if duration >= 20.0 else SEVERITY_MEDIUM,
                                bbox=[float(ix1), float(iy1), float(ix1 + iw), float(iy1 + ih)],
                                description=f"ABANDONED OBJECT DETECTED! Unattended {item_cls} stationary with no person nearby for {duration:.1f}s",
                                extra_data={"item_class": item_cls, "unattended_duration": round(duration, 1)}
                            )
                        )
            else:
                self.item_timestamps.pop(item_key, None)

        return incidents
