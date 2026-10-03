"""
detectors/loitering.py
Loitering & Lingering Person Detector plugin.
"""

import time
import math
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_MEDIUM, SEVERITY_HIGH
from detectors.registry import register_detector


@register_detector
class LoiteringDetector(BaseDetector):
    detector_id = "loitering"
    name = "Loitering Detector"
    description = "Detects individuals remaining stationary or lingering in a monitored area beyond configured duration limits."
    default_config = {
        "cooldown_sec": 20,
        "max_loiter_sec": 10.0,
        "movement_radius_px": 50.0
    }

    def reset(self):
        self.entry_times: Dict[int, float] = {}
        self.initial_centroids: Dict[int, tuple] = {}
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
            cx, cy = pt["centroid"]
            x1, y1, x2, y2 = pt["bbox"]

            if tid not in self.entry_times:
                self.entry_times[tid] = timestamp_sec
                self.initial_centroids[tid] = (cx, cy)
                continue

            init_cx, init_cy = self.initial_centroids[tid]
            dist = math.hypot(cx - init_cx, cy - init_cy)
            duration = timestamp_sec - self.entry_times[tid]

            if dist > self.config["movement_radius_px"]:
                # Reset origin centroid if person moved out of radius
                self.initial_centroids[tid] = (cx, cy)
                self.entry_times[tid] = timestamp_sec
            elif duration >= self.config["max_loiter_sec"]:
                if tid not in self.alerted_tracks and (now - self.last_alert_time >= self.config["cooldown_sec"]):
                    self.last_alert_time = now
                    self.alerted_tracks.add(tid)
                    incidents.append(
                        IncidentData(
                            type="LOITERING",
                            timestamp=timestamp_sec,
                            frame=frame_idx,
                            confidence=0.88,
                            severity=SEVERITY_HIGH if duration >= 20.0 else SEVERITY_MEDIUM,
                            bbox=[float(x1), float(y1), float(x2), float(y2)],
                            description=f"Loitering alert: Person #{tid} remaining in location for {duration:.1f} seconds",
                            extra_data={"track_id": tid, "duration_sec": round(duration, 1)}
                        )
                    )

        return incidents
