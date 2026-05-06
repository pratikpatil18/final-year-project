import mimetypes
import os
import random
import smtplib
import uuid
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
MODEL_PROJECT_DIR = PROJECT_DIR / "model"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
CORS(app)

MODEL_CANDIDATES = [
    MODEL_PROJECT_DIR / "runs/train/weapon_detector2/weights/best.pt",
    MODEL_PROJECT_DIR / "models/yolov8n_custom.pt",
]
DETECTION_CONFIDENCE = 0.35
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", SMTP_USERNAME).strip()
ALERT_TO_EMAIL = os.getenv("ALERT_TO_EMAIL", "").strip()
ALERT_SUBJECT_PREFIX = os.getenv("ALERT_SUBJECT_PREFIX", "AI Ranger Alert").strip()

# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------
detections = []
model = None

# ---------------------------------------------------------------------------
# Admin credentials
# ---------------------------------------------------------------------------
ADMIN_USERNAME = "sysadmin"
ADMIN_PASSWORD = "Pass@123"

LOCATIONS = [
    "North Forest Gate",
    "Riverbank Trail Camera",
    "Watering Hole East",
    "Canopy Watch Tower",
    "Ranger Outpost West",
    "Migration Corridor",
    "Salt Lick Camera 2",
    "Boundary Fence South",
]


def resolve_model_path():
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            return candidate
    return MODEL_CANDIDATES[0]


MODEL_PATH = resolve_model_path()


def get_model():
    global model

    if model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"YOLO weights not found. Expected one of: {', '.join(str(path) for path in MODEL_CANDIDATES)}"
            )
        model = YOLO(str(MODEL_PATH))
    return model


def normalize_label(label):
    key = label.strip().lower().replace("-", " ").replace("_", " ")
    mapping = {
        "gun": "Gun",
        "handgun": "Gun",
        "pistol": "Gun",
        "knife": "Knife",
    }
    return mapping.get(key, label.strip().title())


def determine_severity(detection_type, confidence):
    if detection_type == "No Weapon":
        return "safe"
    if confidence >= 0.75:
        return "critical"
    return "warning"


def extract_label_names(names, class_id):
    if isinstance(names, dict):
        return names.get(class_id, str(class_id))
    if isinstance(names, list) and class_id < len(names):
        return names[class_id]
    return str(class_id)


def notifications_configured():
    return bool(SMTP_HOST and SMTP_PORT and ALERT_FROM_EMAIL and ALERT_TO_EMAIL)


def send_detection_email(detection, attachment_path):
    if not notifications_configured():
        return {
            "sent": False,
            "status": "not_configured",
            "message": "Email notification is not configured.",
        }

    message = EmailMessage()
    message["Subject"] = (
        f"{ALERT_SUBJECT_PREFIX}: {detection['detection_type']} detected at {detection['location']}"
    )
    message["From"] = ALERT_FROM_EMAIL
    message["To"] = ALERT_TO_EMAIL
    message.set_content(
        "\n".join(
            [
                "AI Ranger detected a possible weapon in wildlife forest footage.",
                "",
                f"Detection type: {detection['detection_type']}",
                f"Confidence: {detection['confidence']:.2f}",
                f"Location: {detection['location']}",
                f"Timestamp: {detection['timestamp']}",
                f"Source file: {detection['original_filename']}",
            ]
        )
    )

    if attachment_path.exists():
        mime_type, _ = mimetypes.guess_type(str(attachment_path))
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        with attachment_path.open("rb") as attachment_file:
            message.add_attachment(
                attachment_file.read(),
                maintype=maintype,
                subtype=subtype,
                filename=attachment_path.name,
            )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            if SMTP_USE_TLS:
                smtp.starttls()
                smtp.ehlo()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:
        return {
            "sent": False,
            "status": "failed",
            "message": str(exc),
        }

    return {
        "sent": True,
        "status": "sent",
        "message": f"Alert email sent to {ALERT_TO_EMAIL}.",
    }


def run_detection(image_path):
    results = get_model().predict(
        source=str(image_path),
        conf=DETECTION_CONFIDENCE,
        verbose=False,
    )
    result = results[0]

    annotated_filename = f"{image_path.stem}_annotated.jpg"
    annotated_path = UPLOADS_DIR / annotated_filename
    result.save(filename=str(annotated_path))

    parsed_detections = []
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = round(float(box.conf[0].item()), 4)
            raw_label = extract_label_names(result.names, class_id)
            parsed_detections.append(
                {
                    "label": normalize_label(raw_label),
                    "raw_label": raw_label,
                    "confidence": confidence,
                }
            )

    parsed_detections.sort(key=lambda item: item["confidence"], reverse=True)

    if parsed_detections:
        primary = parsed_detections[0]
        detection_type = primary["label"]
        confidence = round(primary["confidence"], 2)
    else:
        detection_type = "No Weapon"
        confidence = 0.0

    return {
        "annotated_filename": annotated_filename,
        "detection_type": detection_type,
        "confidence": confidence,
        "severity": determine_severity(detection_type, confidence),
        "detections": parsed_detections,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return jsonify(
        {
            "service": "AI Ranger - Wildlife Protection Monitoring",
            "status": "operational",
            "model_path": str(MODEL_PATH),
            "model_ready": MODEL_PATH.exists(),
            "email_notifications_configured": notifications_configured(),
        }
    )


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return jsonify(
            {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "username": username,
                    "role": "System Administrator",
                    "name": "System Admin",
                    "email": "admin@airanger.com",
                },
            }
        )

    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("image") or request.files.get("media")
    if file is None:
        return jsonify({"error": "No image file provided"}), 400

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = UPLOADS_DIR / filename
    file.save(str(filepath))

    try:
        detection_result = run_detection(filepath)
    except Exception as exc:
        return jsonify({"error": f"Model inference failed: {exc}"}), 500

    annotated_path = UPLOADS_DIR / detection_result["annotated_filename"]
    detection = {
        "id": len(detections) + 1,
        "original_filename": file.filename,
        "saved_filename": filename,
        "original_image_url": f"/uploads/{filename}",
        "image_url": f"/uploads/{detection_result['annotated_filename']}",
        "detection_type": detection_result["detection_type"],
        "confidence": detection_result["confidence"],
        "severity": detection_result["severity"],
        "detection_count": len(detection_result["detections"]),
        "detections": detection_result["detections"],
        "location": random.choice(LOCATIONS),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if detection["detection_type"] != "No Weapon":
        detection["notification"] = send_detection_email(detection, annotated_path)
    else:
        detection["notification"] = {
            "sent": False,
            "status": "skipped",
            "message": "No email sent because no weapon was detected.",
        }

    detections.insert(0, detection)

    return jsonify({"success": True, "detection": detection})


@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"detections": detections, "total": len(detections)})


@app.route("/analysis", methods=["GET"])
def get_analysis():
    gun_count = sum(1 for d in detections if d["detection_type"] == "Gun")
    knife_count = sum(1 for d in detections if d["detection_type"] == "Knife")
    no_weapon_count = sum(1 for d in detections if d["detection_type"] == "No Weapon")
    critical_count = sum(1 for d in detections if d["severity"] == "critical")

    timeline = []
    for d in detections[:20]:
        timeline.append(
            {
                "time": d["timestamp"],
                "type": d["detection_type"],
                "confidence": d["confidence"],
            }
        )

    total = len(detections)
    weapons = gun_count + knife_count
    threat_level = "HIGH" if critical_count > 0 else "MODERATE" if weapons > 0 else "LOW"

    return jsonify(
        {
            "gun_count": gun_count,
            "knife_count": knife_count,
            "no_weapon_count": no_weapon_count,
            "critical_count": critical_count,
            "total": total,
            "timeline": timeline,
            "threat_level": threat_level,
        }
    )


@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(str(UPLOADS_DIR), filename)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  AI Ranger - Wildlife Protection Monitoring")
    print("  Backend running on http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
