"""
detectors package for Phylax AI surveillance plugins.
Auto-registers all available detector modules.
"""

from detectors.base import BaseDetector, IncidentData
from detectors.registry import DetectorRegistry, register_detector

# Import all plugins to auto-register
import detectors.accident
import detectors.theft
import detectors.intrusion
import detectors.loitering
import detectors.fire_smoke
import detectors.crowd_density
import detectors.fall
import detectors.fight
import detectors.abandoned_object

__all__ = [
    "BaseDetector",
    "IncidentData",
    "DetectorRegistry",
    "register_detector"
]
