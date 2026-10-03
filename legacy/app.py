import os
import sys
import json
import sqlite3
import time
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session,
    send_from_directory, redirect, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import config
from run_evaluation import run_evaluation

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "auto_accident_detection_secret_key_2026"

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
OUTPUT_FOLDER = os.path.join(os.getcwd(), "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

DB_PATH = "database.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS video_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'COMPLETED',
                accident_detected BOOLEAN DEFAULT 0,
                first_accident_time_sec REAL,
                max_score INTEGER DEFAULT 0,
                total_frames INTEGER DEFAULT 0,
                video_fps REAL DEFAULT 0,
                processing_fps REAL DEFAULT 0,
                annotated_path TEXT,
                csv_path TEXT,
                summary_json_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        # Create demo member user if not exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("demo",))
        if not cursor.fetchone():
            demo_pass = generate_password_hash("demo123")
            conn.execute(
                "INSERT INTO users (username, email, password, full_name) VALUES (?, ?, ?, ?)",
                ("demo", "demo@accident-ai.org", demo_pass, "Demo Safety Officer")
            )
            print("Default demo user created: username='demo', password='demo123'")

        # Seed test video history if empty
        cursor.execute("SELECT COUNT(*) FROM video_history")
        count = cursor.fetchone()[0]
        if count == 0 and os.path.exists("outputs/detection_summary.json"):
            try:
                with open("outputs/detection_summary.json", "r") as f:
                    sdata = json.load(f)
                conn.execute("""
                    INSERT INTO video_history (
                        user_id, filename, original_filename, status, accident_detected,
                        first_accident_time_sec, max_score, total_frames, video_fps,
                        processing_fps, annotated_path, csv_path, summary_json_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, "test_accident.mp4", "hMYOFZnqbSY_YouTube_Short.mp4", "COMPLETED",
                    sdata.get("accident_detected", True), sdata.get("first_accident_timestamp_sec", 0.93),
                    sdata.get("max_accident_score", 6), sdata.get("total_frames", 227),
                    sdata.get("video_fps", 30.0), sdata.get("processing_fps", 3.87),
                    "outputs/annotated_output.mp4", "outputs/detection_results.csv",
                    "outputs/detection_summary.json"
                ))
                print("Seeded initial YouTube Short test result into DB history.")
            except Exception as e:
                print("Error seeding initial history:", e)


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip() or username

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed = generate_password_hash(password)
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password, full_name) VALUES (?, ?, ?, ?)",
                (username, email, hashed, full_name)
            )
            user_id = cursor.lastrowid
            session["user_id"] = user_id
            session["username"] = username
            session["full_name"] = full_name
            return jsonify({
                "message": "User registered successfully",
                "user": {"id": user_id, "username": username, "full_name": full_name, "email": email}
            })
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "email": user["email"]
                }
            })
        return jsonify({"error": "Invalid username or password"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.route("/api/me", methods=["GET"])
def get_current_user():
    if "user_id" in session:
        with get_db() as conn:
            user = conn.execute("SELECT id, username, email, full_name FROM users WHERE id = ?", (session["user_id"],)).fetchone()
            if user:
                return jsonify({"user": dict(user)})
    return jsonify({"user": None})


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    orig_filename = secure_filename(file.filename)
    timestamp_prefix = int(time.time())
    save_filename = f"{timestamp_prefix}_{orig_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, save_filename)
    file.save(file_path)

    # Unique output directory per upload
    out_dir_name = f"output_{timestamp_prefix}"
    out_dir_path = os.path.join(OUTPUT_FOLDER, out_dir_name)

    try:
        summary_data = run_evaluation(file_path, out_dir_path)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_history (
                    user_id, filename, original_filename, status, accident_detected,
                    first_accident_time_sec, max_score, total_frames, video_fps,
                    processing_fps, annotated_path, csv_path, summary_json_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                save_filename,
                orig_filename,
                "COMPLETED",
                1 if summary_data.get("accident_detected") else 0,
                summary_data.get("first_accident_timestamp_sec"),
                summary_data.get("max_accident_score", 0),
                summary_data.get("total_frames", 0),
                summary_data.get("video_fps", 0),
                summary_data.get("processing_fps", 0),
                os.path.join(out_dir_name, "annotated_output.mp4"),
                os.path.join(out_dir_name, "detection_results.csv"),
                os.path.join(out_dir_name, "detection_summary.json")
            ))
            history_id = cursor.lastrowid

        return jsonify({
            "message": "Video processed successfully",
            "history_id": history_id,
            "summary": summary_data
        })
    except Exception as e:
        print("Processing error:", e)
        return jsonify({"error": f"Failed to process video: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
@login_required
def get_user_history():
    user_id = session["user_id"]
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM video_history
            WHERE user_id = ?
            ORDER BY upload_time DESC
        """, (user_id,)).fetchall()
        
        history = [dict(row) for row in rows]
        return jsonify({"history": history})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    with get_db() as conn:
        total_videos = conn.execute("SELECT COUNT(*) FROM video_history").fetchone()[0]
        accidents_flagged = conn.execute("SELECT COUNT(*) FROM video_history WHERE accident_detected = 1").fetchone()[0]
        avg_fps = conn.execute("SELECT AVG(processing_fps) FROM video_history").fetchone()[0] or 0.0

    return jsonify({
        "total_videos_analyzed": total_videos,
        "accidents_detected": accidents_flagged,
        "average_processing_fps": round(avg_fps, 2),
        "system_status": "ONLINE",
        "detector_model": config.YOLO_MODEL_PATH
    })


@app.route("/api/video/<int:video_id>", methods=["GET"])
@login_required
def get_video_details(video_id):
    user_id = session["user_id"]
    with get_db() as conn:
        row = conn.execute("""
            SELECT * FROM video_history WHERE id = ? AND user_id = ?
        """, (video_id, user_id)).fetchone()

        if not row:
            return jsonify({"error": "Video record not found"}), 404

        record = dict(row)
        
        # Load summary json if available
        summary_path = os.path.join(OUTPUT_FOLDER, record["summary_json_path"]) if record["summary_json_path"] else ""
        summary_data = {}
        if summary_path and os.path.exists(summary_path):
            try:
                with open(summary_path, "r") as f:
                    summary_data = json.load(f)
            except Exception:
                pass

        return jsonify({
            "record": record,
            "details": summary_data
        })


@app.route("/media/<path:filename>")
def serve_media(filename):
    # Try serving from outputs, uploads, or clips
    for base in [OUTPUT_FOLDER, UPLOAD_FOLDER, "clips", "test_videos"]:
        target = os.path.join(base, filename)
        if os.path.exists(target):
            return send_from_directory(base, filename)
    return jsonify({"error": "File not found"}), 404


@app.route("/api/config", methods=["GET", "POST"])
@login_required
def update_system_config():
    if request.method == "POST":
        data = request.json or {}
        if "CONF_THRESHOLD" in data:
            config.CONF_THRESHOLD = float(data["CONF_THRESHOLD"])
        if "COLLISION_IOU_THRESHOLD" in data:
            config.COLLISION_IOU_THRESHOLD = float(data["COLLISION_IOU_THRESHOLD"])
        if "ACCIDENT_SCORE_THRESHOLD" in data:
            config.ACCIDENT_SCORE_THRESHOLD = int(data["ACCIDENT_SCORE_THRESHOLD"])
        if "SPEED_DROP_RATIO" in data:
            config.SPEED_DROP_RATIO = float(data["SPEED_DROP_RATIO"])

    return jsonify({
        "CONF_THRESHOLD": config.CONF_THRESHOLD,
        "COLLISION_IOU_THRESHOLD": config.COLLISION_IOU_THRESHOLD,
        "ACCIDENT_SCORE_THRESHOLD": config.ACCIDENT_SCORE_THRESHOLD,
        "SPEED_DROP_RATIO": config.SPEED_DROP_RATIO,
        "YOLO_MODEL_PATH": config.YOLO_MODEL_PATH,
        "DRY_RUN": config.DRY_RUN
    })


if __name__ == "__main__":
    print("Starting Auto Accident Detection Dashboard Server at http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
