from datetime import datetime
from utils.role_helpers import normalise_role

from utils.time_helpers import (
    time_value_to_minutes,
    combine_date_and_time,
    daterange
)

from utils.role_helpers import normalise_role
# Importing shift rules functions to check for rule violations
def get_staff_weekly_hours(cursor, staff_id, shift_date):
    from datetime import timedelta

    week_start = shift_date - timedelta(days=shift_date.weekday())
    week_end = week_start + timedelta(days=6)

    cursor.execute("""
        SELECT s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.shift_date BETWEEN %s AND %s
          AND s.status IN ('Draft', 'Posted')
    """, (staff_id, week_start, week_end))

    total_minutes = 0

    for row in cursor.fetchall():
        total_minutes += (
            time_value_to_minutes(row["end_time"]) -
            time_value_to_minutes(row["start_time"])
        )

    return round(total_minutes / 60, 2)

# Similar function to calculate total hours for a staff member on a specific day, used for risk flag calculations
def get_staff_daily_hours(cursor, staff_id, shift_date):
    cursor.execute("""
        SELECT s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.shift_date = %s
          AND s.status IN ('Draft', 'Posted')
    """, (staff_id, shift_date))

    total_minutes = 0

    for row in cursor.fetchall():
        total_minutes += (
            time_value_to_minutes(row["end_time"]) -
            time_value_to_minutes(row["start_time"])
        )

    return round(total_minutes / 60, 2)

# Function to calculate the smallest rest gap in hours between a proposed shift and a staff member's existing shifts on the same day, used for risk flag calculations
def get_smallest_rest_gap_hours(cursor, staff_id, shift_date, new_start, new_end):
    cursor.execute("""
        SELECT s.shift_date, s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.status IN ('Draft', 'Posted')
    """, (staff_id,))

    new_start_dt = combine_date_and_time(shift_date, new_start)
    new_end_dt = combine_date_and_time(shift_date, new_end)

    smallest_gap_hours = None

    for row in cursor.fetchall():
        existing_start_dt = combine_date_and_time(
            row["shift_date"],
            row["start_time"]
        )
        existing_end_dt = combine_date_and_time(
            row["shift_date"],
            row["end_time"]
        )

        gap_after_existing = (new_start_dt - existing_end_dt).total_seconds() / 3600
        gap_before_existing = (existing_start_dt - new_end_dt).total_seconds() / 3600

        if gap_after_existing > 0:
            if smallest_gap_hours is None or gap_after_existing < smallest_gap_hours:
                smallest_gap_hours = gap_after_existing

        if gap_before_existing > 0:
            if smallest_gap_hours is None or gap_before_existing < smallest_gap_hours:
                smallest_gap_hours = gap_before_existing

    return smallest_gap_hours

# Function to get the count of staff members scheduled for each role on a specific day, used for risk flag calculations
def get_day_skill_coverage(cursor, shift_date):
    cursor.execute("""
        SELECT LOWER(st.position) AS role_name, COUNT(*) AS count_value
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        JOIN staff st ON ss.staff_id = st.staff_id
        WHERE s.shift_date = %s
          AND s.status IN ('Draft', 'Posted')
        GROUP BY LOWER(st.position)
    """, (shift_date,))

    coverage = {
        "manager": 0,
        "crew trainer": 0,
        "crew member": 0,
        "trainee": 0
    }

    for row in cursor.fetchall():
        role_name = normalise_role(row["role_name"])

        if role_name in coverage:
            coverage[role_name] = row["count_value"]

    return coverage

# Function to check if a specific day has full manager coverage from 6am to 10pm, used for risk flag calculations
def day_has_full_manager_cover(cursor, day_date):
    required_start_minutes = 6 * 60
    required_end_minutes = 22 * 60

    cursor.execute("""
        SELECT s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        JOIN staff st ON ss.staff_id = st.staff_id
        WHERE s.shift_date = %s
          AND s.status IN ('Draft', 'Posted')
          AND LOWER(st.position) = 'manager'
        ORDER BY s.start_time
    """, (day_date,))

    manager_shifts = cursor.fetchall()

    if not manager_shifts:
        return False

    current_cover = required_start_minutes

    for row in manager_shifts:
        shift_start = time_value_to_minutes(row["start_time"])
        shift_end = time_value_to_minutes(row["end_time"])

        if shift_end <= current_cover:
            continue

        if shift_start > current_cover:
            return False

        if shift_start <= current_cover and shift_end > current_cover:
            current_cover = shift_end

        if current_cover >= required_end_minutes:
            return True

    return current_cover >= required_end_minutes

# Function to check if a week has full manager coverage, used for risk flag calculations
def week_has_manager_cover(cursor, start_date, end_date):
    start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    for single_day in daterange(start_obj, end_obj):
        if not day_has_full_manager_cover(cursor, single_day):
            return False, str(single_day)

    return True, ""

# Main function to build a list of risk flags and calculate a risk score for assigning a specific staff member to a specific shift, based on various factors such as weekly hours, rest gaps, and coverage of required roles
def build_ai_risk_flags(cursor, staff_id, shift_date, shift_start, shift_end, required_role):
    flags = []
    risk_score = 0
    fairness_score = 0

    weekly_hours = get_staff_weekly_hours(cursor, staff_id, shift_date)
    daily_hours = get_staff_daily_hours(cursor, staff_id, shift_date)
    smallest_rest_gap = get_smallest_rest_gap_hours(
        cursor, staff_id, shift_date, shift_start, shift_end
    )
    coverage = get_day_skill_coverage(cursor, shift_date)

    required_role_lower = normalise_role(required_role)

    if weekly_hours > 40:
        flags.append("High weekly workload")
        risk_score += 30
    elif weekly_hours > 30:
        flags.append("Moderate weekly workload")
        risk_score += 15

    if weekly_hours < 10:
        flags.append("Underutilised staff")
        fairness_score += 20
    elif weekly_hours < 20:
        fairness_score += 10

    if smallest_rest_gap is not None and smallest_rest_gap < 13:
        flags.append("Tight turnaround between shifts")
        risk_score += 15

    if required_role_lower != "manager":
        if coverage["manager"] == 0:
            flags.append("No manager scheduled for this day")
            risk_score += 40
        elif coverage["manager"] <= 1:
            flags.append("Low manager coverage for day")
            risk_score += 20

    if required_role_lower != "crew trainer":
        if coverage["crew trainer"] == 0:
            flags.append("No crew trainer currently scheduled")
            risk_score += 20

    return {
        "flags": flags,
        "risk_score": risk_score,
        "fairness_score": fairness_score,
        "weekly_hours": weekly_hours,
        "daily_hours": daily_hours,
        "smallest_rest_gap": round(smallest_rest_gap, 2) if smallest_rest_gap is not None else None
    }

# Helper function to convert a risk score into a risk level category (e.g. LOW, MEDIUM, HIGH) for easier interpretation of results
def get_risk_level(risk_score):
    if risk_score >= 50:
        return "HIGH"
    if risk_score >= 20:
        return "MEDIUM"
    return "LOW"