"""
detectors/registry.py
Central registry for Phylax detection plugins.
"""

from typing import Dict, Type, List, Optional, Any
from detectors.base import BaseDetector, IncidentData


class DetectorRegistry:
    _registry: Dict[str, Type[BaseDetector]] = {}

    @classmethod
    def register(cls, detector_cls: Type[BaseDetector]):
        """Register a detector plugin class."""
        if not hasattr(detector_cls, "detector_id") or not detector_cls.detector_id:
            raise ValueError(f"Detector class {detector_cls.__name__} must define 'detector_id'")
        cls._registry[detector_cls.detector_id] = detector_cls
        return detector_cls

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseDetector]]:
        return dict(cls._registry)

    @classmethod
    def get_metadata_list(cls) -> List[Dict[str, Any]]:
        meta = []
        for det_id, det_cls in cls._registry.items():
            meta.append({
                "id": det_id,
                "name": getattr(det_cls, "name", det_id),
                "description": getattr(det_cls, "description", ""),
                "default_config": getattr(det_cls, "default_config", {})
            })
        return meta

    @classmethod
    def create_instances(
        cls,
        enabled_ids: Optional[List[str]] = None,
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[BaseDetector]:
        """
        Instantiate and initialize selected detector plugins.
        If enabled_ids is None, instantiates all registered detectors.
        """
        instances = []
        target_ids = enabled_ids if enabled_ids is not None else list(cls._registry.keys())
        configs = configs or {}

        for det_id in target_ids:
            if det_id in cls._registry:
                det_cls = cls._registry[det_id]
                det_config = configs.get(det_id, {})
                instance = det_cls(config=det_config)
                instances.append(instance)

        return instances


def register_detector(detector_cls: Type[BaseDetector]):
    """Decorator for registering detector plugins."""
    DetectorRegistry.register(detector_cls)
    return detector_cls
