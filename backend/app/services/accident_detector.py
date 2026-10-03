"""
accident_detector.py
Heuristic accident detection built on top of tracked vehicle trajectories.

Signals used (each contributes to a score; combined score above threshold
triggers an alert):
  1. Sudden deceleration  - a vehicle's speed drops sharply frame-to-frame
                             after having been moving normally.
  2. Bounding-box overlap - two vehicle tracks' boxes overlap (IOU) beyond
                             a threshold, suggesting physical contact.
  3. Erratic trajectory   - a sharp change in direction (angle) combined
                             with a speed drop (spin-out / impact signature).

This is intentionally simple/interpretable so it's easy to explain to judges
and tune live. It is NOT a substitute for a trained accident-classification
model, but it works well for demo footage of staged/real collisions.
"""

import math
import time
from backend.app.services import config


def _speed(history):
    """Average px/frame speed over the track's recent history."""
    if len(history) < 2:
        return 0.0
    dists = []
    for i in range(1, len(history)):
        (x1, y1), (x2, y2) = history[i - 1], history[i]
        dists.append(math.hypot(x2 - x1, y2 - y1))
    return sum(dists) / len(dists)


def _instant_speed(history):
    """Speed over just the last two points (most recent motion)."""
    if len(history) < 2:
        return 0.0
    (x1, y1), (x2, y2) = history[-2], history[-1]
    return math.hypot(x2 - x1, y2 - y1)


def _direction_change(history):
    """Angle (degrees) between the two most recent motion vectors."""
    if len(history) < 3:
        return 0.0
    (x1, y1), (x2, y2), (x3, y3) = history[-3], history[-2], history[-1]
    v1 = (x2 - x1, y2 - y1)
    v2 = (x3 - x2, y3 - y2)
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 < 1e-3 or mag2 < 1e-3:
        return 0.0
    cos_angle = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def _iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area == 0:
        return 0.0

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


class AccidentDetector:
    def __init__(self):
        self.last_alert_time = 0
        self.last_speeds = {}  # track_id -> previous avg speed (for delta comparison)

    def _sudden_deceleration_score(self, track):
        history = track["history"]
        avg_speed = _speed(history[:-1]) if len(history) > 1 else 0.0
        current_speed = _instant_speed(history)

        score = 0
        if avg_speed >= config.MIN_SPEED_TO_CONSIDER:
            drop_ratio = (avg_speed - current_speed) / avg_speed if avg_speed > 0 else 0
            if drop_ratio >= config.SPEED_DROP_RATIO:
                score += 1
        return score

    def _erratic_trajectory_score(self, track):
        angle = _direction_change(track["history"])
        current_speed = _instant_speed(track["history"])
        score = 0
        # Sharp direction change while still moving with some speed = spin/impact
        if angle > 60 and current_speed >= config.MIN_SPEED_TO_CONSIDER * 0.5:
            score += 1
        return score

    def _collision_score(self, tracks):
        """Check all pairs of tracks for significant bbox overlap."""
        pairs_in_collision = []
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                iou = _iou(tracks[i]["bbox"], tracks[j]["bbox"])
                if iou >= config.COLLISION_IOU_THRESHOLD:
                    pairs_in_collision.append((tracks[i]["id"], tracks[j]["id"], iou))
        return pairs_in_collision

    def analyze(self, tracks):
        """
        tracks: list of active track dicts from VehicleTracker.update()
        Returns: (is_accident: bool, details: dict) -- details always
                 returned for logging/debugging even if no accident.
        """
        per_track_scores = {}
        for track in tracks:
            score = 0
            score += self._sudden_deceleration_score(track)
            score += self._erratic_trajectory_score(track)
            per_track_scores[track["id"]] = score

        collisions = self._collision_score(tracks)

        # Combined score: collision is a strong independent signal (+2),
        # plus any per-track anomaly scores for vehicles involved.
        total_score = 0
        involved_ids = set()
        for id_a, id_b, iou in collisions:
            total_score += 2
            involved_ids.update([id_a, id_b])
            total_score += per_track_scores.get(id_a, 0)
            total_score += per_track_scores.get(id_b, 0)

        # Also allow a single-vehicle high-severity anomaly (e.g. rollover,
        # hitting a static object not tracked as a "vehicle") to trigger.
        for tid, score in per_track_scores.items():
            if score >= 2:
                total_score += score
                involved_ids.add(tid)

        details = {
            "total_score": total_score,
            "per_track_scores": per_track_scores,
            "collisions": collisions,
            "involved_ids": list(involved_ids),
        }

        is_accident = total_score >= config.ACCIDENT_SCORE_THRESHOLD
        if is_accident:
            now = time.time()
            if now - self.last_alert_time < config.ALERT_COOLDOWN_SECONDS:
                is_accident = False  # suppress repeat alert within cooldown
            else:
                self.last_alert_time = now

        return is_accident, details
