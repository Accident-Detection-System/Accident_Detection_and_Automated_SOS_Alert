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
    recipients = [x.strip() for x in dict.fromkeys(recipients or []) if x and x.strip()]

    if not recipients:
        print("[EMAIL] No recipients provided.")
        return False

    if not settings.smtp_user:
        print("[EMAIL] SMTP_USER is missing.")
        return False

    if not settings.smtp_password:
        print("[EMAIL] SMTP_PASSWORD is missing.")
        return False

    try:
        print(f"[EMAIL] Preparing email...")
        print(f"[EMAIL] SMTP server: {settings.smtp_host}:{settings.smtp_port}")
        print(f"[EMAIL] Sender: {settings.smtp_user}")
        print(f"[EMAIL] Recipients: {recipients}")

        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach accident screenshot
        if screenshot_path and os.path.exists(screenshot_path):
            print(f"[EMAIL] Attaching screenshot: {screenshot_path}")

            with open(screenshot_path, "rb") as f:
                img = MIMEImage(f.read())

            img.add_header(
                "Content-Disposition",
                "attachment",
                filename="accident_screenshot.png"
            )
            msg.attach(img)

        # Attach accident video clip
        if clip_path and os.path.exists(clip_path):
            print(f"[EMAIL] Attaching clip: {clip_path}")

            with open(clip_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                "attachment",
                filename="accident_clip.mp4"
            )

            msg.attach(part)

        print("[EMAIL] Connecting to SMTP server...")

        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20
        ) as server:

            print("[EMAIL] SMTP connection established.")

            print("[EMAIL] Logging in...")
            server.login(
                settings.smtp_user,
                settings.smtp_password
            )

            print("[EMAIL] SMTP login successful.")

            print("[EMAIL] Sending email...")

            server.sendmail(
                settings.smtp_user,
                recipients,
                msg.as_string()
            )

        print("[EMAIL] Email sent successfully.")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print("[EMAIL ERROR] Gmail authentication failed.")
        print(f"[EMAIL ERROR] {e}")
        return False

    except smtplib.SMTPException as e:
        print("[EMAIL ERROR] SMTP error occurred.")
        print(f"[EMAIL ERROR] {e}")
        return False

    except Exception as e:
        print("[EMAIL ERROR] Unexpected error.")
        print(f"[EMAIL ERROR] {type(e).__name__}: {e}")
        return False