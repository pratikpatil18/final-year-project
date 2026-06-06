# AI Ranger

AI Ranger is a full-stack wildlife forest surveillance application that processes uploaded images or videos, runs a YOLO weapon detector, and sends an email alert with the detected frame when a weapon is found.

## Project Structure

```text
backend/   Flask API, upload handling, video frame extraction, email alerts
frontend/  React + Vite dashboard
model/     Training code, dataset assets, and expected YOLO weight locations
```

## Requirements

- Python 3.10+
- Node.js 18+
- npm
- MySQL 8+

## Configuration

The backend reads its settings from `backend/.env`.

1. Copy `backend/.env.example` to `backend/.env` if it is not already present.
2. Update the MySQL and SMTP values for your machine.

Example:

```env
DETECTION_CONFIDENCE=0.35
VIDEO_FRAME_SAMPLE_SECONDS=1.0
MAX_VIDEO_SAMPLE_FRAMES=180
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=ai_ranger
ADMIN_USERNAME=sysadmin
ADMIN_PASSWORD=Pass@123
ADMIN_NAME=System Admin
ADMIN_EMAIL=admin@airanger.com
ADMIN_ROLE=System Administrator
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
ALERT_FROM_EMAIL=your-email@gmail.com
ALERT_TO_EMAIL=receiver@example.com
ALERT_SUBJECT_PREFIX=AI Ranger Alert
```

## Database

The backend now uses MySQL for:

- `admin_users`: stores the admin login with a hashed password
- `detection_history`: stores every detection result shown in the dashboard

When the Flask app starts, it will create the database and both tables automatically if the configured MySQL user has permission. A reference schema is also included at `backend/schema.sql`.

## Model File

The backend looks for a YOLO weight file in one of these locations:

- `model/runs/train/weapon_detector2/weights/best.pt`
- `model/models/yolov8n_custom.pt`

At least one of those files must exist or detection will fail at runtime.

## Install

From the repository root:

```bash
npm run install:frontend
npm run setup:backend
```

This installs:

- frontend dependencies into `frontend/node_modules`
- backend Python dependencies into `backend/.venv`

## Run

Start the backend:

```bash
npm run backend:dev
```

The Flask API runs on `http://localhost:5000`.

Start the frontend in a second terminal:

```bash
npm run frontend:dev
```

The dashboard runs on `http://localhost:3000`.

On Windows, the `:win` script aliases still exist, but the default scripts now work there too.

## How To Use

1. Open `http://localhost:3000`
2. Log in with:
   the `ADMIN_USERNAME` / `ADMIN_PASSWORD` values from `backend/.env`
3. Upload an image or video
4. The backend will:
   - analyze the image directly, or
   - extract frames from the video and analyze sampled frames
5. If a weapon is detected:
   - an annotated frame is saved in `backend/uploads/`
   - the detection appears in the dashboard
   - an email alert is attempted with the detected frame attached

## Notes

- Videos are sampled using `VIDEO_FRAME_SAMPLE_SECONDS`.
- Uploaded media and generated annotated frames are stored in `backend/uploads/`.
- Login and detection history are persisted in MySQL instead of in-memory storage.
- If SMTP is not configured correctly, detection still works but email sending fails.
