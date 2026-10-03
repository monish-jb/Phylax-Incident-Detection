"""
detectors/crowd_density.py
Crowd Density & Overcrowding Detector plugin.
"""

import time
from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector


@register_detector
class CrowdDensityDetector(BaseDetector):
    detector_id = "crowd_density"
    name = "Crowd Density & Overcrowding Detector"
    description = "Monitors real-time human count against capacity limits for emergency safety and bottleneck management."
    default_config = {
        "cooldown_sec": 20,
        "max_capacity": 5,
        "critical_capacity": 10
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
        people_count = len(person_tracks)

        max_cap = self.config["max_capacity"]
        crit_cap = self.config["critical_capacity"]

        if people_count >= max_cap:
            self.last_alert_time = now
            severity = (
                SEVERITY_CRITICAL if people_count >= crit_cap
                else SEVERITY_HIGH if people_count >= max_cap + 3
                else SEVERITY_MEDIUM
            )

            # Compute composite bounding box encompassing all persons
            bbox = None
            if person_tracks:
                x1 = min(t["bbox"][0] for t in person_tracks)
                y1 = min(t["bbox"][1] for t in person_tracks)
                x2 = max(t["bbox"][2] for t in person_tracks)
                y2 = max(t["bbox"][3] for t in person_tracks)
                bbox = [float(x1), float(y1), float(x2), float(y2)]

            incidents.append(
                IncidentData(
                    type="CROWD_DENSITY",
                    timestamp=timestamp_sec,
                    frame=frame_idx,
                    confidence=0.94,
                    severity=severity,
                    bbox=bbox,
                    description=f"Overcrowding alert: {people_count} individuals present (Capacity limit: {max_cap})",
                    extra_data={"people_count": people_count, "capacity_limit": max_cap}
                )
            )

        return incidents
