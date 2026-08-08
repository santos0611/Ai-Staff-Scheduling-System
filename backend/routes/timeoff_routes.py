from flask import Blueprint, jsonify, request
from datetime import timedelta

from db import get_db_connection

timeoff_bp = Blueprint("timeoff", __name__)

# Helper function to check if any shifts are already posted within the requested time off period
def is_date_in_posted_schedule(cursor, start_date, end_date):
    cursor.execute("""
        SELECT shift_id
        FROM shifts
        WHERE status = 'Posted'
          AND shift_date BETWEEN %s AND %s
        LIMIT 1
    """, (start_date, end_date))

    return cursor.fetchone() is not None

# Route to request time off for a staff member, with validation to prevent requests for dates in an already posted schedule
@timeoff_bp.route("/request-time-off", methods=["POST"])
def request_time_off():
    data = request.get_json()

    staff_id = data.get("staff_id")
    request_type = data.get("request_type")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    reason = data.get("reason", "")

    if not staff_id or not request_type or not start_date or not end_date:
        return jsonify({"success": False, "message": "Missing required fields"})

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if is_date_in_posted_schedule(cursor, start_date, end_date):
        cursor.close()
        db.close()
        return jsonify({
            "success": False,
            "message": "You cannot request time off for dates in an already posted schedule"
        })

    cursor.execute("""
        INSERT INTO time_off (
            staff_id,
            request_type,
            start_date,
            end_date,
            reason,
            status,
            staff_cleared
        )
        VALUES (%s, %s, %s, %s, %s, 'Pending', 0)
    """, (staff_id, request_type, start_date, end_date, reason))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Route to get all approved time off for a staff member, formatted as calendar events
@timeoff_bp.route("/approved-time-off/<int:staff_id>")
def approved_time_off(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT time_off_id, request_type, start_date, end_date, manager_note
        FROM time_off
        WHERE staff_id = %s
          AND status = 'Approved'
        ORDER BY start_date
    """, (staff_id,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    events = []

    for row in rows:
        end_date_exclusive = row["end_date"] + timedelta(days=1)

        events.append({
            "id": f"timeoff-{row['time_off_id']}",
            "title": f"Time Off: {row['request_type']}",
            "start": str(row["start_date"]),
            "end": str(end_date_exclusive),
            "allDay": True,
            "display": "background"
        })

    return jsonify(events)

# Route to get all time off requests for a staff member, including pending, approved, and rejected requests
@timeoff_bp.route("/my-time-off/<int:staff_id>")
def my_time_off(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT time_off_id, request_type, start_date, end_date, reason, status, manager_note, requested_at
        FROM time_off
        WHERE staff_id = %s
        ORDER BY requested_at DESC
    """, (staff_id,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    cleaned = []

    for row in rows:
        cleaned.append({
            "time_off_id": row["time_off_id"],
            "request_type": row["request_type"],
            "start_date": str(row["start_date"]) if row["start_date"] else None,
            "end_date": str(row["end_date"]) if row["end_date"] else None,
            "reason": row["reason"],
            "status": row["status"],
            "manager_note": row["manager_note"],
            "requested_at": str(row["requested_at"]) if row["requested_at"] else None
        })

    return jsonify(cleaned)

# Admin route to get all approved time off requests for all staff members, with staff details included
@timeoff_bp.route("/approve-time-off", methods=["POST"])
def approve_time_off():
    data = request.get_json()

    time_off_id = data.get("time_off_id")
    manager_note = data.get("manager_note", "")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE time_off
        SET status = 'Approved',
            manager_note = %s,
            reviewed_at = NOW(),
            staff_cleared = 0
        WHERE time_off_id = %s
    """, (manager_note, time_off_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Admin route to reject time off requests
@timeoff_bp.route("/reject-time-off", methods=["POST"])
def reject_time_off():
    data = request.get_json()

    time_off_id = data.get("time_off_id")
    manager_note = data.get("manager_note", "")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE time_off
        SET status = 'Rejected',
            manager_note = %s,
            reviewed_at = NOW(),
            staff_cleared = 0
        WHERE time_off_id = %s
    """, (manager_note, time_off_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})