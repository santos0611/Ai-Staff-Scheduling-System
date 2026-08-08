function loadStaffNotifications() {
    const staffId = localStorage.getItem("staff_id");
    const container = document.getElementById("notifications-content");

    if (!staffId || !container) return;

    fetch(`${API_BASE}/staff-notifications/${staffId}`)
        .then(response => response.json())
        .then(data => {
            let html = "";

            html += `<h3>Open Shifts</h3>`;

            if (!data.open_shifts || data.open_shifts.length === 0) {
                html += `<p>No open shifts available.</p>`;
            } else {
                data.open_shifts.forEach(shift => {
                    const openReason = shift.dropped_by_name
                        ? `Dropped by ${shift.dropped_by_name}`
                        : "Created open shift";

                    html += `
                        <div class="shift-card">
                            <p><strong>Type:</strong> Open Shift</p>
                            <p><strong>Date:</strong> ${shift.shift_date}</p>
                            <p><strong>Time:</strong> ${shift.start_time} - ${shift.end_time}</p>
                            <p><strong>Role:</strong> ${shift.required_role}</p>
                            <p><strong>Reason:</strong> ${openReason}</p>
                            <button onclick="requestPickup(${shift.shift_id})">Request Pickup</button>
                        </div>
                    `;
                });
            }

            html += `<h3 class="notification-heading">My Pickup Requests</h3>`;

            if (!data.my_requests || data.my_requests.length === 0) {
                html += `<p>No pickup requests yet.</p>`;
            } else {
                data.my_requests.forEach(req => {
                    let clearButton = "";

                    if (req.status === "Approved" || req.status === "Rejected") {
                        clearButton = `<button onclick="clearPickupNotification(${req.pickup_id})">Clear</button>`;
                    }

                    html += `
                        <div class="shift-card">
                            <p><strong>Date:</strong> ${req.shift_date}</p>
                            <p><strong>Time:</strong> ${req.start_time} - ${req.end_time}</p>
                            <p><strong>Role:</strong> ${req.required_role}</p>
                            <p><strong>Status:</strong> ${req.status}</p>
                            ${clearButton}
                        </div>
                    `;
                });
            }

            html += `<h3 class="notification-heading">Time Off Updates</h3>`;

            if (!data.time_off_updates || data.time_off_updates.length === 0) {
                html += `<p>No time off updates yet.</p>`;
            } else {
                data.time_off_updates.forEach(item => {
                    let clearButton = "";

                    if (item.status === "Approved" || item.status === "Rejected") {
                        clearButton = `<button onclick="clearTimeOffNotification(${item.time_off_id})">Clear</button>`;
                    }

                    html += `
                        <div class="shift-card">
                            <p><strong>Type:</strong> ${item.request_type}</p>
                            <p><strong>Dates:</strong> ${item.start_date} to ${item.end_date}</p>
                            <p><strong>Status:</strong> ${item.status}</p>
                            <p><strong>Manager Message:</strong> ${item.manager_note || "-"}</p>
                            ${clearButton}
                        </div>
                    `;
                });
            }

            container.innerHTML = html;
        })
        .catch(error => {
            console.error("Error loading staff notifications:", error);
            container.innerHTML = "<p>Could not load notifications.</p>";
        });
}

// Function to handle requesting a pickup for an open shift, sends a POST request to the backend with the staff ID and shift ID, shows an alert based on the response and reloads the notifications if successful
function requestPickup(shiftId) {
    const staffId = localStorage.getItem("staff_id");

    if (!staffId) {
        alert("Please log in again.");
        return;
    }

    fetch(`${API_BASE}/request-pickup`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            shift_id: shiftId,
            staff_id: staffId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Pickup request sent.");
            loadStaffNotifications();
        } else {
            alert(data.message || "Could not request shift.");
        }
    })
    .catch(error => {
        console.error("Pickup request error:", error);
        alert("Could not request shift.");
    });
}
// Function to clear a pickup notification for the staff member, sends a POST request to the backend with the pickup ID and staff ID, shows an alert based on the response and reloads the notifications if successful
function clearPickupNotification(pickupId) {
    const staffId = localStorage.getItem("staff_id");

    if (!staffId) {
        alert("Please log in again.");
        return;
    }

    fetch(`${API_BASE}/clear-pickup-notification`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            pickup_id: pickupId,
            staff_id: staffId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStaffNotifications();
        } else {
            alert("Could not clear pickup notification.");
        }
    })
    .catch(error => {
        console.error("Clear pickup notification error:", error);
        alert("Could not clear pickup notification.");
    });
}
// Function to clear a time off notification for the staff member, sends a POST request to the backend with the time off ID and staff ID, 
function clearTimeOffNotification(timeOffId) {
    const staffId = localStorage.getItem("staff_id");

    if (!staffId) {
        alert("Please log in again.");
        return;
    }

    fetch(`${API_BASE}/clear-timeoff-notification`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            time_off_id: timeOffId,
            staff_id: staffId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStaffNotifications();
        } else {
            alert("Could not clear time off notification.");
        }
    })
    .catch(error => {
        console.error("Clear time off notification error:", error);
        alert("Could not clear time off notification.");
    });
}
// Function to load the manager's notifications from the backend and render them on the manager notifications page, shows open shifts, pending pickup requests and pending time off requests with appropriate action buttons for each
function loadManagerNotifications() {
    const container = document.getElementById("notifications-content");
    const managerStaffId = localStorage.getItem("staff_id");

    if (!container) return;

    if (!managerStaffId) {
        container.innerHTML = "<p>Please log in again.</p>";
        return;
    }

    fetch(`${API_BASE}/manager-notifications/${managerStaffId}`)
        .then(response => response.json())
        .then(data => {
            let html = "";

            html += `<h3>Open Shifts</h3>`;

            if (!data.open_shifts || data.open_shifts.length === 0) {
                html += `<p>No open shifts.</p>`;
            } else {
                data.open_shifts.forEach(shift => {
                    const openReason = shift.dropped_by_name
                        ? `Dropped by ${shift.dropped_by_name}`
                        : "Created as an open shift";

                    html += `
                        <div class="shift-card">
                            <p><strong>Type:</strong> Open Shift</p>
                            <p><strong>Date:</strong> ${shift.shift_date}</p>
                            <p><strong>Time:</strong> ${shift.start_time} - ${shift.end_time}</p>
                            <p><strong>Role:</strong> ${shift.required_role}</p>
                            <p><strong>Reason:</strong> ${openReason}</p>
                            <p><strong>Status:</strong> ${shift.status}</p>

                            <div class="notification-action-row">
                                <button onclick="assignOpenShiftFromNotification(${shift.shift_id})">
                                    Assign Staff
                                </button>
                                <button onclick="clearManagerShift(${shift.shift_id})">
                                    Clear
                                </button>
                            </div>
                        </div>
                    `;
                });
            }

            html += `<h3 class="notification-heading">Pending Pickup Requests</h3>`;

            if (!data.pickup_requests || data.pickup_requests.length === 0) {
                html += `<p>No pending pickup requests.</p>`;
            } else {
                data.pickup_requests.forEach(req => {
                    html += `
                        <div class="shift-card">
                            <p><strong>Staff:</strong> ${req.name}</p>
                            <p><strong>Date:</strong> ${req.shift_date}</p>
                            <p><strong>Time:</strong> ${req.start_time} - ${req.end_time}</p>
                            <p><strong>Role:</strong> ${req.required_role}</p>

                            <div class="notification-action-row">
                                <button onclick="approvePickup(${req.pickup_id})">Approve</button>
                                <button onclick="rejectPickup(${req.pickup_id})">Reject</button>
                            </div>
                        </div>
                    `;
                });
            }

            html += `<h3 class="notification-heading">Pending Time Off Requests</h3>`;

            if (!data.time_off_requests || data.time_off_requests.length === 0) {
                html += `<p>No pending time off requests.</p>`;
            } else {
                data.time_off_requests.forEach(req => {
                    html += `
                        <div class="shift-card">
                            <p><strong>Staff:</strong> ${req.name}</p>
                            <p><strong>Type:</strong> ${req.request_type}</p>
                            <p><strong>Dates:</strong> ${req.start_date} to ${req.end_date}</p>
                            <p><strong>Reason:</strong> ${req.reason || "-"}</p>

                            <label for="manager-note-${req.time_off_id}">
                                <strong>Manager Message:</strong>
                            </label>
                            <textarea id="manager-note-${req.time_off_id}" rows="3" class="manager-note-box">Approved</textarea>

                            <div class="notification-action-row">
                                <button onclick="approveTimeOff(${req.time_off_id})">Approve</button>
                                <button onclick="rejectTimeOff(${req.time_off_id})">Reject</button>
                            </div>
                        </div>
                    `;
                });
            }

            container.innerHTML = html;
        })
        .catch(error => {
            console.error("Error loading manager notifications:", error);
            container.innerHTML = "<p>Could not load notifications.</p>";
        });
}
// Function to handle assigning an open shift from a notification
function assignOpenShiftFromNotification(shiftId) {
    localStorage.setItem("selected_open_shift_id", shiftId);
    window.location.href = "manager-board.html";
}
// Function to clear manager shift
function clearManagerShift(shiftId) {
    const managerStaffId = localStorage.getItem("staff_id");

    if (!managerStaffId) {
        alert("Please log in again.");
        return;
    }

    fetch(`${API_BASE}/clear-manager-open-shift`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            shift_id: shiftId,
            manager_staff_id: managerStaffId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            loadManagerNotifications();
        } else {
            alert("Could not clear notification.");
        }
    });
}
// Function to handle approving a pickup request from the manager notifications, 
function approvePickup(pickupId) {
    fetch(`${API_BASE}/approve-pickup`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            pickup_id: pickupId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Pickup approved.");
            loadManagerNotifications();
        } else {
            alert(data.message || "Could not approve pickup.");
        }
    })
    .catch(error => {
        console.error("Approve pickup error:", error);
        alert("Could not approve pickup.");
    });
}
// Function to handle rejecting a pickup request from the manager notifications,
function rejectPickup(pickupId) {
    fetch(`${API_BASE}/reject-pickup`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            pickup_id: pickupId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Pickup rejected.");
            loadManagerNotifications();
        } else {
            alert("Could not reject pickup.");
        }
    })
    .catch(error => {
        console.error("Reject pickup error:", error);
        alert("Could not reject pickup.");
    });
}
// Function to handle approving a time off request from the manager notifications, sends a POST request to the backend with the time off ID and manager note, shows an alert based on the response and reloads the notifications if successful
function approveTimeOff(timeOffId) {
    const noteBox = document.getElementById(`manager-note-${timeOffId}`);
    const managerNote = noteBox ? noteBox.value : "";

    fetch(`${API_BASE}/approve-time-off`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            time_off_id: timeOffId,
            manager_note: managerNote
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Time off approved.");
            loadManagerNotifications();
        } else {
            alert("Could not approve time off.");
        }
    })
    .catch(error => {
        console.error("Approve time off error:", error);
        alert("Could not approve time off.");
    });
}
// Function to handle rejecting a time off request from the manager notifications
function rejectTimeOff(timeOffId) {
    const noteBox = document.getElementById(`manager-note-${timeOffId}`);
    const managerNote = noteBox ? noteBox.value : "";

    fetch(`${API_BASE}/reject-time-off`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            time_off_id: timeOffId,
            manager_note: managerNote
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Time off rejected.");
            loadManagerNotifications();
        } else {
            alert("Could not reject time off.");
        }
    })
    .catch(error => {
        console.error("Reject time off error:", error);
        alert("Could not reject time off.");
    });
}