import mimetypes
import os
import random
import smtplib
import uuid
import json
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import cv2
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
MODEL_PROJECT_DIR = PROJECT_DIR / "model"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
CORS(app)

MODEL_DEFAULT_CANDIDATES = [
    MODEL_PROJECT_DIR / "runs/train/weapon_detector2/weights/best.pt",
    MODEL_PROJECT_DIR / "models/yolov8n_custom.pt",
]
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
DETECTION_CONFIDENCE = float(os.getenv("DETECTION_CONFIDENCE", "0.35"))
VIDEO_FRAME_SAMPLE_SECONDS = float(os.getenv("VIDEO_FRAME_SAMPLE_SECONDS", "1.0"))
MAX_VIDEO_SAMPLE_FRAMES = int(os.getenv("MAX_VIDEO_SAMPLE_FRAMES", "180"))
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", SMTP_USERNAME).strip()
ALERT_TO_EMAIL = os.getenv("ALERT_TO_EMAIL", "").strip()
ALERT_SUBJECT_PREFIX = os.getenv("ALERT_SUBJECT_PREFIX", "AI Ranger Alert").strip()
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root").strip()
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_ranger").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "sysadmin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Pass@123").strip()
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Admin").strip()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@airanger.com").strip()
ADMIN_ROLE = os.getenv("ADMIN_ROLE", "System Administrator").strip()

model = None
loaded_model_path = None
DATABASE_READY = False
DATABASE_ERROR = ""

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


def mysql_driver_available():
    return mysql is not None


def database_configured():
    return bool(MYSQL_HOST and MYSQL_USER and MYSQL_DATABASE)


def build_database_error(message):
    return (
        f"{message} Configure MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, "
        f"and MYSQL_DATABASE in backend/.env."
    )


def open_database_connection(include_database=True):
    if not mysql_driver_available():
        raise RuntimeError(
            "mysql-connector-python is not installed. Run the backend setup again to install it."
        )

    if not database_configured():
        raise RuntimeError(build_database_error("MySQL is not configured."))

    connection_settings = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
    }
    if include_database:
        connection_settings["database"] = MYSQL_DATABASE
    return mysql.connector.connect(**connection_settings)


def initialize_database():
    global DATABASE_ERROR, DATABASE_READY

    if DATABASE_READY:
        return True

    if not mysql_driver_available():
        DATABASE_ERROR = "mysql-connector-python is not installed."
        return False

    if not database_configured():
        DATABASE_ERROR = build_database_error("MySQL is not configured.")
        return False

    try:
        bootstrap_connection = open_database_connection(include_database=False)
        bootstrap_cursor = bootstrap_connection.cursor()
        bootstrap_cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        bootstrap_cursor.close()
        bootstrap_connection.close()

        connection = open_database_connection(include_database=True)
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(150) NOT NULL,
                email VARCHAR(200) NOT NULL,
                role VARCHAR(100) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS detection_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_filename VARCHAR(255) NOT NULL,
                saved_filename VARCHAR(255) NOT NULL,
                original_image_url VARCHAR(255) NOT NULL,
                image_url VARCHAR(255) NOT NULL,
                detection_type VARCHAR(100) NOT NULL,
                confidence FLOAT NOT NULL,
                severity VARCHAR(32) NOT NULL,
                detection_count INT NOT NULL DEFAULT 0,
                detections_json LONGTEXT NOT NULL,
                location VARCHAR(150) NOT NULL,
                timestamp DATETIME NOT NULL,
                source_type VARCHAR(32) NOT NULL,
                source_frame_index INT NULL,
                source_timestamp_seconds FLOAT NULL,
                processed_frames INT NULL,
                notification_status VARCHAR(64) NULL,
                notification_message TEXT NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO admin_users (username, password_hash, full_name, email, role)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                full_name = VALUES(full_name),
                email = VALUES(email),
                role = VALUES(role)
            """,
            (
                ADMIN_USERNAME,
                generate_password_hash(ADMIN_PASSWORD),
                ADMIN_NAME,
                ADMIN_EMAIL,
                ADMIN_ROLE,
            ),
        )
        connection.commit()
        cursor.close()
        connection.close()
        DATABASE_READY = True
        DATABASE_ERROR = ""
        return True
    except (MySQLError, RuntimeError) as exc:
        DATABASE_READY = False
        DATABASE_ERROR = str(exc)
        return False


def require_database():
    if initialize_database():
        return
    raise RuntimeError(DATABASE_ERROR or "Unable to connect to the MySQL database.")


def get_database_status():
    initialize_database()
    return {
        "database_ready": DATABASE_READY,
        "database_host": MYSQL_HOST,
        "database_port": MYSQL_PORT,
        "database_name": MYSQL_DATABASE,
        "database_error": DATABASE_ERROR or None,
        "mysql_driver_installed": mysql_driver_available(),
    }


def parse_detection_items(detections_json):
    if not detections_json:
        return []

    try:
        parsed = json.loads(detections_json)
    except json.JSONDecodeError:
        return []

    return parsed if isinstance(parsed, list) else []


def row_to_detection(row):
    timestamp = row["timestamp"]
    if isinstance(timestamp, datetime):
        timestamp_value = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp_value = str(timestamp)

    detection = {
        "id": row["id"],
        "original_filename": row["original_filename"],
        "saved_filename": row["saved_filename"],
        "original_image_url": row["original_image_url"],
        "image_url": row["image_url"],
        "detection_type": row["detection_type"],
        "confidence": float(row["confidence"]),
        "severity": row["severity"],
        "detection_count": int(row["detection_count"]),
        "detections": parse_detection_items(row["detections_json"]),
        "location": row["location"],
        "timestamp": timestamp_value,
        "source_type": row["source_type"],
        "notification": {
            "sent": row["notification_status"] == "sent",
            "status": row["notification_status"] or "unknown",
            "message": row["notification_message"] or "",
        },
    }

    if row["source_frame_index"] is not None:
        detection["source_frame_index"] = int(row["source_frame_index"])
    if row["source_timestamp_seconds"] is not None:
        detection["source_timestamp_seconds"] = float(row["source_timestamp_seconds"])
    if row["processed_frames"] is not None:
        detection["processed_frames"] = int(row["processed_frames"])

    return detection


def get_history_records(limit=None):
    require_database()
    try:
        connection = open_database_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                original_filename,
                saved_filename,
                original_image_url,
                image_url,
                detection_type,
                confidence,
                severity,
                detection_count,
                detections_json,
                location,
                timestamp,
                source_type,
                source_frame_index,
                source_timestamp_seconds,
                processed_frames,
                notification_status,
                notification_message
            FROM detection_history
            ORDER BY timestamp DESC, id DESC
        """
        params = ()
        if limit is not None:
            query += " LIMIT %s"
            params = (limit,)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return [row_to_detection(row) for row in rows]
    except MySQLError as exc:
        raise RuntimeError(f"MySQL query failed: {exc}") from exc


def insert_detection_record(detection, detected_at):
    require_database()
    try:
        connection = open_database_connection()
        cursor = connection.cursor()
        notification = detection.get("notification") or {}
        cursor.execute(
            """
            INSERT INTO detection_history (
                original_filename,
                saved_filename,
                original_image_url,
                image_url,
                detection_type,
                confidence,
                severity,
                detection_count,
                detections_json,
                location,
                timestamp,
                source_type,
                source_frame_index,
                source_timestamp_seconds,
                processed_frames,
                notification_status,
                notification_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                detection["original_filename"],
                detection["saved_filename"],
                detection["original_image_url"],
                detection["image_url"],
                detection["detection_type"],
                detection["confidence"],
                detection["severity"],
                detection["detection_count"],
                json.dumps(detection["detections"]),
                detection["location"],
                detected_at,
                detection["source_type"],
                detection.get("source_frame_index"),
                detection.get("source_timestamp_seconds"),
                detection.get("processed_frames"),
                notification.get("status"),
                notification.get("message"),
            ),
        )
        connection.commit()
        inserted_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return inserted_id
    except MySQLError as exc:
        raise RuntimeError(f"MySQL insert failed: {exc}") from exc


def authenticate_admin(username, password):
    require_database()
    try:
        connection = open_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT username, password_hash, full_name, email, role
            FROM admin_users
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        admin_user = cursor.fetchone()
        cursor.close()
        connection.close()
    except MySQLError as exc:
        raise RuntimeError(f"MySQL login lookup failed: {exc}") from exc

    if admin_user and check_password_hash(admin_user["password_hash"], password):
        return {
            "username": admin_user["username"],
            "role": admin_user["role"],
            "name": admin_user["full_name"],
            "email": admin_user["email"],
        }

    return None


def configured_model_path():
    configured_path = os.getenv("MODEL_PATH", "").strip()
    if not configured_path:
        return None

    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_DIR / path
    return path.resolve()


def get_model_candidates():
    candidates = []
    seen = set()

    def add_candidate(path):
        normalized = str(path)
        if normalized not in seen:
            seen.add(normalized)
            candidates.append(path)

    explicit_path = configured_model_path()
    if explicit_path is not None:
        add_candidate(explicit_path)

    for candidate in MODEL_DEFAULT_CANDIDATES:
        add_candidate(candidate)

    train_runs_dir = MODEL_PROJECT_DIR / "runs" / "train"
    if train_runs_dir.exists():
        for candidate in sorted(train_runs_dir.glob("**/weights/best.pt")):
            add_candidate(candidate)

    models_dir = MODEL_PROJECT_DIR / "models"
    if models_dir.exists():
        for candidate in sorted(models_dir.glob("*.pt")):
            add_candidate(candidate)

    return candidates


def resolve_model_path():
    candidates = get_model_candidates()
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else MODEL_DEFAULT_CANDIDATES[0]


def get_model_status():
    candidates = get_model_candidates()
    resolved_model_path = next((candidate for candidate in candidates if candidate.exists()), None)
    configured_path = configured_model_path()

    return {
        "model_path": str(resolved_model_path or (candidates[0] if candidates else MODEL_DEFAULT_CANDIDATES[0])),
        "model_ready": resolved_model_path is not None,
        "configured_model_path": str(configured_path) if configured_path else None,
        "model_candidates": [str(candidate) for candidate in candidates],
        "hint": (
            "Set MODEL_PATH in backend/.env to your trained .pt file, or restore "
            "model/runs/train/weapon_detector2/weights/best.pt."
        ),
    }


def get_model():
    global loaded_model_path, model

    status = get_model_status()
    model_path = Path(status["model_path"])

    if not status["model_ready"]:
        raise FileNotFoundError(
            "YOLO weights not found. Set MODEL_PATH in backend/.env or restore "
            "model/runs/train/weapon_detector2/weights/best.pt."
        )

    if model is None or loaded_model_path != model_path:
        model = YOLO(str(model_path))
        loaded_model_path = model_path
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


def is_video_upload(file):
    mimetype = (getattr(file, "mimetype", "") or "").lower()
    extension = Path(file.filename or "").suffix.lower()
    return mimetype.startswith("video/") or extension in VIDEO_EXTENSIONS


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


def summarize_prediction_result(result):
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
        "detection_type": detection_type,
        "confidence": confidence,
        "severity": determine_severity(detection_type, confidence),
        "detections": parsed_detections,
    }


def analyze_source(source):
    results = get_model().predict(
        source=source,
        conf=DETECTION_CONFIDENCE,
        verbose=False,
    )
    result = results[0]
    return result, summarize_prediction_result(result)


def save_annotated_result(result, output_stem):
    annotated_filename = f"{output_stem}_annotated.jpg"
    annotated_path = UPLOADS_DIR / annotated_filename
    result.save(filename=str(annotated_path))
    return annotated_filename


def run_image_detection(image_path):
    result, detection_result = analyze_source(str(image_path))
    detection_result["annotated_filename"] = save_annotated_result(result, image_path.stem)
    return {
        "saved_filename": image_path.name,
        "original_image_url": f"/uploads/{image_path.name}",
        "image_url": f"/uploads/{detection_result['annotated_filename']}",
        "detection_result": detection_result,
        "source_type": "image",
    }


def run_video_detection(video_path):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("Unable to open the uploaded video.")

    fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
    if fps <= 0:
        fps = 1.0
    sample_stride = max(int(round(fps * VIDEO_FRAME_SAMPLE_SECONDS)), 1)

    frame_index = 0
    sampled_frames = 0
    selected_frame = None
    selected_result = None
    selected_detection = None
    selected_frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        if frame_index % sample_stride == 0:
            sampled_frames += 1
            result, detection_result = analyze_source(frame)

            if selected_frame is None:
                selected_frame = frame.copy()
                selected_result = result
                selected_detection = detection_result
                selected_frame_index = frame_index

            if detection_result["detection_type"] != "No Weapon":
                selected_frame = frame.copy()
                selected_result = result
                selected_detection = detection_result
                selected_frame_index = frame_index
                break

            if sampled_frames >= MAX_VIDEO_SAMPLE_FRAMES:
                break

        frame_index += 1

    capture.release()

    if selected_frame is None or selected_result is None or selected_detection is None:
        raise ValueError("No readable frames were found in the uploaded video.")

    frame_stem = f"{video_path.stem}_frame_{selected_frame_index:06d}"
    frame_filename = f"{frame_stem}.jpg"
    frame_path = UPLOADS_DIR / frame_filename
    if not cv2.imwrite(str(frame_path), selected_frame):
        raise ValueError("Failed to save the extracted frame from the video.")

    selected_detection["annotated_filename"] = save_annotated_result(selected_result, frame_stem)

    return {
        "saved_filename": frame_filename,
        "original_image_url": f"/uploads/{frame_filename}",
        "image_url": f"/uploads/{selected_detection['annotated_filename']}",
        "detection_result": selected_detection,
        "source_type": "video",
        "source_frame_index": selected_frame_index,
        "source_timestamp_seconds": round(selected_frame_index / fps, 2),
        "processed_frames": sampled_frames,
    }


def build_status_payload():
    model_status = get_model_status()
    return {
        "service": "AI Ranger - Wildlife Protection Monitoring",
        "status": "operational",
        "email_notifications_configured": notifications_configured(),
        "video_processing_enabled": True,
        "video_frame_sample_seconds": VIDEO_FRAME_SAMPLE_SECONDS,
        **get_database_status(),
        **model_status,
    }


@app.route("/")
@app.route("/status")
def home():
    return jsonify(build_status_payload())


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    try:
        user = authenticate_admin(username, password)
    except RuntimeError as exc:
        return jsonify({"success": False, "message": str(exc), **get_database_status()}), 503

    if user:
        return jsonify(
            {
                "success": True,
                "message": "Authentication successful",
                "user": user,
            }
        )

    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route("/upload", methods=["POST"])
def upload():
    try:
        require_database()
    except RuntimeError as exc:
        return jsonify({"error": str(exc), **get_database_status()}), 503

    file = request.files.get("image") or request.files.get("media")
    if file is None:
        return jsonify({"error": "No media file provided"}), 400

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    video_upload = is_video_upload(file)
    ext = Path(file.filename).suffix or (".mp4" if video_upload else ".jpg")
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = UPLOADS_DIR / filename
    file.save(str(filepath))

    try:
        media_result = run_video_detection(filepath) if video_upload else run_image_detection(filepath)
    except FileNotFoundError as exc:
        model_status = get_model_status()
        return (
            jsonify(
                {
                    "error": "Model is not configured for inference.",
                    "message": str(exc),
                    **model_status,
                }
            ),
            503,
        )
    except Exception as exc:
        return jsonify({"error": f"Model inference failed: {exc}"}), 500
    finally:
        if video_upload and filepath.exists():
            filepath.unlink()

    detection_result = media_result["detection_result"]
    annotated_path = UPLOADS_DIR / detection_result["annotated_filename"]
    detected_at = datetime.now()

    detection = {
        "original_filename": file.filename,
        "saved_filename": media_result["saved_filename"],
        "original_image_url": media_result["original_image_url"],
        "image_url": media_result["image_url"],
        "detection_type": detection_result["detection_type"],
        "confidence": detection_result["confidence"],
        "severity": detection_result["severity"],
        "detection_count": len(detection_result["detections"]),
        "detections": detection_result["detections"],
        "location": random.choice(LOCATIONS),
        "timestamp": detected_at.strftime("%Y-%m-%d %H:%M:%S"),
        "source_type": media_result["source_type"],
    }

    if media_result["source_type"] == "video":
        detection["source_frame_index"] = media_result["source_frame_index"]
        detection["source_timestamp_seconds"] = media_result["source_timestamp_seconds"]
        detection["processed_frames"] = media_result["processed_frames"]

    if detection["detection_type"] != "No Weapon":
        detection["notification"] = send_detection_email(detection, annotated_path)
    else:
        detection["notification"] = {
            "sent": False,
            "status": "skipped",
            "message": "No email sent because no weapon was detected.",
        }

    try:
        detection["id"] = insert_detection_record(detection, detected_at)
    except RuntimeError as exc:
        return jsonify({"error": f"Detection completed but could not be saved: {exc}"}), 500

    return jsonify({"success": True, "detection": detection})


@app.route("/history", methods=["GET"])
def get_history():
    try:
        detections = get_history_records()
    except RuntimeError as exc:
        return jsonify({"error": str(exc), **get_database_status()}), 503

    return jsonify({"detections": detections, "total": len(detections)})


@app.route("/analysis", methods=["GET"])
def get_analysis():
    try:
        detections = get_history_records()
    except RuntimeError as exc:
        return jsonify({"error": str(exc), **get_database_status()}), 503

    gun_count = sum(1 for d in detections if d["detection_type"] == "Gun")
    knife_count = sum(1 for d in detections if d["detection_type"] == "Knife")
    no_weapon_count = sum(1 for d in detections if d["detection_type"] == "No Weapon")
    critical_count = sum(1 for d in detections if d["severity"] == "critical")

    timeline = [
        {
            "time": d["timestamp"],
            "type": d["detection_type"],
            "confidence": d["confidence"],
        }
        for d in detections[:20]
    ]

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


if __name__ == "__main__":
    print("=" * 55)
    print("  AI Ranger - Wildlife Protection Monitoring")
    print("  Backend running on http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
