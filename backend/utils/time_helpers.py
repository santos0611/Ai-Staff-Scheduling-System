from datetime import datetime, timedelta

# Utility functions for handling time values in various formats and performing date calculations, used across multiple modules for shift validation and risk flag calculations
def time_value_to_minutes(value):
    if value is None:
        return 0

    if isinstance(value, timedelta):
        return int(value.total_seconds() // 60)

    if isinstance(value, datetime):
        return value.hour * 60 + value.minute

    if hasattr(value, "hour") and hasattr(value, "minute"):
        return value.hour * 60 + value.minute

    if isinstance(value, str):
        parts = value.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    raise TypeError(f"Unsupported time value type: {type(value)}")

# Function to convert various time value formats to a standard time object, used for consistent time handling across modules
def time_value_to_time(value):
    if value is None:
        return None

    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return datetime.strptime(
            f"{hours:02}:{minutes:02}:{seconds:02}",
            "%H:%M:%S"
        ).time()

    if isinstance(value, datetime):
        return value.time()

    if hasattr(value, "hour") and hasattr(value, "minute"):
        return value

    if isinstance(value, str):
        value = value.strip()
        if len(value) >= 8:
            return datetime.strptime(value[:8], "%H:%M:%S").time()
        return datetime.strptime(value[:5], "%H:%M").time()

    raise TypeError(f"Unsupported time value type: {type(value)}")

# Function to combine a date and time value into a single datetime object, used for calculating rest gaps and shift overlaps
def combine_date_and_time(date_value, time_value):
    safe_time = time_value_to_time(time_value)
    return datetime.combine(date_value, safe_time)

#'Function to generate a range of dates between two given dates, used for iterating over date ranges in risk flag calculations
def daterange(start_date, end_date):
    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)

# Function to get the day name (e.g. Monday, Tuesday) from a date value, used for display purposes and potential day-based rules
def get_day_name_from_date(date_value):
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()

    return date_value.strftime("%A")