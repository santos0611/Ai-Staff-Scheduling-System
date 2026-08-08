from services.shift_rules import (
    does_role_match,
    trainee_has_trainer_cover,
    is_staff_available_for_shift,
    has_shift_conflict,
    exceeds_daily_hours,
    exceeds_weekly_hours,
    violates_rest_period
)

from services.risk_service import (
    build_ai_risk_flags,
    get_risk_level
)

# Main function to assess the suitability of assigning a specific staff member to a specific shift, returning detailed feedback on any issues and risk factors
def assess_shift_assignment(cursor, staff_id, shift_date, shift_start, shift_end, required_role):
    hard_blockers = []
    soft_warnings = []

    role_ok, role_message = does_role_match(cursor, staff_id, required_role)
    if not role_ok:
        hard_blockers.append(role_message)

    trainee_ok, trainee_message = trainee_has_trainer_cover(
        cursor,
        staff_id,
        shift_date,
        shift_start,
        shift_end
    )
    if not trainee_ok:
        hard_blockers.append(trainee_message)

    cursor.execute("""
        SELECT time_off_id
        FROM time_off
        WHERE staff_id = %s
          AND status = 'Approved'
          AND %s BETWEEN start_date AND end_date
        LIMIT 1
    """, (staff_id, shift_date))

    if cursor.fetchone():
        hard_blockers.append("Staff member is on approved time off")

    available, availability_message = is_staff_available_for_shift(
        cursor,
        staff_id,
        shift_date,
        shift_start,
        shift_end
    )
    # If the staff member is not available for the shift, add a hard blocker with the reason why they are not available (e.g. unavailable due to unavailability, already working another shift, etc
    if not available:
        hard_blockers.append(availability_message)

    if has_shift_conflict(cursor, staff_id, shift_date, shift_start, shift_end):
        hard_blockers.append("Shift overlaps with an existing shift")

    if exceeds_daily_hours(cursor, staff_id, shift_date, shift_start, shift_end, 8):
        hard_blockers.append("Illegal daily hours limit exceeded")

    if exceeds_weekly_hours(cursor, staff_id, shift_date, shift_start, shift_end, 48):
        hard_blockers.append("Illegal weekly hours limit exceeded")

    if violates_rest_period(cursor, staff_id, shift_date, shift_start, shift_end, 11):
        hard_blockers.append("Illegal rest period violation")

    risk_data = build_ai_risk_flags(
        cursor,
        staff_id,
        shift_date,
        shift_start,
        shift_end,
        required_role
    )

    warning_flags = [
        "High weekly workload",
        "Moderate weekly workload",
        "Underutilised staff",
        "Tight turnaround between shifts",
        "No crew trainer currently scheduled",
        "Low manager coverage for day",
        "No manager scheduled for this day"
    ]

    for flag in risk_data["flags"]:
        if flag in warning_flags:
            soft_warnings.append(flag)

    final_risk_score = 100 if hard_blockers else risk_data["risk_score"]

    return {
        "allowed": len(hard_blockers) == 0,
        "hard_blockers": hard_blockers,
        "soft_warnings": soft_warnings,
        "risk_level": get_risk_level(final_risk_score),
        "risk_score": final_risk_score,
        "weekly_hours": risk_data["weekly_hours"],
        "daily_hours": risk_data["daily_hours"],
        "rest_gap_hours": risk_data["smallest_rest_gap"]
    }