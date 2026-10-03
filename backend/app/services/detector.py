import logging
from ultralytics import YOLO
from backend.app.services import config

logger = logging.getLogger(__name__)


class VehicleDetector:
    def __init__(self, model_path=config.YOLO_MODEL_PATH):
        logger.info(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        # Dictionary mapping class ID to class name
        self.class_names = self.model.names if hasattr(self.model, "names") else {}

    def detect(self, frame):
        """
        Run YOLO on a single frame and return a list of detections
        filtered to vehicle classes only.
        Returns: [ ([x, y, w, h], conf, class_name), ... ]
        """
        if frame is None or frame.size == 0:
            return []

        results = self.model(
            frame,
            conf=config.CONF_THRESHOLD,
            iou=config.IOU_NMS_THRESHOLD,
            verbose=False,
        )[0]

        detections = []
        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.class_names.get(cls_id, "")
            if cls_name not in config.VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])

            # DeepSORT (deep-sort-realtime) expects [x, y, w, h]
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            detections.append(([x1, y1, w, h], conf, cls_name))

        return detections

