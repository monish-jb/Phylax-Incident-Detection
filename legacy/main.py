"""
main.py
Entry point. Runs the full pipeline:

    video frame -> YOLO detection -> DeepSORT tracking
                -> accident heuristics -> clip saving -> emergency alert

Usage:
    python main.py                     # use webcam (config.VIDEO_SOURCE = 0)
    python main.py --source path.mp4   # run on a video file instead
    python main.py --no-display        # run headless without GUI window
"""

import os
import argparse
import cv2

import config
from detector import VehicleDetector
from tracker import VehicleTracker
from accident_detector import AccidentDetector
from clip_saver import ClipSaver
from alert_system import EmergencyAlertSystem


def draw_overlay(frame, tracks, is_accident, details):
    for track in tracks:
        x1, y1, x2, y2 = [int(v) for v in track["bbox"]]
        involved = track["id"] in details.get("involved_ids", [])
        color = (0, 0, 255) if involved else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        speed = track.get("speed", 0.0)
        label = f"ID {track['id']} {track['class_name']} ({speed:.1f}px/f)"
        cv2.putText(
            frame, label,
            (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )

    if is_accident:
        score = details.get("total_score", 0)
        cv2.putText(
            frame, f"ACCIDENT DETECTED (Score: {score})", (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3
        )
    return frame


def main(source, show_display=True):
    # Ensure required directories exist at startup
    os.makedirs("logs", exist_ok=True)
    os.makedirs("clips", exist_ok=True)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    detector = VehicleDetector()
    tracker = VehicleTracker()
    accident_detector = AccidentDetector()
    clip_saver = ClipSaver(fps=fps, frame_size=(width, height))
    alert_system = EmergencyAlertSystem()

    print("Starting accident detection pipeline. Press 'q' to quit.")

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            detections = detector.detect(frame)
            tracks = tracker.update(detections, frame)
            is_accident, details = accident_detector.analyze(tracks)

            annotated = draw_overlay(frame.copy(), tracks, is_accident, details)
            clip_saver.add_frame(annotated)

            if is_accident:
                clip_path = clip_saver.trigger()
                print(f"[ALERT] Accident detected at frame {frame_count}! "
                      f"score={details['total_score']} involved={details['involved_ids']}")
                alert_system.dispatch(clip_path, details)

            if show_display:
                try:
                    cv2.imshow("Accident Detection", annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except cv2.error as e:
                    print(f"[WARN] OpenCV GUI error encountered ({e}). Disabling display window.")
                    show_display = False
    finally:
        clip_saver.close()
        cap.release()
        if show_display:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        print(f"Pipeline finished. Processed {frame_count} frames.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=str, default=None,
        help="Path to a video file. If omitted, uses config.VIDEO_SOURCE (webcam by default)."
    )
    parser.add_argument(
        "--no-display", action="store_true",
        help="Run headless without showing the OpenCV video display window."
    )
    args = parser.parse_args()
    video_source = args.source if args.source is not None else config.VIDEO_SOURCE
    # Convert string '0' to integer for webcam device index
    if isinstance(video_source, str) and video_source.isdigit():
        video_source = int(video_source)

    main(video_source, show_display=not args.no_display)

