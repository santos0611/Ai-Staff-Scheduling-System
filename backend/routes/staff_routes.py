from flask import Blueprint, jsonify
from db import get_db_connection

staff_bp = Blueprint("staff", __name__)

# Route to get all staff members with their ID, name, and position
@staff_bp.route("/all-staff")
def all_staff():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT staff_id, name, position
        FROM staff
        ORDER BY name
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(rows)
# Route to get details of a specific staff member by ID
@staff_bp.route("/my-shifts/<int:staff_id>")
def my_shifts(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.shift_id, s.shift_date, s.start_time, s.end_time, s.required_role
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.status = 'Posted'
        ORDER BY s.shift_date, s.start_time
    """, (staff_id,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    shifts = []

    for row in rows:
        shifts.append({
            "id": row["shift_id"],
            "title": f"Shift: {str(row['start_time'])} - {str(row['end_time'])}",
            "start": str(row["shift_date"]),
            "allDay": True,
            "extendedProps": {
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "required_role": row["required_role"]
            }
        })

    return jsonify(shifts)
# Route to get the next upcoming shift for a specific staff member
@staff_bp.route("/next-shift/<int:staff_id>")
def next_shift(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.shift_id, s.shift_date, s.start_time, s.end_time, s.required_role
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.status = 'Posted'
          AND TIMESTAMP(s.shift_date, s.end_time) > NOW()
        ORDER BY s.shift_date, s.start_time
        LIMIT 1
    """, (staff_id,))

    row = cursor.fetchone()

    cursor.close()
    db.close()

    if not row:
        return jsonify({"success": False})

    return jsonify({
        "success": True,
        "id": row["shift_id"],
        "date": str(row["shift_date"]),
        "start_time": str(row["start_time"]),
        "end_time": str(row["end_time"]),
        "required_role": row["required_role"]
    })