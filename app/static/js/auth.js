/**
 * auth.js
 * Handles the login form. There is no registration — this app has a
 * single admin account authenticated via ADMIN_EMAIL/ADMIN_PASSWORD.
 */

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        const errorEl = document.getElementById("formError");
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            hideError(errorEl);

            const payload = {
                email: document.getElementById("email").value.trim(),
                password: document.getElementById("password").value,
            };

            try {
                await API.post("/api/auth/login", payload);
                window.location.href = "/dashboard";
            } catch (err) {
                showError(errorEl, err.message);
            }
        });
    }
});
