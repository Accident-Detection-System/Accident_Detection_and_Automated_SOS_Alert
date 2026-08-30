from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import mysql.connector
import bcrypt
import os
import threading
import cv2
import time
import smtplib
import requests
import base64
import numpy as np
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from shapely.geometry import Polygon
from ultralytics import YOLO
import math
import re

app = Flask(__name__)
app.secret_key = "accidentDetectionSecret123"
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10 * 1024 * 1024)

UPLOAD_FOLDER = "uploads"
SCREENSHOT_FOLDER = "static/screenshots"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

model = YOLO("yolov8n.pt")

# ==================== DB ====================

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jamsheer@2006",
        database="accident_detection"
    )

# ==================== HAVERSINE ====================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def find_nearest_hospitals(accident_lat, accident_lon, top_n=3):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, location, latitude, longitude, phone FROM hospitals WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        hospitals = cursor.fetchall()
        cursor.close()
        db.close()
        for h in hospitals:
            h["distance_km"] = haversine(accident_lat, accident_lon, float(h["latitude"]), float(h["longitude"]))
        hospitals.sort(key=lambda x: x["distance_km"])
        return hospitals[:top_n]
    except Exception as e:
        print(f"Error finding nearest hospitals: {e}")
        return []

# ==================== SEVERITY SCORING ====================

def compute_severity(iou, vehicle_classes, num_objects):
    score = iou * 40
    if "truck" in vehicle_classes or "bus" in vehicle_classes:
        score += 30
    elif "car" in vehicle_classes:
        score += 20
    elif "motorcycle" in vehicle_classes:
        score += 15
    score += min(num_objects * 3, 20)
    score = min(int(score), 100)
    if score >= 75:
        label, color = "CRITICAL", "#ff4757"
    elif score >= 55:
        label, color = "HIGH", "#ff6b35"
    elif score >= 35:
        label, color = "MEDIUM", "#ffa502"
    else:
        label, color = "LOW", "#2ed573"
    return {"score": score, "label": label, "color": color}

# ==================== AMBULANCE ETA ====================

def estimate_eta_minutes(distance_km):
    if distance_km <= 0:
        return 1
    return max(1, round((distance_km / 40) * 60))

# ==================== VIDEO CLIP ====================

def save_accident_clip(frames_buffer, alert_id):
    if not frames_buffer:
        return None
    clip_path = f"{SCREENSHOT_FOLDER}/clip_{alert_id}.mp4"
    h, w = frames_buffer[0].shape[:2]
    out = cv2.VideoWriter(clip_path, cv2.VideoWriter_fourcc(*'mp4v'), 10, (w, h))
    for f in frames_buffer:
        out.write(f)
    out.release()
    return clip_path

# ==================== EMAIL ====================

SENDER_EMAIL = "jamsheerkhan118@gmail.com"
SENDER_PASSWORD = "snby caik mngj kalx"

def send_email(screenshot_path, location, receiver_emails, hospital_names=None,
               distances=None, clip_path=None, severity=None, etas=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(receiver_emails)
        severity_label = severity["label"] if severity else "UNKNOWN"
        msg["Subject"] = f"ACCIDENT [{severity_label}] - Emergency Alert"

        nearest_info = ""
        if hospital_names and distances:
            nearest_info = "\n\nNEAREST HOSPITALS ALERTED:\n"
            for i, (name, dist) in enumerate(zip(hospital_names, distances)):
                eta_min = etas[i] if etas and i < len(etas) else estimate_eta_minutes(dist)
                nearest_info += f"  Hospital: {name} - {dist:.1f} km away - ETA ~{eta_min} min\n"

        severity_line = ""
        if severity:
            severity_line = f"\nSEVERITY: {severity['label']} (Score: {severity['score']}/100)\n"

        body = (
            f"ACCIDENT DETECTED!\n"
            f"{severity_line}"
            f"\nLocation: {location}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{nearest_info}\n"
            f"Please dispatch emergency response immediately."
        )
        msg.attach(MIMEText(body, "plain"))

        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-Disposition", "attachment", filename="accident_screenshot.png")
                msg.attach(img)

        if clip_path and os.path.exists(clip_path):
            with open(clip_path, "rb") as f:
                clip = MIMEBase('application', 'octet-stream')
                clip.set_payload(f.read())
                encoders.encode_base64(clip)
                clip.add_header('Content-Disposition', 'attachment', filename='accident_clip.mp4')
                msg.attach(clip)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for email in receiver_emails:
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== SMS (SMSMobileAPI) ====================
# Get your API key from your SMSMobileAPI dashboard: https://smsmobileapi.com
# Preferred: set it as an environment variable before starting Flask, e.g.
#   Windows (cmd):  set SMS_API_KEY=your_key_here
#   Windows (PowerShell): $env:SMS_API_KEY="your_key_here"
#   Linux/Mac:      export SMS_API_KEY=your_key_here
# Fallback: paste it directly into SMS_API_KEY below for local testing.
# If no key is available either way, SMS sending is skipped (email still works).
SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
SMS_API_URL = "https://api.smsmobileapi.com/sendsms/"
SMS_DEFAULT_COUNTRY_CODE = "91"  # used when a hospital's phone number has no country code

def send_sms_alerts(nearest_hospitals, location, severity=None):
    if not SMS_API_KEY:
        print("SMS skipped: SMS_API_KEY not set (env var or SMS_API_KEY in app.py)")
        return False

    clean_phones = []
    for h in nearest_hospitals or []:
        digits = "".join(ch for ch in str(h.get("phone", "")) if ch.isdigit())
        if len(digits) < 10:
            continue
        # If the number doesn't already include a country code, prefix the default one.
        if len(digits) == 10:
            phone = f"+{SMS_DEFAULT_COUNTRY_CODE}{digits}"
        else:
            phone = f"+{digits}"
        clean_phones.append(phone)
    if not clean_phones:
        return False

    severity_label = severity["label"] if severity else "UNKNOWN"
    message = f"ACCIDENT ALERT [{severity_label}]: {location}. Please dispatch emergency response immediately."

    all_ok = True
    for phone in clean_phones:
        try:
            resp = requests.get(
                SMS_API_URL,
                params={
                    "apikey": SMS_API_KEY,
                    "recipients": phone,
                    "message": message,
                },
                timeout=8,
            )
            result = resp.json()
            print(f"SMSMobileAPI response for {phone}:", result)
            if resp.status_code != 200:
                all_ok = False
        except Exception as e:
            print(f"SMS error sending to {phone}: {e}")
            all_ok = False

    return all_ok

# ==================== LOCATION ====================

def get_ip_location():
    try:
        ip = requests.get("https://api64.ipify.org?format=json", timeout=5).json()["ip"]
        loc = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        if loc["status"] == "success":
            return {"label": f"{loc['city']}, {loc['country']}", "lat": loc["lat"], "lon": loc["lon"]}
    except:
        pass
    return {"label": "Location unavailable", "lat": None, "lon": None}

# ==================== ACCIDENT HANDLER ====================

def handle_accident_detected(frame, alert_id, camera_id, hospital_id, hospital_email,
                              gps_lat=None, gps_lon=None, frames_buffer=None,
                              user_id=None, severity=None):
    screenshot_path = f"{SCREENSHOT_FOLDER}/accident_{alert_id}.png"
    cv2.imwrite(screenshot_path, frame)

    clip_path = None
    if frames_buffer:
        clip_path = save_accident_clip(frames_buffer, alert_id)

    if gps_lat and gps_lon:
        location_label = f"Lat: {gps_lat:.6f}, Lon: {gps_lon:.6f} (GPS)"
        acc_lat, acc_lon = gps_lat, gps_lon
    else:
        loc = get_ip_location()
        location_label = loc["label"]
        acc_lat, acc_lon = loc.get("lat"), loc.get("lon")

    nearest = []
    emails_to_alert = []
    hospital_names = []
    distances = []
    etas = []

    if acc_lat and acc_lon:
        nearest = find_nearest_hospitals(acc_lat, acc_lon, top_n=3)
        for h in nearest:
            if h["email"] not in emails_to_alert:
                emails_to_alert.append(h["email"])
            hospital_names.append(h["name"])
            distances.append(h["distance_km"])
            etas.append(estimate_eta_minutes(h["distance_km"]))

    if hospital_email and hospital_email not in emails_to_alert:
        emails_to_alert.append(hospital_email)

    email_sent = send_email(
        screenshot_path, location_label, emails_to_alert,
        hospital_names, distances, clip_path=clip_path,
        severity=severity, etas=etas
    )
    send_sms_alerts(nearest, location_label, severity)

    severity_label = severity["label"] if severity else "UNKNOWN"
    severity_score = severity["score"] if severity else 0
    notified_ids_str = ",".join(str(h["id"]) for h in nearest if h.get("id"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE alerts SET accident_detected=%s, screenshot_path=%s, location=%s, "
        "email_sent=%s, accident_clip_path=%s, severity_label=%s, severity_score=%s, "
        "notified_hospital_ids=%s, user_id=COALESCE(user_id,%s) WHERE id=%s",
        (True, screenshot_path, location_label, email_sent,
         clip_path, severity_label, severity_score, notified_ids_str, user_id, alert_id)
    )
    db.commit()
    cursor.close()
    db.close()

    nearest_info = [
        {
            "id": h["id"],
            "name": h["name"],
            "distance_km": round(h["distance_km"], 1),
            "phone": h.get("phone", ""),
            "eta_min": estimate_eta_minutes(h["distance_km"])
        }
        for h in nearest
    ]

    payload = {
        "alert_id": alert_id,
        "location": location_label,
        "screenshot": "/" + screenshot_path,
        "clip": "/" + clip_path if clip_path else None,
        "nearest_hospitals": nearest_info,
        "gps_lat": acc_lat,
        "gps_lon": acc_lon,
        "severity": severity,
        "status": "pending",
    }

    notified_hospital_ids = set()
    if hospital_id:
        socketio.emit("accident_alert", {**payload, "camera_id": camera_id}, room=f"hospital_{hospital_id}")
        notified_hospital_ids.add(hospital_id)

    for h in nearest:
        h_id = h.get("id")
        if h_id and h_id not in notified_hospital_ids:
            socketio.emit("accident_alert", {**payload, "camera_id": camera_id}, room=f"hospital_{h_id}")
            notified_hospital_ids.add(h_id)

    if user_id:
        socketio.emit("accident_alert", payload, room=f"user_{user_id}")

    return location_label, nearest_info

# ==================== VIDEO PROCESSING ====================

processing_status = {}

def process_video_task(video_path, video_name, alert_id, camera_id, hospital_id,
                       hospital_email, user_id=None, gps_lat=None, gps_lon=None):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        processing_status[alert_id] = {"status": "error"}
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count = 0
    screenshot_taken = False
    frames_buffer = []
    processing_status[alert_id] = {"status": "processing", "progress": 0, "accident": False}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        progress = int((frame_count / total_frames) * 100)
        processing_status[alert_id]["progress"] = progress

        frames_buffer.append(frame.copy())
        if len(frames_buffer) > 50:
            frames_buffer.pop(0)

        if frame_count % 5 != 0:
            continue

        results = model(frame, verbose=False)
        detected_now = False
        best_iou = 0
        involved_classes = []
        num_objects = len(results[0].boxes)

        if num_objects >= 2:
            for i in range(num_objects):
                for j in range(i + 1, num_objects):
                    obj1 = results[0].boxes[i]
                    obj2 = results[0].boxes[j]
                    cls1 = model.names[int(obj1.cls)]
                    cls2 = model.names[int(obj2.cls)]
                    if (("person" in [cls1, cls2]) and
                            (cls1 in ["car", "motorcycle", "truck", "bus"] or
                             cls2 in ["car", "motorcycle", "truck", "bus"])):
                        x1_1, y1_1, x2_1, y2_1 = obj1.xyxy[0]
                        x1_2, y1_2, x2_2, y2_2 = obj2.xyxy[0]
                        poly1 = Polygon([(x1_1, y1_1), (x2_1, y1_1), (x2_1, y2_1), (x1_1, y2_1)])
                        poly2 = Polygon([(x1_2, y1_2), (x2_2, y1_2), (x2_2, y2_2), (x1_2, y2_2)])
                        iou = poly1.intersection(poly2).area / poly1.union(poly2).area
                        if iou > 0.37:
                            detected_now = True
                            if iou > best_iou:
                                best_iou = iou
                                involved_classes = [cls1, cls2]

        if detected_now and not screenshot_taken:
            severity = compute_severity(best_iou, involved_classes, num_objects)
            location_label, nearest = handle_accident_detected(
                frame, alert_id, camera_id, hospital_id, hospital_email,
                gps_lat=gps_lat, gps_lon=gps_lon,
                frames_buffer=list(frames_buffer),
                user_id=user_id, severity=severity
            )
            processing_status[alert_id]["accident"] = True
            processing_status[alert_id]["screenshot"] = f"/{SCREENSHOT_FOLDER}/accident_{alert_id}.png"
            processing_status[alert_id]["clip"] = f"/{SCREENSHOT_FOLDER}/clip_{alert_id}.mp4"
            processing_status[alert_id]["location"] = location_label
            processing_status[alert_id]["nearest_hospitals"] = nearest
            processing_status[alert_id]["gps_lat"] = gps_lat
            processing_status[alert_id]["gps_lon"] = gps_lon
            processing_status[alert_id]["severity"] = severity
            screenshot_taken = True

    cap.release()
    processing_status[alert_id]["status"] = "done"
    processing_status[alert_id]["progress"] = 100

# ==================== LIVE CAMERA ====================

live_sessions = {}

@socketio.on("join")
def on_join(data):
    hospital_id = data.get("hospital_id")
    user_id = data.get("user_id")
    if hospital_id:
        join_room(f"hospital_{hospital_id}")
    if user_id:
        join_room(f"user_{user_id}")
    emit("joined", {"message": "Joined room"})

@socketio.on("gps_update")
def on_gps_update(data):
    sid = request.sid
    if sid in live_sessions:
        live_sessions[sid]["lat"] = data.get("lat")
        live_sessions[sid]["lon"] = data.get("lon")

# ==================== PER-ALERT LIVE TRACKING ====================
# Once an alert exists, the road user and any hospital/ambulance responding to it
# join a shared "alert_<id>" room and stream each other their live GPS position,
# so both sides can watch the other approach on a map in real time.

@socketio.on("join_alert_room")
def on_join_alert_room(data):
    alert_id = data.get("alert_id")
    role = data.get("role")
    name = data.get("name")
    if not alert_id:
        return
    join_room(f"alert_{alert_id}")
    emit("peer_joined_alert", {"alert_id": alert_id, "role": role, "name": name},
         room=f"alert_{alert_id}", include_self=False)

@socketio.on("share_live_location")
def on_share_live_location(data):
    alert_id = data.get("alert_id")
    lat = data.get("lat")
    lon = data.get("lon")
    if not alert_id or lat is None or lon is None:
        return
    emit("peer_location_update", {
        "alert_id": alert_id,
        "lat": lat,
        "lon": lon,
        "role": data.get("role"),
        "name": data.get("name"),
    }, room=f"alert_{alert_id}", include_self=False)

@socketio.on("live_frame")
def on_live_frame(data):
    sid = request.sid
    session_data = live_sessions.get(sid)
    if not session_data or session_data.get("accident_sent"):
        return

    try:
        img_data = base64.b64decode(data["frame"])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return

        session_data.setdefault("frames_buffer", []).append(frame.copy())
        if len(session_data["frames_buffer"]) > 50:
            session_data["frames_buffer"].pop(0)

        results = model(frame, verbose=False)
        detected = False
        best_iou = 0
        involved_classes = []
        num_objects = len(results[0].boxes)

        if num_objects >= 2:
            for i in range(num_objects):
                for j in range(i + 1, num_objects):
                    obj1 = results[0].boxes[i]
                    obj2 = results[0].boxes[j]
                    cls1 = model.names[int(obj1.cls)]
                    cls2 = model.names[int(obj2.cls)]
                    if (("person" in [cls1, cls2]) and
                            (cls1 in ["car", "motorcycle", "truck", "bus"] or
                             cls2 in ["car", "motorcycle", "truck", "bus"])):
                        x1_1, y1_1, x2_1, y2_1 = obj1.xyxy[0]
                        x1_2, y1_2, x2_2, y2_2 = obj2.xyxy[0]
                        poly1 = Polygon([(x1_1, y1_1), (x2_1, y1_1), (x2_1, y2_1), (x1_1, y2_1)])
                        poly2 = Polygon([(x1_2, y1_2), (x2_2, y1_2), (x2_2, y2_2), (x1_2, y2_2)])
                        iou = poly1.intersection(poly2).area / poly1.union(poly2).area
                        if iou > 0.37:
                            detected = True
                            if iou > best_iou:
                                best_iou = iou
                                involved_classes = [cls1, cls2]

        emit("detection_result", {"detected": detected})

        if detected:
            severity = compute_severity(best_iou, involved_classes, num_objects)
            hospital_id = session_data.get("hospital_id")
            user_id = session_data.get("user_id")
            camera_id = session_data.get("camera_id")  # None for a road user's own live phone stream
            hospital_email = session_data.get("hospital_email", "")

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO alerts (camera_id, hospital_id, user_id, video_name, status) VALUES (%s,%s,%s,%s,'pending')",
                (camera_id, hospital_id, user_id, "live_camera")
            )
            db.commit()
            alert_id = cursor.lastrowid
            cursor.close()
            db.close()

            location_label, nearest = handle_accident_detected(
                frame, alert_id, camera_id, hospital_id, hospital_email,
                gps_lat=session_data.get("lat"),
                gps_lon=session_data.get("lon"),
                frames_buffer=list(session_data.get("frames_buffer", [])),
                user_id=user_id, severity=severity
            )

            live_sessions[sid]["accident_sent"] = True
            confirmed_payload = {
                "alert_id": alert_id,
                "location": location_label,
                "nearest_hospitals": nearest,
                "gps_lat": session_data.get("lat"),
                "gps_lon": session_data.get("lon"),
                "severity": severity,
                "status": "pending",
            }
            emit("accident_confirmed", confirmed_payload)
            for h in nearest:
                h_id = h.get("id")
                if h_id:
                    socketio.emit("accident_confirmed", confirmed_payload, room=f"hospital_{h_id}")

    except Exception as e:
        print(f"Live frame error: {e}")

@socketio.on("start_live")
def on_start_live(data):
    sid = request.sid
    live_sessions[sid] = {
        "hospital_id": data.get("hospital_id"),
        "hospital_email": data.get("hospital_email", ""),
        "user_id": data.get("user_id"),
        "camera_id": data.get("camera_id"),
        "lat": None, "lon": None,
        "accident_sent": False,
        "frames_buffer": []
    }
    emit("live_started", {"message": "Live detection started"})

@socketio.on("stop_live")
def on_stop_live():
    live_sessions.pop(request.sid, None)
    emit("live_stopped", {"message": "Stopped"})

@socketio.on("disconnect")
def on_disconnect():
    live_sessions.pop(request.sid, None)

# ==================== HOSPITAL AUTH ====================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    location = data.get("location")
    phone = data.get("phone")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if not all([name, email, password]):
        return jsonify({"error": "All fields required"}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO hospitals (name, email, password, location, phone, latitude, longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (name, email, hashed, location, phone, latitude, longitude)
        )
        db.commit()
        hospital_id = cursor.lastrowid
        cursor.close()
        db.close()
        session["hospital_id"] = hospital_id
        session["hospital_name"] = name
        session["hospital_email"] = email
        session["user_type"] = "hospital"
        return jsonify({"message": "Registered successfully", "hospital_id": hospital_id,
                        "name": name, "email": email, "user_type": "hospital"})
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already registered"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM hospitals WHERE email=%s", (email,))
        hospital = cursor.fetchone()
        cursor.close()
        db.close()
        if not hospital or not bcrypt.checkpw(password.encode(), hospital["password"].encode()):
            return jsonify({"error": "Invalid email or password"}), 400
        session["hospital_id"] = hospital["id"]
        session["hospital_name"] = hospital["name"]
        session["hospital_email"] = hospital["email"]
        session["user_type"] = "hospital"
        return jsonify({"message": "Login successful", "hospital_id": hospital["id"],
                        "name": hospital["name"], "email": hospital["email"], "user_type": "hospital"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/me")
def me():
    if session.get("user_type") == "hospital" and "hospital_id" in session:
        return jsonify({"user_type": "hospital", "hospital_id": session["hospital_id"],
                        "name": session["hospital_name"], "email": session["hospital_email"]})
    if session.get("user_type") == "user" and "user_id" in session:
        return jsonify({"user_type": "user", "user_id": session["user_id"],
                        "name": session["user_name"], "email": session["user_email"]})
    return jsonify({"error": "Not logged in"}), 401

# ==================== USER AUTH ====================

@app.route("/api/user/register", methods=["POST"])
def user_register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    if not all([name, email, password]):
        return jsonify({"error": "All fields required"}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, phone) VALUES (%s,%s,%s,%s)",
            (name, email, hashed, phone)
        )
        db.commit()
        user_id = cursor.lastrowid
        cursor.close()
        db.close()
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email
        session["user_type"] = "user"
        return jsonify({"message": "Registered successfully", "user_id": user_id,
                        "name": name, "email": email, "user_type": "user"})
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already registered"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/login", methods=["POST"])
def user_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Invalid email or password"}), 400
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_type"] = "user"
        return jsonify({"message": "Login successful", "user_id": user["id"],
                        "name": user["name"], "email": user["email"], "user_type": "user"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== CAMERA ROUTES ====================

@app.route("/api/cameras/request", methods=["POST"])
def request_camera():
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    name = data.get("name")
    location = data.get("location")
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO cameras (name, location, status, hospital_id) VALUES (%s,%s,'accepted',%s)",
            (name, location, session["hospital_id"])
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "Camera added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/cameras/my")
def my_cameras():
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cameras WHERE hospital_id=%s", (session["hospital_id"],))
    cameras = cursor.fetchall()
    cursor.close()
    db.close()
    for c in cameras:
        c["created_at"] = str(c["created_at"])
    return jsonify(cameras)

@app.route("/api/cameras/accept/<int:camera_id>", methods=["POST"])
def accept_camera(camera_id):
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE cameras SET status='accepted' WHERE id=%s AND hospital_id=%s",
                   (camera_id, session["hospital_id"]))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"message": "Camera accepted"})

# ==================== VIDEO UPLOAD ====================

@app.route("/api/upload", methods=["POST"])
def upload():
    hospital_id = session.get("hospital_id")
    user_id = session.get("user_id")
    hospital_email = session.get("hospital_email", "")
    if not hospital_id and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    camera_id = request.form.get("camera_id")
    if not camera_id and hospital_id:
        return jsonify({"error": "Select a camera"}), 400
    if not camera_id:
        camera_id = None  # road user uploading their own video, not tied to any camera
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400
    video = request.files["video"]
    video_name = f"{int(time.time())}_{video.filename}"
    video_path = os.path.join(UPLOAD_FOLDER, video_name)
    video.save(video_path)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO alerts (camera_id, hospital_id, user_id, video_name, status) VALUES (%s,%s,%s,%s,'pending')",
        (camera_id, hospital_id, user_id, video_name)
    )
    db.commit()
    alert_id = cursor.lastrowid
    cursor.close()
    db.close()
    gps_lat = request.form.get("gps_lat")
    gps_lon = request.form.get("gps_lon")
    gps_lat = float(gps_lat) if gps_lat else None
    gps_lon = float(gps_lon) if gps_lon else None
    thread = threading.Thread(
        target=process_video_task,
        args=(video_path, video_name, alert_id, camera_id, hospital_id, hospital_email, user_id),
        kwargs={"gps_lat": gps_lat, "gps_lon": gps_lon}
    )
    thread.start()
    return jsonify({"alert_id": alert_id, "message": "Processing started"})

@app.route("/api/status/<int:alert_id>")
def status(alert_id):
    if alert_id in processing_status:
        return jsonify(processing_status[alert_id])
    return jsonify({"status": "not found"}), 404

# ==================== HELPERS ====================

def parse_lat_lon(location_str):
    if not location_str:
        return None, None
    m = re.search(r"Lat:\s*(-?\d+\.\d+),\s*Lon:\s*(-?\d+\.\d+)", location_str)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

@app.route("/api/alerts")
def get_alerts():
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    hid = session["hospital_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT a.*, c.name as camera_name, ah.name as accepted_by_name, ah.phone as accepted_by_phone "
        "FROM alerts a "
        "LEFT JOIN cameras c ON a.camera_id=c.id "
        "LEFT JOIN hospitals ah ON a.accepted_by_hospital_id=ah.id "
        "WHERE a.hospital_id=%s OR FIND_IN_SET(%s, a.notified_hospital_ids) "
        "ORDER BY a.created_at DESC",
        (hid, str(hid))
    )
    alerts = cursor.fetchall()
    cursor.close()
    db.close()
    for a in alerts:
        a["created_at"] = str(a["created_at"])
        a["accepted_at"] = str(a["accepted_at"]) if a.get("accepted_at") else None
        a["lat"], a["lon"] = parse_lat_lon(a.get("location"))
    return jsonify(alerts)

# ==================== ACCEPT / RESOLVE ====================
# A hospital accepting an alert is the "confidence signal" the road user needs — it
# confirms a real responder has seen the crash and is coming, not just that an email
# went out. Only one hospital can hold an alert; the rest get told it was taken.

@app.route("/api/alerts/<int:alert_id>/accept", methods=["POST"])
def accept_alert(alert_id):
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    hospital_id = session["hospital_id"]
    hospital_name = session["hospital_name"]

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alerts WHERE id=%s", (alert_id,))
    alert = cursor.fetchone()
    if not alert:
        cursor.close(); db.close()
        return jsonify({"error": "Alert not found"}), 404
    if alert.get("status") == "accepted":
        cursor.close(); db.close()
        already = "your hospital" if alert.get("accepted_by_hospital_id") == hospital_id else "another hospital"
        return jsonify({"error": f"This alert was already accepted by {already}"}), 409

    cursor.execute(
        "UPDATE alerts SET status='accepted', accepted_by_hospital_id=%s, accepted_at=NOW() WHERE id=%s",
        (hospital_id, alert_id)
    )
    db.commit()
    cursor.execute("SELECT phone, location FROM hospitals WHERE id=%s", (hospital_id,))
    hinfo = cursor.fetchone() or {}
    cursor.close()
    db.close()

    accept_payload = {
        "alert_id": alert_id,
        "hospital_id": hospital_id,
        "hospital_name": hospital_name,
        "hospital_phone": hinfo.get("phone"),
        "hospital_location": hinfo.get("location"),
        "status": "accepted",
    }

    # Confirm to the road user directly (confidence signal) and to anyone already
    # sharing the alert room (both sides may have joined it before this point).
    if alert.get("user_id"):
        socketio.emit("alert_accepted", accept_payload, room=f"user_{alert['user_id']}")
    socketio.emit("alert_accepted", accept_payload, room=f"alert_{alert_id}")

    # Tell every other hospital that was notified about this alert that it's been
    # taken, so their pending toast/list entry can be greyed out instead of sitting
    # there implying they should still respond.
    notified = (alert.get("notified_hospital_ids") or "").split(",")
    for hid_str in notified:
        hid_str = hid_str.strip()
        if hid_str.isdigit() and int(hid_str) != hospital_id:
            socketio.emit("alert_taken", {"alert_id": alert_id, "by": hospital_name},
                          room=f"hospital_{hid_str}")

    return jsonify({"message": "Alert accepted", **accept_payload})

@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    hospital_id = session["hospital_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alerts WHERE id=%s AND accepted_by_hospital_id=%s", (alert_id, hospital_id))
    alert = cursor.fetchone()
    if not alert:
        cursor.close(); db.close()
        return jsonify({"error": "You can only resolve an alert your hospital accepted"}), 403
    cursor.execute("UPDATE alerts SET status='resolved' WHERE id=%s", (alert_id,))
    db.commit()
    cursor.close()
    db.close()
    payload = {"alert_id": alert_id, "status": "resolved"}
    if alert.get("user_id"):
        socketio.emit("alert_resolved", payload, room=f"user_{alert['user_id']}")
    socketio.emit("alert_resolved", payload, room=f"alert_{alert_id}")
    return jsonify({"message": "Alert marked resolved", **payload})

# ==================== SOS PANIC BUTTON ====================

@app.route("/api/sos", methods=["POST"])
def sos_alert():
    user_id = session.get("user_id")
    hospital_id = session.get("hospital_id")
    if not user_id and not hospital_id:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    if not lat or not lon:
        return jsonify({"error": "GPS location required. Please allow location access."}), 400
    lat = float(lat)
    lon = float(lon)
    location_label = f"Lat: {lat:.6f}, Lon: {lon:.6f} (SOS Manual Report)"
    nearest = find_nearest_hospitals(lat, lon, top_n=3)
    emails_to_alert = [h["email"] for h in nearest]
    hospital_names = [h["name"] for h in nearest]
    distances = [h["distance_km"] for h in nearest]
    etas = [estimate_eta_minutes(h["distance_km"]) for h in nearest]
    severity = {"score": 60, "label": "HIGH", "color": "#ff6b35"}
    email_sent = send_email(
        None, location_label, emails_to_alert,
        hospital_names, distances,
        severity=severity, etas=etas
    )
    send_sms_alerts(nearest, location_label, severity)
    notified_ids_str = ",".join(str(h["id"]) for h in nearest if h.get("id"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO alerts (camera_id, hospital_id, user_id, video_name, accident_detected, "
        "location, email_sent, severity_label, severity_score, status, notified_hospital_ids) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (None, hospital_id, user_id, "SOS_MANUAL", True, location_label,
         email_sent, severity["label"], severity["score"], "pending", notified_ids_str)
    )
    db.commit()
    alert_id = cursor.lastrowid
    cursor.close()
    db.close()
    nearest_info = [
        {
            "id": h["id"],
            "name": h["name"],
            "distance_km": round(h["distance_km"], 1),
            "phone": h.get("phone", ""),
            "eta_min": estimate_eta_minutes(h["distance_km"])
        }
        for h in nearest
    ]
    payload = {
        "alert_id": alert_id,
        "location": location_label,
        "nearest_hospitals": nearest_info,
        "gps_lat": lat,
        "gps_lon": lon,
        "severity": severity,
        "sos": True,
        "status": "pending",
    }
    for h in nearest:
        socketio.emit("accident_alert", payload, room=f"hospital_{h['id']}")
    if user_id:
        socketio.emit("accident_alert", payload, room=f"user_{user_id}")
    return jsonify({
        "alert_id": alert_id,
        "message": f"SOS sent! {len(nearest)} hospital(s) alerted.",
        "nearest_hospitals": nearest_info,
        "email_sent": email_sent
    })

# ==================== ROAD USER: AUTOMATIC MOTION-BASED CRASH DETECTION ====================
# Unlike /api/hardware/alert (unauthenticated, for standalone devices like an ESP32),
# this route is for a logged-in Road User's own phone — it uses their session, the same
# way /api/sos does, so the alert is tied to their account and history.

@app.route("/api/motion-alert", methods=["POST"])
def motion_alert():
    user_id = session.get("user_id")
    hospital_id = session.get("hospital_id")
    if not user_id and not hospital_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    impact_g = data.get("impact_g")
    speed_confirmed = bool(data.get("speed_confirmed"))
    sound_confirmed = bool(data.get("sound_confirmed"))
    rotation_confirmed = bool(data.get("rotation_confirmed"))
    if not lat or not lon:
        return jsonify({"error": "GPS location required. Please allow location access."}), 400
    lat, lon = float(lat), float(lon)

    confirmed_signals = []
    if speed_confirmed:
        confirmed_signals.append("speed drop")
    if sound_confirmed:
        confirmed_signals.append("loud sound")
    if rotation_confirmed:
        confirmed_signals.append("sudden rotation")
    confidence_note = f"confirmed by {', '.join(confirmed_signals)}" if confirmed_signals else "impact-only, no confirming signal"
    location_label = f"Lat: {lat:.6f}, Lon: {lon:.6f} (Motion sensor, {confidence_note})"
    nearest = find_nearest_hospitals(lat, lon, top_n=3)
    emails_to_alert = [h["email"] for h in nearest]
    hospital_names = [h["name"] for h in nearest]
    distances = [h["distance_km"] for h in nearest]
    etas = [estimate_eta_minutes(h["distance_km"]) for h in nearest]

    # Sensor fusion: each independent confirming signal adds real confidence to the severity
    # score, not just a cosmetic tag — more signals agreeing = a stronger crash signal.
    bonus = (15 if speed_confirmed else 0) + (10 if sound_confirmed else 0) + (10 if rotation_confirmed else 0)
    score = min(int((impact_g or 0) * 15) + bonus, 100)
    if score >= 75:
        label, color = "CRITICAL", "#ff4757"
    elif score >= 55:
        label, color = "HIGH", "#ff6b35"
    elif score >= 35:
        label, color = "MEDIUM", "#ffa502"
    else:
        label, color = "LOW", "#2ed573"
    severity = {"score": score, "label": label, "color": color}

    email_sent = send_email(
        None, location_label, emails_to_alert,
        hospital_names, distances,
        severity=severity, etas=etas
    )
    send_sms_alerts(nearest, location_label, severity)

    notified_ids_str = ",".join(str(h["id"]) for h in nearest if h.get("id"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO alerts (camera_id, hospital_id, user_id, video_name, accident_detected, "
        "location, email_sent, severity_label, severity_score, status, notified_hospital_ids) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (None, hospital_id, user_id, "MOTION_SENSOR", True, location_label,
         email_sent, severity["label"], severity["score"], "pending", notified_ids_str)
    )
    db.commit()
    alert_id = cursor.lastrowid
    cursor.close()
    db.close()

    nearest_info = [
        {
            "id": h["id"], "name": h["name"],
            "distance_km": round(h["distance_km"], 1),
            "phone": h.get("phone", ""),
            "eta_min": estimate_eta_minutes(h["distance_km"])
        }
        for h in nearest
    ]
    payload = {
        "alert_id": alert_id,
        "location": location_label,
        "nearest_hospitals": nearest_info,
        "gps_lat": lat, "gps_lon": lon,
        "severity": severity,
        "motion_triggered": True,
        "status": "pending",
    }
    for h in nearest:
        socketio.emit("accident_alert", payload, room=f"hospital_{h['id']}")
    if user_id:
        socketio.emit("accident_alert", payload, room=f"user_{user_id}")

    return jsonify({
        "alert_id": alert_id,
        "message": f"Crash motion detected ({impact_g:.1f}g)! {len(nearest)} hospital(s) alerted.",
        "nearest_hospitals": nearest_info,
        "email_sent": email_sent
    })

# ==================== HARDWARE / IOT SENSOR (Wokwi ESP32 + MPU6050) ====================

HARDWARE_API_KEY = "change-this-secret-key"  # must match API_KEY in the Wokwi sketch.ino

@app.route("/api/hardware/alert", methods=["POST"])
def hardware_alert():
    if request.headers.get("X-API-Key") != HARDWARE_API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json(force=True, silent=True) or {}
    device_id = data.get("device_id", "unknown-device")
    lat = data.get("lat")
    lon = data.get("lon")
    impact_g = data.get("impact_g")  # peak acceleration magnitude, in g

    if lat is None or lon is None:
        return jsonify({"error": "lat/lon required"}), 400
    lat, lon = float(lat), float(lon)

    location_label = f"Lat: {lat:.6f}, Lon: {lon:.6f} (Hardware Sensor: {device_id})"
    nearest = find_nearest_hospitals(lat, lon, top_n=3)
    emails_to_alert = [h["email"] for h in nearest]
    hospital_names = [h["name"] for h in nearest]
    distances = [h["distance_km"] for h in nearest]
    etas = [estimate_eta_minutes(h["distance_km"]) for h in nearest]

    # Map impact G-force to a severity score. Tune the multiplier to your sensor/threshold.
    score = min(int((impact_g or 0) * 15), 100)
    if score >= 75:
        label, color = "CRITICAL", "#ff4757"
    elif score >= 55:
        label, color = "HIGH", "#ff6b35"
    elif score >= 35:
        label, color = "MEDIUM", "#ffa502"
    else:
        label, color = "LOW", "#2ed573"
    severity = {"score": score, "label": label, "color": color}

    email_sent = send_email(
        None, location_label, emails_to_alert,
        hospital_names, distances,
        severity=severity, etas=etas
    )
    send_sms_alerts(nearest, location_label, severity)

    notified_ids_str = ",".join(str(h["id"]) for h in nearest if h.get("id"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO alerts (camera_id, hospital_id, video_name, accident_detected, "
        "location, email_sent, severity_label, severity_score, status, notified_hospital_ids) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (None, None, f"HARDWARE_{device_id}", True, location_label,
         email_sent, severity["label"], severity["score"], "pending", notified_ids_str)
    )
    db.commit()
    alert_id = cursor.lastrowid
    cursor.close()
    db.close()

    nearest_info = [
        {
            "id": h["id"], "name": h["name"],
            "distance_km": round(h["distance_km"], 1),
            "phone": h.get("phone", ""),
            "eta_min": estimate_eta_minutes(h["distance_km"])
        }
        for h in nearest
    ]
    payload = {
        "alert_id": alert_id,
        "location": location_label,
        "nearest_hospitals": nearest_info,
        "gps_lat": lat, "gps_lon": lon,
        "severity": severity,
        "hardware": True,
        "device_id": device_id,
        "status": "pending",
    }
    for h in nearest:
        socketio.emit("accident_alert", payload, room=f"hospital_{h['id']}")

    return jsonify({
        "message": f"Hardware alert received. {len(nearest)} hospital(s) notified.",
        "alert_id": alert_id,
        "nearest_hospitals": nearest_info,
        "email_sent": email_sent
    })

# ==================== ANALYTICS ====================

@app.route("/api/stats")
def hospital_stats():
    if "hospital_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    hid = session["hospital_id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM alerts
        WHERE hospital_id=%s AND accident_detected=1
          AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    """, (hid,))
    per_day = cursor.fetchall()
    for row in per_day:
        row["day"] = str(row["day"])
    cursor.execute("""
        SELECT HOUR(created_at) as hour, COUNT(*) as count
        FROM alerts
        WHERE hospital_id=%s AND accident_detected=1
        GROUP BY HOUR(created_at)
        ORDER BY hour ASC
    """, (hid,))
    per_hour = cursor.fetchall()
    cursor.execute("""
        SELECT severity_label, COUNT(*) as count
        FROM alerts
        WHERE hospital_id=%s AND accident_detected=1
          AND severity_label IS NOT NULL AND severity_label != ''
        GROUP BY severity_label
    """, (hid,))
    severity_breakdown = cursor.fetchall()
    cursor.execute("""
        SELECT
            COUNT(*) as total_videos,
            SUM(accident_detected) as total_accidents,
            SUM(email_sent) as emails_sent
        FROM alerts WHERE hospital_id=%s
    """, (hid,))
    summary = cursor.fetchone()
    if summary:
        summary["total_videos"] = int(summary["total_videos"] or 0)
        summary["total_accidents"] = int(summary["total_accidents"] or 0)
        summary["emails_sent"] = int(summary["emails_sent"] or 0)
    cursor.close()
    db.close()
    return jsonify({
        "per_day": per_day,
        "per_hour": per_hour,
        "severity_breakdown": severity_breakdown,
        "summary": summary
    })

# ==================== PAGES ====================

@app.route("/phone-sensor")
def phone_sensor():
    return render_template("phone_sensor.html")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
