import cv2
import threading
import time
from .detection import detect_frame, save_clip
from .alerts import create_alert_response, send_email, nearest_hospitals, eta_minutes
from ..config import settings
from ..db import db_cursor
from ..websocket_manager import manager

processing_status: dict[int, dict] = {}
status_lock = threading.Lock()


def update_status(alert_id, **values):
    with status_lock:
        processing_status.setdefault(alert_id, {}).update(values)


def process_video(video_path, alert_id, camera_id, hospital_id, user_id, gps_lat, gps_lon):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        update_status(alert_id, status="error", error="Could not open the uploaded video")
        return
    total = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    frame_count = 0
    frames = []
    accident_done = False
    update_status(alert_id, status="processing", progress=0, accident=False)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            frames.append(frame.copy())
            if len(frames) > 50:
                frames.pop(0)
            update_status(alert_id, progress=min(99, int(frame_count / total * 100)))
            if frame_count % settings.process_every_n_frames != 0 or accident_done:
                continue
            result = detect_frame(frame)
            if not result["detected"]:
                continue
            severity = result["severity"]
            with db_cursor() as (_, cur):
                cur.execute("UPDATE alerts SET accident_detected=1, severity_label=%s, severity_score=%s WHERE id=%s", (severity["label"], severity["score"], alert_id))
            screenshot_path = settings.screenshot_dir / f"accident_{alert_id}.jpg"
            cv2.imwrite(str(screenshot_path), frame)
            clip_path = save_clip(frames, alert_id)
            hospitals = nearest_hospitals(gps_lat, gps_lon) if gps_lat is not None and gps_lon is not None else []
            recipients = [h["email"] for h in hospitals if h.get("email")]
            if settings.alert_fallback_email:
                recipients.append(settings.alert_fallback_email)
            location = f"Lat: {gps_lat:.6f}, Lon: {gps_lon:.6f}" if gps_lat is not None and gps_lon is not None else "Location unavailable"
            body = f"ACCIDENT DETECTED\nSeverity: {severity['label']} ({severity['score']}/100)\nLocation: {location}\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\nNearest hospitals:\n" + "\n".join(f"- {h['name']}: {h['distance_km']:.1f} km, ETA ~{eta_minutes(h['distance_km'])} min" for h in hospitals)
            email_sent = send_email(f"ACCIDENT [{severity['label']}] - Emergency Alert", body, recipients, str(screenshot_path), clip_path)
            with db_cursor() as (_, cur):
                cur.execute("UPDATE alerts SET screenshot_path=%s, accident_clip_path=%s, location=%s, email_sent=%s WHERE id=%s", (str(screenshot_path), clip_path, location, int(email_sent), alert_id))
            payload = create_alert_response(alert_id, gps_lat, gps_lon, severity, str(screenshot_path), clip_path)
            update_status(alert_id, accident=True, screenshot=payload["screenshot"], clip=payload["clip"], location=payload["location"], nearest_hospitals=payload["nearest_hospitals"], severity=severity, gps_lat=gps_lat, gps_lon=gps_lon, email_sent=email_sent)
            awaitable_emit(payload, hospital_id, user_id)
            accident_done = True
        update_status(alert_id, status="done", progress=100)
    except Exception as exc:
        update_status(alert_id, status="error", error=str(exc))
    finally:
        cap.release()


def awaitable_emit(payload, hospital_id=None, user_id=None):
    # WebSocket manager supports synchronous fan-out from worker threads.
    if hospital_id:
        manager.broadcast_sync(f"hospital:{hospital_id}", {"type": "accident_alert", "data": payload})
    if user_id:
        manager.broadcast_sync(f"user:{user_id}", {"type": "accident_alert", "data": payload})
    for h in payload.get("nearest_hospitals", []):
        manager.broadcast_sync(f"hospital:{h['id']}", {"type": "accident_alert", "data": payload})
