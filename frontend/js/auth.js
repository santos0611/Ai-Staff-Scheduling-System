//==================LOGIN PAGE - index.html======================
function login(event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem("staff_id", data.staff_id);
            localStorage.setItem("position", data.position);
            localStorage.setItem("name", data.name);
            localStorage.setItem("is_admin", data.is_admin);

            if (data.is_admin === 1 || data.is_admin === "1") {
                localStorage.setItem("view_mode", "staff");
                window.location.href = "homepage.html";
            } else if (data.position.toLowerCase() === "manager") {
                localStorage.setItem("view_mode", "manager");
                window.location.href = "manager-board.html";
            } else {
                localStorage.setItem("view_mode", "staff");
                window.location.href = "homepage.html";
            }
        } else {
            alert("Invalid login details");
        }
    })
    .catch(error => {
        console.error("Login error:", error);
        alert("Could not connect to server");
    });
}

//==================RESET PASSWORD PAGE - reset-password.html======================
function resetPassword() {
    fetch(`${API_BASE}/reset-password`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            staff_id: document.getElementById("reset-staff-id").value,
            dob: document.getElementById("reset-dob").value,
            email: document.getElementById("reset-email").value,
            phone: document.getElementById("reset-phone").value,
            new_password: document.getElementById("reset-password").value,
            confirm_password: document.getElementById("reset-confirm-password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.success) window.location.href = "index.html";
    });
}
//FUNCTION TO UPDATE PASSWORD RULES IN REALTIME AS THE USER TYPES IN THE NEW PASSWORD   FORGOT-PASSWORD.html
function updatePasswordRules(passwordInputId) {
    const passwordInput = document.getElementById(passwordInputId);
    if (!passwordInput) return;

    const password = passwordInput.value;

    const rules = {
        "rule-length": password.length >= 8,
        "rule-uppercase": /[A-Z]/.test(password),
        "rule-lowercase": /[a-z]/.test(password),
        "rule-number": /\d/.test(password),
        "rule-special": /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    Object.keys(rules).forEach(ruleId => {
        const ruleEl = document.getElementById(ruleId);
        if (!ruleEl) return;

        if (rules[ruleId]) {
            ruleEl.classList.add("valid-rule");
        } else {
            ruleEl.classList.remove("valid-rule");
        }
    });
}
//FUNCTION TO CREATE ACCOUNT - create-account.html

function createAccount(event) {
    event.preventDefault();

    const password = document.getElementById("new-password").value;
    const passwordErrors = [];

    if (password.length < 8) passwordErrors.push("rule-length");
    if (!/[A-Z]/.test(password)) passwordErrors.push("rule-uppercase");
    if (!/[a-z]/.test(password)) passwordErrors.push("rule-lowercase");
    if (!/\d/.test(password)) passwordErrors.push("rule-number");
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) passwordErrors.push("rule-special");

    updatePasswordRules("new-password");

    if (passwordErrors.length > 0) {
        alert("Password does not meet all requirements. Missing items are highlighted in red.");
        return;
    }

    fetch(`${API_BASE}/create-account`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: document.getElementById("new-name").value,
            dob: document.getElementById("new-dob").value,
            position: document.getElementById("new-position").value,
            email: document.getElementById("new-email").value,
            phone: document.getElementById("new-phone").value,
            password: password,
            confirm_password: document.getElementById("new-confirm-password").value
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Account request submitted.");

        if (data.success) {
            window.location.href = "index.html";
        }
    })
    .catch(error => {
        console.error("Create account error:", error);
        alert("Could not create account.");
    });
}