from flask import Blueprint, jsonify, request
from db import get_db_connection

availability_bp = Blueprint("availability", __name__)

# Route to get availability for all staff
@availability_bp.route("/all-availability")
def all_availability():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.staff_id,
            a.day_of_week,
            a.is_available,
            a.is_all_day,
            a.start_time,
            a.end_time,
            s.name,
            s.position
        FROM availability a
        JOIN staff s ON a.staff_id = s.staff_id
        ORDER BY
            s.name,
            FIELD(a.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    cleaned = []

    for row in rows:
        cleaned.append({
            "staff_id": row["staff_id"],
            "name": row["name"],
            "position": row["position"],
            "day_of_week": row["day_of_week"],
            "is_available": row["is_available"],
            "is_all_day": row["is_all_day"],
            "start_time": str(row["start_time"]) if row["start_time"] is not None else "",
            "end_time": str(row["end_time"]) if row["end_time"] is not None else ""
        })

    return jsonify(cleaned)

# Route to get availability for a specific staff member
@availability_bp.route("/availability/<int:staff_id>")
def get_availability(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            day_of_week,
            is_available,
            is_all_day,
            start_time,
            end_time
        FROM availability
        WHERE staff_id = %s
        ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    """, (staff_id,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    cleaned = []

    for row in rows:
        cleaned.append({
            "day_of_week": row["day_of_week"],
            "is_available": row["is_available"],
            "is_all_day": row["is_all_day"],
            "start_time": str(row["start_time"]) if row["start_time"] is not None else "",
            "end_time": str(row["end_time"]) if row["end_time"] is not None else ""
        })

    return jsonify(cleaned)

# Route to save availability for a staff member
@availability_bp.route("/save-availability", methods=["POST"])
def save_availability():
    data = request.get_json()

    staff_id = data.get("staff_id")
    availability = data.get("availability", [])

    if not staff_id:
        return jsonify({"success": False, "message": "Missing staff_id"})

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM availability WHERE staff_id = %s", (staff_id,))

    for item in availability:
        day_of_week = item.get("day_of_week")
        is_available = int(item.get("is_available", 0))
        is_all_day = int(item.get("is_all_day", 0))
        start_time = item.get("start_time")
        end_time = item.get("end_time")

        if is_available == 0:
            start_time = None
            end_time = None
            is_all_day = 0

        elif is_all_day == 1:
            start_time = None
            end_time = None

        cursor.execute("""
            INSERT INTO availability (
                staff_id,
                day_of_week,
                is_available,
                is_all_day,
                start_time,
                end_time
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            staff_id,
            day_of_week,
            is_available,
            is_all_day,
            start_time,
            end_time
        ))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})