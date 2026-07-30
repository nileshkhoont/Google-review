/**
 * social.js
 * Powers the public social-media landing page opened after scanning a
 * business's social QR code. No authentication is required or used here.
 */

function resolveSocialLogoUrl(logoPath) {
    if (!logoPath) return null;
    const marker = "app/static/";
    const idx = logoPath.indexOf(marker);
    return idx >= 0 ? `/static/${logoPath.slice(idx + marker.length)}` : null;
}

const SOCIAL_PLATFORMS = [
    {
        key: "website",
        label: "Website",
        icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 12h18M12 3c2.5 2.5 4 5.5 4 9s-1.5 6.5-4 9c-2.5-2.5-4-5.5-4-9s1.5-6.5 4-9z" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    },
    {
        key: "instagram",
        label: "Instagram",
        icon: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/></svg>',
    },
    {
        key: "facebook",
        label: "Facebook",
        icon: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="4" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M14 8h-1.5c-1 0-1.5.5-1.5 1.5V11h3l-.4 3H11v6h-3v-6H6.5v-3H8V9.2C8 6.9 9.3 5.5 11.6 5.5H14V8z" fill="currentColor"/></svg>',
    },
    {
        key: "whatsapp_channel",
        label: "WhatsApp Channel",
        icon: '<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.7-1.2A9 9 0 1 0 12 3z" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8.5 9.5c-.3 1 .1 2.3 1.4 3.6 1.3 1.3 2.6 1.7 3.6 1.4.5-.1.9-.6 1-1.1l.1-.6-1.7-.9-.5.7c-.1.1-.3.2-.4.1-.6-.2-1.2-.6-1.7-1.1-.5-.5-.9-1.1-1.1-1.7-.1-.2 0-.4.1-.4l.7-.5-.9-1.7-.6.1c-.5.1-1 .5-1 1.1z" fill="currentColor"/></svg>',
    },
    {
        key: "youtube",
        label: "YouTube",
        icon: '<svg viewBox="0 0 24 24"><rect x="2.5" y="5.5" width="19" height="13" rx="3.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10.5 9.5v5l4.5-2.5-4.5-2.5z" fill="currentColor"/></svg>',
    },
    {
        key: "linkedin",
        label: "LinkedIn",
        icon: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="4" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="7.5" cy="8" r="1.2" fill="currentColor"/><path d="M7.5 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M11.5 17v-3.5c0-1.4.8-2.2 2-2.2s1.8.8 1.8 2.2V17" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M11.5 11v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    },
    {
        key: "twitter_x",
        label: "X (Twitter)",
        icon: '<svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    },
];

const CUSTOM_LINK_ICON = '<svg viewBox="0 0 24 24"><path d="M9 15l6-6M10 6l1-1a4 4 0 0 1 5.6 5.6l-1 1M14 18l-1 1a4 4 0 0 1-5.6-5.6l1-1" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector(".customer-landing");
    if (!root) return;

    const slug = root.dataset.slug;
    const errorEl = document.getElementById("customerError");
    const loadingEl = document.getElementById("socialLoading");
    const emptyStateEl = document.getElementById("socialEmptyState");
    const linksContainer = document.getElementById("socialLinksContainer");

    loadingEl.classList.remove("hidden");

    let business;
    try {
        business = await API.get(`/api/customer/social/${slug}`);
    } catch (err) {
        loadingEl.classList.add("hidden");
        document.getElementById("socialInteractive").classList.add("hidden");

        const isDisabled = err.status === 403 || /disabled/i.test(err.message || "");
        if (isDisabled) {
            document.getElementById("qrDisabledState").classList.remove("hidden");
        } else {
            showError(errorEl, "This business could not be found.");
        }
        return;
    }

    document.getElementById("businessName").textContent = business.business_name;
    document.getElementById("serviceType").textContent = business.service_type;

    const logoUrl = resolveSocialLogoUrl(business.logo_path);
    if (logoUrl) {
        const logoEl = document.getElementById("businessLogo");
        logoEl.src = logoUrl;
        logoEl.classList.remove("hidden");
    }

    const availableLinks = SOCIAL_PLATFORMS
        .map((platform) => ({ ...platform, url: business[platform.key] }))
        .filter((platform) => !!platform.url);

    const customLinks = (business.custom_links || [])
        .filter((link) => !!link.url)
        .map((link) => ({ key: "other", label: link.title, url: link.url, icon: CUSTOM_LINK_ICON }));

    const allLinks = [...availableLinks, ...customLinks];

    loadingEl.classList.add("hidden");

    if (allLinks.length === 0) {
        emptyStateEl.classList.remove("hidden");
        return;
    }

    if (allLinks.length === 1) {
        window.location.replace(allLinks[0].url);
        return;
    }

    linksContainer.innerHTML = allLinks
        .map(
            (platform) => `
        <a class="social-link-btn social-link-btn--${platform.key}" href="${escapeHtml(platform.url)}" target="_blank" rel="noopener noreferrer">
            <span class="social-link-icon">${platform.icon}</span>
            <span class="social-link-label">${escapeHtml(platform.label)}</span>
        </a>
    `
        )
        .join("");
    linksContainer.classList.remove("hidden");
});
