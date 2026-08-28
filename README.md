# AI Staff Scheduling & Decision Support System

A web-based workforce scheduling application built with **Python, Flask, MySQL and JavaScript**. The system combines rota management with a transparent, rule-based AI decision-support engine that evaluates staff suitability, scheduling constraints, workload and operational risk before recommending assignments.

This repository is a cleaned portfolio version configured to run locally. It contains no personal assessment data, database passwords, virtual environments or private test records.

## Key Features

### Workforce Scheduling

- Create and manage weekly staff rotas
- Assign staff to shifts
- Draft and publish shifts
- View staff and manager calendars
- Open-shift and pickup workflows
- Shift drop requests
- Attendance tracking
- Staff availability management
- Time-off request and approval workflow
- Account registration and admin approval

### AI Decision Support

The recommendation engine evaluates proposed staff assignments against scheduling rules and ranks suitable employees.

Hard constraints include:

- Staff availability
- Approved time off
- Role compatibility
- Overlapping shifts
- Maximum **8 working hours per day**
- Maximum **48 working hours per week**
- Minimum **11-hour rest period**
- Trainee supervision by a Crew Trainer
- Open-shift timing rules

The decision-support layer also considers workload and fairness signals and returns explanations for recommendations rather than operating as a black-box scheduler.

### Risk & Fairness Analysis

The system can surface scheduling risks such as:

- High or moderate weekly workload
- Underutilised staff
- Tight turnaround between shifts
- Missing trainer cover
- Low manager coverage

This allows the manager to make the final scheduling decision while receiving structured decision support.

## Screenshots

### AI Staff Recommendations
![AI staff recommendations]<img width="1852" height="886" alt="Screenshot 2026-05-07 015755" src="https://github.com/user-attachments/assets/83e12b31-9488-4f5e-ab5f-46e918724935" /><img width="453" height="705" alt="Screenshot 2026-04-29 162653" src="https://github.com/user-attachments/assets/c8b9fd4c-4279-4b81-90e5-6fa580f9dbb5" />



### Weekly Rota
![Weekly rota]<img width="1577" height="829" alt="Screenshot 2026-05-07 015927" src="https://github.com/user-attachments/assets/f7af5e99-7d39-4f8c-9d7d-db6261dfcf8f" />


### Calendar
![Calendar].<img width="1698" height="915" alt="Screenshot 2026-05-07 011112" src="https://github.com/user-attachments/assets/e6c345cf-0f7f-4ae8-abe3-d815b325b421" />



### Staff Availability
![Staff availability]<img width="848" height="613" alt="Screenshot 2026-04-26 004419" src="https://github.com/user-attachments/assets/491546bb-0390-469e-abcc-75e229589598" />


## Technology Stack

**Backend**
- Python
- Flask
- Flask-CORS
- Werkzeug password hashing

**Frontend**
- HTML5
- CSS3
- JavaScript
- FullCalendar

**Database**
- MySQL
- `mysql-connector-python`

**Architecture / Design**
- Flask Blueprints
- Modular route, service and utility layers
- Rule-based decision-support logic
- Environment-variable configuration
- Parameterised SQL queries

## Project Structure

```text
ai-staff-scheduling-system/
├── backend/
│   ├── routes/
│   │   ├── ai_routes.py
│   │   ├── auth_routes.py
│   │   ├── availability_routes.py
│   │   ├── notification_routes.py
│   │   ├── shift_routes.py
│   │   ├── staff_routes.py
│   │   └── timeoff_routes.py
│   ├── services/
│   │   ├── assessment_service.py
│   │   ├── risk_service.py
│   │   └── shift_rules.py
│   ├── utils/
│   ├── app.py
│   └── db.py
├── frontend/
│   ├── css/
│   ├── images/
│   ├── js/
│   └── pages/
├── database/
│   └── schema.sql
├── scripts/
│   └── seed_demo.py
├── screenshots/
├── .env.example
├── .gitignore
├── requirements.txt
├── setup_windows.bat
├── seed_demo.bat
└── run_local.bat
```

# Running Locally

## Requirements

You will need:

- **Python 3.10+**
- **MySQL 8+**
- MySQL Workbench or another way to execute a `.sql` file
- A modern web browser

## Windows Quick Setup

### 1. Create the Python environment

Double-click:

```text
setup_windows.bat
```

This will:

- Create `.venv`
- Install the required Python packages
- Create `.env` from `.env.example` if one does not already exist

### 2. Configure MySQL

Open the generated `.env` file and enter your local MySQL credentials:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=staff_rota
HOST=127.0.0.1
PORT=5000
FLASK_DEBUG=false
```

**Never commit your real `.env` file to GitHub.** It is already excluded by `.gitignore`.

### 3. Create the database

Open MySQL Workbench and run:

```text
database/schema.sql
```

The script creates the `staff_rota` database and all required tables without importing personal or historical test data.

### 4. Add generic demo accounts

Double-click:

```text
seed_demo.bat
```

This creates generic portfolio demo users with all-day availability.

### 5. Start the application

Double-click:

```text
run_local.bat
```

The application will be available at:

```text
http://127.0.0.1:5000
```

The Flask application serves both the API and frontend locally, so a separate frontend web server is not required.

## Demo Accounts

The demo seeding script creates the following local-only accounts:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `AdminDemo1!` |
| Manager | `manager@example.com` | `ManagerDemo1!` |
| Crew Trainer | `trainer@example.com` | `TrainerDemo1!` |
| Crew Member | `member@example.com` | `MemberDemo1!` |
| Trainee | `trainee@example.com` | `TraineeDemo1!` |

These credentials are intentionally generic demonstration data and are generated only in your local database when the seed script is run.

# Manual Setup

If you prefer not to use the Windows scripts:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment template:

```bash
copy .env.example .env
```

After configuring `.env` and importing `database/schema.sql`, seed the demo data:

```bash
python scripts/seed_demo.py
```

Run the application:

```bash
python backend/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Security & Portfolio Cleanup

This public version has been prepared with the following safeguards:

- Database passwords removed from source code
- Local configuration moved to `.env`
- `.env` excluded from Git
- Virtual environment removed and ignored
- Python cache files removed and ignored
- Personal/test database records removed
- Original full database dump excluded
- Academic submission documents excluded
- Passwords created by the demo seeder are hashed with Werkzeug
- SQL queries use parameterised values throughout the application code

## Design Approach

The AI component acts as **decision support rather than autonomous scheduling**. Managers remain responsible for the final rota while the system provides recommendations, blockers, workload information and explanatory reasons.

This design prioritises:

- Transparency
- Human oversight
- Scheduling compliance
- Fairness awareness
- Practical usability

## Future Improvements

Potential future development includes:

- Copying a previous rota with automatic rule revalidation
- Drag-and-drop shift editing and swapping
- More advanced fairness metrics
- Machine-learning-assisted absence prediction
- Manager override reason capture
- Real-time notifications
- Mobile optimisation
- Configurable hard and soft scheduling rules
- Enhanced analytics and reporting

## Author

**Sergio Camara**

Computer Science / Computational Systems graduate portfolio project.
