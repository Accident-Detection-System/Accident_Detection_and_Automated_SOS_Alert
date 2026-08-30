# 🚨 AccidentAlert AI

## AI-Powered Accident Detection & Emergency Response Platform

AccidentAlert AI is a full-stack-style accident detection and emergency
response web application built with **Python, Flask, YOLOv8, OpenCV,
MySQL, Flask-SocketIO, GPS/location services, severity analysis,
hospital discovery, email notifications, SMS support, SOS alerts, and
browser-based phone crash sensing**.

The project is designed to identify potential road accidents from
uploaded videos and live camera frames, generate accident evidence,
estimate severity, identify nearby hospitals, and communicate emergency
alerts.

The project supports two main user roles:

-   🏥 Hospital operators
-   👤 Citizens / users

------------------------------------------------------------------------

# 📌 Table of Contents

-   [Project Overview](#-project-overview)
-   [Key Features](#-key-features)
-   [How the System Works](#-how-the-system-works)
-   [Technology Stack](#-technology-stack)
-   [Project Architecture](#-project-architecture)
-   [Project Structure](#-project-structure)
-   [Database](#-database)
-   [Prerequisites](#-prerequisites)
-   [Installation](#-installation)
-   [Backend Setup](#-backend-setup)
-   [Running the Project](#-running-the-project)
-   [API Documentation](#-api-documentation)
-   [AI Accident Detection](#-ai-accident-detection)
-   [Severity Detection](#-severity-detection)
-   [Live Camera Detection](#-live-camera-detection)
-   [GPS and Nearby Hospitals](#-gps-and-nearby-hospitals)
-   [SOS Emergency System](#-sos-emergency-system)
-   [Phone Crash Sensor](#-phone-crash-sensor)
-   [Hardware Alert API](#-hardware-alert-api)
-   [Email Notifications](#-email-notifications)
-   [SMS Notifications](#-sms-notifications)
-   [Analytics](#-analytics)
-   [Evidence Generation](#-evidence-generation)
-   [Testing](#-testing)
-   [Temporary Deployment with ngrok](#-temporary-deployment-with-ngrok)
-   [Production Deployment](#-production-deployment)
-   [Environment Variables](#-environment-variables)
-   [Security](#-security)
-   [Limitations](#-limitations)
-   [Future Enhancements](#-future-enhancements)
-   [Troubleshooting](#-troubleshooting)
-   [Project Workflow](#-project-workflow)
-   [License](#-license)

------------------------------------------------------------------------

# 📖 Project Overview

Road accidents require rapid identification and emergency response.

AccidentAlert AI attempts to reduce the delay between accident detection
and emergency notification by combining computer vision, real-time
communication, location services, hospital discovery, and emergency
alerting in one web application.

The system can:

1.  Accept road/accident video input.
2.  Process video frames using OpenCV.
3.  Detect people and vehicles using YOLOv8.
4.  Analyze person/vehicle bounding-box overlap.
5.  Detect a potential accident when the configured IoU threshold is
    exceeded.
6.  Calculate a rule-based accident severity score.
7.  Capture an accident screenshot.
8.  Generate an accident video clip from buffered frames.
9.  Obtain GPS coordinates when supplied.
10. Fall back to approximate IP-based location when GPS is unavailable.
11. Find the nearest registered hospitals.
12. Estimate an approximate hospital response ETA from distance.
13. Send email emergency notifications.
14. Optionally send SMS notifications through SMSMobileAPI.
15. Store accident information in MySQL.
16. Notify connected hospital clients through Socket.IO.
17. Support hospital alert acceptance and resolution.
18. Support citizen SOS alerts.
19. Support browser phone-motion crash alerts.
20. Support an external hardware alert API.
21. Provide hospital statistics and analytics.

------------------------------------------------------------------------

# ✨ Key Features

## 🔐 Authentication

The application provides separate authentication flows for hospitals and
citizens.

### 🏥 Hospital

Hospital operators can:

-   Register an account.
-   Log in.
-   Log out.
-   Register/request CCTV cameras.
-   View their cameras.
-   Accept camera requests.
-   Monitor live camera detection.
-   Upload and analyze videos.
-   View accident alerts.
-   Accept accident alerts.
-   Resolve accident alerts.
-   View accident evidence.
-   View accident severity.
-   View statistics.

### 👤 Citizen

Citizens can:

-   Register.
-   Log in.
-   Log out.
-   Upload/analyze videos.
-   Send SOS alerts.
-   Share GPS location.
-   Use the phone crash-sensor page.
-   Participate in live location sharing.

------------------------------------------------------------------------

# 🤖 AI Accident Detection

AccidentAlert AI uses **Ultralytics YOLOv8** for object detection.

The model included with the project is:

``` text
yolov8n.pt
```

The detector can identify objects from the YOLOv8 model's available
classes, with the accident logic specifically considering:

-   Person
-   Car
-   Motorcycle
-   Truck
-   Bus

The current accident detection approach evaluates the spatial overlap
between a detected person and a detected vehicle.

The basic pipeline is:

``` text
Input Video / Camera Frame
          │
          ▼
       OpenCV
          │
          ▼
       YOLOv8
          │
          ▼
 Object Detection
          │
          ├── Person
          │
          └── Vehicle
          │
          ▼
 Bounding Box Analysis
          │
          ▼
 Shapely Polygon Intersection
          │
          ▼
       IoU Score
          │
          ▼
 Accident Decision
          │
          ▼
 Severity + Evidence + Alerts
```

------------------------------------------------------------------------

# ⚠️ AI Detection Note

The current implementation is a prototype accident-detection approach.

The accident decision is based on **YOLOv8 object detection plus
person/vehicle bounding-box overlap** rather than a dedicated
accident-classification model.

The implemented overlap threshold is:

``` text
IoU > 0.37
```

This should not be interpreted as a validated real-world
accident-detection accuracy or safety guarantee.

A production system should be evaluated using representative labeled
accident datasets, temporal tracking/action analysis, false-positive
testing, and real-world validation.

------------------------------------------------------------------------

# 📊 Severity Detection

After a potential accident is detected, the application calculates a
rule-based severity score.

The score uses factors including:

-   Person/vehicle IoU
-   Vehicle class
-   Number of detected objects

The implementation applies additional weighting for vehicle types:

``` text
Truck / Bus      +30
Car              +20
Motorcycle       +15
```

The IoU contributes:

``` text
IoU × 40
```

The number of detected objects can contribute up to:

``` text
20 points
```

The final score is capped at:

``` text
100
```

Severity levels:

      Score Severity
  --------- ----------
      0--34 LOW
     35--54 MEDIUM
     55--74 HIGH
    75--100 CRITICAL

------------------------------------------------------------------------

# 🛠️ Technology Stack

## Web Application

  Technology                    Purpose
  ----------------------------- ---------------------------------
  Python                        Main programming language
  Flask                         Web application and REST API
  Flask-CORS                    Cross-origin request support
  Flask-SocketIO                Real-time communication
  HTML/CSS/JavaScript           Frontend interface
  Chart.js                      Dashboard charts
  Leaflet                       Map/location visualization
  Socket.IO JavaScript client   Real-time browser communication

------------------------------------------------------------------------

## Artificial Intelligence / Computer Vision

  Technology    Purpose
  ------------- ---------------------------------
  YOLOv8        Object detection
  Ultralytics   YOLO implementation
  PyTorch       Deep-learning runtime
  Torchvision   PyTorch computer-vision support
  OpenCV        Video/image processing
  NumPy         Numerical operations
  Shapely       Polygon intersection and IoU

------------------------------------------------------------------------

## Database

``` text
MySQL
```

The backend uses `mysql-connector-python` to communicate with the
database.

------------------------------------------------------------------------

## Communication

The project uses:

-   SMTP / Gmail for email
-   SMSMobileAPI for optional SMS
-   Flask-SocketIO for real-time browser notifications
-   HTTP requests for external location and SMS services

------------------------------------------------------------------------

# 🧱 Project Architecture

``` text
                       ┌──────────────────────┐
                       │      User / CCTV     │
                       │  Video / Camera / SOS│
                       └──────────┬───────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │        Flask         │
                       │    Web Application   │
                       └──────────┬───────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌────────────┐
              │ YOLOv8   │  │  MySQL   │  │ Socket.IO  │
              │ + OpenCV │  │ Database │  │ Real-time  │
              └────┬─────┘  └──────────┘  └────────────┘
                   │
                   ▼
             ┌────────────┐
             │  Shapely   │
             │ IoU Logic  │
             └─────┬──────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Accident Detected│
          └────────┬─────────┘
                   │
       ┌───────────┼──────────────┐
       ▼           ▼              ▼
  Severity      Evidence       Location
       │           │              │
       └───────────┼──────────────┘
                   ▼
          ┌──────────────────┐
          │ Nearby Hospitals │
          └────────┬─────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
      Email / SMS       Hospital Dashboard
```

------------------------------------------------------------------------

# 📂 Project Structure

``` text
Accident-detection-yolov8-main/
│
├── LICENSE
├── README.md
├── app.py
├── main.py
├── yolo_detect.py
├── requirements.txt
├── yolov8n.pt
├── db_migration_accept_and_tracking.sql
│
├── templates/
│   ├── index.html
│   └── phone_sensor.html
│
└── uploads/
    └── generated at runtime
```

The application creates/uses:

``` text
uploads/
static/screenshots/
```

for uploaded files and accident evidence.

------------------------------------------------------------------------

# 🗄️ Database

The application connects to:

``` text
accident_detection
```

MySQL database.

The supplied migration file is:

``` text
db_migration_accept_and_tracking.sql
```

It adds support for accident alert acceptance and tracking.

The migration adds fields including:

``` text
status
user_id
accepted_by_hospital_id
accepted_at
notified_hospital_ids
```

The alert status values are:

``` text
pending
accepted
resolved
```

The application also expects database tables used for:

-   Users
-   Hospitals
-   Cameras
-   Alerts

The exact base-table creation SQL is not included in the uploaded
project ZIP, so an existing compatible `accident_detection`
database/schema is required before running the full web application.

------------------------------------------------------------------------

# 🧰 Prerequisites

Before running AccidentAlert AI, install:

-   Python 3.10+ recommended
-   MySQL Server
-   MySQL Workbench (optional)
-   pip

Optional:

-   ngrok for temporary public access
-   SMSMobileAPI account/API key for SMS alerts

Check Python:

``` bash
python --version
```

Check pip:

``` bash
pip --version
```

Check MySQL:

``` bash
mysql --version
```

------------------------------------------------------------------------

# 📥 Installation

## 1. Extract the Project

Extract the ZIP file and open the project folder:

``` text
Accident-detection-yolov8-main
```

Open this folder in VS Code.

------------------------------------------------------------------------

## 2. Create a Virtual Environment

Windows PowerShell:

``` powershell
python -m venv venv
```

Activate it:

``` powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

``` powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

------------------------------------------------------------------------

# 🐍 Backend Setup

This project uses **Flask**, not FastAPI.

Install the dependencies listed in:

``` text
requirements.txt
```

Run:

``` powershell
pip install -r requirements.txt
```

The supplied requirements file contains:

``` text
opencv-python
torch
torchvision
torchaudio
ultralytics
shapely
python-dotenv
requests
```

The main Flask application also imports:

``` text
flask
flask-cors
flask-socketio
mysql-connector-python
bcrypt
```

If these packages are not already installed, install them with:

``` powershell
pip install flask flask-cors flask-socketio mysql-connector-python bcrypt
```

------------------------------------------------------------------------

# 🗃️ MySQL Setup

Create the database:

``` sql
CREATE DATABASE accident_detection;
```

Select it:

``` sql
USE accident_detection;
```

The application expects tables for users, hospitals, cameras and alerts.

The supplied file:

``` text
db_migration_accept_and_tracking.sql
```

contains an additional migration for alert acceptance and live tracking.

Run it only after the required base tables already exist.

------------------------------------------------------------------------

# ⚙️ Email Configuration

The application contains email notification functionality using Gmail
SMTP.

For security, **do not publish real Gmail credentials in GitHub or in
the README**.

The preferred production approach is to move credentials to environment
variables.

Example:

``` text
SENDER_EMAIL=your-gmail-address
SENDER_PASSWORD=your-gmail-app-password
```

For Gmail, use an App Password rather than your normal Gmail password.

------------------------------------------------------------------------

# ▶️ Running the Web Application

The main web application is:

``` text
app.py
```

From the project directory run:

``` powershell
python app.py
```

The Flask application normally starts on:

``` text
http://127.0.0.1:5000
```

Open the URL in your browser.

------------------------------------------------------------------------

# 🎥 Standalone Video Processing

The project also contains:

``` text
main.py
```

It calls:

``` text
yolo_detect.py
```

and expects:

``` text
sample_video.mp4
```

with an output file:

``` text
output_video_v8.mp4
```

Run:

``` powershell
python main.py
```

However, the standalone `yolo_detect.py` currently contains a database
lookup that references `camera_id` without defining it inside that
function. Therefore, the standalone script may require correction before
it can reliably execute the complete email/location workflow.

For the complete web application, use:

``` powershell
python app.py
```

------------------------------------------------------------------------

# 📚 API Documentation

The Flask application exposes REST endpoints under `/api`.

The current application includes endpoints such as:

  Method   Endpoint                            Purpose
  -------- ----------------------------------- -------------------------
  POST     `/api/register`                     Hospital registration
  POST     `/api/login`                        Hospital login
  POST     `/api/logout`                       Logout
  GET      `/api/me`                           Current session/user
  POST     `/api/user/register`                Citizen registration
  POST     `/api/user/login`                   Citizen login
  POST     `/api/cameras/request`              Request/register camera
  GET      `/api/cameras/my`                   Get hospital cameras
  POST     `/api/cameras/accept/<camera_id>`   Accept camera
  POST     `/api/upload`                       Upload video
  GET      `/api/status/<alert_id>`            Check processing status
  GET      `/api/alerts`                       Get alerts
  POST     `/api/alerts/<alert_id>/accept`     Accept an alert
  POST     `/api/alerts/<alert_id>/resolve`    Resolve an alert
  POST     `/api/sos`                          Send SOS
  POST     `/api/motion-alert`                 Motion-based alert
  POST     `/api/hardware/alert`               External hardware alert
  GET      `/api/stats`                        Hospital statistics

------------------------------------------------------------------------

# 📡 Live Camera Detection

The project uses **Flask-SocketIO** for real-time communication.

The browser can send live camera frames to the backend.

The flow is:

``` text
Browser Camera
      │
      ▼
Capture Frame
      │
      ▼
Socket.IO
      │
      ▼
Flask Backend
      │
      ▼
YOLOv8 Detection
      │
      ▼
Accident Analysis
      │
      ▼
Real-Time Event
      │
      ▼
Hospital Dashboard
```

The backend contains Socket.IO handlers for:

-   Joining rooms
-   GPS updates
-   Live location sharing
-   Live frame processing
-   Starting live detection
-   Stopping live detection
-   Disconnect handling

------------------------------------------------------------------------

# 📍 GPS and Nearby Hospitals

The application can use GPS coordinates supplied by the browser or
client.

If GPS coordinates are not supplied, the application can attempt to
obtain an approximate location using:

``` text
api64.ipify.org
+
ip-api.com
```

GPS/location information can be used to:

-   Identify accident location
-   Find nearby hospitals
-   Send location in alerts
-   Support SOS
-   Support live location sharing

------------------------------------------------------------------------

# 🏥 Nearby Hospital Detection

The application calculates distances between an incident and registered
hospitals using the **Haversine formula**.

The workflow is:

``` text
Accident Location
       │
       ▼
Latitude + Longitude
       │
       ▼
Registered Hospitals
       │
       ▼
Haversine Distance
       │
       ▼
Sort by Distance
       │
       ▼
Nearest 3 Hospitals
```

The application attempts to notify up to the nearest three hospitals
with valid coordinates.

------------------------------------------------------------------------

# 🚨 SOS Emergency System

Citizens can trigger an SOS alert using:

``` text
POST /api/sos
```

The alert can contain:

-   User information
-   GPS latitude
-   GPS longitude
-   Location information

The backend can identify nearby hospitals and communicate the emergency
event.

The general flow is:

``` text
Citizen
   │
   ▼
SOS Button
   │
   ▼
GPS Coordinates
   │
   ▼
Flask API
   │
   ▼
Nearest Hospitals
   │
   ▼
Email / SMS / Real-Time Alert
```

------------------------------------------------------------------------

# 📱 Phone Crash Sensor

The project includes:

``` text
templates/phone_sensor.html
```

This page uses the browser's motion sensor and GPS.

The sensor monitors acceleration magnitude.

The configured impact threshold is:

``` text
2.5 g
```

When the threshold is crossed and GPS is available, the page can send an
alert to:

``` text
/api/hardware/alert
```

using an API key.

The page is intended to demonstrate phone-based crash detection without
additional hardware.

------------------------------------------------------------------------

# 🔌 Hardware Alert API

The backend provides:

``` text
POST /api/hardware/alert
```

for external hardware or sensor integrations.

The phone sensor page uses this endpoint.

The request can contain:

``` text
device_id
lat
lon
impact_g
```

The API can then trigger the emergency alert workflow.

An API key is expected for hardware-originated alerts.

------------------------------------------------------------------------

# 📧 Email Notifications

The application uses Gmail SMTP for emergency email notifications.

Email alerts can include:

-   Accident detected message
-   Severity level
-   Severity score
-   Location
-   Detection time
-   Nearby hospitals
-   Approximate distance
-   Approximate ETA
-   Accident screenshot
-   Accident video clip

The email subject is generated using the severity level, for example:

``` text
ACCIDENT [HIGH] - Emergency Alert
```

Email functionality requires valid SMTP credentials.

------------------------------------------------------------------------

# 📲 SMS Notifications

The application contains optional SMS support using:

``` text
SMSMobileAPI
```

The API key is read from:

``` text
SMS_API_KEY
```

Example Windows PowerShell configuration:

``` powershell
$env:SMS_API_KEY="your_api_key"
```

If no API key is configured, SMS sending is skipped while the rest of
the alert workflow can continue.

The default country code configured in the project is:

``` text
91
```

for Indian phone numbers without a country code.

------------------------------------------------------------------------

# 📈 Analytics

The application provides hospital statistics through:

``` text
/api/stats
```

The frontend uses **Chart.js** for dashboard visualization.

The application can expose operational information such as:

-   Accident counts
-   Email notification status
-   Alert information
-   Hospital-related statistics

The exact charts and dashboard content are implemented in:

``` text
templates/index.html
```

------------------------------------------------------------------------

# 🎥 Evidence Generation

When an accident is detected, the application can create evidence files.

## Uploaded videos

``` text
uploads/
```

## Accident screenshots

``` text
static/screenshots/accident_<alert_id>.png
```

## Accident clips

``` text
static/screenshots/clip_<alert_id>.mp4
```

The screenshot and clip paths are stored with the corresponding alert
record.

------------------------------------------------------------------------

# 🧪 Testing

## Test the Web Application

Start:

``` powershell
python app.py
```

Open:

``` text
http://127.0.0.1:5000
```

Test:

1.  Hospital registration
2.  Hospital login
3.  Citizen registration
4.  Citizen login
5.  Video upload
6.  Accident processing
7.  Alert display
8.  Severity display
9.  Hospital acceptance
10. Alert resolution
11. SOS
12. Phone sensor
13. Analytics
14. Live camera

------------------------------------------------------------------------

# 🌐 Temporary Deployment with ngrok

For a hackathon demonstration, ngrok can be used to expose the Flask
application temporarily.

First run:

``` powershell
python app.py
```

Then in another terminal:

``` powershell
ngrok http 5000
```

ngrok will provide a public HTTPS URL similar to:

``` text
https://example.ngrok-free.app
```

Use that URL for temporary external access.

------------------------------------------------------------------------

# ⚠️ ngrok Important Notes

The Flask application must remain running.

The ngrok tunnel must also remain running.

If the terminal running either process is closed, the temporary public
URL stops working.

The public URL may change when a new tunnel is created.

------------------------------------------------------------------------

# ☁️ Production Deployment

This project is currently structured primarily as a Flask application
and is suitable for development/hackathon demonstration.

For production deployment, the application should be served using a
production WSGI server and configured with:

-   Secure environment variables
-   Production MySQL database
-   HTTPS
-   Strong authentication
-   Secure API keys
-   Persistent file/object storage
-   Proper logging
-   Monitoring
-   Rate limiting
-   Error handling

The current source code should be reviewed and hardened before
production use.

------------------------------------------------------------------------

# 🔐 Environment Variables

The current project uses environment variables for some optional
configuration, including:

``` text
SMS_API_KEY
```

The email credentials in the uploaded source are currently hard-coded.

For a secure version, move all secrets to environment variables:

``` text
SECRET_KEY
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
SENDER_EMAIL
SENDER_PASSWORD
SMS_API_KEY
HARDWARE_API_KEY
```

Never commit real secrets to GitHub.

------------------------------------------------------------------------

# 🔒 Security

Before publishing the project:

-   Remove hard-coded email credentials.
-   Change the Flask secret key.
-   Configure database credentials securely.
-   Use environment variables for API keys.
-   Change the hardware API key from its default value.
-   Use HTTPS for public deployments.
-   Restrict CORS in production.
-   Add proper authentication and authorization checks.
-   Avoid exposing private database information.
-   Rotate any credentials that have already been exposed.

------------------------------------------------------------------------

# ⚠️ Project Limitations

AccidentAlert AI is a prototype and should not be treated as a
safety-critical emergency system.

## AI limitations

The current accident detection mechanism uses:

``` text
YOLOv8 object detection
+
Person/vehicle bounding-box IoU
```

It does not include a dedicated trained accident-classification model in
the uploaded project.

------------------------------------------------------------------------

## False positives / false negatives

Object overlap alone cannot reliably distinguish every real accident
from:

-   People standing near vehicles
-   Crowded scenes
-   Vehicles passing close to people
-   Camera perspective effects
-   Occlusions
-   Unusual road conditions

A production system requires temporal analysis and extensive validation.

------------------------------------------------------------------------

## Location limitations

IP-based geolocation is approximate and should not be considered
equivalent to GPS.

------------------------------------------------------------------------

## ETA limitations

The ambulance/hospital ETA is a simple distance-based estimate using an
assumed speed of:

``` text
40 km/h
```

It does not represent real-time traffic-aware routing.

------------------------------------------------------------------------

## SMS limitations

SMS depends on the external SMSMobileAPI service and a valid API key.

------------------------------------------------------------------------

## Standalone script limitation

The current `yolo_detect.py` references `camera_id` inside
`process_video()` without defining it there, so the standalone `main.py`
workflow may require correction.

------------------------------------------------------------------------

## Security limitations

The uploaded source contains sensitive credentials and a hard-coded
Flask secret key.

These should be changed before public deployment.

------------------------------------------------------------------------

# 🚀 Future Enhancements

Possible improvements include:

-   Dedicated accident classification model
-   Custom accident dataset
-   Temporal video/action analysis
-   Object tracking
-   Better false-positive reduction
-   Confidence calibration
-   Real CCTV/RTSP camera integration
-   Multiple simultaneous camera processing
-   Real-time traffic-aware ambulance ETA
-   Google Maps or other routing integration
-   Ambulance integration
-   Push notifications
-   WhatsApp/SMS expansion
-   Cloud storage for evidence
-   GPU inference
-   Production authentication
-   Role-based access control
-   Admin dashboard
-   Advanced incident reporting
-   Model performance monitoring
-   Automated model retraining
-   Real-world validation and benchmarking

------------------------------------------------------------------------

# 🔄 Project Workflow

## 🏥 Hospital Workflow

``` text
Hospital Registration
        │
        ▼
Hospital Login
        │
        ▼
Hospital Dashboard
        │
        ├───────────────┐
        │               │
        ▼               ▼
 Register Camera    Upload Video
        │               │
        ▼               ▼
 Live Detection     YOLOv8
        │               │
        │               ▼
        │        Accident Detection
        │               │
        │               ▼
        │        Severity Assessment
        │               │
        │               ▼
        │        Evidence Generation
        │               │
        └───────┬───────┘
                │
                ▼
          Accident Alert
                │
                ▼
        Accept / Resolve
                │
                ▼
        Emergency Response
```

------------------------------------------------------------------------

## 👤 Citizen Workflow

``` text
Citizen Registration
        │
        ▼
Citizen Login
        │
        ├───────────────────┐
        │                   │
        ▼                   ▼
   Analyze Video         Send SOS
        │                   │
        ▼                   ▼
      YOLOv8             GPS Location
        │                   │
        ▼                   ▼
 Accident Analysis    Find Hospitals
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
          Emergency Alert
```

------------------------------------------------------------------------

## 📱 Phone Sensor Workflow

``` text
Phone Motion Sensor
        │
        ▼
Acceleration Measurement
        │
        ▼
Impact > 2.5g
        │
        ▼
GPS Available?
        │
        ▼
Hardware Alert API
        │
        ▼
Emergency Processing
        │
        ▼
Hospital Notification
```

------------------------------------------------------------------------

# 🧩 Core Components

  Component                 Technology
  ------------------------- -------------------------
  Web Application           Flask
  Frontend                  HTML + CSS + JavaScript
  Real-Time Communication   Flask-SocketIO
  AI                        YOLOv8
  Deep Learning             PyTorch
  Video Processing          OpenCV
  Geometry                  Shapely
  Database                  MySQL
  Database Driver           mysql-connector-python
  Authentication            Flask Session + bcrypt
  Charts                    Chart.js
  Maps                      Leaflet
  Location                  IP Geolocation + GPS
  Email                     Gmail SMTP
  SMS                       SMSMobileAPI
  HTTP Requests             Requests
  Numerical Processing      NumPy

------------------------------------------------------------------------

# 📦 Dependency Installation Summary

Create and activate the environment:

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the supplied requirements:

``` powershell
pip install -r requirements.txt
```

Install the Flask/database packages required by `app.py`:

``` powershell
pip install flask flask-cors flask-socketio mysql-connector-python bcrypt
```

Run the application:

``` powershell
python app.py
```

------------------------------------------------------------------------

# 🆘 Troubleshooting

## `ModuleNotFoundError: No module named 'flask'`

Run:

``` powershell
pip install flask
```

------------------------------------------------------------------------

## `ModuleNotFoundError: No module named 'flask_socketio'`

Run:

``` powershell
pip install flask-socketio
```

------------------------------------------------------------------------

## `ModuleNotFoundError: No module named 'mysql'`

Run:

``` powershell
pip install mysql-connector-python
```

------------------------------------------------------------------------

## `ModuleNotFoundError: No module named 'bcrypt'`

Run:

``` powershell
pip install bcrypt
```

------------------------------------------------------------------------

## YOLO model cannot be loaded

Make sure:

``` text
yolov8n.pt
```

is present in the project root.

The application loads:

``` python
YOLO("yolov8n.pt")
```

------------------------------------------------------------------------

## MySQL connection error

Check that:

-   MySQL Server is running.
-   Database `accident_detection` exists.
-   Required tables exist.
-   The credentials configured in `app.py` are correct.

------------------------------------------------------------------------

## Video cannot be opened

Check that:

-   The video file exists.
-   The file format is supported by OpenCV.
-   The upload directory exists.
-   The video is not corrupted.

------------------------------------------------------------------------

## Email does not work

Check:

-   Gmail SMTP settings.
-   Sender email.
-   Gmail App Password.
-   Recipient email.
-   Internet connection.

------------------------------------------------------------------------

## SMS does not work

Check:

``` text
SMS_API_KEY
```

is configured and valid.

If it is not configured, the application intentionally skips SMS
sending.

------------------------------------------------------------------------

## Phone sensor does not work

Check:

-   Browser motion permissions.
-   GPS permissions.
-   HTTPS/public access where required by the browser.
-   `SERVER_URL` in `phone_sensor.html`.
-   `API_KEY` matches the backend hardware API configuration.

------------------------------------------------------------------------

# 🎯 Project Goal

The primary goal of AccidentAlert AI is to demonstrate how computer
vision, real-time communication, location services, hospital discovery,
and emergency notifications can be combined into an accident-response
platform.

The central concept is:

``` text
Detect
  ↓
Assess
  ↓
Locate
  ↓
Find Nearby Hospitals
  ↓
Alert
  ↓
Hospital Response
  ↓
Resolve
```

------------------------------------------------------------------------

# 🏆 Project Highlights

AccidentAlert AI demonstrates the integration of:

-   YOLOv8 object detection
-   OpenCV video processing
-   Person/vehicle IoU analysis
-   Rule-based severity scoring
-   Accident screenshot generation
-   Accident video clip generation
-   GPS and IP-based location
-   Nearby hospital discovery
-   Haversine distance calculation
-   Email emergency alerts
-   Optional SMS alerts
-   Flask-SocketIO real-time communication
-   Hospital camera management
-   Hospital alert acceptance/resolution
-   Citizen SOS
-   Browser phone crash sensing
-   External hardware alert API
-   MySQL data storage
-   Dashboard analytics
-   Leaflet maps
-   Chart.js visualizations

------------------------------------------------------------------------

# 📜 License

See the project's `LICENSE` file for the applicable license.

------------------------------------------------------------------------

# 🚨 AccidentAlert AI

### AI-Based Accident Detection & Emergency Response System

Built with:

**Python • Flask • YOLOv8 • OpenCV • MySQL • Flask-SocketIO • Shapely •
GPS • SMTP**
