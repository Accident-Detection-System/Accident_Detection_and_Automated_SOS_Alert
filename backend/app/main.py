from pathlib import Path
import base64
import json
import threading
import time
import cv2
import numpy as np
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from mysql.connector import IntegrityError
from .config import settings
from .db import db_cursor
from .auth import create_token, decode_token, hash_password, verify_password
from .schemas import LoginIn, HospitalRegisterIn, UserRegisterIn, CameraIn, SOSIn
from .services.alerts import nearest_hospitals, eta_minutes, send_email
from .services.detection import detect_frame, save_clip
from .services.processing import process_video, processing_status
from .websocket_manager import manager

app = FastAPI(title=settings.app_name, version="2.0.0")
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/media", StaticFiles(directory=str(settings.upload_dir.parent)), name="media")


def current_user(authorization: str | None = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    return decode_token(authorization[7:])


def public_user(row, user_type):
    return {"id": row["id"], "name": row["name"], "email": row["email"], "user_type": user_type, "phone": row.get("phone")}


def auth_dep(authorization: str = Depends(lambda: None)):
    return current_user(authorization)

# FastAPI's dependency resolver cannot inject an optional header via lambda cleanly; explicit helper below.
from fastapi import Header

def get_current(authorization: str | None = Header(default=None)):
    return current_user(authorization)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}

@app.post("/api/register")
def hospital_register(payload: HospitalRegisterIn):
    try:
        with db_cursor() as (_, cur):
            cur.execute("INSERT INTO hospitals (name,email,password,location,phone,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s,%s)", (payload.name, payload.email, hash_password(payload.password), payload.location, payload.phone, payload.latitude, payload.longitude))
            hid = cur.lastrowid
            cur.execute("SELECT * FROM hospitals WHERE id=%s", (hid,))
            row = cur.fetchone()
        return {"token": create_token(hid, "hospital"), "user": public_user(row, "hospital")}
    except IntegrityError:
        raise HTTPException(400, "Email already registered")

@app.post("/api/login")
def hospital_login(payload: LoginIn):
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT * FROM hospitals WHERE email=%s", (payload.email,))
        row = cur.fetchone()
    if not row or not verify_password(payload.password, row["password"]):
        raise HTTPException(400, "Invalid email or password")
    return {"token": create_token(row["id"], "hospital"), "user": public_user(row, "hospital")}

@app.post("/api/user/register")
def user_register(payload: UserRegisterIn):
    try:
        with db_cursor() as (_, cur):
            cur.execute("INSERT INTO users (name,email,password,phone,latitude,longitude) VALUES (%s,%s,%s,%s,%s,%s)", (payload.name, payload.email, hash_password(payload.password), payload.phone, payload.latitude, payload.longitude))
            uid = cur.lastrowid
            cur.execute("SELECT * FROM users WHERE id=%s", (uid,))
            row = cur.fetchone()
        return {"token": create_token(uid, "user"), "user": public_user(row, "user")}
    except IntegrityError:
        raise HTTPException(400, "Email already registered")

@app.post("/api/user/login")
def user_login(payload: LoginIn):
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT * FROM users WHERE email=%s", (payload.email,))
        row = cur.fetchone()
    if not row or not verify_password(payload.password, row["password"]):
        raise HTTPException(400, "Invalid email or password")
    return {"token": create_token(row["id"], "user"), "user": public_user(row, "user")}

@app.get("/api/me")
def me(user=Depends(get_current)):
    table = "hospitals" if user["type"] == "hospital" else "users"
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute(f"SELECT * FROM {table} WHERE id=%s", (int(user["sub"]),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(401, "Account not found")
    return public_user(row, user["type"])

@app.post("/api/cameras/request")
def camera_create(payload: CameraIn, user=Depends(get_current)):
    if user["type"] != "hospital": raise HTTPException(403, "Hospital account required")
    with db_cursor() as (_, cur):
        cur.execute("INSERT INTO cameras (name,location,status,hospital_id) VALUES (%s,%s,'accepted',%s)", (payload.name, payload.location, int(user["sub"])))
        cid = cur.lastrowid
    return {"id": cid, "message": "Camera added"}

@app.get("/api/cameras/my")
def cameras(user=Depends(get_current)):
    if user["type"] != "hospital": raise HTTPException(403, "Hospital account required")
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT * FROM cameras WHERE hospital_id=%s ORDER BY created_at DESC", (int(user["sub"]),))
        rows = cur.fetchall()
    for r in rows: r["created_at"] = str(r["created_at"])
    return rows

@app.post("/api/cameras/accept/{camera_id}")
def camera_accept(camera_id: int, user=Depends(get_current)):
    if user["type"] != "hospital": raise HTTPException(403, "Hospital account required")
    with db_cursor() as (_, cur):
        cur.execute("UPDATE cameras SET status='accepted' WHERE id=%s AND hospital_id=%s", (camera_id, int(user["sub"])))
    return {"message": "Camera accepted"}

@app.post("/api/upload")
async def upload(background_tasks: BackgroundTasks, video: UploadFile = File(...), camera_id: int | None = Form(default=None), gps_lat: float | None = Form(default=None), gps_lon: float | None = Form(default=None), user=Depends(get_current)):
    hospital_id = int(user["sub"]) if user["type"] == "hospital" else None
    user_id = int(user["sub"]) if user["type"] == "user" else None
    if hospital_id and not camera_id: raise HTTPException(400, "Select a camera")
    if user_id: camera_id = None
    safe_name = Path(video.filename or "video.mp4").name
    if not safe_name.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        raise HTTPException(400, "Unsupported video format")
    stamp = int(time.time() * 1000)
    file_name = f"{stamp}_{safe_name}"
    path = settings.upload_dir / file_name
    size = 0
    with path.open("wb") as f:
        while chunk := await video.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                path.unlink(missing_ok=True); raise HTTPException(413, "Video exceeds the configured size limit")
            f.write(chunk)
    with db_cursor() as (_, cur):
        cur.execute("INSERT INTO alerts (camera_id,hospital_id,video_name) VALUES (%s,%s,%s)", (camera_id, hospital_id, file_name))
        alert_id = cur.lastrowid
    background_tasks.add_task(process_video, str(path), alert_id, camera_id, hospital_id, user_id, gps_lat, gps_lon)
    return {"alert_id": alert_id, "message": "Processing started"}

@app.get("/api/status/{alert_id}")
def status(alert_id: int, user=Depends(get_current)):
    value = processing_status.get(alert_id)
    if value is None: raise HTTPException(404, "Processing job not found")
    return value

@app.get("/api/alerts")
def alerts(user=Depends(get_current)):
    if user["type"] != "hospital": return []
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT a.*,c.name AS camera_name FROM alerts a LEFT JOIN cameras c ON a.camera_id=c.id WHERE a.hospital_id=%s ORDER BY a.created_at DESC LIMIT 100", (int(user["sub"]),))
        rows = cur.fetchall()
    for r in rows: r["created_at"] = str(r["created_at"]); r["accident_detected"] = bool(r["accident_detected"]); r["email_sent"] = bool(r["email_sent"])
    return rows

@app.post("/api/sos")
def sos(payload: SOSIn, user=Depends(get_current)):
    hospitals = nearest_hospitals(payload.lat, payload.lon)
    severity = {"score": 60, "label": "HIGH"}
    recipients = [h["email"] for h in hospitals if h.get("email")]
    if settings.alert_fallback_email: recipients.append(settings.alert_fallback_email)
    location = f"Lat: {payload.lat:.6f}, Lon: {payload.lon:.6f} (SOS Manual Report)"
    body = "SOS EMERGENCY REPORT\n\n" + location + "\n\nNearest hospitals:\n" + "\n".join(f"- {h['name']}: {h['distance_km']:.1f} km, ETA ~{eta_minutes(h['distance_km'])} min" for h in hospitals)
    email_sent = send_email("SOS EMERGENCY ALERT", body, recipients)
    hospital_id = int(user["sub"]) if user["type"] == "hospital" else None
    with db_cursor() as (_, cur):
        cur.execute("INSERT INTO alerts (camera_id,hospital_id,video_name,accident_detected,location,email_sent,severity_label,severity_score) VALUES (%s,%s,%s,1,%s,%s,%s,%s)", (None, hospital_id, "SOS_MANUAL", location, int(email_sent), severity["label"], severity["score"]))
        alert_id = cur.lastrowid
    nearest = [{"id":h["id"],"name":h["name"],"distance_km":round(h["distance_km"],1),"phone":h.get("phone") or "","eta_min":eta_minutes(h["distance_km"])} for h in hospitals]
    result = {"message": f"SOS sent! {len(nearest)} hospital(s) alerted.", "nearest_hospitals": nearest, "email_sent": email_sent, "alert_id": alert_id, "severity": severity, "location": location, "gps_lat": payload.lat, "gps_lon": payload.lon, "sos": True}
    for h in hospitals: manager.broadcast_sync(f"hospital:{h['id']}", {"type":"accident_alert","data":result})
    manager.broadcast_sync(f"user:{int(user['sub'])}", {"type":"accident_alert","data":result})
    return result

@app.get("/api/stats")
def stats(user=Depends(get_current)):
    if user["type"] != "hospital": raise HTTPException(403, "Hospital account required")
    hid = int(user["sub"])
    with db_cursor(dictionary=True) as (_, cur):
        cur.execute("SELECT DATE(created_at) day,COUNT(*) count FROM alerts WHERE hospital_id=%s AND accident_detected=1 AND created_at>=DATE_SUB(NOW(),INTERVAL 30 DAY) GROUP BY DATE(created_at) ORDER BY day", (hid,)); per_day=cur.fetchall()
        cur.execute("SELECT HOUR(created_at) hour,COUNT(*) count FROM alerts WHERE hospital_id=%s AND accident_detected=1 GROUP BY HOUR(created_at) ORDER BY hour", (hid,)); per_hour=cur.fetchall()
        cur.execute("SELECT severity_label,COUNT(*) count FROM alerts WHERE hospital_id=%s AND accident_detected=1 AND severity_label IS NOT NULL GROUP BY severity_label", (hid,)); severity_breakdown=cur.fetchall()
        cur.execute("SELECT COUNT(*) total_videos,COALESCE(SUM(accident_detected),0) total_accidents,COALESCE(SUM(email_sent),0) emails_sent FROM alerts WHERE hospital_id=%s", (hid,)); summary=cur.fetchone()
    for r in per_day: r["day"] = str(r["day"])
    for r in per_hour: r["hour"] = int(r["hour"]); r["count"] = int(r["count"])
    return {"per_day":per_day,"per_hour":per_hour,"severity_breakdown":severity_breakdown,"summary":{k:int(v or 0) for k,v in summary.items()}}

@app.get("/api/hospitals/nearest")
def nearest(lat: float, lon: float, user=Depends(get_current)):
    rows = nearest_hospitals(lat, lon)
    return [{"id":h["id"],"name":h["name"],"location":h.get("location"),"phone":h.get("phone"),"distance_km":round(h["distance_km"],1),"eta_min":eta_minutes(h["distance_km"])} for h in rows]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    room = None

    try:
        user = decode_token(token)
        user_type, user_id = user["type"], int(user["sub"])
        room = f"{user_type}:{user_id}"
        await manager.connect(websocket, room)
        live = {"active": False, "hospital_id": user_id if user_type == "hospital" else None, "user_id": user_id if user_type == "user" else None, "lat": None, "lon": None, "frames": [], "accident_sent": False, "camera_id": None}
        while True:
            message = await websocket.receive_json()
            kind = message.get("type")
            if kind == "join":
                if user_type == "hospital": await manager.connect(websocket, f"hospital:{user_id}")
                else: await manager.connect(websocket, f"user:{user_id}")
            elif kind == "gps_update":
                live["lat"], live["lon"] = message.get("lat"), message.get("lon")
            elif kind == "start_live":
                live.update({"active": True, "accident_sent": False, "camera_id": message.get("camera_id")})
                await websocket.send_json({"type":"live_started"})
            elif kind == "stop_live":
                live["active"] = False; live["frames"] = []
                await websocket.send_json({"type":"live_stopped"})
            elif kind == "live_frame" and live["active"] and not live["accident_sent"]:
                raw = base64.b64decode(message.get("frame", "")); frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                if frame is None: continue
                live["frames"].append(frame.copy()); live["frames"] = live["frames"][-50:]
                result = detect_frame(frame)
                await websocket.send_json({"type":"detection_result","data":{"detected":result["detected"],"severity":result["severity"]}})
                if result["detected"]:
                    camera_id = live["camera_id"] if user_type == "hospital" else None
                    with db_cursor() as (_, cur):
                        cur.execute("INSERT INTO alerts (camera_id,hospital_id,video_name) VALUES (%s,%s,%s)", (camera_id, int(user["sub"]) if user_type=="hospital" else None, "live_camera")); alert_id=cur.lastrowid
                    screenshot_path = settings.screenshot_dir / f"accident_{alert_id}.jpg"; cv2.imwrite(str(screenshot_path), frame)
                    clip_path = save_clip(live["frames"], alert_id)
                    lat,lon=live["lat"],live["lon"]; hospitals=nearest_hospitals(lat,lon) if lat is not None and lon is not None else []
                    recipients=[h["email"] for h in hospitals if h.get("email")]; recipients.append(settings.alert_fallback_email)
                    location=f"Lat: {lat:.6f}, Lon: {lon:.6f} (Live)" if lat is not None and lon is not None else "Location unavailable"
                    email_sent=send_email(f"ACCIDENT [{result['severity']['label']}] - Live Alert", f"ACCIDENT DETECTED\nSeverity: {result['severity']['label']} ({result['severity']['score']}/100)\nLocation: {location}", recipients, str(screenshot_path), clip_path)
                    with db_cursor() as (_,cur): cur.execute("UPDATE alerts SET accident_detected=1,screenshot_path=%s,accident_clip_path=%s,location=%s,email_sent=%s,severity_label=%s,severity_score=%s WHERE id=%s",(str(screenshot_path),clip_path,location,int(email_sent),result['severity']['label'],result['severity']['score'],alert_id))
                    payload={"alert_id":alert_id,"location":location,"gps_lat":lat,"gps_lon":lon,"severity":result["severity"],"nearest_hospitals":[{"id":h["id"],"name":h["name"],"distance_km":round(h["distance_km"],1),"phone":h.get("phone") or "","eta_min":eta_minutes(h["distance_km"])} for h in hospitals],"screenshot":f"/media/screenshots/{screenshot_path.name}","clip":f"/media/clips/{clip_path.split('/')[-1]}" if clip_path else None}
                    await websocket.send_json({"type":"accident_confirmed","data":payload})
                    for h in hospitals: manager.broadcast_sync(f"hospital:{h['id']}", {"type":"accident_alert","data":payload})
                    live["accident_sent"] = True
            
    except WebSocketDisconnect:
        pass
    except Exception:
        try: await websocket.close()
        except Exception: pass
    finally:
        if room:
            manager.disconnect(websocket, room)

@app.get("/media/screenshots/{filename}")
def screenshot(filename: str):
    path = settings.screenshot_dir / Path(filename).name

    if not path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(path)


@app.get("/media/clips/{filename}")
def clip(filename: str):
    path = settings.clip_dir / Path(filename).name

    if not path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(path, media_type="video/mp4")


# ------------------------------------------------------------------
# React frontend
# ------------------------------------------------------------------

if FRONTEND_DIST.exists():

    @app.get("/", response_class=HTMLResponse)
    async def serve_react():
        return FileResponse(FRONTEND_DIST / "index.html")


    @app.get("/{path:path}")
    async def serve_react_routes(path: str):
        requested_file = FRONTEND_DIST / path

        # Serve React static assets
        if requested_file.is_file():
            return FileResponse(requested_file)

        # React SPA fallback
        return FileResponse(FRONTEND_DIST / "index.html")

else:

    @app.get("/", response_class=HTMLResponse)
    async def frontend_not_built():
        return HTMLResponse(
            "<h2>AccidentGuard backend is running.</h2>"
            "<p>React frontend build was not found. Run "
            "<code>npm run build</code> inside the frontend folder.</p>"
        )
