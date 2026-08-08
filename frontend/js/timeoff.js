// Function to handle submitting a time off request
function submitTimeOffRequest() {
    const staffId = localStorage.getItem("staff_id");
    const requestType = document.getElementById("request-type").value;
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    const reason = document.getElementById("reason").value;

    if (!staffId || !requestType || !startDate || !endDate) {
        alert("Please complete all required fields.");
        return;
    }

    fetch(`${API_BASE}/request-time-off`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            staff_id: staffId,
            request_type: requestType,
            start_date: startDate,
            end_date: endDate,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Time off request submitted.");
            loadMyTimeOffRequests(staffId);

            document.getElementById("start-date").value = "";
            document.getElementById("end-date").value = "";
            document.getElementById("reason").value = "";
        } else {
            alert(data.message || "Could not submit request.");
        }
    })
    .catch(error => {
        console.error("Time off request error:", error);
        alert("Could not submit request.");
    });
}
// Function to load the staff member's time off requests from the backend and render them in a list on the time off page, shows a message if there are no requests or if there was an error loading them
function loadMyTimeOffRequests(staffId) {
    fetch(`${API_BASE}/my-time-off/${staffId}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("my-time-off-list");
            if (!container) return;

            if (data.length === 0) {
                container.innerHTML = "<p>No time off requests yet.</p>";
                return;
            }

            let html = "";

            data.forEach(req => {
                html += `
                    <div class="request-card">
                        <p><strong>Type:</strong> ${req.request_type}</p>
                        <p><strong>Dates:</strong> ${req.start_date} to ${req.end_date}</p>
                        <p><strong>Status:</strong> ${req.status}</p>
                        <p><strong>Reason:</strong> ${req.reason || "-"}</p>
                        <p><strong>Manager Note:</strong> ${req.manager_note || "-"}</p>
                    </div>
                `;
            });

            container.innerHTML = html;
        })
        .catch(error => {
            console.error("Error loading my time off:", error);
            const container = document.getElementById("my-time-off-list");
            if (container) {
                container.innerHTML = "<p>Could not load requests.</p>";
            }
        });
}