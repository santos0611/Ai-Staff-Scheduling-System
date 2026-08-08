from flask import Blueprint, jsonify, request
from datetime import datetime

from db import get_db_connection

from utils.role_helpers import normalise_role
# Importing shift rules and risk service functions
from services.shift_rules import (
    validate_shift_assignment_rules,
    does_role_match,
    has_shift_conflict,
    exceeds_daily_hours,
    exceeds_weekly_hours,
    violates_rest_period
)
# Risk service functions to calculate risk flags and levels for AI suggestions
from services.risk_service import (
    build_ai_risk_flags,
    get_risk_level
)


ai_bp = Blueprint("ai", __name__)

# Route to suggest staff for a shift based on AI analysis of rules and risk factors
@ai_bp.route("/ai-suggest-staff", methods=["POST"])
def ai_suggest_staff():
    data = request.get_json()

    shift_date = data.get("shift_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    required_role = normalise_role(data.get("required_role"))

    if not shift_date or not start_time or not end_time:
        return jsonify({
            "success": False,
            "message": "Missing data"
        })

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        shift_date_obj = datetime.strptime(shift_date, "%Y-%m-%d").date()
        start_obj = datetime.strptime(start_time, "%H:%M").time()
        end_obj = datetime.strptime(end_time, "%H:%M").time()

        cursor.execute("""
            SELECT staff_id, name, position
            FROM staff
            ORDER BY name
        """)
        staff_list = cursor.fetchall()

        suggestions = []

        for staff in staff_list:
            staff_id = staff["staff_id"]

            allowed, message = validate_shift_assignment_rules(
                cursor,
                staff_id,
                shift_date_obj,
                start_obj,
                end_obj,
                required_role
            )

            risk_data = build_ai_risk_flags(
                cursor,
                staff_id,
                shift_date_obj,
                start_obj,
                end_obj,
                required_role
            )


            score = 0 # Base score that will be adjusted based on rules and risk factors
            reasons = []

            if allowed:
                score += 50
                reasons.append("Eligible for shift")
            else:
                risk_data["risk_score"] = 100
                risk_data["flags"].insert(0, message)
                reasons.append(message)

            role_ok, role_message = does_role_match(cursor, staff_id, required_role)

            if role_ok:
                score += 20
                reasons.append("Role match")
            else:
                reasons.append(role_message)

            if not has_shift_conflict(cursor, staff_id, shift_date_obj, start_obj, end_obj):
                score += 10
                reasons.append("No conflict")

            if not exceeds_daily_hours(cursor, staff_id, shift_date_obj, start_obj, end_obj):
                score += 10
                reasons.append("Within daily hours")

            if not exceeds_weekly_hours(cursor, staff_id, shift_date_obj, start_obj, end_obj):
                score += 10
                reasons.append("Within weekly hours")

            if not violates_rest_period(cursor, staff_id, shift_date_obj, start_obj, end_obj):
                score += 10
                reasons.append("Rest rule satisfied")

            score += risk_data["fairness_score"]

            if not allowed:
                score = 0
                
                # If not allowed, we set risk score to max to push them to the bottom of suggestions
            suggestions.append({
                "staff_id": staff_id,
                "name": staff["name"],
                "position": staff["position"],
                "score": score,
                "allowed": allowed,
                "risk_level": get_risk_level(risk_data["risk_score"]),
                "risk_score": risk_data["risk_score"],
                "risk_flags": risk_data["flags"],
                "weekly_hours": risk_data["weekly_hours"],
                "daily_hours": risk_data["daily_hours"],
                "rest_gap_hours": risk_data["smallest_rest_gap"],
                "reasons": reasons
            })

        suggestions.sort(key=lambda x: (
            not x["allowed"],
            x["risk_score"],
            -x["score"],
            x["weekly_hours"]
        ))

        return jsonify({
            "success": True,
            "suggestions": suggestions[:5]
        })

    except Exception as e:
        print("AI ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Server error"
        })

    finally:
        cursor.close()
        db.close()