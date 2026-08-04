/**
 * combined.js
 * Powers the public combined landing page (/c/{slug}) opened after a QR
 * scan — the review-generation flow on top, social links below it. No
 * authentication is required or used here.
 */

function resolveCombinedLogoUrl(logoPath) {
    if (!logoPath) return null;
    const marker = "app/static/";
    const idx = logoPath.indexOf(marker);
    return idx >= 0 ? `/static/${logoPath.slice(idx + marker.length)}` : null;
}

const COMBINED_SOCIAL_PLATFORMS = [
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

const COMBINED_CUSTOM_LINK_ICON = '<svg viewBox="0 0 24 24"><path d="M9 15l6-6M10 6l1-1a4 4 0 0 1 5.6 5.6l-1 1M14 18l-1 1a4 4 0 0 1-5.6-5.6l1-1" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>';

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector(".combined-landing");
    if (!root) return;

    const slug = root.dataset.slug;
    const trackEndpoint = `/api/customer/combined/${slug}/track-click`;
    const errorEl = document.getElementById("customerError");

    let googleReviewLink = "#";

    let reviewList = [];
    let currentReviewIndex = 0;
    let currentLanguage = "en";

    let business;
    try {
        business = await API.get(`/api/customer/combined/${slug}`);

        document.getElementById("businessName").textContent = business.business_name;
        document.getElementById("serviceType").textContent = business.service_type;
        googleReviewLink = business.google_review_link;

        const aspectSection = document.getElementById("reviewAspectSection");
        const aspectContainer = document.getElementById("customerReviewAspects");
        if (business.review_aspects && business.review_aspects.length > 0) {
            aspectSection.classList.remove("hidden");
            aspectContainer.innerHTML = "";
            business.review_aspects.forEach((aspect) => {
                const label = document.createElement("label");
                label.className = "customer-review-aspect";
                label.innerHTML =
                    `<input type="checkbox" value="${aspect}">
                <span>${aspect}</span>`;
                aspectContainer.appendChild(label);
            });
        }

        const logoUrl = resolveCombinedLogoUrl(business.logo_path);
        if (logoUrl) {
            const logoEl = document.getElementById("businessLogo");
            logoEl.src = logoUrl;
            logoEl.classList.remove("hidden");
        }
    } catch (err) {
        document.getElementById("customerInteractive").classList.add("hidden");

        const isDisabled = err.status === 403 || /disabled/i.test(err.message || "");
        if (isDisabled) {
            document.getElementById("qrDisabledState").classList.remove("hidden");
        } else {
            showError(errorEl, "This business could not be found.");
        }
        return;
    }

    renderCombinedSocialLinks(business);

    const regenerateBtn = document.getElementById("regenerateReviewBtn");

    const ratingSelector = document.getElementById("ratingSelector");
    const ratingStars = ratingSelector ? Array.from(ratingSelector.querySelectorAll(".rating-star")) : [];
    const selectedRatingValueEl = document.getElementById("selectedRatingValue");

    function setRating(rating) {
        ratingStars.forEach((starEl) => {
            const v = Number(starEl.dataset.value);
            if (v <= rating) {
                starEl.classList.add("filled");
                starEl.textContent = "★";
            } else {
                starEl.classList.remove("filled");
                starEl.textContent = "☆";
            }
        });
        if (selectedRatingValueEl) selectedRatingValueEl.textContent = String(rating);
    }

    function initRating() {
        if (!ratingSelector || ratingStars.length !== 5) return;
        setRating(5);

        ratingStars.forEach((starEl) => {
            const value = Number(starEl.dataset.value);
            starEl.addEventListener("click", () => {
                setRating(value);
            });
            starEl.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setRating(value);
                }
            });
        });
    }

    initRating();

    const loadingEl = document.getElementById("loadingIndicator");
    const resultEl = document.getElementById("reviewResult");
    const textArea = document.getElementById("reviewText");
    const languageSelector = document.getElementById("reviewLanguageSelector");
    const languageButtons = document.querySelectorAll(".review-language-btn");

    const reviewNavigator = document.getElementById("reviewNavigator");
    const previousReviewBtn = document.getElementById("previousReviewBtn");
    const nextReviewBtn = document.getElementById("nextReviewBtn");
    const reviewIndicators = document.getElementById("reviewIndicators");

    const openGoogleBtn = document.getElementById("openGoogleReviewBtn");
    const copyBtn = document.getElementById("copyReviewBtn");

    let touchStartX = 0;
    let touchEndX = 0;

    textArea.addEventListener("touchstart", (event) => {
        touchStartX = event.changedTouches[0].screenX;
    });

    textArea.addEventListener("touchend", (event) => {
        touchEndX = event.changedTouches[0].screenX;
        handleSwipe();
    });

    function getSelectedReviewAspects() {
        return Array.from(
            document.querySelectorAll("#customerReviewAspects input[type='checkbox']:checked"))
            .map(item => item.value);
    }

    function renderReviewIndicators() {
        reviewIndicators.innerHTML = "";

        reviewList.forEach((_, index) => {
            const dot = document.createElement("span");
            dot.className = "review-indicator";
            if (index === currentReviewIndex) {
                dot.classList.add("active");
            }
            dot.addEventListener("click", () => {
                currentReviewIndex = index;
                showCurrentReview();
            });
            reviewIndicators.appendChild(dot);
        });
    }

    function renderReview() {
        if (reviewList.length === 0) {
            return;
        }

        const review = reviewList[currentReviewIndex];
        textArea.value = review[currentLanguage] ?? "";

        languageButtons.forEach((button) => {
            button.classList.toggle(
                "active",
                button.dataset.language === currentLanguage
            );
        });

        renderReviewIndicators();

        reviewNavigator.classList.toggle(
            "hidden",
            reviewList.length <= 1
        );

        previousReviewBtn.disabled = currentReviewIndex === 0;
        nextReviewBtn.disabled = currentReviewIndex === reviewList.length - 1;
    }

    async function ensureTranslation(review, language) {
        if (language === "en" || review[language]) {
            return;
        }
        const result = await API.post(`/api/customer/combined/${slug}/translate-review`, {
            text: review.en,
            language,
        });
        review[language] = result.translation;
    }

    function setLanguageControlsDisabled(disabled) {
        languageButtons.forEach((button) => { button.disabled = disabled; });
        previousReviewBtn.disabled = disabled || currentReviewIndex === 0;
        nextReviewBtn.disabled = disabled || currentReviewIndex === reviewList.length - 1;
    }

    async function showCurrentReview() {
        if (reviewList.length === 0) {
            return;
        }

        const review = reviewList[currentReviewIndex];

        if (currentLanguage === "en" || review[currentLanguage]) {
            renderReview();
            return;
        }

        hideError(errorEl);
        setLanguageControlsDisabled(true);
        textArea.value = "Translating...";

        try {
            await ensureTranslation(review, currentLanguage);
            renderReview();
        } catch (err) {
            showError(errorEl, "Could not translate this review. Please try again.");
            renderReview();
        } finally {
            setLanguageControlsDisabled(false);
        }
    }

    function handleSwipe() {
        const distance = touchEndX - touchStartX;

        if (distance < -60) {
            if (currentReviewIndex < reviewList.length - 1) {
                currentReviewIndex++;
                showCurrentReview();
            }
        } else if (distance > 60) {
            if (currentReviewIndex > 0) {
                currentReviewIndex--;
                showCurrentReview();
            }
        }
    }

    function switchLanguage(language) {
        currentLanguage = language;
        showCurrentReview();
    }

    async function copyReview() {
        try {
            await navigator.clipboard.writeText(textArea.value);
        } catch (_) {
            textArea.select();
            document.execCommand("copy");
        }
    }

    async function generateReview() {
        hideError(errorEl);
        regenerateBtn.classList.add("hidden");
        resultEl.classList.add("hidden");
        loadingEl.classList.remove("hidden");

        try {
            const selectedRating = Number(document.getElementById("selectedRatingValue").textContent) || null;
            const selectedReviewAspects = getSelectedReviewAspects();
            const result = await API.post(`/api/customer/combined/${slug}/generate-review`,
                {
                    rating: selectedRating,
                    selected_review_aspects: selectedReviewAspects,
                }
            );

            reviewList = result.reviews;
            currentReviewIndex = 0;
            currentLanguage = "en";

            languageSelector.classList.remove("hidden");

            renderReview();

            openGoogleBtn.href = result.google_review_link || googleReviewLink;

            loadingEl.classList.add("hidden");

            regenerateBtn.classList.remove("hidden");
            resultEl.classList.remove("hidden");
        } catch (err) {
            loadingEl.classList.add("hidden");
            regenerateBtn.classList.remove("hidden");
            resultEl.classList.remove("hidden");
            showError(errorEl, err.message);
        }
    }

    regenerateBtn.addEventListener("click", () => {
        trackClick(trackEndpoint, "generate_review");
        generateReview();
    });

    // Initial load auto-generates a review — not a customer click, so it
    // bypasses the listener above and isn't tracked.
    generateReview();

    previousReviewBtn.addEventListener("click", () => {
        if (currentReviewIndex === 0) {
            return;
        }
        trackClick(trackEndpoint, "previous_review");
        currentReviewIndex--;
        showCurrentReview();
    });

    nextReviewBtn.addEventListener("click", () => {
        if (currentReviewIndex >= reviewList.length - 1) {
            return;
        }
        trackClick(trackEndpoint, "next_review");
        currentReviewIndex++;
        showCurrentReview();
    });

    languageButtons.forEach((button) => {
        button.addEventListener("click", () => {
            trackClick(trackEndpoint, `language_switch_${button.dataset.language}`);
            switchLanguage(button.dataset.language);
        });
    });

    copyBtn.addEventListener("click", async () => {
        trackClick(trackEndpoint, "copy_review");
        await copyReview();
        copyBtn.textContent = "✅ Copied!";
        setTimeout(() => {
            copyBtn.textContent = "📋 Copy Review";
        }, 2000);
    });

    openGoogleBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        trackClick(trackEndpoint, "open_google_review");
        await copyReview();
        window.open(openGoogleBtn.href, "_blank");
    });

    function renderCombinedSocialLinks(businessData) {
        const section = document.getElementById("combinedSocialSection");
        const linksContainer = document.getElementById("socialLinksContainer");

        const availableLinks = COMBINED_SOCIAL_PLATFORMS
            .map((platform) => ({ ...platform, url: businessData[platform.key] }))
            .filter((platform) => !!platform.url);

        const customLinks = (businessData.custom_links || [])
            .filter((link) => !!link.url)
            .map((link) => ({ key: "other", label: link.title, url: link.url, icon: COMBINED_CUSTOM_LINK_ICON }));

        const allLinks = [...availableLinks, ...customLinks];

        // No links at all — leave the whole "Connect With Us" section
        // (heading included) hidden instead of showing an empty state.
        if (allLinks.length === 0) {
            return;
        }

        section.classList.remove("hidden");

        linksContainer.innerHTML = allLinks
            .map(
                (platform, index) => `
            <a class="social-link-btn social-link-btn--${platform.key}" data-link-index="${index}" href="${escapeHtml(platform.url)}" target="_blank" rel="noopener noreferrer">
                <span class="social-link-icon">${platform.icon}</span>
                <span class="social-link-label">${escapeHtml(platform.label)}</span>
            </a>
        `
            )
            .join("");
        linksContainer.classList.remove("hidden");

        linksContainer.querySelectorAll("[data-link-index]").forEach((linkEl) => {
            const platform = allLinks[Number(linkEl.dataset.linkIndex)];
            linkEl.addEventListener("click", () => {
                trackClick(trackEndpoint, `social_link_${platform.key}`);
            });
        });
    }
});
