import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

class Settings:
    app_name = os.getenv("APP_NAME", "AccidentGuard API")
    app_env = os.getenv("APP_ENV", "development")
    secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "accident_detection")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    alert_fallback_email = os.getenv("ALERT_FALLBACK_EMAIL", "")
    yolo_model_path = os.getenv("YOLO_MODEL_PATH", str(BASE_DIR / "yolov8n.pt"))
    yolo_confidence = float(os.getenv("YOLO_CONFIDENCE", "0.35"))
    accident_iou_threshold = float(os.getenv("ACCIDENT_IOU_THRESHOLD", "0.37"))
    process_every_n_frames = max(1, int(os.getenv("PROCESS_EVERY_N_FRAMES", "5")))
    upload_dir = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "storage/uploads")))
    screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", str(BASE_DIR / "storage/screenshots")))
    clip_dir = Path(os.getenv("CLIP_DIR", str(BASE_DIR / "storage/clips")))
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "250"))

settings = Settings()
for folder in (settings.upload_dir, settings.screenshot_dir, settings.clip_dir):
    folder.mkdir(parents=True, exist_ok=True)
