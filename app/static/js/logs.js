/**
 * logs.js
 * Powers the admin-only /logs page: per-company click totals and a
 * paginated, filterable raw event table.
 */

const LOGS_PAGE_SIZE = 25;

let logsState = {
    skip: 0,
    businessId: "",
    total: 0,
};

function companySummaryRowHTML(row) {
    return `
        <a class="company-summary-row" href="/businesses/${row.business_id}">
            <span class="company-summary-name">${escapeHtml(row.business_name)}</span>
            <span class="company-summary-clicks">${row.total_clicks} clicks</span>
            <span class="company-summary-time muted">Last activity ${formatIST(row.last_activity_at)}</span>
        </a>
    `;
}

async function loadCompanySummary() {
    const container = document.getElementById("companySummary");
    const filterSelect = document.getElementById("logsBusinessFilter");

    try {
        const summary = await API.get("/api/logs/summary");

        if (summary.length === 0) {
            container.innerHTML = `<p class="muted">No activity recorded yet.</p>`;
        } else {
            container.innerHTML = summary.map(companySummaryRowHTML).join("");
        }

        summary.forEach((row) => {
            const option = document.createElement("option");
            option.value = row.business_id;
            option.textContent = row.business_name;
            filterSelect.appendChild(option);
        });
    } catch (err) {
        container.innerHTML = `<p class="form-error">${err.message}</p>`;
    }
}

function logRowHTML(entry) {
    return `
        <div class="log-row">
            <span class="log-row-time">${formatIST(entry.created_at)}</span>
            <a class="log-row-business" href="/businesses/${entry.business_id}">${escapeHtml(entry.business_name)}</a>
            <span class="log-row-page">${entry.page === "social" ? "Social Page" : "Review Page"}</span>
            <span class="log-row-action">${escapeHtml(formatActionLabel(entry.action))}</span>
        </div>
    `;
}

async function loadLogsTable() {
    const container = document.getElementById("logsTable");
    const prevBtn = document.getElementById("logsPrevBtn");
    const nextBtn = document.getElementById("logsNextBtn");
    const pageLabel = document.getElementById("logsPageLabel");

    try {
        const params = new URLSearchParams({
            limit: LOGS_PAGE_SIZE,
            skip: logsState.skip,
        });
        if (logsState.businessId) params.set("business_id", logsState.businessId);

        const result = await API.get(`/api/logs?${params.toString()}`);
        logsState.total = result.total;

        container.innerHTML =
            result.items.length === 0
                ? `<p class="muted">No clicks recorded yet.</p>`
                : result.items.map(logRowHTML).join("");

        const currentPage = Math.floor(logsState.skip / LOGS_PAGE_SIZE) + 1;
        const totalPages = Math.max(1, Math.ceil(logsState.total / LOGS_PAGE_SIZE));
        pageLabel.textContent = `Page ${currentPage} of ${totalPages}`;

        prevBtn.disabled = logsState.skip === 0;
        nextBtn.disabled = logsState.skip + LOGS_PAGE_SIZE >= logsState.total;
    } catch (err) {
        container.innerHTML = `<p class="form-error">${err.message}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    const user = await guardProtectedPage();
    if (!user) return;

    const page = document.querySelector(".logs-page");
    if (!page) return;

    await loadCompanySummary();
    await loadLogsTable();

    document.getElementById("logsBusinessFilter").addEventListener("change", (e) => {
        logsState.businessId = e.target.value;
        logsState.skip = 0;
        loadLogsTable();
    });

    document.getElementById("logsPrevBtn").addEventListener("click", () => {
        logsState.skip = Math.max(0, logsState.skip - LOGS_PAGE_SIZE);
        loadLogsTable();
    });

    document.getElementById("logsNextBtn").addEventListener("click", () => {
        logsState.skip += LOGS_PAGE_SIZE;
        loadLogsTable();
    });
});
