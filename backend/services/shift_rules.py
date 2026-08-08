from utils.time_helpers import (
    time_value_to_minutes,
    combine_date_and_time,
    get_day_name_from_date
)

from utils.role_helpers import normalise_role, ROLE_COVERAGE

# Importing staff availability functions
def is_staff_available_for_shift(cursor, staff_id, shift_date, shift_start, shift_end):
    day_name = get_day_name_from_date(shift_date)

    cursor.execute("""
        SELECT is_available, is_all_day, start_time, end_time
        FROM availability
        WHERE staff_id = %s
          AND day_of_week = %s
        LIMIT 1
    """, (staff_id, day_name))

    availability = cursor.fetchone()

    if not availability:
        return False, "No availability set for that day"

    if int(availability["is_available"]) == 0:
        return False, "Staff member is unavailable that day"

    if int(availability["is_all_day"]) == 1:
        return True, ""

    available_start = availability["start_time"]
    available_end = availability["end_time"]

    if available_start is None or available_end is None:
        return False, "Availability times are missing for that day"

    shift_start_minutes = time_value_to_minutes(shift_start)
    shift_end_minutes = time_value_to_minutes(shift_end)
    available_start_minutes = time_value_to_minutes(available_start)
    available_end_minutes = time_value_to_minutes(available_end)

    if shift_start_minutes < available_start_minutes or shift_end_minutes > available_end_minutes:
        return False, "Shift is outside staff availability hours"

    return True, ""

# Main function to validate conflict assignment rules, returning a list of hard blockers if any rules are violated
def has_shift_conflict(cursor, staff_id, shift_date, new_start, new_end):
    cursor.execute("""
        SELECT s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.shift_date = %s
          AND s.status IN ('Draft', 'Posted')
    """, (staff_id, shift_date))

    new_start_minutes = time_value_to_minutes(new_start)
    new_end_minutes = time_value_to_minutes(new_end)

    for shift in cursor.fetchall():
        existing_start = time_value_to_minutes(shift["start_time"])
        existing_end = time_value_to_minutes(shift["end_time"])

        if new_start_minutes < existing_end and new_end_minutes > existing_start:
            return True

    return False

# Function to check if a staff member exceeds maximum daily hours with a proposed shift, used for conflict validation
def exceeds_daily_hours(cursor, staff_id, shift_date, new_start, new_end, max_hours=8):
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

    total_minutes += time_value_to_minutes(new_end) - time_value_to_minutes(new_start)

    return total_minutes > (max_hours * 60)

# Function to check if a staff member exceeds maximum weekly hours with a proposed shift, used for conflict validation
def exceeds_weekly_hours(cursor, staff_id, shift_date, new_start, new_end, max_hours=48):
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

    total_minutes += time_value_to_minutes(new_end) - time_value_to_minutes(new_start)

    return total_minutes > (max_hours * 60)

# Function to check if a proposed shift violates minimum rest period requirements with a staff member's existing shifts, used for conflict validation
def violates_rest_period(cursor, staff_id, shift_date, new_start, new_end, min_rest_hours=11):
    cursor.execute("""
        SELECT s.shift_date, s.start_time, s.end_time
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        WHERE ss.staff_id = %s
          AND s.status IN ('Draft', 'Posted')
    """, (staff_id,))

    min_rest_minutes = min_rest_hours * 60
    new_start_dt = combine_date_and_time(shift_date, new_start)
    new_end_dt = combine_date_and_time(shift_date, new_end)

    for row in cursor.fetchall():
        existing_start_dt = combine_date_and_time(row["shift_date"], row["start_time"])
        existing_end_dt = combine_date_and_time(row["shift_date"], row["end_time"])

        gap_after_existing = (new_start_dt - existing_end_dt).total_seconds() / 60
        gap_before_existing = (existing_start_dt - new_end_dt).total_seconds() / 60

        if 0 < gap_after_existing < min_rest_minutes:
            return True

        if 0 < gap_before_existing < min_rest_minutes:
            return True

    return False

#
def does_role_match(cursor, staff_id, required_role):
    if not required_role:
        return True, ""

    cursor.execute("""
        SELECT position
        FROM staff
        WHERE staff_id = %s
        LIMIT 1
    """, (staff_id,))

    staff = cursor.fetchone()

    if not staff:
        return False, "Staff member not found"

    staff_role = normalise_role(staff["position"])
    shift_role = normalise_role(required_role)

    allowed_roles = ROLE_COVERAGE.get(staff_role, [staff_role])

    if shift_role not in allowed_roles:
        return False, f"Role mismatch: {staff['position']} cannot work a {required_role} shift"

    return True, ""

# Function to check if a trainee has trainer cover during their shift, used for conflict validation
def trainee_has_trainer_cover(cursor, staff_id, shift_date, shift_start, shift_end):
    cursor.execute("""
        SELECT position
        FROM staff
        WHERE staff_id = %s
        LIMIT 1
    """, (staff_id,))

    staff = cursor.fetchone()

    if not staff:
        return False, "Staff member not found"

    staff_role = normalise_role(staff["position"])

    if staff_role != "trainee":
        return True, ""

    cursor.execute("""
        SELECT s.start_time, s.end_time, st.position
        FROM staff_shifts ss
        JOIN shifts s ON ss.shift_id = s.shift_id
        JOIN staff st ON ss.staff_id = st.staff_id
        WHERE s.shift_date = %s
          AND s.status IN ('Draft', 'Posted')
    """, (shift_date,))

    shift_start_minutes = time_value_to_minutes(shift_start)
    shift_end_minutes = time_value_to_minutes(shift_end)

    for row in cursor.fetchall():
        existing_role = normalise_role(row["position"])
        existing_start = time_value_to_minutes(row["start_time"])
        existing_end = time_value_to_minutes(row["end_time"])

        overlaps = shift_start_minutes < existing_end and shift_end_minutes > existing_start

        if overlaps and existing_role == "crew trainer":
            return True, ""

    return False, "Trainees must be scheduled with a Crew Trainer on shift"

# Main function to validate all shift assignment rules and return a boolean indicating if the assignment is valid along with a message for any rule violation
def validate_shift_assignment_rules(cursor, staff_id, shift_date, shift_start, shift_end, required_role):
    role_ok, role_message = does_role_match(cursor, staff_id, required_role)

    if not role_ok:
        return False, role_message

    trainee_ok, trainee_message = trainee_has_trainer_cover(
        cursor,
        staff_id,
        shift_date,
        shift_start,
        shift_end
    )

    if not trainee_ok:
        return False, trainee_message

    cursor.execute("""
        SELECT time_off_id
        FROM time_off
        WHERE staff_id = %s
          AND status = 'Approved'
          AND %s BETWEEN start_date AND end_date
    """, (staff_id, shift_date))

    blocked = cursor.fetchone()

    if blocked:
        return False, "Staff member is on approved time off for that date"

    available, message = is_staff_available_for_shift(
        cursor,
        staff_id,
        shift_date,
        shift_start,
        shift_end
    )

    if not available:
        return False, message

    if has_shift_conflict(cursor, staff_id, shift_date, shift_start, shift_end):
        return False, "Shift overlaps with an existing shift"

    if exceeds_daily_hours(cursor, staff_id, shift_date, shift_start, shift_end, 8):
        return False, "Shift exceeds maximum daily hours"

    if exceeds_weekly_hours(cursor, staff_id, shift_date, shift_start, shift_end, 48):
        return False, "Shift exceeds maximum weekly hours"

    if violates_rest_period(cursor, staff_id, shift_date, shift_start, shift_end, 11):
        return False, "Shift violates minimum rest period"

    return True, ""

