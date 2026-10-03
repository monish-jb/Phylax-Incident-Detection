"""
detectors/fall.py
Fall Detection plugin based on horizontal posture ratios and immobility.
"""

import time
import math
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector


@register_detector
class FallDetector(BaseDetector):
    detector_id = "fall"
    name = "Fall Detection Plugin"
    description = "Detects sudden horizontal posture changes and post-fall immobility."
    default_config = {
        "cooldown_sec": 15,
        "aspect_ratio_thresh": 1.15,  # Width / Height > 1.15 indicates horizontal lying posture
        "immobility_sec": 3.0
    }

    def reset(self):
        self.horizontal_start_times: Dict[int, float] = {}
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
        person_tracks = [t for t in tracks if t.get("class_name") == "person"]

        for pt in person_tracks:
            tid = pt["id"]
            x1, y1, x2, y2 = pt["bbox"]
            w = max(1.0, x2 - x1)
            h = max(1.0, y2 - y1)
            aspect_ratio = w / h
            speed = pt.get("speed", 0.0)

            # Horizontal posture check with near-zero speed
            if aspect_ratio >= self.config["aspect_ratio_thresh"] and speed < 3.0:
                if tid not in self.horizontal_start_times:
                    self.horizontal_start_times[tid] = timestamp_sec

                duration = timestamp_sec - self.horizontal_start_times[tid]
                if duration >= self.config["immobility_sec"]:
                    if tid not in self.alerted_tracks and (now - self.last_alert_time >= self.config["cooldown_sec"]):
                        self.last_alert_time = now
                        self.alerted_tracks.add(tid)
                        incidents.append(
                            IncidentData(
                                type="FALL",
                                timestamp=timestamp_sec,
                                frame=frame_idx,
                                confidence=0.91,
                                severity=SEVERITY_HIGH,
                                bbox=[float(x1), float(y1), float(x2), float(y2)],
                                description=f"FALL DETECTED! Person #{tid} horizontal posture and immobile for {duration:.1f}s",
                                extra_data={"track_id": tid, "immobility_duration": round(duration, 1)}
                            )
                        )
            else:
                self.horizontal_start_times.pop(tid, None)

        return incidents
