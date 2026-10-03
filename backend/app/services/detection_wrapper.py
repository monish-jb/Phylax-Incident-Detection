import os
import sys
import time
import json
import asyncio
import cv2
import numpy as np
from datetime import datetime

# Import workspace root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from backend.app.services import config
from backend.app.services.detector import VehicleDetector
from backend.app.services.tracker import VehicleTracker
from detectors import DetectorRegistry
from alert_engine import AlertEngine
from profiles import LOCATION_PROFILES, get_profile_detectors

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import Video, AnalysisJob, Incident, Camera, Zone, User
from backend.app.services.websocket_manager import manager


def run_video_analysis_job(video_id: int, enabled_detectors: list = None):
    """
    Multi-Detector Synchronous Worker Routine executed via BackgroundTasks.
    Unified single YOLO backbone + DeepSort tracker shared across active detectors.
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        job = db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).first()

        if not video or not job:
            return

        user = db.query(User).filter(User.id == video.user_id).first()

        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.progress = 5
        db.commit()

        input_path = video.file_path
        if not os.path.exists(input_path):
            job.status = "failed"
            job.error_message = f"Input file not found at {input_path}"
            db.commit()
            return

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            job.status = "failed"
            job.error_message = "Failed to open video file via OpenCV"
            db.commit()
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps if fps > 0 else 0.0

        video.duration_sec = round(duration_sec, 2)
        video.width = width
        video.height = height
        video.fps = round(fps, 2)

        # Retrieve camera polygon zones if associated
        zones = []
        if video.camera_id:
            db_zones = db.query(Zone).filter(Zone.camera_id == video.camera_id).all()
            for z in db_zones:
                zones.append({
                    "id": z.id,
                    "name": z.name,
                    "polygon_coords": z.polygon_coords,
                    "detector_types": z.detector_types
                })

        # Resolve active detectors for this job
        profile_key = (video.profile or "ROAD_PARKING").upper()
        target_detector_ids = enabled_detectors or get_profile_detectors(profile_key)
        
        # Instantiate active detector plugins
        detector_plugins = DetectorRegistry.create_instances(enabled_ids=target_detector_ids)

        # Output file paths
        annotated_filename = f"annotated_{video.id}.mp4"
        annotated_full_path = os.path.join(settings.ANNOTATED_DIR, annotated_filename)
        rel_annotated_path = f"storage/annotated/{annotated_filename}"

        poster_filename = f"poster_{video.id}.jpg"
        poster_full_path = os.path.join(settings.POSTERS_DIR, poster_filename)
        rel_poster_path = f"storage/posters/{poster_filename}"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(annotated_full_path, fourcc, fps, (width, height))

        # Shared YOLO backbone and tracker
        yolo_detector = VehicleDetector()
        tracker = VehicleTracker()
        alert_engine = AlertEngine(db)

        frame_idx = 0
        max_score = 0
        has_accident = False
        incidents_recorded = 0
        midpoint_frame = max(1, total_frames // 4)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            timestamp_sec = round((frame_idx - 1) / fps, 3)

            # Save poster snapshot
            if frame_idx == midpoint_frame:
                cv2.imwrite(poster_full_path, frame)
                video.poster_path = rel_poster_path

            # 1. Shared Detection & Tracking
            raw_detections = yolo_detector.detect(frame)
            active_tracks = tracker.update(raw_detections, frame)

            # 2. Run all active detector plugins
            current_frame_incidents = []
            for plugin in detector_plugins:
                try:
                    plugin_incidents = plugin.process_frame(
                        frame=frame,
                        frame_idx=frame_idx,
                        timestamp_sec=timestamp_sec,
                        tracks=active_tracks,
                        detections=raw_detections,
                        zones=zones
                    )
                    current_frame_incidents.extend(plugin_incidents)
                except Exception as e:
                    print(f"Error running plugin {plugin.detector_id}: {e}")

            annotated = frame.copy()

            # Draw camera polygon zones if configured
            for zone in zones:
                pts = zone.get("polygon_coords", [])
                if pts:
                    poly_pts = np.array([
                        [int(p[0] * width) if p[0] <= 1.0 else int(p[0]), int(p[1] * height) if p[1] <= 1.0 else int(p[1])]
                        for p in pts
                    ], np.int32)
                    cv2.polylines(annotated, [poly_pts], isClosed=True, color=(255, 191, 0), thickness=2)
                    cv2.putText(annotated, f"ZONE: {zone['name']}", (poly_pts[0][0], poly_pts[0][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 191, 0), 2)

            # Draw tracked bounding boxes
            for track in active_tracks:
                x1, y1, x2, y2 = [int(v) for v in track["bbox"]]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                lbl = f"#{track['id']} {track['class_name']}"
                cv2.putText(annotated, lbl, (x1 + 4, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

            # Draw Top Command Overlay HUD Bar
            cv2.rectangle(annotated, (0, 0), (width, 60), (12, 17, 26), -1)
            hud_text = f"PHYLAX AI | PROFILE: {profile_key} | FRAME: {frame_idx}/{total_frames} | TRACKS: {len(active_tracks)} | INCIDENTS: {incidents_recorded}"
            cv2.putText(annotated, hud_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 220, 255), 2)

            # Process flagged incidents for frame
            if current_frame_incidents:
                has_accident = True
                for inc_data in current_frame_incidents:
                    incidents_recorded += 1
                    
                    # Draw incident bounding box if provided
                    if inc_data.bbox:
                        bx1, by1, bx2, by2 = [int(v) for v in inc_data.bbox]
                        cv2.rectangle(annotated, (bx1, by1), (bx2, by2), (0, 0, 255), 3)

                    # Save thumbnail image
                    thumb_filename = f"thumb_v{video.id}_f{frame_idx}_{inc_data.type}.jpg"
                    thumb_full_path = os.path.join(settings.THUMBNAILS_DIR, thumb_filename)
                    rel_thumb_path = f"storage/thumbnails/{thumb_filename}"
                    cv2.imwrite(thumb_full_path, annotated)

                    # Record Incident in DB labeled "FLAGGED_FOR_REVIEW"
                    inc_record = Incident(
                        video_id=video.id,
                        zone_id=inc_data.zone_id,
                        type=inc_data.type,
                        timestamp_sec=inc_data.timestamp,
                        frame_number=inc_data.frame,
                        confidence=inc_data.confidence,
                        severity=inc_data.severity.upper(),
                        accident_score=inc_data.extra_data.get("accident_score", 2),
                        bbox=inc_data.bbox,
                        keyframe_thumbnail_path=rel_thumb_path,
                        involved_tracks_json=inc_data.extra_data,
                        description=inc_data.description,
                        reviewed_status="FLAGGED_FOR_REVIEW"
                    )
                    db.add(inc_record)
                    db.commit()
                    db.refresh(inc_record)

                    # Dispatch alert if severity is HIGH or CRITICAL
                    if user and inc_data.severity in ["high", "critical"]:
                        alert_engine.dispatch_incident_alert(inc_record, video, user)

                    # Render Red Alert Banner
                    cv2.rectangle(annotated, (0, 60), (width, 120), (0, 0, 220), -1)
                    alert_banner = f"!!! {inc_data.type} DETECTED [FLAGGED FOR REVIEW] (SEVERITY: {inc_data.severity.upper()}) !!!"
                    cv2.putText(annotated, alert_banner, (15, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2)

            out_writer.write(annotated)

            # Update job progress in DB
            if frame_idx % 10 == 0 or frame_idx == total_frames:
                prog = int((frame_idx / total_frames) * 95)
                job.progress = max(5, prog)
                db.commit()

        cap.release()
        out_writer.release()

        if not video.poster_path and os.path.exists(annotated_full_path):
            video.poster_path = rel_annotated_path

        video.has_accident = has_accident
        video.max_score = incidents_recorded

        job.annotated_video_path = rel_annotated_path
        job.progress = 100
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        print(f"Phylax Job #{job.id} completed for Video #{video.id} ({incidents_recorded} incidents flagged for review)")

    except Exception as e:
        print(f"Error processing video job #{video_id}:", e)
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()
