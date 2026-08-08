import re
from datetime import datetime
from flask import jsonify

from utils.role_helpers import normalise_role

# Utility functions for validating input data for API routes, including date and time formats, role validation, and text cleaning, used across multiple route modules to ensure consistent validation logic
ALLOWED_ROLES = {"manager", "crew trainer", "crew member", "trainee"}
ALLOWED_SHIFT_STATUSES = {"Draft", "Posted"}
ALLOWED_TIME_OFF_TYPES = {
    "Holiday",
    "Sickness",
    "Unpaid Leave",
    "Emergency Leave",
    "Other"
}
ALLOWED_DAYS = {
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")

# Function to check if a staff member's role matches the required role for a shift, used for shift assignment validation
def api_error(message, status=400):
    return jsonify({
        "success": False,
        "message": message
    }), status

# Function to safely convert a value to an integer, used for validating numeric input fields
def safe_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")


def validate_date(value, field_name="date"):
    if not value or not DATE_RE.match(str(value)):
        raise ValueError(f"Invalid {field_name}")

    return datetime.strptime(value, "%Y-%m-%d").date()

# Function to convert various time value formats to total minutes, used for time calculations in shift validation and risk flag calculations
def validate_time(value, field_name="time"):
    if not value or not TIME_RE.match(str(value)):
        raise ValueError(f"Invalid {field_name}")

    return datetime.strptime(value, "%H:%M").time()

# Function to check if a staff member's role matches the required role for a shift, used for shift assignment validation
def validate_role(role):
    if not role:
        raise ValueError("Required role is missing")

    clean_role = normalise_role(role)

    if clean_role not in ALLOWED_ROLES:
        raise ValueError("Invalid role")

    return clean_role

#
def clean_text(value, max_length=255):
    if value is None:
        return ""

    value = str(value).strip()

    if len(value) > max_length:
        value = value[:max_length]

    return value