// Function to load the staff member's next upcoming shift from the backend and render it on the homepage
function loadShifts(staffId) {
    fetch(`${API_BASE}/next-shift/${staffId}`)
        .then(response => response.json())
        .then(data => {
            const shiftList = document.getElementById("shift-list");
            if (!shiftList) return;

            if (!data.success) {
                shiftList.innerHTML = "<p>No upcoming shifts.</p>";
                return;
            }

            shiftList.innerHTML = `
                <div class="shift-card">
                    <p><strong>Date:</strong> ${data.date}</p>
                    <p><strong>Time:</strong> ${data.start_time} - ${data.end_time}</p>
                    <p><strong>Role:</strong> ${data.required_role}</p>
                </div>
            `;
        })
        .catch(error => {
            console.error("Error loading next shift:", error);
            const shiftList = document.getElementById("shift-list");
            if (shiftList) {
                shiftList.innerHTML = "<p>Could not load shift.</p>";
            }
        });
}