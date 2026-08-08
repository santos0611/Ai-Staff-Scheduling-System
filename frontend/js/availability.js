let originalAvailabilitySnapshot = "";

// Function to load the staff member's current availability from the backend and render it in the form, also creates a summary box at the top showing the current availability status for each day of the week
function loadAvailability(staffId) {
    fetch(`${API_BASE}/availability/${staffId}`)
        .then(response => response.json())
        .then(data => {
            const form = document.getElementById("availability-form");
            if (!form) return;

            const days = [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"
            ];

            const availabilityMap = {};
            data.forEach(item => {
                availabilityMap[item.day_of_week] = item;
            });

            let html = "";
            let summaryHtml = "";

            days.forEach(day => {
                const item = availabilityMap[day] || {
                    day_of_week: day,
                    is_available: 1,
                    is_all_day: 0,
                    start_time: "",
                    end_time: ""
                };

                let statusClass = "status-partial";
                let statusText = "";

                if (Number(item.is_available) === 0) {
                    statusClass = "status-unavailable";
                    statusText = `${day}: Unavailable`;
                } else if (Number(item.is_all_day) === 1) {
                    statusClass = "status-available";
                    statusText = `${day}: Available All Day`;
                } else {
                    statusClass = "status-partial";
                    statusText = `${day}: Available ${item.start_time || "--:--"} to ${item.end_time || "--:--"}`;
                }

                summaryHtml += `
                    <div class="current-day-status ${statusClass}">
                        ${statusText}
                    </div>
                `;

                html += `
                    <div class="availability-row">
                        <div class="day-name">${day}</div>

                        <select id="available-${day}" onchange="toggleAvailabilityRow('${day}')">
                            <option value="1" ${Number(item.is_available) === 1 ? "selected" : ""}>Available</option>
                            <option value="0" ${Number(item.is_available) === 0 ? "selected" : ""}>Unavailable</option>
                        </select>

                        <label class="all-day-field">
                            <input type="checkbox" id="allday-${day}"
                                ${Number(item.is_all_day) === 1 ? "checked" : ""}
                                onchange="toggleAllDay('${day}')">
                            All Day
                        </label>

                        <div class="time-field">
                            <label for="start-${day}">Start</label>
                            <input type="time" id="start-${day}" value="${item.start_time || ""}">
                        </div>

                        <div class="time-field">
                            <label for="end-${day}">End</label>
                            <input type="time" id="end-${day}" value="${item.end_time || ""}">
                        </div>
                    </div>
                `;
            });

            form.innerHTML = html;

            const summaryBox = document.getElementById("current-availability-summary");
            if (summaryBox) {
                summaryBox.innerHTML = summaryHtml;
            }

            days.forEach(day => {
                toggleAvailabilityRow(day);
            });

            originalAvailabilitySnapshot = JSON.stringify(getAvailabilityPayloadFromForm());
        })
        .catch(error => {
            console.error("Error loading availability:", error);
            const form = document.getElementById("availability-form");
            if (form) {
                form.innerHTML = "<p>Could not load availability.</p>";
            }
        });
}
// Function to handle changes to the availability dropdown for each day, enables/disables the all day checkbox and time inputs based on the selected availability status
function toggleAvailabilityRow(day) {
    const available = document.getElementById(`available-${day}`);
    const allDay = document.getElementById(`allday-${day}`);
    const startInput = document.getElementById(`start-${day}`);
    const endInput = document.getElementById(`end-${day}`);

    if (!available || !allDay || !startInput || !endInput) return;

    if (available.value === "0") {
        allDay.disabled = true;
        allDay.checked = false;
        startInput.disabled = true;
        endInput.disabled = true;
        startInput.value = "";
        endInput.value = "";
    } else {
        allDay.disabled = false;

        if (allDay.checked) {
            startInput.disabled = true;
            endInput.disabled = true;
            startInput.value = "";
            endInput.value = "";
        } else {
            startInput.disabled = false;
            endInput.disabled = false;
        }
    }
}

function toggleAllDay(day) {
    const allDay = document.getElementById(`allday-${day}`);
    const start = document.getElementById(`start-${day}`);
    const end = document.getElementById(`end-${day}`);

    if (!allDay || !start || !end) return;

    if (allDay.checked) {
        start.disabled = true;
        end.disabled = true;
        start.value = "";
        end.value = "";
    } else {
        start.disabled = false;
        end.disabled = false;
    }
}
// Function to gather the availability data from the form and construct a payload to send to the backend when saving availability changes
function getAvailabilityPayloadFromForm() {
    const days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ];

    const availability = [];

    for (const day of days) {
        const isAvailable = document.getElementById(`available-${day}`).value;
        const isAllDay = document.getElementById(`allday-${day}`).checked;
        const startTime = document.getElementById(`start-${day}`).value;
        const endTime = document.getElementById(`end-${day}`).value;

        availability.push({
            day_of_week: day,
            is_available: parseInt(isAvailable),
            is_all_day: isAllDay ? 1 : 0,
            start_time: isAllDay || isAvailable === "0" ? null : startTime,
            end_time: isAllDay || isAvailable === "0" ? null : endTime
        });
    }

    return availability;
}
// Function to display a message box at the top of the availability page with a custom message and styling based on the type of message (success, error, info)
function showAvailabilityMessage(message, type) {
    const box = document.getElementById("availability-message");
    if (!box) return;

    box.textContent = message;
    box.className = "availability-message " + type;
    box.style.display = "block";
}
// Function to handle saving availability changes, validates the form data and sends a POST request to the backend with the updated availability information, 
// also checks if any changes were made before sending the request and shows an appropriate message if not
function saveAvailability() {
    const staffId = localStorage.getItem("staff_id");

    if (!staffId) {
        alert("Please log in again.");
        return;
    }

    const availability = getAvailabilityPayloadFromForm();

    for (const item of availability) {
        if (
            item.is_available === 1 &&
            item.is_all_day === 0 &&
            (!item.start_time || !item.end_time)
        ) {
            alert(`Please enter start and end time for ${item.day_of_week}, or tick All Day.`);
            return;
        }
    }

    const newSnapshot = JSON.stringify(availability);

    if (newSnapshot === originalAvailabilitySnapshot) {
        showAvailabilityMessage(
            "No changes were made because this matches your current availability.",
            "message-info"
        );
        return;
    }

    fetch(`${API_BASE}/save-availability`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            staff_id: staffId,
            availability: availability
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAvailabilityMessage(
                "Availability updated successfully.",
                "message-success"
            );

            loadAvailability(staffId);
        } else {
            alert(data.message || "Could not save availability.");
        }
    })
    .catch(error => {
        console.error("Save availability error:", error);
        alert("Could not save availability.");
    });
}