
//Admin dashboard JavaScript for managing pending account approvals
function loadPendingAccounts() {
    fetch(`${API_BASE}/pending-accounts`)
        .then(res => res.json())
        .then(accounts => {
            const box = document.getElementById("pending-accounts-list");

            if (!box) return;

            if (!accounts.length) {
                box.innerHTML = "<p>No pending accounts.</p>";
                return;
            }

            box.innerHTML = accounts.map(account => `
                <div class="account-card">
                    <h3>${account.name}</h3>
                    <p><strong>Staff ID:</strong> ${account.staff_id}</p>
                    <p><strong>DOB:</strong> ${account.dob}</p>
                    <p><strong>Position:</strong> ${account.position}</p>
                    <p><strong>Email:</strong> ${account.email}</p>
                    <p><strong>Phone:</strong> ${account.phone}</p>

                    <button onclick="approveAccount(${account.staff_id})">Approve</button>
                    <button class="danger-btn" onclick="rejectAccount(${account.staff_id})">Reject</button>
                </div>
            `).join("");
        });
}
// Call loadPendingAccounts when the admin dashboard page loads to display any pending account approvals
function approveAccount(staffId) {
    fetch(`${API_BASE}/approve-account`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({staff_id: staffId})
    })
    .then(res => res.json())
    .then(data => {
        alert(data.success ? "Account approved." : "Could not approve account.");
        loadPendingAccounts();
    });
}
// Function to handle rejecting a pending account approval, sends a POST request to the backend and refreshes the pending accounts list on success
function rejectAccount(staffId) {
    fetch(`${API_BASE}/reject-account`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({staff_id: staffId})
    })
    .then(res => res.json())
    .then(data => {
        alert(data.success ? "Account rejected." : "Could not reject account.");
        loadPendingAccounts();
    });
}