/**
 * business.js
 * Powers the business list, create, details, and edit pages.
 */
let reviewAspects = [];
function resolveLogoUrl(logoPath) {
    if (!logoPath) return null;
    const marker = "app/static/";
    const idx = logoPath.indexOf(marker);
    return idx >= 0 ? `/static/${logoPath.slice(idx + marker.length)}` : null;
}

function businessListRowHTML(biz) {
    const logo = resolveLogoUrl(biz.logo_path);
    const isActive = biz.is_active !== false;
    return `
        <div class="business-row" data-business-id="${biz.id}">
            <div class="business-row-info">
                ${logo ? `<img src="${logo}" class="business-logo-thumb" alt="">` : `<div class="business-logo-thumb"></div>`}
                <div class="business-row-text">
                    <h4 title="${biz.business_name}">${biz.business_name}</h4>
                    <div class="service-type">${biz.service_type}</div>
                </div>
            </div>
            <div class="business-row-actions">
                <a href="/businesses/${biz.id}" class="btn btn-secondary">View</a>
                <a href="/businesses/${biz.id}/edit" class="btn btn-secondary">Edit</a>
                <a href="/api/qr/${biz.id}/download" class="btn btn-secondary">QR</a>
            </div>
            <label class="qr-status-toggle">
                <input type="checkbox" class="qr-active-toggle" data-business-id="${biz.id}" ${isActive ? "checked" : ""}>
                <span class="toggle-slider"></span>
                <span class="qr-status-label">${isActive ? "Active" : "Disabled"}</span>
            </label>
        </div>
    `;
}

async function initBusinessListPage() {
    const grid = document.getElementById("businessGrid");
    if (!grid) return;

    try {
        const businesses = await API.get("/api/business");
        if (businesses.length === 0) {
            grid.classList.add("hidden");
            document.getElementById("emptyState").classList.remove("hidden");
        } else {
            grid.innerHTML = businesses.map(businessListRowHTML).join("");
        }
    } catch (err) {
        grid.innerHTML = `<p class="form-error">${err.message}</p>`;
        return;
    }

    grid.addEventListener("change", async (e) => {
        const checkbox = e.target;
        if (!checkbox.classList.contains("qr-active-toggle")) return;

        const businessId = checkbox.dataset.businessId;
        const newStatus = checkbox.checked;
        const label = checkbox.closest(".qr-status-toggle").querySelector(".qr-status-label");

        checkbox.disabled = true;
        try {
            await API.patch(`/api/business/${businessId}/status`, { is_active: newStatus });
            label.textContent = newStatus ? "Active" : "Disabled";
        } catch (err) {
            checkbox.checked = !newStatus;
            alert(err.message);
        } finally {
            checkbox.disabled = false;
        }
    });
}

async function initCreateBusinessPage() {
    const form = document.getElementById("createBusinessForm");
    if (!form) return;

    const errorEl = document.getElementById("formError");
    const addAspectBtn = document.getElementById("addReviewAspectBtn");
    const generateAspectBtn =document.getElementById("generateAspectBtn");
    if (addAspectBtn) {
        addAspectBtn.addEventListener("click", addReviewAspect);
    }
    
    if (generateAspectBtn) {
        generateAspectBtn.addEventListener("click",generateReviewAspects);
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError(errorEl);
        
        updateHiddenInput();
        const formData = new FormData(form);

        try {
            const business = await API.post("/api/business", formData);
            window.location.href = `/businesses/${business.id}`;
        } catch (err) {
            showError(errorEl, err.message);
        }
    });
}

async function initBusinessDetailsPage() {
    const container = document.getElementById("businessDetails");
    if (!container) return;

    const businessId = document.querySelector("[data-business-id]").dataset.businessId;

    try {
        const biz = await API.get(`/api/business/${businessId}`);

        container.innerHTML = `
            <h2>${biz.business_name}</h2>
            <div class="details-row"><span>Service Type</span><span>${biz.service_type}</span></div>
            <div class="details-row"><span>Google Review Link</span><span><a href="${biz.google_review_link}" target="_blank">Open</a></span></div>
            <div class="details-row"><span>Created</span><span>${new Date(biz.created_at).toLocaleDateString()}</span></div>
        `;

        document.getElementById("editBusinessBtn").href = `/businesses/${businessId}/edit`;
        document.getElementById("openCustomerPageBtn").href = `/r/${biz.slug}`;

        // Load QR
        try {
            const qr = await API.get(`/api/qr/${businessId}`);
            const qrImg = document.getElementById("qrImage");
            qrImg.src = `/api/qr/${businessId}/download?t=${Date.now()}`;
            qrImg.classList.remove("hidden");
        } catch (_) {
            // No QR yet — shouldn't normally happen since it's auto-generated.
        }

        // QR activation toggle
        const qrToggle = document.getElementById("qrActiveToggle");
        const qrStatusLabel = document.getElementById("qrStatusLabel");
        const qrDisabledOverlay = document.getElementById("qrDisabledOverlay");

        function updateQrStatusUI(isActive) {
            qrToggle.checked = isActive;
            qrStatusLabel.textContent = isActive ? "Active" : "Disabled";
            qrDisabledOverlay.classList.toggle("hidden", isActive);
        }

        updateQrStatusUI(biz.is_active !== false);

        qrToggle.addEventListener("change", async () => {
            const newStatus = qrToggle.checked;
            qrToggle.disabled = true;
            try {
                await API.patch(`/api/business/${businessId}/status`, { is_active: newStatus });
                updateQrStatusUI(newStatus);
            } catch (err) {
                updateQrStatusUI(!newStatus);
                alert(err.message);
            } finally {
                qrToggle.disabled = false;
            }
        });

        document.getElementById("downloadQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/download`;
        });

        document.getElementById("deleteBusinessBtn").addEventListener("click", async () => {
            if (!confirm(`Delete "${biz.business_name}"? This cannot be undone.`)) return;
            try {
                await API.delete(`/api/business/${businessId}`);
                window.location.href = "/businesses";
            } catch (err) {
                alert(err.message);
            }
        });
    } catch (err) {
        container.innerHTML = `<p class="form-error">${err.message}</p>`;
    }
}

async function initEditBusinessPage() {
    const form = document.getElementById("editBusinessForm");
    if (!form) return;

    const businessId = document.querySelector("[data-business-id]").dataset.businessId;
    const errorEl = document.getElementById("formError");
    const addAspectBtn = document.getElementById("addReviewAspectBtn");
    const generateAspectBtn =document.getElementById("generateAspectBtn");

    if (addAspectBtn) {
        addAspectBtn.addEventListener("click", addReviewAspect);
    }

    if (generateAspectBtn) {
        generateAspectBtn.addEventListener("click",generateReviewAspects);
    }

    document.getElementById("cancelEditBtn").href = `/businesses/${businessId}`;

    try {
        const biz = await API.get(`/api/business/${businessId}`);
        document.getElementById("businessName").value = biz.business_name;
        document.getElementById("serviceType").value = biz.service_type;
        document.getElementById("googleReviewLink").value = biz.google_review_link;

        const descEl = document.getElementById("businessDescription");
        if (descEl) descEl.value = biz.business_description || "";

        reviewAspects = [...(biz.review_aspects || [])];
        renderReviewAspects();
    } catch (err) {
        showError(errorEl, err.message);
        return;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError(errorEl);

        updateHiddenInput();
        const formData = new FormData(form);

        try {
            await API.request(`/api/business/${businessId}`, {
                method: "PUT",
                body: formData,
            });
            window.location.href = `/businesses/${businessId}`;
        } catch (err) {
            showError(errorEl, err.message);
        }
    });
}

function updateHiddenInput() {
    const hidden = document.getElementById("reviewAspects");
    if (hidden) {
        hidden.value = JSON.stringify(reviewAspects);
    }
}

function renderReviewAspects() {
    const container = document.getElementById("reviewAspectsContainer");
    if (!container) return;

    container.innerHTML = "";

    reviewAspects.forEach((aspect, index) => {
        const chip = document.createElement("div");
        chip.className = "review-aspect-chip";

        chip.innerHTML = `
            <span>${aspect}</span>
            <button type="button" data-index="${index}">&times;</button>
        `;

        chip.querySelector("button").addEventListener("click", () => {
            reviewAspects.splice(index, 1);
            renderReviewAspects();
        });

        container.appendChild(chip);
    });

    updateHiddenInput();
}

function addReviewAspect() {
    const input = document.getElementById("reviewAspectInput");

    if (!input) return;

    const value = input.value.trim();

    if (!value) return;

    const exists = reviewAspects.some(
        item => item.toLowerCase() === value.toLowerCase()
    );

    if (exists) {
        input.value = "";
        return;
    }

    reviewAspects.push(value);

    input.value = "";

    renderReviewAspects();
}

async function generateReviewAspects() {

    const serviceType =
        document.getElementById("serviceType").value.trim();

    const businessDescription =
        document.getElementById("businessDescription").value.trim();

    if (!serviceType) {
        alert("Please enter the Service Type first.");
        return;
    }

    const generateBtn =
        document.getElementById("generateAspectBtn");

    const originalText = generateBtn.textContent;

    generateBtn.disabled = true;
    generateBtn.textContent = "Generating...";

    try {

        const result = await API.post(
            "/api/business/review-aspects",
            {
                service_type: serviceType,
                business_description: businessDescription,
            }
        );

        const suggestions = result.review_aspects || [];

        suggestions.forEach((aspect) => {

            const exists = reviewAspects.some(
                item => item.toLowerCase() === aspect.toLowerCase()
            );

            if (!exists) {
                reviewAspects.push(aspect);
            }

        });

        renderReviewAspects();

    } catch (err) {

        alert(err.message || "Unable to generate suggestions.");

    } finally {

        generateBtn.disabled = false;
        generateBtn.textContent = originalText;

    }

}

document.addEventListener("DOMContentLoaded", async () => {
    const user = await guardProtectedPage();
    if (!user) return;

    initBusinessListPage();
    initCreateBusinessPage();
    initBusinessDetailsPage();
    initEditBusinessPage();
});
