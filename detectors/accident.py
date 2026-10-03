"""
detectors/accident.py
Accident / Vehicle Collision detector plugin wrapping existing accident logic.
"""

from typing import List, Dict, Any, Optional
from detectors.base import BaseDetector, IncidentData, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL
from detectors.registry import register_detector
from accident_detector import AccidentDetector


@register_detector
class AccidentPluginDetector(BaseDetector):
    detector_id = "accident"
    name = "Accident & Vehicle Collision Detector"
    description = "Detects sudden vehicle decelerations, erratic trajectory spins, and bounding-box collisions."
    default_config = {
        "cooldown_sec": 30,
        "score_threshold": 2,
    }

    def reset(self):
        self.inner_detector = AccidentDetector()

    def process_frame(
        self,
        frame,
        frame_idx: int,
        timestamp_sec: float,
        tracks: List[Dict[str, Any]],
        detections: List[Any],
        zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[IncidentData]:
        is_accident, details = self.inner_detector.analyze(tracks)
        incidents = []

        if is_accident:
            score = details.get("total_score", 0)
            involved_ids = details.get("involved_ids", [])
            collisions = details.get("collisions", [])

            severity = (
                SEVERITY_CRITICAL if score >= 5
                else SEVERITY_HIGH if score >= 3
                else SEVERITY_MEDIUM
            )

            # Compute composite bounding box of involved tracks if available
            bbox = None
            if involved_ids:
                inv_boxes = [t["bbox"] for t in tracks if t["id"] in involved_ids]
                if inv_boxes:
                    x1 = min(b[0] for b in inv_boxes)
                    y1 = min(b[1] for b in inv_boxes)
                    x2 = max(b[2] for b in inv_boxes)
                    y2 = max(b[3] for b in inv_boxes)
                    bbox = [float(x1), float(y1), float(x2), float(y2)]

            incidents.append(
                IncidentData(
                    type="ACCIDENT",
                    timestamp=timestamp_sec,
                    frame=frame_idx,
                    confidence=0.92,
                    severity=severity,
                    bbox=bbox,
                    description=f"Vehicle accident / collision detected (Score: {score}, Vehicles involved: {len(involved_ids)})",
                    extra_data={
                        "accident_score": score,
                        "involved_ids": involved_ids,
                        "collisions": collisions,
                        "per_track_scores": details.get("per_track_scores", {})
                    }
                )
            )

        return incidents
