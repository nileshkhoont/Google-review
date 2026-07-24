/**
 * customer.js
 * Powers the public customer landing page opened after a QR scan.
 * No authentication is required or used here.
 */

function resolveLogoUrl(logoPath) {
    if (!logoPath) return null;
    const marker = "app/static/";
    const idx = logoPath.indexOf(marker);
    return idx >= 0 ? `/static/${logoPath.slice(idx + marker.length)}` : null;
}

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector(".customer-landing");
    if (!root) return;

    const slug = root.dataset.slug;
    const errorEl = document.getElementById("customerError");

    let googleReviewLink = "#";

    let reviewList = [];
    let currentReviewIndex = 0;
    let currentLanguage = "en";

    try {
        const business = await API.get(`/api/customer/${slug}`);

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

        const logoUrl = resolveLogoUrl(business.logo_path);
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

    const generateBtn = document.getElementById("generateReviewBtn");
    const regenerateBtn = document.getElementById("regenerateReviewBtn");

    const ratingSelector = document.getElementById("ratingSelector");
    const ratingStars = ratingSelector ? Array.from(ratingSelector.querySelectorAll(".rating-star")) : [];
    const selectedRatingValueEl = document.getElementById("selectedRatingValue");

    function setRating(rating) {
        // rating is 1..5
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

                displayCurrentReview();

            });

            reviewIndicators.appendChild(dot);

        });

    }

    function displayCurrentReview() {

        if (reviewList.length === 0) {
            return;
        }

        const review = reviewList[currentReviewIndex];

        textArea.value =
            review.translations[currentLanguage];

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

        nextReviewBtn.disabled =
            currentReviewIndex === reviewList.length - 1;

    }

    let touchStartX = 0;
    let touchEndX = 0;

    function handleSwipe() {

        const distance = touchEndX - touchStartX;

        // Swipe Left → Next Review
        if (distance < -60) {

            if (currentReviewIndex < reviewList.length - 1) {

                currentReviewIndex++;

                displayCurrentReview();

            }

        }

        // Swipe Right → Previous Review
        else if (distance > 60) {

            if (currentReviewIndex > 0) {

                currentReviewIndex--;

                displayCurrentReview();

            }

        }

    }

    function switchLanguage(language) {

        currentLanguage = language;

        displayCurrentReview();

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
        generateBtn.classList.add("hidden");
        regenerateBtn.classList.add("hidden");
        resultEl.classList.add("hidden");
        loadingEl.classList.remove("hidden");

        try {
            const selectedRating = Number(document.getElementById("selectedRatingValue").textContent) || null;
            const selectedReviewAspects = getSelectedReviewAspects();
            const result = await API.post(`/api/customer/${slug}/generate-review`,
                {
                    rating: selectedRating,
                    selected_review_aspects: selectedReviewAspects,
                }
            );

            reviewList = result.reviews;
            console.log(result);
            console.log(reviewList);
            console.log("Total Reviews:", reviewList.length);


            currentReviewIndex = 0;
            currentLanguage = "en";


            languageSelector.classList.remove("hidden");

            displayCurrentReview();

            openGoogleBtn.href = result.google_review_link || googleReviewLink;

            loadingEl.classList.add("hidden");

            regenerateBtn.classList.remove("hidden");
            resultEl.classList.remove("hidden");
        } catch (err) {
            console.error("Generate Review Error:", err);
            loadingEl.classList.add("hidden");
            generateBtn.classList.remove("hidden");
            showError(errorEl, err.message);
        }
    }

    generateBtn.addEventListener("click", generateReview);
    regenerateBtn.addEventListener("click", generateReview);

    generateReview();

    previousReviewBtn.addEventListener("click", () => {

        if (currentReviewIndex === 0) {
            return;
        }

        currentReviewIndex--;

        displayCurrentReview();

    });

    nextReviewBtn.addEventListener("click", () => {

        if (currentReviewIndex >= reviewList.length - 1) {
            return;
        }

        currentReviewIndex++;

        displayCurrentReview();

    });

    languageButtons.forEach((button) => {

        button.addEventListener("click", () => {

            switchLanguage(button.dataset.language);

        });

    });

    copyBtn.addEventListener("click", async () => {
        await copyReview();
        copyBtn.textContent = "✅ Copied!";
        setTimeout(() => {
            copyBtn.textContent = "📋 Copy Review";
        }, 2000);
    });

    openGoogleBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        await copyReview();
        window.open(openGoogleBtn.href, "_blank");
    });
});
