import os
import sys
import time
import json
import csv
import cv2
import numpy as np

import config
from detector import VehicleDetector
from tracker import VehicleTracker
from accident_detector import AccidentDetector


def run_evaluation(video_path, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    key_frames_dir = os.path.join(output_dir, "key_frames")
    os.makedirs(key_frames_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "detection_results.csv")
    json_path = os.path.join(output_dir, "detection_summary.json")
    annotated_video_path = os.path.join(output_dir, "annotated_output.mp4")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 30.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))

    detector = VehicleDetector()
    tracker = VehicleTracker()
    accident_detector = AccidentDetector()

    print(f"=== Starting Evaluation on {video_path} ===")
    print(f"Video Specs: {width}x{height} @ {fps:.2f} FPS, {total_frames} frames total")

    accident_events = []
    start_proc_time = time.time()

    frame_idx = 0
    max_score = 0
    accident_detected_any = False
    first_accident_frame = None
    first_accident_timestamp = None

    # CSV Header
    csv_file = open(csv_path, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "frame_idx", "timestamp_sec", "num_tracked_vehicles", "accident_score",
        "is_accident", "involved_ids", "collisions", "tracks_summary"
    ])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        timestamp_sec = round((frame_idx - 1) / fps, 3)

        detections = detector.detect(frame)
        tracks = tracker.update(detections, frame)
        is_accident, details = accident_detector.analyze(tracks)

        score = details.get("total_score", 0)
        involved = details.get("involved_ids", [])
        collisions = details.get("collisions", [])

        if score > max_score:
            max_score = score

        if is_accident:
            if not accident_detected_any:
                accident_detected_any = True
                first_accident_frame = frame_idx
                first_accident_timestamp = timestamp_sec
            
            accident_events.append({
                "frame": frame_idx,
                "timestamp_sec": timestamp_sec,
                "score": score,
                "involved_ids": involved,
                "collisions": collisions
            })

        # Summarize tracks for CSV log
        tracks_summary = [
            f"ID:{t['id']}({t['class_name']},spd:{t['speed']:.1f})"
            for t in tracks
        ]

        csv_writer.writerow([
            frame_idx,
            timestamp_sec,
            len(tracks),
            score,
            is_accident,
            ";".join(map(str, involved)),
            ";".join([f"{c[0]}-{c[1]}(iou:{c[2]:.2f})" for c in collisions]),
            " | ".join(tracks_summary)
        ])

        # Draw Annotations
        annotated = frame.copy()
        
        # Bounding boxes
        for track in tracks:
            x1, y1, x2, y2 = [int(v) for v in track["bbox"]]
            is_inv = track["id"] in involved
            box_color = (0, 0, 255) if is_inv else (0, 255, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 3)
            
            spd = track.get("speed", 0.0)
            lbl = f"#{track['id']} {track['class_name']} {spd:.1f}px/f"
            
            # Label background pill
            (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 10)), (x1 + tw + 10, y1), box_color, -1)
            cv2.putText(annotated, lbl, (x1 + 5, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Top Info Bar
        info_bar_color = (20, 20, 20)
        cv2.rectangle(annotated, (0, 0), (width, 80), info_bar_color, -1)
        
        status_str = f"Frame: {frame_idx}/{total_frames} | Time: {timestamp_sec:.2f}s | Vehicles: {len(tracks)} | Score: {score}"
        cv2.putText(annotated, status_str, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Large Banner if Accident Triggered or within window
        if is_accident or (first_accident_frame and abs(frame_idx - first_accident_frame) < 60):
            banner_bg = (0, 0, 220)
            cv2.rectangle(annotated, (0, 80), (width, 160), banner_bg, -1)
            cv2.putText(
                annotated, f"!!! ACCIDENT DETECTED !!! (Score: {score})", (30, 135),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3
            )
            
            # Save key frame
            key_frame_filename = f"frame_{frame_idx:04d}_time_{timestamp_sec:.2f}s.jpg"
            cv2.imwrite(os.path.join(key_frames_dir, key_frame_filename), annotated)

        out_writer.write(annotated)

    csv_file.close()
    cap.release()
    out_writer.release()

    proc_duration = time.time() - start_proc_time
    actual_fps = total_frames / proc_duration if proc_duration > 0 else 0

    summary = {
        "video_path": video_path,
        "total_frames": total_frames,
        "video_fps": fps,
        "video_resolution": f"{width}x{height}",
        "processing_time_sec": round(proc_duration, 2),
        "processing_fps": round(actual_fps, 2),
        "accident_detected": accident_detected_any,
        "first_accident_frame": first_accident_frame,
        "first_accident_timestamp_sec": first_accident_timestamp,
        "max_accident_score": max_score,
        "total_accident_frames": len(accident_events),
        "accident_events_summary": accident_events[:10],
        "annotated_video_path": annotated_video_path,
        "csv_log_path": csv_path
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Evaluation Completed ===")
    print(f"Accident Detected: {accident_detected_any}")
    if accident_detected_any:
        print(f"First Detection Frame: {first_accident_frame} ({first_accident_timestamp:.2f}s)")
        print(f"Max Accident Score: {max_score}")
    print(f"Processing Speed: {actual_fps:.2f} FPS")
    print(f"Results saved in {output_dir}/")
    return summary


if __name__ == "__main__":
    vpath = sys.argv[1] if len(sys.argv) > 1 else "test_videos/test_accident.mp4"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    run_evaluation(vpath, out_dir)
