from flask import Blueprint, jsonify, request
from datetime import datetime

from db import get_db_connection

from utils.time_helpers import daterange, combine_date_and_time
from utils.validators import (
    validate_date,
    validate_time,
    validate_role,
    safe_int,
    api_error
)

from services.assessment_service import assess_shift_assignment
from services.shift_rules import validate_shift_assignment_rules
from services.risk_service import week_has_manager_cover

shift_bp = Blueprint("shift", __name__)

# Helper function to clean shift data for API responses
def clean_shift_row(row):
    return {
        "shift_id": row.get("shift_id"),
        "shift_date": str(row.get("shift_date")) if row.get("shift_date") is not None else None,
        "start_time": str(row.get("start_time")) if row.get("start_time") is not None else None,
        "end_time": str(row.get("end_time")) if row.get("end_time") is not None else None,
        "required_role": row.get("required_role"),
        "status": row.get("status"),
        "is_open_shift": row.get("is_open_shift"),
        "notes": row.get("notes"),
        "location": row.get("location")
    }

# Helper function to check if a shift is within 24 hours (used for blocking last-minute drop requests)
def is_within_24_hours_of_shift(shift_date, shift_start_time):
    shift_start_dt = combine_date_and_time(shift_date, shift_start_time)
    now = datetime.now()
    hours_until_shift = (shift_start_dt - now).total_seconds() / 3600

    return hours_until_shift <= 24

# Helper function to check if a shift falls within the next 24 hours (used for filtering open shifts)
@shift_bp.route("/all-shifts")
def all_shifts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM shifts
        ORDER BY shift_date, start_time
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify([clean_shift_row(row) for row in rows])

# Route to get all shifts in a format suitable for calendar display
@shift_bp.route("/all-calendar-shifts")
def all_calendar_shifts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT ss.staff_shift_id, st.name, s.shift_date, s.start_time, s.end_time, s.required_role
        FROM staff_shifts ss
        JOIN staff st ON ss.staff_id = st.staff_id
        JOIN shifts s ON ss.shift_id = s.shift_id
        ORDER BY s.shift_date, s.start_time
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    shifts = []

    for row in rows:
        shifts.append({
            "id": row["staff_shift_id"],
            "title": f"{row['name']} {str(row['start_time'])} - {str(row['end_time'])}",
            "start": str(row["shift_date"]),
            "allDay": True,
            "extendedProps": {
                "staff_name": row["name"],
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "required_role": row["required_role"]
            }
        })

    return jsonify(shifts)

# Route to get shifts for a specific day for manager view, including time off
@shift_bp.route("/manager-day-shifts/<date>")
def manager_day_shifts(date):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            ss.staff_shift_id,
            CASE
                WHEN COALESCE(ss.attendance_status,'Scheduled') = 'Scheduled'
                    AND TIMESTAMP(s.shift_date, s.end_time) < NOW()
                THEN 'Present'
                ELSE COALESCE(ss.attendance_status,'Scheduled')
            END AS attendance_status,
            st.staff_id,
            st.name,
            s.shift_id,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role,
            COALESCE(s.status, 'Draft') AS status
        FROM staff_shifts ss
        JOIN staff st ON ss.staff_id = st.staff_id
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE s.shift_date = %s
        ORDER BY s.start_time
    """, (date,))

    shift_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            t.time_off_id,
            t.staff_id,
            st.name,
            t.request_type,
            t.start_date,
            t.end_date
        FROM time_off t
        JOIN staff st ON t.staff_id = st.staff_id
        WHERE t.status = 'Approved'
          AND %s BETWEEN t.start_date AND t.end_date
        ORDER BY st.name
    """, (date,))

    holiday_rows = cursor.fetchall()

    cursor.close()
    db.close()

    items = []

    for row in shift_rows:
        initials = "".join([part[0] for part in row["name"].split()[:2]]).upper()

        items.append({
            "staff_shift_id": row["staff_shift_id"],
            "staff_id": row["staff_id"],
            "name": row["name"],
            "initials": initials,
            "shift_date": str(row["shift_date"]),
            "start_time": str(row["start_time"]),
            "end_time": str(row["end_time"]),
            "required_role": row["required_role"],
            "status": row["status"],
            "attendance_status": row["attendance_status"],
            "is_time_off": 0
        })

    for row in holiday_rows:
        initials = "".join([part[0] for part in row["name"].split()[:2]]).upper()

        items.append({
            "staff_shift_id": f"timeoff-{row['time_off_id']}",
            "staff_id": row["staff_id"],
            "name": row["name"],
            "initials": initials,
            "shift_date": date,
            "start_time": "",
            "end_time": "",
            "required_role": f"Holiday: {row['request_type']}",
            "status": "Approved Holiday",
            "attendance_status": "Holiday",
            "is_time_off": 1
        })

    return jsonify(items)

# Route to get shifts for a specific week for manager view, including time off
@shift_bp.route("/manager-week-shifts/<start_date>/<end_date>")
def manager_week_shifts(start_date, end_date):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            st.staff_id,
            st.name,
            ss.staff_shift_id,
            COALESCE(ss.attendance_status, 'Scheduled') AS attendance_status,
            s.shift_id,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role,
            s.status,
            s.is_open_shift
        FROM staff st
        LEFT JOIN staff_shifts ss ON st.staff_id = ss.staff_id
        LEFT JOIN shifts s ON ss.shift_id = s.shift_id
            AND s.shift_date BETWEEN %s AND %s
        ORDER BY st.name, s.shift_date, s.start_time
    """, (start_date, end_date))

    shift_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            t.time_off_id,
            t.staff_id,
            st.name,
            t.request_type,
            t.start_date,
            t.end_date
        FROM time_off t
        JOIN staff st ON t.staff_id = st.staff_id
        WHERE t.status = 'Approved'
          AND t.start_date <= %s
          AND t.end_date >= %s
        ORDER BY st.name, t.start_date
    """, (end_date, start_date))

    holiday_rows = cursor.fetchall()

    cursor.close()
    db.close()

    items = []

    for row in shift_rows:
        if row["shift_id"] is not None:
            items.append({
                "staff_id": row["staff_id"],
                "name": row["name"],
                "staff_shift_id": row["staff_shift_id"],
                "attendance_status": row["attendance_status"],
                "shift_id": row["shift_id"],
                "shift_date": str(row["shift_date"]),
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "required_role": row["required_role"],
                "status": row["status"] if row["status"] else "Draft",
                "is_open_shift": row["is_open_shift"],
                "is_time_off": 0
            })

    week_start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    week_end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    for row in holiday_rows:
        holiday_start = max(row["start_date"], week_start_obj)
        holiday_end = min(row["end_date"], week_end_obj)

        for single_day in daterange(holiday_start, holiday_end):
            items.append({
                "staff_id": row["staff_id"],
                "name": row["name"],
                "staff_shift_id": f"timeoff-{row['time_off_id']}-{single_day}",
                "attendance_status": "Holiday",
                "shift_id": f"timeoff-{row['time_off_id']}-{single_day}",
                "shift_date": str(single_day),
                "start_time": "",
                "end_time": "",
                "required_role": f"Holiday: {row['request_type']}",
                "status": "Approved Holiday",
                "is_open_shift": 0,
                "is_time_off": 1
            })

    return jsonify(items)

# Route to get shifts for a specific staff member
@shift_bp.route("/create-shift", methods=["POST"])
def create_shift():
    data = request.get_json()

    shift_date = data.get("shift_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    required_role = data.get("required_role")
    status = data.get("status", "Draft")
    is_open_shift = int(data.get("is_open_shift", 0))
    notes = data.get("notes", "")
    location = data.get("location", "")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO shifts (
            shift_date,
            start_time,
            end_time,
            required_role,
            status,
            is_open_shift,
            notes,
            location
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (shift_date, start_time, end_time, required_role, status, is_open_shift, notes, location))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Route to create a new shift and assign it to a staff member in one step, with validation and assessment
@shift_bp.route("/create-shift-and-assign", methods=["POST"])
def create_shift_and_assign():
    data = request.get_json()

    try:
        staff_id = data.get("staff_id")
        shift_date = validate_date(data.get("shift_date"), "shift_date")
        start_time = validate_time(data.get("start_time"), "start_time")
        end_time = validate_time(data.get("end_time"), "end_time")
        required_role = validate_role(data.get("required_role"))
        is_open_shift = safe_int(data.get("is_open_shift", 0), "is_open_shift")

        if start_time >= end_time:
            return api_error("Start time must be before end time")

        if is_open_shift not in [0, 1]:
            return api_error("Invalid open shift value")

        if is_open_shift == 0:
            staff_id = safe_int(staff_id, "staff_id")

    except ValueError as e:
        return api_error(str(e))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        assessment = None

        if is_open_shift == 0:
            assessment = assess_shift_assignment(
                cursor,
                staff_id,
                shift_date,
                start_time,
                end_time,
                required_role
            )

            if not assessment["allowed"]:
                return jsonify({
                    "success": False,
                    "message": "Shift assignment blocked",
                    "hard_blockers": assessment["hard_blockers"],
                    "soft_warnings": assessment["soft_warnings"]
                })

        cursor.execute("""
            INSERT INTO shifts (
                shift_date,
                start_time,
                end_time,
                required_role,
                status,
                is_open_shift,
                notes,
                location
            )
            VALUES (%s, %s, %s, %s, 'Draft', %s, '', '')
        """, (shift_date, start_time, end_time, required_role, is_open_shift))

        new_shift_id = cursor.lastrowid

        if is_open_shift == 0:
            cursor.execute("""
                INSERT INTO staff_shifts (staff_id, shift_id, attendance_status)
                VALUES (%s, %s, 'Scheduled')
            """, (staff_id, new_shift_id))

        db.commit()

        return jsonify({
            "success": True,
            "shift_id": new_shift_id,
            "soft_warnings": assessment["soft_warnings"] if assessment else [],
            "risk_level": assessment["risk_level"] if assessment else "LOW"
        })

    except Exception as e:
        db.rollback()
        print("CREATE SHIFT AND ASSIGN ERROR:", e)
        return api_error("Server error", 500)

    finally:
        cursor.close()
        db.close()

# Route to assign an existing shift to a staff member, with validation
@shift_bp.route("/assign-shift", methods=["POST"])
def assign_shift():
    data = request.get_json()

    staff_id = data.get("staff_id")
    shift_id = data.get("shift_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT shift_date, start_time, end_time, required_role
            FROM shifts
            WHERE shift_id = %s
        """, (shift_id,))

        shift = cursor.fetchone()

        if not shift:
            return jsonify({
                "success": False,
                "message": "Shift not found"
            })

        allowed, message = validate_shift_assignment_rules(
            cursor,
            staff_id,
            shift["shift_date"],
            shift["start_time"],
            shift["end_time"],
            shift["required_role"]
        )

        if not allowed:
            return jsonify({
                "success": False,
                "message": message
            })

        cursor.execute("""
            INSERT INTO staff_shifts (staff_id, shift_id)
            VALUES (%s, %s)
        """, (staff_id, shift_id))

        cursor.execute("""
            UPDATE shifts
            SET is_open_shift = 0
            WHERE shift_id = %s
        """, (shift_id,))

        db.commit()

        return jsonify({"success": True})

    finally:
        cursor.close()
        db.close()

# Route to delete a draft shift (only allowed if the shift is still in draft status)
@shift_bp.route("/delete-draft-shift", methods=["POST"])
def delete_draft_shift():
    data = request.get_json()

    shift_id = data.get("shift_id")

    if not shift_id:
        return jsonify({"success": False, "message": "Missing shift_id"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT shift_id, status
            FROM shifts
            WHERE shift_id = %s
            LIMIT 1
        """, (shift_id,))

        shift = cursor.fetchone()

        if not shift:
            return jsonify({"success": False, "message": "Shift not found"}), 404

        if shift["status"] != "Draft":
            return jsonify({
                "success": False,
                "message": "Only draft shifts can be deleted"
            }), 400

        cursor.execute("DELETE FROM staff_shifts WHERE shift_id = %s", (shift_id,))
        cursor.execute("DELETE FROM shift_pickups WHERE shift_id = %s", (shift_id,))
        cursor.execute("DELETE FROM shifts WHERE shift_id = %s", (shift_id,))

        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        print("DELETE DRAFT SHIFT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()

# Route to publish a week of shifts, with validation to ensure manager cover is in place
@shift_bp.route("/publish-week", methods=["POST"])
def publish_week():
    data = request.get_json()

    start_date = data.get("start_date")
    end_date = data.get("end_date")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        ok, failed_day = week_has_manager_cover(cursor, start_date, end_date)

        if not ok:
            return jsonify({
                "success": False,
                "message": f"Cannot publish week. Manager cover is missing for {failed_day} between 06:00 and 23:00."
            })

        cursor.execute("""
            UPDATE shifts
            SET status = 'Posted'
            WHERE shift_date BETWEEN %s AND %s
        """, (start_date, end_date))

        db.commit()

        return jsonify({"success": True})

    finally:
        cursor.close()
        db.close()

# Route to get all open shifts that are available for pickup, excluding shifts within the next 24 hours and those already picked up
@shift_bp.route("/open-shifts")
def open_shifts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT shift_id, shift_date, start_time, end_time, required_role, status, is_open_shift, notes, location
        FROM shifts
        WHERE is_open_shift = 1
          AND status = 'Posted'
          AND TIMESTAMP(shift_date, start_time) > DATE_ADD(NOW(), INTERVAL 24 HOUR)
          AND shift_id NOT IN (
              SELECT shift_id FROM shift_pickups WHERE status = 'Approved'
          )
        ORDER BY shift_date, start_time
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify([clean_shift_row(row) for row in rows])

# Route to request to pick up an open shift
@shift_bp.route("/drop-shift", methods=["POST"])
def drop_shift():
    data = request.get_json()

    shift_id = data.get("shift_id")
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT ss.staff_shift_id, s.shift_date, s.start_time
            FROM staff_shifts ss
            JOIN shifts s ON ss.shift_id = s.shift_id
            WHERE ss.shift_id = %s
              AND ss.staff_id = %s
        """, (shift_id, staff_id))

        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "Shift assignment not found"})

        if is_within_24_hours_of_shift(row["shift_date"], row["start_time"]):
            return jsonify({
                "success": False,
                "message": "You cannot drop a shift within 24 hours of the start time"
            })

        cursor.execute("""
            SELECT drop_request_id
            FROM drop_requests
            WHERE shift_id = %s
              AND staff_id = %s
              AND status = 'Pending'
        """, (shift_id, staff_id))

        existing = cursor.fetchone()

        if existing:
            return jsonify({"success": False, "message": "Drop request already pending"})

        cursor.execute("""
            INSERT INTO drop_requests (shift_id, staff_id, status)
            VALUES (%s, %s, 'Pending')
        """, (shift_id, staff_id))

        cursor.execute("""
            UPDATE shifts
            SET is_open_shift = 1,
                status = 'Posted'
            WHERE shift_id = %s
        """, (shift_id,))

        db.commit()

        return jsonify({"success": True, "message": "Shift marked as available for pickup"})

    except Exception as e:
        db.rollback()
        print("DROP SHIFT ERROR:", e)
        return jsonify({"success": False, "message": "Could not drop shift"})

    finally:
        cursor.close()
        db.close()

# Route to mark attendance for a shift
@shift_bp.route("/mark-attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()

    staff_shift_id = data.get("staff_shift_id")
    attendance_status = data.get("attendance_status")

    allowed_statuses = ["Scheduled", "Present", "Absent", "Sick"]

    if not staff_shift_id:
        return jsonify({"success": False, "message": "Missing staff_shift_id"}), 400

    if attendance_status not in allowed_statuses:
        return jsonify({"success": False, "message": "Invalid attendance status"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE staff_shifts
        SET attendance_status = %s
        WHERE staff_shift_id = %s
    """, (attendance_status, staff_shift_id))

    db.commit()

    if cursor.rowcount == 0:
        cursor.close()
        db.close()
        return jsonify({"success": False, "message": "Shift record not found"}), 404

    cursor.close()
    db.close()

    return jsonify({"success": True})