/**
 * app.js
 * Shared utilities used across every page: a small fetch wrapper,
 * dynamic navbar rendering based on auth state, and a simple
 * page-guard for routes that require login.
 */

function showError(el, message) {
    if (!el) return;
    el.textContent = message;
    el.classList.remove("hidden");
}

function hideError(el) {
    if (!el) return;
    el.classList.add("hidden");
}

function escapeHtml(value) {
    return (value == null ? "" : String(value))
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/**
 * Reads the current page's own `?from=` context (set by whichever link the
 * user clicked to get here — see FROM.*Link() below) and resolves it to a
 * real URL: "dashboard" -> /dashboard, "businesses" -> /businesses.
 * Falls back to /dashboard when the page was opened without that context
 * (bookmarked, typed URL, etc).
 */
function resolveBackHref() {
    const from = new URLSearchParams(window.location.search).get("from");
    if (from === "businesses") return "/businesses";
    return "/dashboard";
}

/**
 * Appends the given `from` context ("dashboard" or "businesses") to a URL,
 * so pages reached through it know which admin root they should return to.
 */
function withFrom(url, from) {
    const separator = url.includes("?") ? "&" : "?";
    return `${url}${separator}from=${from}`;
}

const API = {
    async request(url, options = {}) {
        const response = await fetch(url, {
            credentials: "include",
            headers: options.body instanceof FormData
                ? {}
                : { "Content-Type": "application/json" },
            ...options,
        });

        if (response.status === 204) {
            return null;
        }

        let data = null;
        try {
            data = await response.json();
        } catch (_) {
            data = null;
        }

        if (!response.ok) {
            const message = (data && data.detail) || "Something went wrong. Please try again.";
            const error = new Error(typeof message === "string" ? message : JSON.stringify(message));
            error.status = response.status;
            throw error;
        }

        return data;
    },

    get(url) {
        return this.request(url, { method: "GET" });
    },

    post(url, body) {
        return this.request(url, {
            method: "POST",
            body: body instanceof FormData ? body : JSON.stringify(body || {}),
        });
    },

    put(url, body) {
        return this.request(url, {
            method: "PUT",
            body: body instanceof FormData ? body : JSON.stringify(body || {}),
        });
    },

    patch(url, body) {
        return this.request(url, {
            method: "PATCH",
            body: body instanceof FormData ? body : JSON.stringify(body || {}),
        });
    },

    delete(url) {
        return this.request(url, { method: "DELETE" });
    },
};

async function getCurrentUser() {
    try {
        return await API.get("/api/auth/me");
    } catch (_) {
        return null;
    }
}

function renderNavbar(user) {
    const navLinks = document.getElementById("navLinks");
    if (!navLinks) return;

    if (user) {
        navLinks.innerHTML = `
            <a href="/dashboard">Dashboard</a>
            <a href="/businesses">Businesses</a>
            <button id="logoutBtn">Logout</button>
        `;
        const logoutBtn = document.getElementById("logoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", async () => {
                await API.post("/api/auth/logout");
                window.location.href = "/login";
            });
        }
    } else {
        navLinks.innerHTML = `
            <a href="/login" class="btn btn-primary">Login</a>
        `;
    }
}

async function initAuthAwareNavbar() {
    const user = await getCurrentUser();
    renderNavbar(user);
    return user;
}

/**
 * Pages marked with [data-requires-auth] redirect to /login if there's
 * no valid session. Called on DOMContentLoaded from every protected page.
 */
async function guardProtectedPage() {
    const protectedEl = document.querySelector("[data-requires-auth]");
    if (!protectedEl) return null;

    const user = await getCurrentUser();
    if (!user) {
        window.location.href = "/login";
        return null;
    }
    return user;
}

document.addEventListener("DOMContentLoaded", () => {
    initAuthAwareNavbar();
});
