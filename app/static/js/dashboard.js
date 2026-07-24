/**
 * dashboard.js
 * Populates the dashboard: welcome message, business count, recent businesses.
 */

function businessCardHTML(biz) {
    const logo = biz.logo_path
        ? `/static/${biz.logo_path.split("app/static/")[1] || ""}`
        : null;

    return `
        <div class="business-card">
            <div class="business-card-header">
                ${logo ? `<img src="${logo}" class="business-logo-thumb" alt="">` : `<div class="business-logo-thumb"></div>`}
                <div>
                    <h4>${biz.business_name}</h4>
                    <div class="service-type">${biz.service_type}</div>
                </div>
            </div>
            <div class="business-card-actions">
                <a href="/businesses/${biz.id}" class="btn btn-secondary">View</a>
                <a href="/businesses/${biz.id}/edit" class="btn btn-secondary">Edit</a>
            </div>
        </div>
    `;
}

document.addEventListener("DOMContentLoaded", async () => {
    const user = await guardProtectedPage();
    if (!user) return;

    const welcomeEl = document.getElementById("welcomeMessage");
    if (welcomeEl) {
        welcomeEl.textContent = `Welcome back, ${user.full_name.split(" ")[0]}`;
    }

    try {
        const businesses = await API.get("/api/business");

        document.getElementById("businessCount").textContent = businesses.length;

        const recentContainer = document.getElementById("recentBusinesses");
        const recent = businesses.slice(0, 3);

        if (recent.length === 0) {
            recentContainer.innerHTML = `<p class="muted">No businesses yet. Create your first one above.</p>`;
        } else {
            recentContainer.innerHTML = recent.map(businessCardHTML).join("");
        }
    } catch (err) {
        console.error(err);
    }
});
