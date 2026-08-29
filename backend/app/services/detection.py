import cv2
import math
import threading
from pathlib import Path
from typing import Any
from shapely.geometry import box as shapely_box
from ultralytics import YOLO
from ..config import settings

VEHICLES = {"car", "motorcycle", "truck", "bus"}
model = YOLO(settings.yolo_model_path)
model_lock = threading.Lock()


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_severity(iou: float, vehicle_classes: list[str], num_objects: int) -> dict[str, Any]:
    score = iou * 40
    if "truck" in vehicle_classes or "bus" in vehicle_classes:
        score += 30
    elif "car" in vehicle_classes:
        score += 20
    elif "motorcycle" in vehicle_classes:
        score += 15
    score += min(num_objects * 3, 20)
    score = min(int(round(score)), 100)
    if score >= 75: label = "CRITICAL"
    elif score >= 55: label = "HIGH"
    elif score >= 35: label = "MEDIUM"
    else: label = "LOW"
    return {"score": score, "label": label}


def detect_frame(frame):
    with model_lock:
        results = model(frame, conf=settings.yolo_confidence, verbose=False)[0]
    boxes = results.boxes
    best_iou = 0.0
    involved: list[str] = []
    detected = False
    num_objects = len(boxes)
    for i in range(num_objects):
        cls1 = model.names[int(boxes[i].cls)]
        if cls1 != "person" and cls1 not in VEHICLES:
            continue
        for j in range(i + 1, num_objects):
            cls2 = model.names[int(boxes[j].cls)]
            if not ((cls1 == "person" and cls2 in VEHICLES) or (cls2 == "person" and cls1 in VEHICLES)):
                continue
            b1 = boxes[i].xyxy[0].cpu().numpy().tolist()
            b2 = boxes[j].xyxy[0].cpu().numpy().tolist()
            poly1, poly2 = shapely_box(*b1), shapely_box(*b2)
            union = poly1.union(poly2).area
            iou = poly1.intersection(poly2).area / union if union else 0
            if iou >= settings.accident_iou_threshold and iou > best_iou:
                detected = True
                best_iou = float(iou)
                involved = [cls1, cls2]
    return {
        "detected": detected,
        "iou": best_iou,
        "involved_classes": involved,
        "num_objects": num_objects,
        "severity": compute_severity(best_iou, involved, num_objects) if detected else None,
    }


def save_clip(frames: list, alert_id: int) -> str | None:
    if not frames:
        return None
    path = settings.clip_dir / f"clip_{alert_id}.mp4"
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w, h))
    if not writer.isOpened():
        return None
    for frame in frames:
        writer.write(frame)
    writer.release()
    return str(path)
