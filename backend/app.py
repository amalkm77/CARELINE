import json
import os
import re
import threading
import webbrowser
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, create_tables

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path="",
)
app.secret_key = os.environ.get("CARELINE_SECRET_KEY", "careline-local-dev-key")
CORS(
    app,
    supports_credentials=True,
    origins=[
        "null",
        re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"),
    ],
)

FEEDBACK_CATEGORIES = {
    "Doctor Consultation",
    "Nursing Care",
    "Cleanliness & Hygiene",
    "Hospital Facilities",
    "Emergency Services",
    "Pharmacy Service",
    "Waiting Time",
    "Staff Behaviour",
}
FEEDBACK_DEPARTMENTS = {
    "Cardiology",
    "General Medicine",
    "Orthopaedics",
    "Paediatrics",
    "Gynaecology",
    "Dermatology",
    "Neurology",
    "Pharmacy",
    "Dental",
    "Emergency",
    "ENT",
    "Ophthalmology",
    "Other",
}
sentiment_analyzer = SentimentIntensityAnalyzer()

create_tables()


def analyze_sentiment(text):
    compound_score = sentiment_analyzer.polarity_scores(text)["compound"]
    if compound_score >= 0.05:
        label = "Positive"
    elif compound_score <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return label, compound_score


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "home.html")


@app.route("/images/<path:filename>")
def hospital_image(filename):
    return send_from_directory(os.path.join(PROJECT_DIR, "images"), filename)

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    conn = get_connection()

    try:
        hashed_password = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        return jsonify({"message": "Registration successful"}), 201

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return jsonify({"message": "Email already registered"}), 409
        return jsonify({"message": "Registration failed"}), 500

    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_connection()

    try:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return jsonify({"message": "Login successful", "name": user["name"]})

        return jsonify({"message": "Invalid email or password"}), 401

    finally:
        conn.close()

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@app.route("/api/session", methods=["GET"])
def current_session():
    if "user_id" not in session:
        return jsonify({"message": "Not logged in"}), 401
    return jsonify({"name": session["user_name"]})


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "A JSON feedback object is required"}), 400

    name = data.get("name")
    department = data.get("department")
    comments = data.get("comments", "")
    ratings = data.get("ratings")

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        return jsonify({"message": "Enter a patient name (up to 120 characters)"}), 400
    if not isinstance(department, str) or department.strip() not in FEEDBACK_DEPARTMENTS:
        return jsonify({"message": "Select a valid department"}), 400
    if not isinstance(comments, str) or len(comments) > 5000:
        return jsonify({"message": "Comments must be 5000 characters or fewer"}), 400
    if not isinstance(ratings, dict) or set(ratings) != FEEDBACK_CATEGORIES:
        return jsonify({"message": "Rate all eight hospital services"}), 400
    if any(type(value) is not int or value < 1 or value > 5 for value in ratings.values()):
        return jsonify({"message": "Ratings must be whole numbers from 1 to 5"}), 400

    created_at = datetime.now(timezone.utc).isoformat()
    sentiment, sentiment_score = analyze_sentiment(comments.strip())
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO feedback (
                department, doctor_rating, cleanliness_rating, service_rating,
                comments, patient_name, ratings_json, created_at,
                sentiment, sentiment_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                department.strip(),
                ratings["Doctor Consultation"],
                ratings["Cleanliness & Hygiene"],
                round(sum(ratings.values()) / len(ratings)),
                comments.strip(),
                name.strip(),
                json.dumps(ratings),
                created_at,
                sentiment,
                sentiment_score,
            ),
        )
        conn.commit()
        return jsonify({
            "id": cursor.lastrowid,
            "message": "Feedback submitted successfully",
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
        }), 201
    except Exception:
        app.logger.exception("Failed to save patient feedback")
        return jsonify({"message": "Feedback could not be saved"}), 500
    finally:
        conn.close()


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    if "user_id" not in session:
        return jsonify({"message": "Please log in to view feedback"}), 401

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, patient_name, department, ratings_json, comments, created_at,
                   sentiment, sentiment_score, is_demo
            FROM feedback
            ORDER BY id ASC
            """
        ).fetchall()
        records = []
        for row in rows:
            calculated_sentiment, calculated_score = analyze_sentiment(row["comments"] or "")
            records.append({
                "id": row["id"],
                "name": row["patient_name"],
                "department": row["department"] or "",
                "ratings": json.loads(row["ratings_json"] or "{}"),
                "comments": row["comments"] or "",
                "date": row["created_at"] or "",
                "sentiment": calculated_sentiment,
                "sentiment_score": calculated_score,
                "is_demo": bool(row["is_demo"]),
            })
        return jsonify({"feedback": records})
    except (json.JSONDecodeError, TypeError):
        app.logger.exception("Stored feedback has invalid ratings data")
        return jsonify({"message": "Feedback records could not be loaded"}), 500
    finally:
        conn.close()


@app.route("/api/feedback/<int:feedback_id>", methods=["DELETE"])
def delete_feedback(feedback_id):
    if "user_id" not in session:
        return jsonify({"message": "Please log in to delete feedback"}), 401

    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
        if cursor.rowcount == 0:
            return jsonify({"message": "Feedback record not found"}), 404
        conn.commit()
        return jsonify({"message": "Feedback deleted successfully"})
    except Exception:
        app.logger.exception("Failed to delete patient feedback")
        return jsonify({"message": "Feedback could not be deleted"}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
