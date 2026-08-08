"""Create generic demo accounts and availability for local portfolio testing."""

import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from db import get_db_connection  # noqa: E402


DEMO_USERS = [
    {
        "name": "Demo Admin",
        "dob": "1990-01-01",
        "position": "Admin",
        "email": "admin@example.com",
        "phone": "07000000001",
        "password": "AdminDemo1!",
        "is_admin": 1,
    },
    {
        "name": "Demo Manager",
        "dob": "1991-02-02",
        "position": "Manager",
        "email": "manager@example.com",
        "phone": "07000000002",
        "password": "ManagerDemo1!",
        "is_admin": 0,
    },
    {
        "name": "Demo Trainer",
        "dob": "1992-03-03",
        "position": "Crew Trainer",
        "email": "trainer@example.com",
        "phone": "07000000003",
        "password": "TrainerDemo1!",
        "is_admin": 0,
    },
    {
        "name": "Demo Crew Member",
        "dob": "1993-04-04",
        "position": "Crew Member",
        "email": "member@example.com",
        "phone": "07000000004",
        "password": "MemberDemo1!",
        "is_admin": 0,
    },
    {
        "name": "Demo Trainee",
        "dob": "2000-05-05",
        "position": "Trainee",
        "email": "trainee@example.com",
        "phone": "07000000005",
        "password": "TraineeDemo1!",
        "is_admin": 0,
    },
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def main():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        for user in DEMO_USERS:
            cursor.execute("SELECT staff_id FROM staff WHERE email = %s LIMIT 1", (user["email"],))
            existing = cursor.fetchone()

            if existing:
                staff_id = existing["staff_id"]
            else:
                cursor.execute(
                    """
                    INSERT INTO staff
                    (name, dob, position, email, phone, password, account_status, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Approved', %s)
                    """,
                    (
                        user["name"],
                        user["dob"],
                        user["position"],
                        user["email"],
                        user["phone"],
                        generate_password_hash(user["password"]),
                        user["is_admin"],
                    ),
                )
                staff_id = cursor.lastrowid

            cursor.execute("SELECT COUNT(*) AS total FROM availability WHERE staff_id = %s", (staff_id,))
            if cursor.fetchone()["total"] == 0:
                for day in DAYS:
                    cursor.execute(
                        """
                        INSERT INTO availability
                        (staff_id, day_of_week, is_available, start_time, end_time, is_all_day)
                        VALUES (%s, %s, 1, NULL, NULL, 1)
                        """,
                        (staff_id, day),
                    )

        db.commit()
    finally:
        cursor.close()
        db.close()

    print("Demo data created successfully.\n")
    print("Demo logins:")
    for user in DEMO_USERS:
        print(f"  {user['position']:<13} {user['email']:<24} {user['password']}")


if __name__ == "__main__":
    main()
