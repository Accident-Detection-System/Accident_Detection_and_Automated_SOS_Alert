# AccidentGuard Backend — FastAPI

## Setup
1. Create a MySQL database using `../database/schema.sql`.
2. Copy `.env.example` to `.env` and set your MySQL credentials and optional Gmail SMTP app password.
3. Create a virtual environment and install `requirements.txt`.
4. Run `python run.py`.

API: http://localhost:8000
Swagger: http://localhost:8000/docs

The YOLO weights are included as `yolov8n.pt`. The current detector uses YOLO object detection plus person/vehicle bounding-box overlap as the accident heuristic. It is not a trained accident-classification model; for production accuracy, replace the weights/detection logic with a domain-trained accident model.
