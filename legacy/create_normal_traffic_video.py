import os
import cv2
import numpy as np

os.makedirs("test_videos", exist_ok=True)
output_path = os.path.join("test_videos", "normal_traffic.mp4")

width, height = 640, 480
fps = 30
num_frames = 150

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# 3 vehicles moving smoothly in separate lanes with steady speed
vehicles = [
    {"x": 50, "y": 180, "speed": 4.0, "color": (255, 120, 0), "label": "Car 1"},
    {"x": 100, "y": 260, "speed": 5.0, "color": (0, 200, 255), "label": "Car 2"},
    {"x": 200, "y": 340, "speed": 3.5, "color": (100, 255, 100), "label": "Truck 1"}
]

for frame_idx in range(num_frames):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Road background
    cv2.rectangle(img, (0, 150), (640, 420), (40, 40, 40), -1)
    # Lane markers
    for lx in range(0, 640, 40):
        cv2.line(img, (lx, 230), (lx + 20, 230), (255, 255, 255), 2)
        cv2.line(img, (lx, 310), (lx + 20, 310), (255, 255, 255), 2)

    for v in vehicles:
        v["x"] = (v["x"] + v["speed"]) % 600
        x, y = int(v["x"]), int(v["y"])
        cv2.rectangle(img, (x, y), (x + 70, y + 45), v["color"], -1)
        cv2.putText(img, v["label"], (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    out.write(img)

out.release()
print(f"Created normal traffic control video: {output_path}")
