/**
 * business.js
 * Powers the business list, create, details, and edit pages.
 */
let reviewAspects = [];
let customLinks = [];
let editingCustomLinkIndex = null;
function resolveLogoUrl(logoPath) {
    if (!logoPath) return null;
    const marker = "app/static/";
    const idx = logoPath.indexOf(marker);
    return idx >= 0 ? `/static/${logoPath.slice(idx + marker.length)}` : null;
}

function businessListRowHTML(biz) {
    const logo = resolveLogoUrl(biz.logo_path);
    const isActive = biz.is_active !== false;
    const isSocialActive = biz.social_is_active !== false;
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
                <a href="/businesses/${biz.id}?from=businesses" class="btn btn-secondary">View</a>
                <a href="/businesses/${biz.id}/edit?from=businesses" class="btn btn-secondary">Edit</a>
                <a href="/api/qr/${biz.id}/download" class="btn btn-secondary">Review QR</a>
                <a href="/api/qr/${biz.id}/social/download" class="btn btn-secondary">Social QR</a>
            </div>
            <div class="qr-status-toggles">
                <label class="qr-status-toggle">
                    <span class="qr-status-name">Review QR</span>
                    <input type="checkbox" class="qr-active-toggle" data-business-id="${biz.id}" ${isActive ? "checked" : ""}>
                    <span class="toggle-slider"></span>
                    <span class="qr-status-label">${isActive ? "Active" : "Disabled"}</span>
                </label>
                <label class="qr-status-toggle">
                    <span class="qr-status-name">Social QR</span>
                    <input type="checkbox" class="social-qr-active-toggle" data-business-id="${biz.id}" ${isSocialActive ? "checked" : ""}>
                    <span class="toggle-slider"></span>
                    <span class="qr-status-label">${isSocialActive ? "Active" : "Disabled"}</span>
                </label>
            </div>
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
        const isReview = checkbox.classList.contains("qr-active-toggle");
        const isSocial = checkbox.classList.contains("social-qr-active-toggle");
        if (!isReview && !isSocial) return;

        const businessId = checkbox.dataset.businessId;
        const newStatus = checkbox.checked;
        const label = checkbox.closest(".qr-status-toggle").querySelector(".qr-status-label");
        const endpoint = isReview
            ? `/api/business/${businessId}/status`
            : `/api/business/${businessId}/social-status`;

        checkbox.disabled = true;
        try {
            await API.patch(endpoint, { is_active: newStatus });
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

    const backLink = document.getElementById("backLink");
    if (backLink) backLink.href = resolveBackHref();

    const errorEl = document.getElementById("formError");
    const addAspectBtn = document.getElementById("addReviewAspectBtn");
    const generateAspectBtn =document.getElementById("generateAspectBtn");
    if (addAspectBtn) {
        addAspectBtn.addEventListener("click", addReviewAspect);
    }

    if (generateAspectBtn) {
        generateAspectBtn.addEventListener("click",generateReviewAspects);
    }

    const addCustomLinkBtn = document.getElementById("addCustomLinkBtn");
    if (addCustomLinkBtn) {
        addCustomLinkBtn.addEventListener("click", addOrUpdateCustomLink);
    }
    renderCustomLinks();

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError(errorEl);

        updateHiddenInput();
        updateCustomLinksHiddenInput();
        const formData = new FormData(form);

        try {
            const business = await API.post("/api/business", formData);
            const from = new URLSearchParams(window.location.search).get("from") || "dashboard";
            window.location.href = withFrom(`/businesses/${business.id}`, from);
        } catch (err) {
            showError(errorEl, err.message);
        }
    });
}

async function initBusinessDetailsPage() {
    const container = document.getElementById("businessDetails");
    if (!container) return;

    const businessId = document.querySelector("[data-business-id]").dataset.businessId;

    const backLink = document.getElementById("backLink");
    if (backLink) backLink.href = resolveBackHref();

    const currentFrom = new URLSearchParams(window.location.search).get("from") || "dashboard";

    try {
        const biz = await API.get(`/api/business/${businessId}`);

        container.innerHTML = `
            <h2>${biz.business_name}</h2>
            <div class="details-row"><span>Service Type</span><span>${biz.service_type}</span></div>
            <div class="details-row"><span>Google Review Link</span><span><a href="${biz.google_review_link}" target="_blank">Open</a></span></div>
            <div class="details-row"><span>Created</span><span>${new Date(biz.created_at).toLocaleDateString()}</span></div>
        `;

        document.getElementById("editBusinessBtn").href = withFrom(`/businesses/${businessId}/edit`, currentFrom);
        document.getElementById("openCustomerPageBtn").href = `/r/${biz.slug}`;
        document.getElementById("openSocialPageBtn").href = `/s/${biz.social_slug}`;

        // Load QR
        try {
            const qr = await API.get(`/api/qr/${businessId}`);
            const qrImg = document.getElementById("qrImage");
            qrImg.src = `/api/qr/${businessId}/download?t=${Date.now()}`;
            qrImg.classList.remove("hidden");
        } catch (_) {
            // No QR yet — shouldn't normally happen since it's auto-generated.
        }

        // Load social QR
        try {
            await API.get(`/api/qr/${businessId}/social`);
            const socialQrImg = document.getElementById("socialQrImage");
            socialQrImg.src = `/api/qr/${businessId}/social/download?t=${Date.now()}`;
            socialQrImg.classList.remove("hidden");
        } catch (_) {
            // No social QR yet — shouldn't normally happen since it's auto-generated.
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

        // Social QR activation toggle
        const socialQrToggle = document.getElementById("socialQrActiveToggle");
        const socialQrStatusLabel = document.getElementById("socialQrStatusLabel");
        const socialQrDisabledOverlay = document.getElementById("socialQrDisabledOverlay");

        function updateSocialQrStatusUI(isActive) {
            socialQrToggle.checked = isActive;
            socialQrStatusLabel.textContent = isActive ? "Active" : "Disabled";
            socialQrDisabledOverlay.classList.toggle("hidden", isActive);
        }

        updateSocialQrStatusUI(biz.social_is_active !== false);

        socialQrToggle.addEventListener("change", async () => {
            const newStatus = socialQrToggle.checked;
            socialQrToggle.disabled = true;
            try {
                await API.patch(`/api/business/${businessId}/social-status`, { is_active: newStatus });
                updateSocialQrStatusUI(newStatus);
            } catch (err) {
                updateSocialQrStatusUI(!newStatus);
                alert(err.message);
            } finally {
                socialQrToggle.disabled = false;
            }
        });

        document.getElementById("downloadQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/download`;
        });

        document.getElementById("downloadSocialQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/social/download`;
        });

        await loadBusinessActivity(businessId);

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

async function loadBusinessActivity(businessId) {
    const breakdown = document.getElementById("activityBreakdown");
    if (!breakdown) return;

    try {
        const actions = await API.get(`/api/business/${businessId}/click-logs/summary`);

        // "qr_scan" is recorded on both the review and social landing pages,
        // so there can be two separate rows for it here (one per page) —
        // sum them for the headline stat, but keep them split in the
        // breakdown list below via formatActionRowLabel().
        const scanRows = actions.filter((a) => a.action === "qr_scan");
        const buttonActions = actions.filter((a) => a.action !== "qr_scan");

        document.getElementById("activityTotalScans").textContent =
            scanRows.reduce((sum, a) => sum + a.count, 0);
        document.getElementById("activityTotalClicks").textContent =
            buttonActions.reduce((sum, a) => sum + a.count, 0);
        document.getElementById("activityTopButton").textContent =
            buttonActions.length > 0 ? formatActionLabel(buttonActions[0].action) : "—";

        const lastSeen = actions.reduce(
            (latest, a) => (!latest || a.last_clicked_at > latest ? a.last_clicked_at : latest),
            null
        );
        document.getElementById("activityLastSeen").textContent = lastSeen
            ? formatIST(lastSeen)
            : "—";

        if (actions.length === 0) {
            breakdown.innerHTML = `<p class="muted">No activity recorded yet.</p>`;
            return;
        }

        const maxCount = actions[0].count;
        breakdown.innerHTML = actions
            .map(
                (a) => `
            <div class="activity-row">
                <div class="activity-row-label">
                    <span>${escapeHtml(formatActionRowLabel(a.action, a.page))}</span>
                    <span class="activity-row-count">${a.count}</span>
                </div>
                <div class="activity-bar-track">
                    <div class="activity-bar-fill" style="width: ${(a.count / maxCount) * 100}%"></div>
                </div>
                <span class="activity-row-time muted">Last clicked ${formatIST(a.last_clicked_at)}</span>
            </div>
        `
            )
            .join("");
    } catch (err) {
        breakdown.innerHTML = `<p class="form-error">${err.message}</p>`;
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

    const addCustomLinkBtn = document.getElementById("addCustomLinkBtn");
    if (addCustomLinkBtn) {
        addCustomLinkBtn.addEventListener("click", addOrUpdateCustomLink);
    }

    const backLink = document.getElementById("backLink");
    if (backLink) backLink.href = resolveBackHref();

    const currentFrom = new URLSearchParams(window.location.search).get("from") || "dashboard";

    document.getElementById("cancelEditBtn").href = withFrom(`/businesses/${businessId}`, currentFrom);

    try {
        const biz = await API.get(`/api/business/${businessId}`);
        document.getElementById("businessName").value = biz.business_name;
        document.getElementById("serviceType").value = biz.service_type;
        document.getElementById("googleReviewLink").value = biz.google_review_link;

        const descEl = document.getElementById("businessDescription");
        if (descEl) descEl.value = biz.business_description || "";

        const socialFields = ["website", "instagram", "facebook", "whatsapp_channel", "youtube", "linkedin", "twitter_x"];
        socialFields.forEach((field) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) input.value = biz[field] || "";
        });

        reviewAspects = [...(biz.review_aspects || [])];
        renderReviewAspects();

        customLinks = (biz.custom_links || []).map((link) => ({ ...link }));
        renderCustomLinks();
    } catch (err) {
        showError(errorEl, err.message);
        return;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError(errorEl);

        updateHiddenInput();
        updateCustomLinksHiddenInput();
        const formData = new FormData(form);

        try {
            await API.request(`/api/business/${businessId}`, {
                method: "PUT",
                body: formData,
            });
            window.location.href = withFrom(`/businesses/${businessId}`, currentFrom);
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

function updateCustomLinksHiddenInput() {
    const hidden = document.getElementById("customLinks");
    if (hidden) {
        hidden.value = JSON.stringify(customLinks);
    }
}

function renderCustomLinks() {
    const container = document.getElementById("customLinksContainer");
    if (!container) return;

    container.innerHTML = "";

    customLinks.forEach((link, index) => {
        const item = document.createElement("div");
        item.className = "custom-link-item";

        item.innerHTML = `
            <div class="custom-link-info">
                <strong>${escapeHtml(link.title)}</strong>
                <span>${escapeHtml(link.url)}</span>
            </div>
            <div class="custom-link-actions">
                <button type="button" class="btn btn-secondary btn-edit-link" data-index="${index}">Edit</button>
                <button type="button" class="btn btn-danger btn-remove-link" data-index="${index}">Remove</button>
            </div>
        `;

        item.querySelector(".btn-edit-link").addEventListener("click", () => editCustomLink(index));
        item.querySelector(".btn-remove-link").addEventListener("click", () => removeCustomLink(index));

        container.appendChild(item);
    });

    updateCustomLinksHiddenInput();
}

function addOrUpdateCustomLink() {
    const titleInput = document.getElementById("customLinkTitle");
    const urlInput = document.getElementById("customLinkUrl");
    if (!titleInput || !urlInput) return;

    const title = titleInput.value.trim();
    const url = urlInput.value.trim();

    if (!title) {
        alert("Title is required.");
        return;
    }

    if (!url || !/^https?:\/\/.+/i.test(url)) {
        alert("Please enter a valid URL starting with http:// or https://");
        return;
    }

    if (editingCustomLinkIndex !== null) {
        customLinks[editingCustomLinkIndex] = { title, url };
        editingCustomLinkIndex = null;
        document.getElementById("addCustomLinkBtn").textContent = "Add";
    } else {
        customLinks.push({ title, url });
    }

    titleInput.value = "";
    urlInput.value = "";

    renderCustomLinks();
}

function editCustomLink(index) {
    const link = customLinks[index];
    if (!link) return;

    document.getElementById("customLinkTitle").value = link.title;
    document.getElementById("customLinkUrl").value = link.url;
    editingCustomLinkIndex = index;
    document.getElementById("addCustomLinkBtn").textContent = "Update";
}

function removeCustomLink(index) {
    customLinks.splice(index, 1);

    if (editingCustomLinkIndex === index) {
        editingCustomLinkIndex = null;
        document.getElementById("customLinkTitle").value = "";
        document.getElementById("customLinkUrl").value = "";
        document.getElementById("addCustomLinkBtn").textContent = "Add";
    } else if (editingCustomLinkIndex !== null && index < editingCustomLinkIndex) {
        editingCustomLinkIndex -= 1;
    }

    renderCustomLinks();
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
