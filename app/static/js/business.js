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

/**
 * Prepends "https://" to a URL field if the user typed a bare domain
 * (e.g. "instagram.com/biz" instead of "https://instagram.com/biz").
 * Without this, <input type="url"> fails native browser validation on a
 * missing scheme and silently blocks the whole form's submit — no error,
 * no request sent, nothing visibly happens when Save is clicked.
 */
function normalizeUrlOnBlur(input) {
    const value = input.value.trim();
    if (value && !/^https?:\/\//i.test(value)) {
        input.value = `https://${value}`;
    }
}

/** Wires normalizeUrlOnBlur() to every url-type field in a form. */
function wireUrlNormalization(form) {
    form.querySelectorAll('input[type="url"]').forEach((input) => {
        input.addEventListener("blur", () => normalizeUrlOnBlur(input));
    });
}

// Matches DEFAULT_PRIMARY_COLOR in app/utils/qr_generator.py — shown as
// the picker's starting value so what the owner sees here matches what a
// business with no primary_color set actually renders as.
const DEFAULT_PRIMARY_COLOR = "#4f46e5";
const COLOR_PRESETS = ["#4f46e5", "#2563eb", "#16a34a", "#dc2626", "#f97316", "#0891b2", "#7c3aed", "#db2777"];

/** Renders the preset swatches and keeps them in sync with the color input. */
function initColorPicker(form) {
    const colorInput = form.querySelector("#primaryColor");
    const presetsContainer = form.querySelector("#colorPresets");
    if (!colorInput || !presetsContainer) return;

    function syncActivePreset() {
        presetsContainer.querySelectorAll(".color-preset").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.color.toLowerCase() === colorInput.value.toLowerCase());
        });
    }

    presetsContainer.innerHTML = COLOR_PRESETS.map(
        (color) => `<button type="button" class="color-preset" data-color="${color}" style="background:${color}" aria-label="Use ${color}"></button>`
    ).join("");

    presetsContainer.querySelectorAll(".color-preset").forEach((btn) => {
        btn.addEventListener("click", () => {
            colorInput.value = btn.dataset.color;
            syncActivePreset();
        });
    });

    colorInput.addEventListener("input", syncActivePreset);
    syncActivePreset();
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

    wireUrlNormalization(form);
    initColorPicker(form);

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

/**
 * Wires an on/off toggle to a PATCH endpoint of the shape {is_active}.
 * Shared by the review/social/combined QR toggles and the combined page's
 * Review/Social sub-toggles — same behavior, different endpoint.
 */
function wireStatusToggle(toggleEl, statusLabelEl, initialActive, endpoint, disabledOverlayEl) {
    function updateUI(isActive) {
        toggleEl.checked = isActive;
        statusLabelEl.textContent = isActive ? "Active" : "Disabled";
        if (disabledOverlayEl) disabledOverlayEl.classList.toggle("hidden", isActive);
    }

    updateUI(initialActive);

    toggleEl.addEventListener("change", async () => {
        const newStatus = toggleEl.checked;
        toggleEl.disabled = true;
        try {
            await API.patch(endpoint, { is_active: newStatus });
            updateUI(newStatus);
        } catch (err) {
            updateUI(!newStatus);
            alert(err.message);
        } finally {
            toggleEl.disabled = false;
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
        document.getElementById("openCombinedPageBtn").href = `/c/${biz.combined_slug}`;

        // combined_only businesses (created after the single-QR change) never
        // got a review-only or social-only QR generated, so those two cards
        // have nothing to show — hide them and only fetch the combined QR.
        const isCombinedOnly = !!biz.combined_only;
        document.getElementById("reviewQrCard").classList.toggle("hidden", isCombinedOnly);
        document.getElementById("socialQrCard").classList.toggle("hidden", isCombinedOnly);

        const qrFetches = [
            (async () => {
                try {
                    await API.get(`/api/qr/${businessId}/combined`);
                    const combinedQrImg = document.getElementById("combinedQrImage");
                    combinedQrImg.src = `/api/qr/${businessId}/combined/download?t=${Date.now()}`;
                    combinedQrImg.classList.remove("hidden");
                } catch (_) {
                    // No combined QR yet — shouldn't normally happen since it's auto-generated.
                }
            })(),
        ];

        if (!isCombinedOnly) {
            qrFetches.push(
                (async () => {
                    try {
                        await API.get(`/api/qr/${businessId}`);
                        const qrImg = document.getElementById("qrImage");
                        qrImg.src = `/api/qr/${businessId}/download?t=${Date.now()}`;
                        qrImg.classList.remove("hidden");
                    } catch (_) {
                        // No QR yet — shouldn't normally happen since it's auto-generated.
                    }
                })(),
                (async () => {
                    try {
                        await API.get(`/api/qr/${businessId}/social`);
                        const socialQrImg = document.getElementById("socialQrImage");
                        socialQrImg.src = `/api/qr/${businessId}/social/download?t=${Date.now()}`;
                        socialQrImg.classList.remove("hidden");
                    } catch (_) {
                        // No social QR yet — shouldn't normally happen since it's auto-generated.
                    }
                })(),
            );
        }

        // QR, social QR, and combined QR are independent lookups — run them
        // concurrently instead of one after another.
        await Promise.all(qrFetches);

        if (isCombinedOnly) {
            // This business's only QR is the combined one — its two halves
            // (review flow / social links) are toggled independently, reusing
            // the same is_active / social_is_active fields and endpoints that
            // legacy businesses use to gate their separate review-only and
            // social-only pages.
            document.getElementById("combinedSingleToggle").classList.add("hidden");
            document.getElementById("combinedDualToggle").classList.remove("hidden");
            document.getElementById("combinedQrDisabledOverlay").classList.add("hidden");

            wireStatusToggle(
                document.getElementById("combinedReviewToggle"),
                document.getElementById("combinedReviewStatusLabel"),
                biz.is_active !== false,
                `/api/business/${businessId}/status`,
            );
            wireStatusToggle(
                document.getElementById("combinedSocialToggle"),
                document.getElementById("combinedSocialStatusLabel"),
                biz.social_is_active !== false,
                `/api/business/${businessId}/social-status`,
            );
        } else {
            wireStatusToggle(
                document.getElementById("qrActiveToggle"),
                document.getElementById("qrStatusLabel"),
                biz.is_active !== false,
                `/api/business/${businessId}/status`,
                document.getElementById("qrDisabledOverlay"),
            );
            wireStatusToggle(
                document.getElementById("socialQrActiveToggle"),
                document.getElementById("socialQrStatusLabel"),
                biz.social_is_active !== false,
                `/api/business/${businessId}/social-status`,
                document.getElementById("socialQrDisabledOverlay"),
            );
            wireStatusToggle(
                document.getElementById("combinedQrActiveToggle"),
                document.getElementById("combinedQrStatusLabel"),
                biz.combined_is_active !== false,
                `/api/business/${businessId}/combined-status`,
                document.getElementById("combinedQrDisabledOverlay"),
            );
        }

        document.getElementById("downloadQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/download`;
        });

        document.getElementById("downloadSocialQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/social/download`;
        });

        document.getElementById("downloadCombinedQrBtn").addEventListener("click", () => {
            window.location.href = `/api/qr/${businessId}/combined/download`;
        });

        // Not awaited: the activity summary is its own aggregation query and
        // shouldn't hold up attaching the listeners below (the delete
        // button in particular) behind an extra round trip. It manages its
        // own "Loading..." / error state in the DOM once it resolves.
        loadBusinessActivity(businessId);

        const activityStartDateFilter = document.getElementById("activityStartDateFilter");
        const activityEndDateFilter = document.getElementById("activityEndDateFilter");
        const activityDateClearBtn = document.getElementById("activityDateClearBtn");
        const activityDatePresets = document.getElementById("activityDatePresets");
        const todayIST = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
        activityStartDateFilter.max = todayIST;
        activityEndDateFilter.max = todayIST;

        function syncActivityPresetHighlight() {
            const start = activityStartDateFilter.value;
            const end = activityEndDateFilter.value;
            activityDatePresets.querySelectorAll(".date-preset-btn").forEach((btn) => {
                const preset = ACTIVITY_DATE_PRESETS.find((p) => p.key === btn.dataset.presetKey);
                const [presetStart, presetEnd] = preset.range(todayIST);
                btn.classList.toggle("active", start === presetStart && end === presetEnd);
            });
        }

        function applyActivityDateFilter() {
            // Keep the range coherent: start can't be after end, in either
            // direction of edit.
            if (activityStartDateFilter.value && activityEndDateFilter.value) {
                if (activityStartDateFilter.value > activityEndDateFilter.value) {
                    activityEndDateFilter.value = activityStartDateFilter.value;
                }
            }
            const hasFilter = activityStartDateFilter.value || activityEndDateFilter.value;
            activityDateClearBtn.classList.toggle("hidden", !hasFilter);
            syncActivityPresetHighlight();
            loadBusinessActivity(businessId, activityStartDateFilter.value, activityEndDateFilter.value);
        }

        activityStartDateFilter.addEventListener("change", applyActivityDateFilter);
        activityEndDateFilter.addEventListener("change", applyActivityDateFilter);

        activityDateClearBtn.addEventListener("click", () => {
            activityStartDateFilter.value = "";
            activityEndDateFilter.value = "";
            activityDateClearBtn.classList.add("hidden");
            syncActivityPresetHighlight();
            loadBusinessActivity(businessId);
        });

        activityDatePresets.innerHTML = ACTIVITY_DATE_PRESETS.map(
            (preset) => `
            <button type="button" class="date-preset-btn" data-preset-key="${preset.key}">${preset.label}</button>
        `
        ).join("");

        activityDatePresets.querySelectorAll(".date-preset-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const preset = ACTIVITY_DATE_PRESETS.find((p) => p.key === btn.dataset.presetKey);
                const [start, end] = preset.range(todayIST);
                activityStartDateFilter.value = start;
                activityEndDateFilter.value = end;
                applyActivityDateFilter();
            });
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

/**
 * Shifts a "YYYY-MM-DD" calendar date by whole days and/or months. Uses
 * Date.UTC as a pure calendar-math anchor (not a real moment) so this never
 * drifts across the admin's local timezone or DST — only the Y/M/D fields
 * matter here, never a time-of-day.
 */
function shiftISTDate(dateStr, { days = 0, months = 0 } = {}) {
    const [y, m, d] = dateStr.split("-").map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d));
    if (months) dt.setUTCMonth(dt.getUTCMonth() + months);
    if (days) dt.setUTCDate(dt.getUTCDate() + days);
    return dt.toISOString().slice(0, 10);
}

const ACTIVITY_DATE_PRESETS = [
    { key: "yesterday", label: "Yesterday", range: (today) => {
        const yesterday = shiftISTDate(today, { days: -1 });
        return [yesterday, yesterday];
    } },
    { key: "last5", label: "Last 5 Days", range: (today) => [shiftISTDate(today, { days: -4 }), today] },
    { key: "last10", label: "Last 10 Days", range: (today) => [shiftISTDate(today, { days: -9 }), today] },
    { key: "lastMonth", label: "Last Month", range: (today) => [shiftISTDate(today, { months: -1 }), today] },
    { key: "last3Months", label: "Last 3 Months", range: (today) => [shiftISTDate(today, { months: -3 }), today] },
];

// Fixed categorical order (never reassigned per-render) so a slice's color
// stays tied to its rank, not its identity — acceptable here since the
// legend is always shown alongside and carries the real identity mapping.
const PIE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const PIE_OTHER_COLOR = "#9aa1b1";
const PIE_MAX_SLICES = 7;

function polarToCartesian(cx, cy, r, angleDeg) {
    const rad = ((angleDeg - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

/** SVG path for one pie wedge; a >=360° slice (only one category) draws as a full circle. */
function describePieSlice(cx, cy, r, startAngle, endAngle) {
    if (endAngle - startAngle >= 359.999) {
        const p1 = polarToCartesian(cx, cy, r, 0);
        const p2 = polarToCartesian(cx, cy, r, 180);
        return `M ${p1.x} ${p1.y} A ${r} ${r} 0 1 1 ${p2.x} ${p2.y} A ${r} ${r} 0 1 1 ${p1.x} ${p1.y} Z`;
    }
    const start = polarToCartesian(cx, cy, r, endAngle);
    const end = polarToCartesian(cx, cy, r, startAngle);
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`;
}

/**
 * Collapses the (page, action) rows into pie slices, folding everything
 * past the top 7 into "Other" — past that many slots, adjacent hues stop
 * being reliably distinguishable (see the dataviz skill's series-count
 * ladder), and a legend row per slice stops being scannable anyway.
 */
function buildPieSlices(actions) {
    const sorted = [...actions].sort((a, b) => b.count - a.count);
    const top = sorted.slice(0, PIE_MAX_SLICES);
    const rest = sorted.slice(PIE_MAX_SLICES);

    const slices = top.map((a) => ({
        label: formatActionRowLabel(a.action, a.page),
        count: a.count,
    }));
    if (rest.length > 0) {
        slices.push({
            label: `Other (${rest.length})`,
            count: rest.reduce((sum, a) => sum + a.count, 0),
        });
    }
    return slices;
}

function positionPieTooltip(tooltip, container, evt) {
    const rect = container.getBoundingClientRect();
    const x = evt.clientX !== undefined ? evt.clientX - rect.left : rect.width / 2;
    const y = evt.clientY !== undefined ? evt.clientY - rect.top : rect.height / 2;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
}

function wirePieTooltips(container) {
    const tooltip = container.querySelector(".pie-tooltip");
    if (!tooltip) return;

    container.querySelectorAll(".pie-slice").forEach((slice) => {
        const show = (evt) => {
            // textContent, not innerHTML: action/page strings ultimately come
            // from the public track-click endpoint, so treat their labels as
            // untrusted even though they're already escaped once upstream.
            tooltip.textContent = "";
            const value = document.createElement("span");
            value.className = "pie-tooltip-value";
            value.textContent = slice.dataset.count;
            const label = document.createElement("span");
            label.className = "pie-tooltip-label";
            label.textContent = `${slice.dataset.label} · ${slice.dataset.percent}%`;
            tooltip.append(value, label);
            tooltip.classList.remove("hidden");
            positionPieTooltip(tooltip, container, evt);
            slice.classList.add("pie-slice-active");
        };
        const hide = () => {
            tooltip.classList.add("hidden");
            slice.classList.remove("pie-slice-active");
        };

        slice.addEventListener("pointerenter", show);
        slice.addEventListener("pointermove", (evt) => positionPieTooltip(tooltip, container, evt));
        slice.addEventListener("pointerleave", hide);
        slice.addEventListener("focus", show);
        slice.addEventListener("blur", hide);
    });
}

function renderActivityPieChart(actions) {
    const chartEl = document.getElementById("activityPieChart");
    const legendEl = document.getElementById("activityPieLegend");
    if (!chartEl || !legendEl) return;

    if (actions.length === 0) {
        chartEl.innerHTML = "";
        legendEl.innerHTML = "";
        return;
    }

    const slices = buildPieSlices(actions);
    const total = slices.reduce((sum, s) => sum + s.count, 0);
    const size = 200;
    const cx = size / 2;
    const cy = size / 2;
    const r = 90;

    let angle = 0;
    const paths = slices
        .map((slice, i) => {
            const fraction = slice.count / total;
            const startAngle = angle;
            const endAngle = angle + fraction * 360;
            angle = endAngle;
            const color = i < PIE_COLORS.length ? PIE_COLORS[i] : PIE_OTHER_COLOR;
            const percent = Math.round(fraction * 100);
            const label = escapeHtml(slice.label);
            return `
            <path
                d="${describePieSlice(cx, cy, r, startAngle, endAngle)}"
                fill="${color}"
                class="pie-slice"
                tabindex="0"
                aria-label="${label}: ${slice.count} (${percent}%)"
                data-label="${label}"
                data-count="${slice.count}"
                data-percent="${percent}"
            ></path>
        `;
        })
        .join("");

    chartEl.innerHTML = `
        <svg viewBox="0 0 ${size} ${size}" class="pie-svg" role="img" aria-label="Click breakdown by action">${paths}</svg>
        <div class="pie-tooltip hidden"></div>
    `;

    legendEl.innerHTML = slices
        .map((slice, i) => {
            const color = i < PIE_COLORS.length ? PIE_COLORS[i] : PIE_OTHER_COLOR;
            const percent = Math.round((slice.count / total) * 100);
            return `
            <div class="pie-legend-row">
                <span class="pie-legend-swatch" style="background:${color}"></span>
                <span class="pie-legend-label">${escapeHtml(slice.label)}</span>
                <span class="pie-legend-value">${slice.count} <span class="muted">(${percent}%)</span></span>
            </div>
        `;
        })
        .join("");

    wirePieTooltips(chartEl);
}

async function loadBusinessActivity(businessId, startDate, endDate) {
    const breakdown = document.getElementById("activityBreakdown");
    if (!breakdown) return;

    try {
        const params = new URLSearchParams();
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);
        const query = params.toString();
        const url = `/api/business/${businessId}/click-logs/summary${query ? `?${query}` : ""}`;
        const actions = await API.get(url);
        const hasDateFilter = Boolean(startDate || endDate);

        renderActivityPieChart(actions);

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
            breakdown.innerHTML = hasDateFilter
                ? `<p class="muted">No activity in this date range.</p>`
                : `<p class="muted">No activity recorded yet.</p>`;
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
        renderActivityPieChart([]);
    }
}

async function initEditBusinessPage() {
    const form = document.getElementById("editBusinessForm");
    if (!form) return;

    wireUrlNormalization(form);
    initColorPicker(form);

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

        const qrTitleInput = form.querySelector("#qrTitle");
        if (qrTitleInput) qrTitleInput.value = biz.qr_title || "";

        const gujaratiCheckbox = form.querySelector("#enableGujarati");
        if (gujaratiCheckbox) gujaratiCheckbox.checked = Boolean(biz.enable_gujarati);

        const hindiCheckbox = form.querySelector("#enableHindi");
        if (hindiCheckbox) hindiCheckbox.checked = Boolean(biz.enable_hindi);

        const colorInput = form.querySelector("#primaryColor");
        if (colorInput) {
            colorInput.value = biz.primary_color || DEFAULT_PRIMARY_COLOR;
            colorInput.dispatchEvent(new Event("input"));
        }

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
    let url = urlInput.value.trim();
    if (url && !/^https?:\/\//i.test(url)) {
        url = `https://${url}`;
    }

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
