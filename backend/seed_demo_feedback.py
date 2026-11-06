import json
from datetime import datetime, timedelta, timezone

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from database import create_tables, get_connection


FEEDBACK_CATEGORIES = (
    "Doctor Consultation",
    "Nursing Care",
    "Cleanliness & Hygiene",
    "Hospital Facilities",
    "Emergency Services",
    "Pharmacy Service",
    "Waiting Time",
    "Staff Behaviour",
)

DEPARTMENTS = {
    "Cardiology": (
        "heart clinic", "cardiology team", "ECG and monitoring",
        "cardiology outpatient service",
    ),
    "Neurology": (
        "neurology clinic", "neurology team", "diagnostic tests",
        "neurology outpatient service",
    ),
    "Orthopaedics": (
        "orthopaedic clinic", "orthopaedic team", "mobility treatment",
        "orthopaedic clinic",
    ),
    "Paediatrics": (
        "children's clinic", "paediatric team", "my child's treatment",
        "children's outpatient service",
    ),
    "General Medicine": (
        "medical clinic", "medical team", "follow-up plan",
        "general medicine clinic",
    ),
    "Dermatology": (
        "skin clinic", "dermatology team", "treatment instructions",
        "dermatology clinic",
    ),
    "Emergency": (
        "emergency department", "emergency team", "initial assessment",
        "intake unit",
    ),
    "Pharmacy": (
        "hospital pharmacy", "pharmacy team", "prescription service",
        "prescription counter",
    ),
}

COMMENTS = (
    (
        "Dr. {doctor} listened carefully, explained the options in clear language, "
        "and the {team} made me feel comfortable throughout my visit."
    ),
    (
        "The {care} was organised and reassuring. Staff answered my questions, "
        "and I left with a clear plan for the next steps."
    ),
    (
        "The waiting area during my {care} visit and the consultation room were "
        "clean, and the nurses checked on me regularly. Overall, I felt well cared for."
    ),
    (
        "I had a very good experience with {focus}. The team was professional, "
        "the facilities were comfortable, and everything was explained clearly."
    ),
    (
        "Even though the {care} was busy, staff kept me informed and the doctor "
        "took time to discuss my concerns. A thoughtful and efficient visit."
    ),
    (
        "The {team} were kind and professional, and the instructions about "
        "medication and follow-up were easy to understand."
    ),
    (
        "At the {unit}, the visit took about an hour. I asked two questions about "
        "the next steps, and the appointment ended after a routine consultation."
    ),
    (
        "At the {unit}, my appointment was scheduled for 10:30. The waiting area "
        "had chairs and water, and the visit included a consultation and follow-up date."
    ),
    (
        "My appointment at the {care} started later than expected, and updates about "
        "the delay were limited. The doctor was courteous, but I left unsure about my results."
    ),
    (
        "Check-in at the {care} took longer than expected, and the room needed better "
        "attention to cleanliness. Staff were polite, but the overall visit was frustrating."
    ),
)

RATING_PROFILES = (
    (5, 5, 4, 4, 5, 4, 4, 5),
    (5, 4, 5, 4, 4, 5, 3, 5),
    (4, 5, 5, 4, 4, 4, 5, 5),
    (5, 4, 4, 5, 4, 5, 3, 4),
    (5, 5, 4, 5, 4, 4, 4, 5),
    (4, 5, 4, 4, 5, 5, 3, 5),
    (3, 3, 3, 3, 3, 3, 3, 3),
    (4, 3, 3, 4, 3, 3, 3, 4),
    (2, 3, 3, 3, 2, 3, 2, 3),
    (2, 2, 2, 3, 2, 2, 1, 3),
)

PATIENT_NAMES = (
    "Aarav Mehta", "Ananya Rao", "Ishaan Kapoor", "Mira Nair",
    "Kabir Shah", "Diya Iyer", "Rohan Das", "Sana Khan",
    "Arjun Menon", "Leela Joshi", "Vihaan Patel", "Nisha Thomas",
    "Devika Sen", "Karan Malhotra", "Tara Kulkarni", "Omar Ali",
    "Meera Pillai", "Neil D'Souza", "Riya Bose", "Aditya Verma",
)


def build_demo_records():
    analyzer = SentimentIntensityAnalyzer()
    records = []
    now = datetime.now(timezone.utc)

    for department_index, (department, terms) in enumerate(DEPARTMENTS.items()):
        care, team, focus, unit = terms
        for review_index, template in enumerate(COMMENTS):
            index = department_index * len(COMMENTS) + review_index
            doctor = ("Sharma", "Iyer", "Patel", "Rao", "Thomas")[index % 5]
            comment = template.format(
                doctor=doctor,
                care=care,
                team=team,
                focus=focus,
                unit=unit,
            )
            ratings = {
                category: RATING_PROFILES[review_index][category_index]
                for category_index, category in enumerate(FEEDBACK_CATEGORIES)
            }
            sentiment_score = analyzer.polarity_scores(comment)["compound"]
            if sentiment_score >= 0.05:
                sentiment = "Positive"
            elif sentiment_score <= -0.05:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"

            submitted_at = now - timedelta(
                days=(index * 37) % 120,
                hours=(index * 7) % 13,
                minutes=(index * 17) % 60,
            )
            name = (
                "Anonymous"
                if index % 13 == 0
                else PATIENT_NAMES[index % len(PATIENT_NAMES)]
            )
            records.append({
                "name": name,
                "department": department,
                "ratings": ratings,
                "comments": comment,
                "created_at": submitted_at.isoformat(),
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
            })

    return records


def seed_demo_feedback():
    create_tables()
    records = build_demo_records()
    conn = get_connection()
    try:
        existing_count = conn.execute(
            "SELECT COUNT(*) FROM feedback WHERE is_demo = 1"
        ).fetchone()[0]
        if existing_count:
            print(f"Demo feedback already exists ({existing_count} records); no rows added.")
            return

        conn.executemany(
            """
            INSERT INTO feedback (
                department, doctor_rating, cleanliness_rating, service_rating,
                comments, patient_name, ratings_json, created_at,
                sentiment, sentiment_score, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            [
                (
                    record["department"],
                    record["ratings"]["Doctor Consultation"],
                    record["ratings"]["Cleanliness & Hygiene"],
                    round(sum(record["ratings"].values()) / len(FEEDBACK_CATEGORIES)),
                    record["comments"],
                    record["name"],
                    json.dumps(record["ratings"]),
                    record["created_at"],
                    record["sentiment"],
                    record["sentiment_score"],
                )
                for record in records
            ],
        )
        conn.commit()
        sentiment_counts = {
            label: sum(record["sentiment"] == label for record in records)
            for label in ("Positive", "Neutral", "Negative")
        }
        print(
            f"Seeded {len(records)} fictional demo feedback records "
            f"({sentiment_counts}); no real patient feedback was created."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_demo_feedback()
