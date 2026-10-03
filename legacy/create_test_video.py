"""
create_test_video.py
Generates a synthetic MP4 video in test_videos/ containing two moving vehicles
that collide and stop, triggering the accident detector heuristics for testing.
"""

import os
import cv2
import numpy as np

os.makedirs("test_videos", exist_ok=True)
output_path = os.path.join("test_videos", "sample_crash.mp4")

width, height = 640, 480
fps = 20
num_frames = 100

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# Car 1 moves right to left, Car 2 moves left to right
x1, y1 = 100, 200
x2, y2 = 500, 200

speed1 = 8.0
speed2 = -8.0

for frame_idx in range(num_frames):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw road background
    cv2.rectangle(img, (0, 150), (640, 300), (50, 50, 50), -1)
    
    # Before collision (frames 0..40): cars move toward each other
    if frame_idx < 40:
        x1 += speed1
        x2 += speed2
    # Collision & abrupt stop (frames 40..100)
    else:
        # Stop abrupt move
        x1 = 260
        x2 = 280

    # Draw Car 1 (Blue box)
    cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + 60), int(y1 + 40)), (255, 100, 0), -1)
    cv2.putText(img, "Car 1", (int(x1), int(y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Draw Car 2 (Red box)
    cv2.rectangle(img, (int(x2), int(y2)), (int(x2 + 60), int(y2 + 40)), (0, 100, 255), -1)
    cv2.putText(img, "Car 2", (int(x2), int(y2 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    out.write(img)

out.release()
print(f"Created sample video: {output_path}")
