from flask import Blueprint, jsonify, request
from datetime import datetime

from db import get_db_connection
from utils.time_helpers import combine_date_and_time
from services.shift_rules import validate_shift_assignment_rules

notification_bp = Blueprint("notification", __name__)

# Helper function to check if a shift is within 24 hours
def is_within_24_hours_of_shift(shift_date, shift_start_time):
    shift_start_dt = combine_date_and_time(shift_date, shift_start_time)
    now = datetime.now()
    hours_until_shift = (shift_start_dt - now).total_seconds() / 3600

    return hours_until_shift <= 24

# Route to get notifications for a manager
@notification_bp.route("/manager-notifications/<int:manager_staff_id>")
def manager_notifications(manager_staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            sp.pickup_id,
            sp.shift_id,
            sp.staff_id,
            sp.status,
            sp.requested_at,
            st.name,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role
        FROM shift_pickups sp
        JOIN staff st ON sp.staff_id = st.staff_id
        JOIN shifts s ON sp.shift_id = s.shift_id
        WHERE sp.status = 'Pending'
        ORDER BY sp.requested_at DESC
    """)

    pickup_rows = cursor.fetchall()

    cursor.execute("""
        SELECT 
            t.time_off_id,
            t.staff_id,
            s.name,
            t.request_type,
            t.start_date,
            t.end_date,
            t.reason,
            t.status,
            t.requested_at
        FROM time_off t
        JOIN staff s ON t.staff_id = s.staff_id
        WHERE t.status = 'Pending'
        ORDER BY t.requested_at DESC
    """)

    time_off_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            s.shift_id,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role,
            s.status,
            s.is_open_shift,
            dr.staff_id AS dropped_by_staff_id,
            st.name AS dropped_by_name
        FROM shifts s
        LEFT JOIN drop_requests dr
            ON s.shift_id = dr.shift_id
            AND dr.status = 'Pending'
        LEFT JOIN staff st
            ON dr.staff_id = st.staff_id
        WHERE s.is_open_shift = 1
          AND s.status IN ('Draft', 'Posted')
          AND TIMESTAMP(s.shift_date, s.start_time) > NOW()
          AND s.shift_id NOT IN (
              SELECT shift_id
              FROM manager_cleared_notifications
              WHERE manager_staff_id = %s
          )
        ORDER BY s.shift_date, s.start_time
    """, (manager_staff_id,))

    open_shift_rows = cursor.fetchall()

    cursor.close()
    db.close()

    pickups = []

    for row in pickup_rows:
        pickups.append({
            "pickup_id": row["pickup_id"],
            "shift_id": row["shift_id"],
            "staff_id": row["staff_id"],
            "status": row["status"],
            "requested_at": str(row["requested_at"]) if row["requested_at"] else None,
            "name": row["name"],
            "shift_date": str(row["shift_date"]),
            "start_time": str(row["start_time"]),
            "end_time": str(row["end_time"]),
            "required_role": row["required_role"]
        })

    time_off_requests = []

    for row in time_off_rows:
        time_off_requests.append({
            "time_off_id": row["time_off_id"],
            "staff_id": row["staff_id"],
            "name": row["name"],
            "request_type": row["request_type"],
            "start_date": str(row["start_date"]),
            "end_date": str(row["end_date"]),
            "reason": row["reason"],
            "status": row["status"],
            "requested_at": str(row["requested_at"]) if row["requested_at"] else None
        })

    open_shifts = []

    for row in open_shift_rows:
        open_shifts.append({
            "shift_id": row["shift_id"],
            "shift_date": str(row["shift_date"]),
            "start_time": str(row["start_time"]),
            "end_time": str(row["end_time"]),
            "required_role": row["required_role"],
            "status": row["status"],
            "is_open_shift": row["is_open_shift"],
            "dropped_by_staff_id": row["dropped_by_staff_id"],
            "dropped_by_name": row["dropped_by_name"]
        })

    return jsonify({
        "pickup_requests": pickups,
        "time_off_requests": time_off_requests,
        "open_shifts": open_shifts
    })

# Route to get notifications for a staff member
@notification_bp.route("/staff-notifications/<int:staff_id>")
def staff_notifications(staff_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.shift_id,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role,
            s.status,
            s.is_open_shift,
            dr.staff_id AS dropped_by_staff_id,
            st.name AS dropped_by_name
        FROM shifts s
        LEFT JOIN drop_requests dr
            ON s.shift_id = dr.shift_id
            AND dr.status = 'Pending'
        LEFT JOIN staff st
            ON dr.staff_id = st.staff_id
        WHERE s.is_open_shift = 1
          AND s.status = 'Posted'
          AND TIMESTAMP(s.shift_date, s.start_time) > DATE_ADD(NOW(), INTERVAL 24 HOUR)
          AND s.shift_id NOT IN (
              SELECT shift_id
              FROM shift_pickups
              WHERE status = 'Approved'
          )
        ORDER BY s.shift_date, s.start_time
    """)

    open_shift_rows = cursor.fetchall()

    cursor.execute("""
        SELECT 
            sp.pickup_id,
            sp.status,
            sp.requested_at,
            s.shift_date,
            s.start_time,
            s.end_time,
            s.required_role
        FROM shift_pickups sp
        JOIN shifts s ON sp.shift_id = s.shift_id
        WHERE sp.staff_id = %s
          AND (
                sp.status = 'Pending'
                OR (sp.status IN ('Approved', 'Rejected') AND sp.staff_cleared = 0)
              )
        ORDER BY sp.requested_at DESC
    """, (staff_id,))

    my_request_rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            time_off_id,
            request_type,
            start_date,
            end_date,
            status,
            manager_note,
            requested_at,
            reviewed_at
        FROM time_off
        WHERE staff_id = %s
          AND (
                status = 'Pending'
                OR (status IN ('Approved', 'Rejected') AND staff_cleared = 0)
              )
        ORDER BY requested_at DESC
    """, (staff_id,))

    time_off_rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        "open_shifts": [
            {
                "shift_id": row["shift_id"],
                "shift_date": str(row["shift_date"]),
                "start_time": str(row["start_time"]),
                "end_time": str(row["end_time"]),
                "required_role": row["required_role"],
                "status": row["status"],
                "is_open_shift": row["is_open_shift"],
                "dropped_by_staff_id": row["dropped_by_staff_id"],
                "dropped_by_name": row["dropped_by_name"]
            }
            for row in open_shift_rows
        ],
        "my_requests": [
            {
                "pickup_id": row["pickup_id"],
                "status": row["status"],
                "requested_at": str(row["requested_at"]) if row["requested_at"] else None,
                "shift_date": str(row["shift_date"]) if row["shift_date"] else None,
                "start_time": str(row["start_time"]) if row["start_time"] else None,
                "end_time": str(row["end_time"]) if row["end_time"] else None,
                "required_role": row["required_role"]
            }
            for row in my_request_rows
        ],
        "time_off_updates": [
            {
                "time_off_id": row["time_off_id"],
                "request_type": row["request_type"],
                "start_date": str(row["start_date"]) if row["start_date"] else None,
                "end_date": str(row["end_date"]) if row["end_date"] else None,
                "status": row["status"],
                "manager_note": row["manager_note"],
                "requested_at": str(row["requested_at"]) if row["requested_at"] else None,
                "reviewed_at": str(row["reviewed_at"]) if row["reviewed_at"] else None
            }
            for row in time_off_rows
        ]
    })

# Route to get open shift notifications for staff
@notification_bp.route("/request-pickup", methods=["POST"])
def request_pickup():
    data = request.get_json()

    shift_id = data.get("shift_id")
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT shift_date, start_time
            FROM shifts
            WHERE shift_id = %s
        """, (shift_id,))

        shift = cursor.fetchone()

        if not shift:
            return jsonify({"success": False, "message": "Shift not found"})

        if is_within_24_hours_of_shift(shift["shift_date"], shift["start_time"]):
            return jsonify({
                "success": False,
                "message": "You cannot request this shift within 24 hours of the start time"
            })

        cursor.execute("""
            SELECT staff_id
            FROM drop_requests
            WHERE shift_id = %s
              AND status = 'Pending'
            LIMIT 1
        """, (shift_id,))

        drop_request = cursor.fetchone()

        if drop_request and int(drop_request["staff_id"]) == int(staff_id):
            return jsonify({
                "success": False,
                "message": "You cannot request pickup for your own dropped shift"
            })

        cursor.execute("""
            SELECT pickup_id
            FROM shift_pickups
            WHERE shift_id = %s
              AND staff_id = %s
              AND status = 'Pending'
        """, (shift_id, staff_id))

        existing = cursor.fetchone()

        if existing:
            return jsonify({"success": False, "message": "Request already pending"})

        cursor.execute("""
            INSERT INTO shift_pickups (shift_id, staff_id, status)
            VALUES (%s, %s, 'Pending')
        """, (shift_id, staff_id))

        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        print("REQUEST PICKUP ERROR:", e)
        return jsonify({"success": False, "message": "Could not request pickup"})

    finally:
        cursor.close()
        db.close()

# Route to approve a pickup request
@notification_bp.route("/approve-pickup", methods=["POST"])
def approve_pickup():
    data = request.get_json()

    pickup_id = data.get("pickup_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT sp.shift_id, sp.staff_id AS new_staff_id
            FROM shift_pickups sp
            WHERE sp.pickup_id = %s
              AND sp.status = 'Pending'
        """, (pickup_id,))

        pickup = cursor.fetchone()

        if not pickup:
            return jsonify({"success": False, "message": "Pickup request not found"})

        shift_id = pickup["shift_id"]
        new_staff_id = pickup["new_staff_id"]

        cursor.execute("""
            SELECT staff_id AS original_staff_id
            FROM drop_requests
            WHERE shift_id = %s
              AND status = 'Pending'
            LIMIT 1
        """, (shift_id,))

        drop_request = cursor.fetchone()

        cursor.execute("""
            SELECT shift_date, start_time, end_time, required_role
            FROM shifts
            WHERE shift_id = %s
        """, (shift_id,))

        shift = cursor.fetchone()

        if not shift:
            return jsonify({"success": False, "message": "Shift not found"})

        allowed, message = validate_shift_assignment_rules(
            cursor,
            new_staff_id,
            shift["shift_date"],
            shift["start_time"],
            shift["end_time"],
            shift["required_role"]
        )

        if not allowed:
            return jsonify({"success": False, "message": message})

        if drop_request:
            original_staff_id = drop_request["original_staff_id"]

            cursor.execute("""
                DELETE FROM staff_shifts
                WHERE shift_id = %s
                  AND staff_id = %s
            """, (shift_id, original_staff_id))

            cursor.execute("""
                UPDATE drop_requests
                SET status = 'Approved'
                WHERE shift_id = %s
                  AND staff_id = %s
                  AND status = 'Pending'
            """, (shift_id, original_staff_id))

        cursor.execute("""
            INSERT INTO staff_shifts (staff_id, shift_id, attendance_status)
            VALUES (%s, %s, 'Scheduled')
        """, (new_staff_id, shift_id))

        cursor.execute("""
            UPDATE shifts
            SET is_open_shift = 0
            WHERE shift_id = %s
        """, (shift_id,))

        cursor.execute("""
            UPDATE shift_pickups
            SET status = 'Approved'
            WHERE pickup_id = %s
        """, (pickup_id,))

        cursor.execute("""
            UPDATE shift_pickups
            SET status = 'Rejected'
            WHERE shift_id = %s
              AND pickup_id != %s
              AND status = 'Pending'
        """, (shift_id, pickup_id))

        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        print("APPROVE PICKUP ERROR:", e)
        return jsonify({"success": False, "message": "Could not approve pickup"})

    finally:
        cursor.close()
        db.close()

# Route to reject a pickup request
@notification_bp.route("/reject-pickup", methods=["POST"])
def reject_pickup():
    data = request.get_json()

    pickup_id = data.get("pickup_id")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE shift_pickups
        SET status = 'Rejected'
        WHERE pickup_id = %s
    """, (pickup_id,))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Route to clear pickup notification after staff has seen the update
@notification_bp.route("/clear-pickup-notification", methods=["POST"])
def clear_pickup_notification():
    data = request.get_json()

    pickup_id = data.get("pickup_id")
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE shift_pickups
        SET staff_cleared = 1
        WHERE pickup_id = %s
          AND staff_id = %s
          AND status IN ('Approved', 'Rejected')
    """, (pickup_id, staff_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Route to clear time off notification after staff has seen the update
@notification_bp.route("/clear-timeoff-notification", methods=["POST"])
def clear_timeoff_notification():
    data = request.get_json()

    time_off_id = data.get("time_off_id")
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE time_off
        SET staff_cleared = 1
        WHERE time_off_id = %s
          AND staff_id = %s
          AND status IN ('Approved', 'Rejected')
    """, (time_off_id, staff_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Route to clear manager notification for an open shift
@notification_bp.route("/clear-manager-open-shift", methods=["POST"])
def clear_manager_open_shift():
    data = request.get_json()

    shift_id = data.get("shift_id")
    manager_staff_id = data.get("manager_staff_id")

    if not shift_id or not manager_staff_id:
        return jsonify({"success": False, "message": "Missing data"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT IGNORE INTO manager_cleared_notifications
        (manager_staff_id, shift_id)
        VALUES (%s, %s)
    """, (manager_staff_id, shift_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})