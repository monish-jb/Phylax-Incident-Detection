"""
detectors/fight.py
Fight & Violence Motion Anomaly Detector plugin.
"""

import time
import math
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector


@register_detector
class FightDetector(BaseDetector):
    detector_id = "fight"
    name = "Fight & Physical Violence Detector"
    description = "Detects rapid kinetic energy spikes, violent multi-person trajectory interactions, and physical altercations."
    default_config = {
        "cooldown_sec": 20,
        "kinetic_speed_thresh": 8.0,  # High frame-to-frame pixel speed spike
        "proximity_dist_px": 100.0
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
        now = time.time()
        if now - self.last_alert_time < self.config["cooldown_sec"]:
            return incidents

        person_tracks = [t for t in tracks if t.get("class_name") == "person"]

        # Check for multiple fast-moving persons in close proximity
        fast_persons = [t for t in person_tracks if t.get("speed", 0.0) >= self.config["kinetic_speed_thresh"]]

        if len(fast_persons) >= 2:
            for i in range(len(fast_persons)):
                for j in range(i + 1, len(fast_persons)):
                    p1 = fast_persons[i]
                    p2 = fast_persons[j]
                    dist = math.hypot(p1["centroid"][0] - p2["centroid"][0], p1["centroid"][1] - p2["centroid"][1])

                    if dist <= self.config["proximity_dist_px"]:
                        self.last_alert_time = now
                        x1 = min(p1["bbox"][0], p2["bbox"][0])
                        y1 = min(p1["bbox"][1], p2["bbox"][1])
                        x2 = max(p1["bbox"][2], p2["bbox"][2])
                        y2 = max(p1["bbox"][3], p2["bbox"][3])

                        incidents.append(
                            IncidentData(
                                type="FIGHT",
                                timestamp=timestamp_sec,
                                frame=frame_idx,
                                confidence=0.87,
                                severity=SEVERITY_HIGH,
                                bbox=[float(x1), float(y1), float(x2), float(y2)],
                                description=f"FIGHT / VIOLENCE ALTERCATION DETECTED! High-velocity interaction between Person #{p1['id']} and #{p2['id']}",
                                extra_data={"involved_ids": [p1["id"], p2["id"]]}
                            )
                        )
                        break

        return incidents
