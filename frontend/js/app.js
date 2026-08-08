const API_BASE = window.location.origin;
// Utility function to format a JavaScript Date object into a YYYY-MM-DD string format for consistent date handling across the application
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}
// Function to handle user logout, clears local storage and redirects to the login page
function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}
// Function to render the bottom navigation bar based on the user's view mode (staff or manager) and highlight the current page
function renderBottomNav(currentPage) {
    const navContainer = document.getElementById("bottom-nav");
    if (!navContainer) return;

    const viewMode = localStorage.getItem("view_mode");

    let navItems = [];

    if (viewMode === "manager") {
        navItems = [
            { href: "manager-board.html", label: "Schedule" },
            { href: "manager-calendar.html", label: "Calendar" },
            { href: "notificationpage.html", label: "Notifications" },
            { href: "settings.html", label: "Settings" }
        ];
    } else {
        navItems = [
            { href: "homepage.html", label: "Home" },
            { href: "calendar.html", label: "Calendar" },
            { href: "notificationpage.html", label: "Notifications" },
            { href: "settings.html", label: "Settings" }
        ];
    }

    let html = `<nav class="bottom-nav">`;

    navItems.forEach(item => {
        const activeClass = item.href === currentPage ? "nav-item active-nav" : "nav-item";
        html += `<a href="${item.href}" class="${activeClass}">${item.label}</a>`;
    });

    html += `</nav>`;
    navContainer.innerHTML = html;
}
// Function to render a banner at the top of the page indicating the current view mode (manager or staff) and provide a button to switch to manager view if the user has the appropriate permissions
function renderModeBanner() {
    const banner = document.getElementById("mode-banner");
    if (!banner) return;

    const viewMode = localStorage.getItem("view_mode");

    if (viewMode === "manager") {
        banner.innerHTML = `
            <div class="mode-banner">
                MANAGER MODE
                <button onclick="switchToStaffView()" style="margin-left:10px;">
                    Switch to Staff
                </button>
            </div>
        `;
    } else {
        banner.innerHTML = "";
    }
}
// Function to switch the user to staff view, updates local storage and redirects to the staff homepage
function switchToStaffView() {
    localStorage.setItem("view_mode", "staff");
    window.location.href = "homepage.html";
}
// Function to switch the user to manager view, checks if the user has manager or admin permissions before updating local storage and redirecting to the manager board page
function switchToManagerView() {
    const position = localStorage.getItem("position") || "";
    const isAdmin = localStorage.getItem("is_admin");

    if (position.toLowerCase() === "manager" || isAdmin === "1") {
        localStorage.setItem("view_mode", "manager");
        window.location.href = "manager-board.html";
    } else {
        alert("Access denied. Only managers or admins can use manager mode.");
    }
}