from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import re

from db import get_db_connection
from utils.role_helpers import normalise_role

auth_bp = Blueprint("auth", __name__)

# Helper function to validate password strength
def validate_password_strength(password):
    errors = []

    if len(password) < 8:
        errors.append("At least 8 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter")

    if not re.search(r"\d", password):
        errors.append("At least 1 number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("At least 1 special character")

    return errors

# Route for user login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM staff
        WHERE email = %s
          AND account_status = 'Approved'
        LIMIT 1
    """, (email,))

    user = cursor.fetchone()

    if not user:
        cursor.close()
        db.close()
        return jsonify({"success": False})

    stored_password = user["password"]
    login_ok = False

    if stored_password.startswith("pbkdf2:sha256") or stored_password.startswith("scrypt:"):# Check if the stored password is hashed using a modern algorithm
        login_ok = check_password_hash(stored_password, password)
    else:
        if stored_password == password:
            login_ok = True

            new_hash = generate_password_hash(password)

            cursor.execute("""
                UPDATE staff
                SET password = %s
                WHERE staff_id = %s
            """, (new_hash, user["staff_id"]))

            db.commit()

    cursor.close()
    db.close()

    if login_ok:
        return jsonify({
            "success": True,
            "staff_id": user["staff_id"],
            "position": user["position"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        })

    return jsonify({"success": False})

# Route for password reset
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()

    staff_id = data.get("staff_id")
    dob = data.get("dob")
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    new_password = data.get("new_password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()

    if not staff_id or not dob or not email or not phone or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match"}), 400

    password_errors = validate_password_strength(new_password)

    if password_errors:
        return jsonify({
            "success": False,
            "message": "Password does not meet the requirements",
            "password_errors": password_errors
        }), 400

    hashed_password = generate_password_hash(new_password)

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT staff_id
            FROM staff
            WHERE staff_id = %s
              AND dob = %s
              AND email = %s
              AND phone = %s
              AND account_status = 'Approved'
            LIMIT 1
        """, (staff_id, dob, email, phone))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "Details do not match an approved staff account"
            }), 400

        cursor.execute("""
            UPDATE staff
            SET password = %s
            WHERE staff_id = %s
        """, (hashed_password, staff_id))

        db.commit()

        return jsonify({"success": True, "message": "Password reset successfully"})

    finally:
        cursor.close()
        db.close()

# Route for creating a new account
@auth_bp.route("/create-account", methods=["POST"])
def create_account():
    data = request.get_json()

    name = data.get("name", "").strip()
    dob = data.get("dob")
    position = normalise_role(data.get("position"))
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()

    if not name or not dob or not position or not email or not phone or not password or not confirm_password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match"}), 400

    password_errors = validate_password_strength(password)

    if password_errors:
        return jsonify({
            "success": False,
            "message": "Password does not meet the requirements",
            "password_errors": password_errors
        }), 400

    if position not in {"manager", "crew trainer", "crew member", "trainee"}:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    hashed_password = generate_password_hash(password)

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT staff_id
            FROM staff
            WHERE email = %s
            LIMIT 1
        """, (email,))

        existing = cursor.fetchone()

        if existing:
            return jsonify({"success": False, "message": "Email already exists"}), 400

        cursor.execute("""
            INSERT INTO staff
            (name, dob, position, email, phone, password, account_status, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending', 0)
        """, (name, dob, position, email, phone, hashed_password))

        db.commit()

        return jsonify({
            "success": True,
            "message": "Account created. Waiting for admin approval."
        })

    finally:
        cursor.close()
        db.close()

# Admin route to view pending accounts
@auth_bp.route("/pending-accounts")
def pending_accounts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT staff_id, name, dob, position, email, phone
        FROM staff
        WHERE account_status = 'Pending'
        ORDER BY staff_id DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(rows)

# Admin routes to approve or reject accounts
@auth_bp.route("/approve-account", methods=["POST"])
def approve_account():
    data = request.get_json()
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE staff
        SET account_status = 'Approved'
        WHERE staff_id = %s
    """, (staff_id,))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

# Admin route to reject accounts
@auth_bp.route("/reject-account", methods=["POST"])
def reject_account():
    data = request.get_json()
    staff_id = data.get("staff_id")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE staff
        SET account_status = 'Rejected'
        WHERE staff_id = %s
    """, (staff_id,))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})