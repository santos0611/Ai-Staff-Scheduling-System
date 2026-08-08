// Function to load the staff member's shifts and time off from the backend and render them on a calendar using FullCalendar, also sets up an event click handler to show shift details and a drop shift button for each shift, and shows time off details for time off events
function loadCalendar(staffId) {
    Promise.all([
        fetch(`${API_BASE}/my-shifts/${staffId}`).then(res => res.json()),
        fetch(`${API_BASE}/approved-time-off/${staffId}`).then(res => res.json())
    ])
    .then(([shiftData, timeOffData]) => {
        const calendarEl = document.getElementById("calendar");
        if (!calendarEl) return;

        calendarEl.innerHTML = "";

        const allEvents = [...shiftData, ...timeOffData];

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            events: allEvents,
            eventClick: function(info) {
                const item = info.event;
                const detailsBox = document.getElementById("shift-details");
                if (!detailsBox) return;

                if (String(item.id).startsWith("timeoff-")) {
                    detailsBox.innerHTML = `
                        <h3>Time Off</h3>
                        <p><strong>Type:</strong> ${item.title}</p>
                        <p><strong>Start:</strong> ${item.startStr}</p>
                    `;
                    return;
                }

                detailsBox.innerHTML = `
                    <h3>Shift Details</h3>
                    <p><strong>Date:</strong> ${item.startStr}</p>
                    <p><strong>Start Time:</strong> ${item.extendedProps.start_time}</p>
                    <p><strong>End Time:</strong> ${item.extendedProps.end_time}</p>
                    <p><strong>Role:</strong> ${item.extendedProps.required_role}</p>
                    <button onclick="dropShift(${item.id})">Drop Shift</button>
                `;
            }
        });

        calendar.render();
    })
    .catch(error => {
        console.error("Calendar load error:", error);
        const calendarEl = document.getElementById("calendar");
        if (calendarEl) {
            calendarEl.innerHTML = "<p>Could not load calendar.</p>";
        }
    });
}
// Function to handle dropping a shift,
function dropShift(shiftId) {
    const staffId = localStorage.getItem("staff_id");

    if (!staffId) {
        alert("Please log in again.");
        return;
    }

    const confirmed = confirm("Are you sure you want to drop this shift?");
    if (!confirmed) return;

    fetch(`${API_BASE}/drop-shift`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            shift_id: shiftId,
            staff_id: staffId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Shift dropped successfully.");
            loadCalendar(staffId);

            if (typeof loadShifts === "function") {
                loadShifts(staffId);
            }

            const detailsBox = document.getElementById("shift-details");
            if (detailsBox) {
                detailsBox.innerHTML = "<p>Click a shift to view details.</p>";
            }
        } else {
            alert(data.message || "Could not drop shift.");
        }
    })
    .catch(error => {
        console.error("Drop shift error:", error);
        alert("Could not drop shift.");
    });
}

