let boardWeekStart = null;
let boardWeekEnd = null;
let boardStaff = [];
let boardShifts = [];
let boardAvailability = [];

let selectedBoardStaffId = null;
let selectedBoardStaffName = null;
let selectedBoardDate = null;

let currentWeeklyRiskSummary = null;
// Initialization function for the manager board, calculates the current week's Monday and Sunday dates and loads the board data for that week
function initManagerBoard() {
    const today = new Date();
    const day = today.getDay();
    const mondayOffset = day === 0 ? -6 : 1 - day;

    boardWeekStart = new Date(today);
    boardWeekStart.setDate(today.getDate() + mondayOffset);

    boardWeekEnd = new Date(boardWeekStart);
    boardWeekEnd.setDate(boardWeekStart.getDate() + 6);

    loadBoardData();
}
//week navigation functions, adjust the boardWeekStart and boardWeekEnd variables by 7 days forward or backward and then reload the board data for the new week
function changeBoardWeek(direction) {
    boardWeekStart.setDate(boardWeekStart.getDate() + (direction * 7));
    boardWeekEnd = new Date(boardWeekStart);
    boardWeekEnd.setDate(boardWeekStart.getDate() + 6);

    loadBoardData();
}
// Function to loadboard data
function loadBoardData() {
    const startDate = formatDate(boardWeekStart);
    const endDate = formatDate(boardWeekEnd);

    const label = document.getElementById("week-range-label");
    if (label) {
        label.textContent = `${startDate} to ${endDate}`;
    }

    Promise.all([
        fetch(`${API_BASE}/all-staff`).then(res => res.json()),
        fetch(`${API_BASE}/manager-week-shifts/${startDate}/${endDate}`).then(res => res.json()),
        fetch(`${API_BASE}/all-availability`).then(res => res.json())
    ])
    .then(([staffData, shiftData, availabilityData]) => {
        boardStaff = staffData;
        boardShifts = shiftData;
        boardAvailability = availabilityData;

        renderManagerBoard();
        loadWeeklyRiskSummary();
    })
    .catch(error => {
        console.error("Error loading manager board data:", error);
        const grid = document.getElementById("schedule-grid");
        if (grid) {
            grid.innerHTML = "<p>Could not load scheduling board.</p>";
        }
    });
}
//funtion to get the availability object for a specific staff member on a specific date, used when rendering the manager board to show availability status in cells without shifts
function getAvailabilityForStaff(staffId, date) {
    const jsDate = new Date(date);
    const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const dayOfWeek = dayNames[jsDate.getDay()];

    return boardAvailability.find(item =>
        String(item.staff_id) === String(staffId) &&
        item.day_of_week === dayOfWeek
    );
}
//function to get a numeric rank for a staff position, used for sorting staff on the manager board with managers at the top and trainees at the bottom
function getRoleRank(position) {
    const role = (position || "").toLowerCase();

    if (role === "manager") return 1;
    if (role === "crew member") return 2;
    if (role === "crew trainer") return 3;
    if (role === "trainee") return 4;

    return 5;
}
// Function to load the manager board data from the backend for the currently selected week and render the schedule grid, also called when changing weeks to update the board for the new week
function renderManagerBoard() {
    const grid = document.getElementById("schedule-grid");
    if (!grid) return;

    const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const weekDates = [];

    for (let i = 0; i < 7; i++) {
        const d = new Date(boardWeekStart);
        d.setDate(boardWeekStart.getDate() + i);
        weekDates.push(formatDate(d));
    }

    const sortedStaff = [...boardStaff].sort((a, b) => {
        const roleDiff = getRoleRank(a.position) - getRoleRank(b.position);
        if (roleDiff !== 0) return roleDiff;
        return a.name.localeCompare(b.name);
    });

    let html = "";

    html += `<div class="grid-header sticky-left">Employees</div>`;

    weekDates.forEach((date, index) => {
        html += `<div class="grid-header">${dayNames[index]}<br><small>${date}</small></div>`;
    });

    sortedStaff.forEach(staff => {
        html += `
            <div class="staff-name-cell sticky-left">
                ${staff.name}<br>
                <small>${staff.position}</small>
            </div>
        `;

        weekDates.forEach(date => {
            const shiftsForCell = boardShifts.filter(
                shift => String(shift.staff_id) === String(staff.staff_id) && shift.shift_date === date
            );

            const availabilityForDay = getAvailabilityForStaff(staff.staff_id, date);

            let cellHtml = `
                <div class="shift-cell"
                     onclick="selectBoardCell('${staff.staff_id}', '${staff.name.replace(/'/g, "\\'")}', '${date}', this)">
            `;

            if (shiftsForCell.length > 0) {
                shiftsForCell.forEach(shift => {
                    if (shift.is_time_off) {
                        cellHtml += `
                            <div class="holiday-block">
                                Holiday<br>
                                <small>${shift.required_role}</small>
                            </div>
                        `;
                    } else {
                        cellHtml += `
                            <div class="shift-block ${getAttendanceBlockClass(shift.attendance_status)} ${shift.is_open_shift ? "open-shift" : ""}">
                                ${shift.start_time || ""}${shift.end_time ? " - " + shift.end_time : ""}
                                <small>${shift.required_role || ""}</small>

                                ${renderAttendanceButtons(shift)}

                                ${
                                    shift.status === "Draft"
                                        ? `<button class="delete-shift-btn" onclick="event.stopPropagation(); deleteDraftShift(${shift.shift_id})">Delete</button>`
                                        : ""
                                }
                            </div>
                        `;
                    }
                });
            } else if (availabilityForDay) {
                if (Number(availabilityForDay.is_available) === 0) {
                    cellHtml += `<p class="unavailable-label">Unavailable</p>`;
                } else if (Number(availabilityForDay.is_all_day) === 1) {
                    cellHtml += `<p class="available-label">Available (All Day)</p>`;
                } else {
                    cellHtml += `
                        <p class="available-label">
                            ${availabilityForDay.start_time} - ${availabilityForDay.end_time}
                        </p>
                    `;
                }
            } else {
                cellHtml += `<p class="unknown-label">No availability set</p>`;
            }

            cellHtml += `<p class="add-shift-label">Click to add shift</p>`;
            cellHtml += `</div>`;

            html += cellHtml;
        });
    });

    grid.innerHTML = html;
}
// Helper function to select a board cell when clicked, stores the selected staff ID, name, and date in global variables and updates the selected cell styling and info box with the selected staff and date
function selectBoardCell(staffId, staffName, date, cellEl) {
    selectedBoardStaffId = staffId;
    selectedBoardStaffName = staffName;
    selectedBoardDate = date;

    document.querySelectorAll(".shift-cell").forEach(cell => {
        cell.classList.remove("selected-cell");
    });

    if (cellEl) {
        cellEl.classList.add("selected-cell");
    }

    const info = document.getElementById("selected-cell-info");
    if (info) {
        info.innerHTML = `
            <p><strong>Selected Staff:</strong> ${staffName}</p>
            <p><strong>Selected Date:</strong> ${date}</p>
        `;
    }
}
// Function to handle creating a new shift from the selected board cell, validates the form data and sends a POST request to the backend to create the shift, also checks if a cell is selected before allowing shift creation
function createShiftFromCell() {
    if (!selectedBoardStaffId || !selectedBoardDate) {
        alert("Select a board cell first.");
        return;
    }

    const startTime = document.getElementById("create-start-time").value;
    const endTime = document.getElementById("create-end-time").value;
    const requiredRole = document.getElementById("create-role").value;
    const isOpenShift = document.getElementById("create-open-shift").value;

    if (!startTime || !endTime) {
        alert("Enter start and end time.");
        return;
    }

    fetch(`${API_BASE}/create-shift-and-assign`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            staff_id: selectedBoardStaffId,
            shift_date: selectedBoardDate,
            start_time: startTime,
            end_time: endTime,
            required_role: requiredRole,
            is_open_shift: isOpenShift
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Shift created successfully");
            loadBoardData();
        } else {
            let errorMessage = data.message || "Could not create shift";

            if (data.hard_blockers && data.hard_blockers.length > 0) {
                errorMessage += "\n\nRules broken:\n- " + data.hard_blockers.join("\n- ");
            }

            if (data.soft_warnings && data.soft_warnings.length > 0) {
                errorMessage += "\n\nWarnings:\n- " + data.soft_warnings.join("\n- ");
            }

            alert(errorMessage);
        }
    })
    .catch(error => {
        console.error("Create shift error:", error);
    });
}
// Function to handle deleting a draft shift, sends a POST request to the backend to delete the shift and refreshes the board data on success
function deleteDraftShift(shiftId) {
    const confirmed = confirm("Delete this draft shift?");
    if (!confirmed) return;

    fetch(`${API_BASE}/delete-draft-shift`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            shift_id: shiftId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Draft shift deleted.");
            loadBoardData();
        } else {
            alert(data.message || "Could not delete draft shift.");
        }
    })
    .catch(error => {
        console.error("Delete draft shift error:", error);
        alert("Could not delete draft shift.");
    });
}
//
function publishCurrentWeek() {
    const startDate = formatDate(boardWeekStart);
    const endDate = formatDate(boardWeekEnd);

    fetch(`${API_BASE}/publish-week`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Week published successfully");
            loadBoardData();
        } else {
            alert(data.message || "Could not publish week");
        }
    })
    .catch(error => {
        console.error("Publish week error:", error);
    });
}
// Function to publish the currently selected week, sends a POST request to the backend to mark the week as published and refreshes the board data on success
function publishWeek() {
    publishCurrentWeek();
}
// Placeholder function for schedule generation, can be expanded to trigger backend schedule generation and display a loading state while waiting for the response
function generateSchedule() {
    alert("Schedule generation not set up yet.");
}
// Helper function to select a suggested staff member from the AI suggestions and populate the selected cell info with the staff member's name and selected date, also highlights the selected cell on the board
function suggestStaffForSelectedShift() {
    if (!selectedBoardDate) {
        alert("Select a board cell first.");
        return;
    }

    const startTime = document.getElementById("create-start-time").value;
    const endTime = document.getElementById("create-end-time").value;
    const requiredRole = document.getElementById("create-role").value;

    if (!startTime || !endTime || !requiredRole) {
        alert("Enter shift time and role first.");
        return;
    }

    fetch(`${API_BASE}/ai-suggest-staff`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            shift_date: selectedBoardDate,
            start_time: startTime,
            end_time: endTime,
            required_role: requiredRole
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("AI RESPONSE:", data);

        const box = document.getElementById("ai-suggestions");
        if (!box) return;

        if (!data.success || !data.suggestions || data.suggestions.length === 0) {
            box.innerHTML = "<p>No suitable staff suggestions found.</p>";
            return;
        }

        let html = "<h3>Suggested Staff</h3>";

        data.suggestions.forEach((staff, index) => {
            const flagsText = staff.risk_flags && staff.risk_flags.length
                ? staff.risk_flags.join(", ")
                : "No major risks";

            const reasonsText = staff.reasons && staff.reasons.length
                ? staff.reasons.join(", ")
                : "-";

            html += `
                <div class="suggestion-card">
                    <p><strong>${index + 1}. ${staff.name}</strong> (${staff.position})</p>
                    <p><strong>Score:</strong> ${staff.score}</p>
                    <p><strong>Risk Level:</strong> ${staff.risk_level}</p>
                    <p><strong>Weekly Hours:</strong> ${staff.weekly_hours}</p>
                    <p><strong>Daily Hours:</strong> ${staff.daily_hours}</p>
                    <p><strong>Closest Rest Gap:</strong> ${staff.rest_gap_hours ?? "N/A"} hours</p>
                    <p><strong>Reasons:</strong> ${reasonsText}</p>
                    <p><strong>Risk Flags:</strong> ${flagsText}</p>
                    <button onclick="selectSuggestedStaff(${staff.staff_id}, '${staff.name.replace(/'/g, "\\'")}')">
                        Use This Staff Member
                    </button>
                </div>
            `;
        });

        box.innerHTML = html;
    })
    .catch(error => {
        console.error("Suggestion error:", error);
        const box = document.getElementById("ai-suggestions");
        if (box) {
            box.innerHTML = "<p>Could not load staff suggestions.</p>";
        }
    });
}
function selectSuggestedStaff(staffId, staffName) {
    selectedBoardStaffId = staffId;
    selectedBoardStaffName = staffName;

    const info = document.getElementById("selected-cell-info");
    if (info) {
        info.innerHTML = `
            <p><strong>Selected Staff:</strong> ${staffName}</p>
            <p><strong>Selected Date:</strong> ${selectedBoardDate}</p>
        `;
    }

    alert(`${staffName} selected for this shift.`);
}
// Helper function to determine the Risk Severity based on the type and message of the risk, used to style risk detail cards in the weekly risk summary
function getRiskSeverity(type, message) {
    const text = `${type} ${message}`.toLowerCase();

    if (
        text.includes("illegal") ||
        text.includes("manager cover") ||
        text.includes("no manager") ||
        text.includes("trainee") ||
        text.includes("rest period") ||
        text.includes("maximum")
    ) {
        return "law-risk";
    }

    if (
        text.includes("unfilled") ||
        text.includes("no crew trainer") ||
        text.includes("coverage")
    ) {
        return "coverage-risk";
    }

    return "warning-risk";
}
// Function to load the weekly risk summary from the backend for the currently selected week and render it in the manager board sidebar, also called when changing weeks to update the summary for the new week
function loadWeeklyRiskSummary() {
    if (!boardWeekStart || !boardWeekEnd) return;

    const startDate = formatDate(boardWeekStart);
    const endDate = formatDate(boardWeekEnd);

    fetch(`${API_BASE}/weekly-risk-summary/${startDate}/${endDate}`)
        .then(response => response.json())
        .then(data => {
            const box = document.getElementById("weekly-risk-summary");
            if (!box) return;

            if (!data.success) {
                box.innerHTML = "<p>Could not load weekly risk summary.</p>";
                return;
            }

            currentWeeklyRiskSummary = data.summary;
            renderRiskSummaryCategory("Manager Cover");
        })
        .catch(error => {
            console.error("Weekly risk summary error:", error);
            const box = document.getElementById("weekly-risk-summary");
            if (box) {
                box.innerHTML = "<p>Could not load weekly risk summary.</p>";
            }
        });
}
// Function to render the weekly risk summary for a specific category, creates a grid of risk categories at the top and a list of specific risks in the selected category below
function renderRiskSummaryCategory(category) {
    const box = document.getElementById("weekly-risk-summary");
    if (!box || !currentWeeklyRiskSummary) return;

    const summary = currentWeeklyRiskSummary;

    const categoryMap = {
        "Fairness": {
            count: summary.fairness_risks,
            label: "Fairness Risks"
        },
        "Coverage": {
            count: summary.coverage_risks,
            label: "Coverage Risks"
        },
        "Fatigue": {
            count: summary.fatigue_risks,
            label: "Fatigue Risks"
        },
        "Unfilled Shift": {
            count: summary.unfilled_shifts,
            label: "Unfilled Shifts"
        },
        "Manager Cover": {
            count: summary.manager_cover_risks,
            label: "Manager Cover Risks"
        }
    };

    let html = `
        <h3>Weekly AI Risk Summary</h3>

        <div class="risk-summary-grid">
    `;

    Object.keys(categoryMap).forEach(key => {
        const activeClass = key === category ? "active-risk-tile" : "";
        html += `
            <button class="risk-tile ${activeClass}" onclick="renderRiskSummaryCategory('${key}')">
                <strong>${categoryMap[key].count}</strong>
                <span>${categoryMap[key].label}</span>
            </button>
        `;
    });

    html += `</div>`;

    const selectedDetails = (summary.details || []).filter(item => item.type === category);

    html += `
        <div class="risk-detail-list">
            <h4>${categoryMap[category].label}</h4>
    `;

    if (selectedDetails.length === 0) {
        html += `<p>No risks in this category.</p>`;
    } else {
        selectedDetails.forEach(item => {
            const severityClass = getRiskSeverity(item.type, item.message);

            html += `
                <div class="risk-detail-card ${severityClass}">
                    <p><strong>${item.type}</strong>${item.date ? ` - ${item.date}` : ""}</p>
                    <p>${item.message}</p>
                </div>
            `;
        });
    }

    html += `</div>`;

    box.innerHTML = html;
}