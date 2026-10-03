"""
tracker.py
Wraps deep-sort-realtime and keeps a rolling history of each track's
centroid so we can compute speed and direction changes across frames.
"""

import math
from collections import deque
from deep_sort_realtime.deepsort_tracker import DeepSort
from backend.app.services import config


class VehicleTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=config.MAX_TRACK_AGE)
        # track_id -> deque of (cx, cy) centroids, most recent last
        self.history = {}
        # track_id -> frames missing counter for graceful cleanup
        self.missing_count = {}

    def update(self, detections, frame):
        """
        detections: output of VehicleDetector.detect()
        Returns a list of dicts:
            {
                "id": track_id,
                "bbox": (x1, y1, x2, y2),
                "class_name": str,
                "centroid": (cx, cy),
                "history": [(cx, cy), ...],
                "speed": float (px/frame),
                "velocity": (vx, vy),
            }
        """
        tracks = self.tracker.update_tracks(detections, frame=frame)

        active = []
        current_active_ids = set()

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            current_active_ids.add(track_id)
            x1, y1, x2, y2 = track.to_ltrb()
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

            if track_id not in self.history:
                self.history[track_id] = deque(maxlen=config.TRACK_HISTORY_LEN)
            self.history[track_id].append((cx, cy))

            # Compute current speed and velocity vector over recent history
            hist = self.history[track_id]
            if len(hist) >= 2:
                (prev_x, prev_y), (curr_x, curr_y) = hist[-2], hist[-1]
                vx, vy = curr_x - prev_x, curr_y - prev_y
                speed = math.hypot(vx, vy)
            else:
                vx, vy = 0.0, 0.0
                speed = 0.0

            active.append({
                "id": track_id,
                "bbox": (x1, y1, x2, y2),
                "class_name": track.get_det_class() or "vehicle",
                "centroid": (cx, cy),
                "history": list(hist),
                "speed": speed,
                "velocity": (vx, vy),
            })

        # Memory cleanup: remove tracks missing for > MAX_TRACK_AGE frames
        for existing_id in list(self.history.keys()):
            if existing_id not in current_active_ids:
                self.missing_count[existing_id] = self.missing_count.get(existing_id, 0) + 1
                if self.missing_count[existing_id] > config.MAX_TRACK_AGE:
                    del self.history[existing_id]
                    del self.missing_count[existing_id]
            else:
                self.missing_count[existing_id] = 0

        return active

