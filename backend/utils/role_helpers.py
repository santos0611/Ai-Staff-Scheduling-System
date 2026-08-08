# Utility functions for normalising staff roles and defining role coverage for shift assignment rules
def normalise_role(role):
    role = str(role or "").strip().lower()

    if role.startswith("manag"):
        return "manager"

    if role.startswith("crew train"):
        return "crew trainer"

    if role.startswith("crew mem"):
        return "crew member"

    if role.startswith("train"):
        return "trainee"

    return role


ROLE_COVERAGE = {
    "admin": ["manager", "crew trainer", "crew member", "trainee"],
    "manager": ["manager", "crew trainer", "crew member", "trainee"],
    "crew trainer": ["crew trainer", "crew member"],
    "crew member": ["crew member"],
    "trainee": ["trainee"]
}