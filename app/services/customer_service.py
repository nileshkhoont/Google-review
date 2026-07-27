"""Business logic for the customer-facing flow: business lookup by slug
and AI review generation."""

from fastapi import HTTPException, status

from app.ai.review_generator import ReviewGenerator
from app.models.review import build_review_document
from app.repositories.business_repository import BusinessRepository
from app.repositories.review_repository import ReviewRepository
from app.utils.logger import logger

import random
from app.config import settings


class CustomerService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        review_repo: ReviewRepository,
        review_generator: ReviewGenerator | None = None,
    ):
        self.business_repo = business_repo
        self.review_repo = review_repo
        self.review_generator = review_generator or ReviewGenerator()

    async def get_business_by_slug(self, slug: str) -> dict:
        business = await self.business_repo.get_by_slug(slug)
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")
        if not business.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This QR code has been disabled by the business owner.",
            )
        return business

    async def generate_review(
        self, 
        slug: str,  
        rating: int | None = None,
        selected_review_aspects: list[str] | None = None,
    ) -> dict:
        business = await self.get_business_by_slug(slug)
        
        review_aspects = selected_review_aspects
        if not review_aspects: 
            available_aspects = business.get("review_aspects", [])
            
            if available_aspects:
                aspect_count = min(
                    settings.random_aspects_count,
                    len(available_aspects),
                )
                
                review_aspects = random.sample(
                    available_aspects,
                    k=aspect_count,
                )

        try:
            review_list = await self.review_generator.generate(
                business_name=business["business_name"],
                service_type=business["service_type"],
                business_description=business.get("business_description"),
                rating=rating,
                selected_review_aspects=review_aspects,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Review generation failed for slug '%s': %s", slug, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not generate a review right now. Please try again.",
            ) from exc

        # Optional history log — never blocks the customer flow if it fails.
        try:
            for review_text in review_list:
                review_doc = build_review_document(
                    business["_id"],
                    review_text,
                )
                await self.review_repo.create(review_doc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save review history: %s", exc)

        return {
            "reviews": [
                {
                    "en": review_text
                }
                for review_text in review_list
            ],

            "business_name": business["business_name"],
            "google_review_link": business["google_review_link"],
        }

    async def translate_review(
        self,
        slug: str,
        text: str,
        language: str,
    ) -> str:
        """
        Translate one review (the variant currently on screen) into one
        language, on demand — called only when the customer taps that
        language tab, instead of eagerly translating every generated
        variant into every language up front.
        """
        await self.get_business_by_slug(slug)  # 404/403 checks

        try:
            return await self.review_generator.translate_single_review(text, language)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Review translation to '%s' failed for slug '%s': %s", language, slug, exc
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not translate the review right now. Please try again.",
            ) from exc
