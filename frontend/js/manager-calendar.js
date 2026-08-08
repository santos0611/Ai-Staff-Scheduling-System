let currentWeekStart = null;
let selectedDate = null;
let currentManagerShifts = [];
let currentFilter = "All";
// Global variables for the manager board
function initManagerCalendar() {
    const today = new Date();
    const day = today.getDay();
    const mondayOffset = day === 0 ? -6 : 1 - day;

    currentWeekStart = new Date(today);
    currentWeekStart.setDate(today.getDate() + mondayOffset);

    selectedDate = formatDate(currentWeekStart);

    renderWeekStrip();
    loadManagerDayShifts(selectedDate);
}
// Function to render the week strip at the top of the manager calendar page, shows the current week with clickable pills for each day to select that day and load its shifts, also updates the month label and selected date label
function changeWeek(direction) {
    currentWeekStart.setDate(currentWeekStart.getDate() + (direction * 7));
    selectedDate = formatDate(currentWeekStart);
    renderWeekStrip();
    loadManagerDayShifts(selectedDate);
}
//function to get status class for a shift based on its attendance status, used to color code shifts on the manager calendar
function getStatusClass(status) {
    if (!status) return "";

    const s = status.toLowerCase();
    if (s === "absent") return "status-absent";
    if (s === "sick") return "status-sick";

    return "";
}
// function get attendance status class for a shift based on its attendance status, used to color code attendance buttons on the manager calendar
function getAttendanceBlockClass(status) {
    const s = (status || "").toLowerCase();

    if (s === "present") return "shift-present";
    if (s === "sick") return "shift-sick";
    if (s === "absent") return "shift-absent";

    return "";
}
//function render attendance buttons for a shift on the manager calendar, highlights the button for the current attendance status and allows the manager to click to change the attendance status for that shift, sends a request to the backend to update the attendance status when clicked
function renderAttendanceButtons(shift) {
    const status = (shift.attendance_status || "Scheduled").toLowerCase();

    return `
        <div class="attendance-actions">
            <button class="${status === "present" ? "active-present" : ""}"
                onclick="markAttendance('${shift.staff_shift_id}', 'Present', event)">
                Present
            </button>

            <button class="${status === "absent" ? "active-absent" : ""}"
                onclick="markAttendance('${shift.staff_shift_id}', 'Absent', event)">
                Absent
            </button>

            <button class="${status === "sick" ? "active-sick" : ""}"
                onclick="markAttendance('${shift.staff_shift_id}', 'Sick', event)">
                Sick
            </button>
        </div>
    `;
}
function renderWeekStrip() {
    const weekStrip = document.getElementById("week-strip");
    const monthLabel = document.getElementById("month-label");
    const selectedDateLabel = document.getElementById("selected-date-label");

    if (!weekStrip) return;

    weekStrip.innerHTML = "";

    const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

    if (monthLabel) {
        monthLabel.textContent = `${monthNames[currentWeekStart.getMonth()]} ${currentWeekStart.getFullYear()}`;
    }

    for (let i = 0; i < 7; i++) {
        const date = new Date(currentWeekStart);
        date.setDate(currentWeekStart.getDate() + i);

        const isoDate = formatDate(date);
        const dayName = dayNames[date.getDay()];
        const dateNum = date.getDate();

        const pill = document.createElement("div");
        pill.className = "day-pill" + (isoDate === selectedDate ? " active" : "");
        pill.innerHTML = `
            <div>${dayName}</div>
            <div>${dateNum}</div>
        `;
        pill.onclick = function() {
            selectedDate = isoDate;
            renderWeekStrip();
            loadManagerDayShifts(selectedDate);
        };

        weekStrip.appendChild(pill);
    }

    if (selectedDateLabel) {
        const selected = new Date(selectedDate);
        selectedDateLabel.textContent = selected.toLocaleDateString("en-GB", {
            weekday: "short",
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    }
}
// Function to load the shifts for the selected day on the manager calendar from the backend, updates the currentManagerShifts variable and calls the function to render the shift list, also updates the filter counts for that day
function loadManagerDayShifts(date) {
    fetch(`${API_BASE}/manager-day-shifts/${date}`)
        .then(response => response.json())
        .then(data => {
            currentManagerShifts = data;
            updateFilterCounts(data);
            renderManagerShiftList(data);
        })
        .catch(error => {
            console.error("Error loading manager day shifts:", error);
            const container = document.getElementById("manager-shift-list");
            if (container) {
                container.innerHTML = "<p class='empty-message'>Could not load shifts.</p>";
            }
        });
}
// Function to render the list of shifts for the selected day on the manager calendar, applies filters based on attendance status and shows an appropriate message if there are no shifts for that day
function renderManagerShiftList(shifts) {
    const container = document.getElementById("manager-shift-list");
    if (!container) return;

    let filtered = shifts;

    if (currentFilter !== "All") {
        filtered = shifts.filter(shift => {
            let displayStatus =
                shift.attendance_status && shift.attendance_status !== "Scheduled"
                    ? shift.attendance_status
                    : shift.status;

            if ((displayStatus || "").toLowerCase() === "sick") {
                displayStatus = "Absent";
            }

            return (displayStatus || "").toLowerCase() === currentFilter.toLowerCase();
        });
    }

    if (filtered.length === 0) {
        container.innerHTML = "<p class='empty-message'>No shifts for this date.</p>";
        return;
    }

    let html = "";

    filtered.forEach(shift => {
        const timeText =
            shift.is_time_off
                ? "Approved time off"
                : `${shift.start_time || ""}${shift.end_time ? " - " + shift.end_time : ""}`;

        const roleText =
            shift.is_time_off
                ? shift.required_role || "Holiday"
                : shift.required_role || "";

        html += `
            <div class="shift-row">
                <div class="shift-left">
                    <div class="avatar-circle">${shift.initials}</div>

                    <div class="shift-info">
                        <p class="staff-name">${shift.name}</p>
                        <p>${timeText}</p>
                        <p class="shift-role">${roleText}</p>
                    </div>
                </div>

                <div>
                    ${!shift.is_time_off ? renderAttendanceButtons(shift) : ""}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function updateFilterCounts(shifts) {
    const getDisplayStatus = (shift) => {
        let status = shift.attendance_status && shift.attendance_status !== "Scheduled"
            ? shift.attendance_status
            : shift.status;

        if ((status || "").toLowerCase() === "sick") {
            status = "Absent";
        }

        return status;
    };

    const all = shifts.length;
    const absent = shifts.filter(s => (getDisplayStatus(s) || "").toLowerCase() === "absent").length;
    const accepted = shifts.filter(s => (getDisplayStatus(s) || "").toLowerCase() === "accepted").length;
    const pending = shifts.filter(s => (getDisplayStatus(s) || "").toLowerCase() === "pending").length;

    const allEl = document.getElementById("count-all");
    const absentEl = document.getElementById("count-absent");
    const acceptedEl = document.getElementById("count-accepted");
    const pendingEl = document.getElementById("count-pending");

    if (allEl) allEl.textContent = all;
    if (absentEl) absentEl.textContent = absent;
    if (acceptedEl) acceptedEl.textContent = accepted;
    if (pendingEl) pendingEl.textContent = pending;
}

function setFilter(filterName, buttonEl) {
    currentFilter = filterName;

    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    if (buttonEl) buttonEl.classList.add("active");

    renderManagerShiftList(currentManagerShifts);
}

async function markAttendance(staffShiftId, status, event) {
    if (event) event.stopPropagation();

    if (!staffShiftId || String(staffShiftId).startsWith("timeoff-")) {
        alert("Invalid shift record.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/mark-attendance`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                staff_shift_id: staffShiftId,
                attendance_status: status
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            alert(data.message || "Error updating attendance");
            return;
        }

        if (document.getElementById("manager-shift-list") && selectedDate) {
            loadManagerDayShifts(selectedDate);
            return;
        }

        if (document.getElementById("schedule-grid") && typeof boardWeekStart !== "undefined" && boardWeekStart) {
            loadBoardData();
            return;
        }

    } catch (error) {
        console.error("Attendance update error:", error);
        alert("Error updating attendance");
    }
}