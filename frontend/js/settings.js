// Function to render the settings options on the settings page based on the user's position and admin status, shows different options for staff, managers and admins, also displays a welcome message with the user's name and position and an admin badge if applicable
function renderSettingsOptions() {
    const position = localStorage.getItem("position") || "staff";
    const currentMode = localStorage.getItem("view_mode") || "staff";
    const isAdmin = localStorage.getItem("is_admin");
    const userName = localStorage.getItem("name") || "User";
    const userPosition = localStorage.getItem("position") || "staff";

    const welcome = document.getElementById("welcome-user");
    const badge = document.getElementById("settings-admin-badge");
    const area = document.getElementById("manager-switch-area");

    if (welcome) {
        welcome.textContent = `Welcome Back ${userName}, ${userPosition}`;
    }

    if (badge && isAdmin === "1") {
        badge.innerHTML = `<span class="admin-badge">ADMIN</span>`;
    }

    if (!area) return;

    let html = `
        <div class="settings-card">
            <h3>View Mode</h3>
            <p>Current mode: <strong>${currentMode}</strong></p>
    `;

    if (position.toLowerCase() === "manager" || isAdmin === "1") {
        html += `
            <button onclick="switchToStaffView()">Switch to Staff View</button>
            <button onclick="switchToManagerView()">Switch to Manager View</button>
        `;
    } else {
        html += `<p>You are using standard staff access.</p>`;
    }

    html += `</div>`;

    if (isAdmin === "1") {
        html += `
            <div class="settings-card">
                <h3>Admin Controls</h3>
                <button onclick="window.location.href='admin-accounts.html'">
                    Manage Pending Accounts
                </button>
            </div>
        `;
    }

    area.innerHTML = html;
}