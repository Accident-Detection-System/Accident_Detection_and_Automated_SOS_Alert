import math
import os
import smtplib
import time
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from ..config import settings
from ..db import db_cursor
from .detection import haversine


def nearest_hospitals(lat: float, lon: float, top_n=3):
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT id,name,email,location,latitude,longitude,phone FROM hospitals WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        rows = cur.fetchall()
    for h in rows:
        h["distance_km"] = haversine(lat, lon, float(h["latitude"]), float(h["longitude"]))
    rows.sort(key=lambda x: x["distance_km"])
    return rows[:top_n]


def eta_minutes(distance_km):
    return max(1, round(distance_km / 40 * 60))


def send_email(subject, body, recipients, screenshot_path=None, clip_path=None):
    recipients = [x for x in dict.fromkeys(recipients or []) if x]
    if not recipients or not settings.smtp_user or not settings.smtp_password:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                img = MIMEImage(f.read())
            img.add_header("Content-Disposition", "attachment", filename="accident_screenshot.png")
            msg.attach(img)
        if clip_path and os.path.exists(clip_path):
            with open(clip_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename="accident_clip.mp4")
            msg.attach(part)
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, recipients, msg.as_string())
        return True
    except Exception:
        return False


def create_alert_response(alert_id, lat, lon, severity, screenshot_path=None, clip_path=None, sos=False):
    hospitals = nearest_hospitals(lat, lon) if lat is not None and lon is not None else []
    nearest = [{"id": h["id"], "name": h["name"], "distance_km": round(h["distance_km"], 1), "phone": h.get("phone") or "", "eta_min": eta_minutes(h["distance_km"])} for h in hospitals]
    return {
        "alert_id": alert_id,
        "location": f"Lat: {lat:.6f}, Lon: {lon:.6f}" if lat is not None and lon is not None else "Location unavailable",
        "gps_lat": lat,
        "gps_lon": lon,
        "nearest_hospitals": nearest,
        "severity": severity,
        "screenshot": f"/media/screenshots/{PathName(screenshot_path)}" if screenshot_path else None,
        "clip": f"/media/clips/{PathName(clip_path)}" if clip_path else None,
        "sos": sos,
    }


def PathName(path):
    return os.path.basename(path) if path else ""
