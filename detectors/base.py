"""
detectors/base.py
Base class and data structure for all Phylax detection plugins.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"


@dataclass
class IncidentData:
    type: str                                    # e.g., "ACCIDENT", "INTRUSION", "THEFT", "LOITERING", "FIRE", etc.
    timestamp: float                             # Timestamp in seconds
    frame: int                                   # Frame index number
    confidence: float                            # 0.0 to 1.0
    severity: str = SEVERITY_MEDIUM              # "low", "medium", "high", "critical"
    bbox: Optional[List[float]] = None           # [x1, y1, x2, y2]
    zone_id: Optional[int] = None
    thumbnail_path: Optional[str] = None
    description: str = ""
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "frame": self.frame,
            "confidence": self.confidence,
            "severity": self.severity,
            "bbox": self.bbox,
            "zone_id": self.zone_id,
            "thumbnail_path": self.thumbnail_path,
            "description": self.description,
            "extra_data": self.extra_data
        }


class BaseDetector:
    """
    Abstract base class for detector plugins in Phylax.
    All detectors share the frame, YOLO raw detections, DeepSort tracks, and zones.
    """
    detector_id: str = "base"
    name: str = "Base Detector"
    description: str = "Base detector interface"
    default_config: Dict[str, Any] = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.default_config, **(config or {})}
        self.reset()

    def reset(self):
        """Reset internal temporal states (e.g. tracking histories, cooldowns)."""
        pass

    def process_frame(
        self,
        frame,
        frame_idx: int,
        timestamp_sec: float,
        tracks: List[Dict[str, Any]],
        detections: List[Any],
        zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[IncidentData]:
        """
        Analyze a single frame with tracked objects and return any flagged IncidentData instances.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process_frame()")

    def update_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
