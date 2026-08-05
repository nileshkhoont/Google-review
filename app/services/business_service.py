"""Business logic for creating, listing, updating, and deleting businesses."""

import os

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.models.business import build_business_document
from app.repositories.business_repository import BusinessRepository
from app.repositories.qr_repository import QRRepository
from app.schemas.business_schema import SOCIAL_LINK_FIELDS, BusinessCreateRequest, BusinessUpdateRequest

# Fields the edit form always submits in full (never partial), where an
# empty value means "the owner cleared this" and must overwrite whatever
# was saved before — as opposed to business_name/service_type/etc., which
# stay required and should never be nulled out.
_CLEARABLE_UPDATE_FIELDS = {"business_description", *SOCIAL_LINK_FIELDS}
from app.services.qr_service import QRService
from app.ai.review_generator import ReviewGenerator
from app.utils.helper import new_id, serialize_doc
from app.utils.logger import logger


class BusinessService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        qr_repo: QRRepository,
    ):
        self.business_repo = business_repo
        self.qr_service = QRService(qr_repo)
        self.review_generator = ReviewGenerator()

    async def _save_logo(self, business_id: str, logo: UploadFile) -> str:
        logo_dir = "app/static/logos"
        os.makedirs(logo_dir, exist_ok=True)
        extension = os.path.splitext(logo.filename or "logo.png")[1] or ".png"
        file_path = os.path.join(logo_dir, f"{business_id}{extension}")
        contents = await logo.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return file_path

    async def create_business(
        self,
        owner_id: str,
        data: BusinessCreateRequest,
        logo: UploadFile | None = None,
    ) -> dict:
        business_doc = build_business_document(
            owner_id=owner_id,
            business_name=data.business_name,
            service_type=data.service_type,
            google_review_link=data.google_review_link,
            business_description=data.business_description,
            review_aspects=data.review_aspects,
            website=data.website,
            instagram=data.instagram,
            facebook=data.facebook,
            whatsapp_channel=data.whatsapp_channel,
            youtube=data.youtube,
            linkedin=data.linkedin,
            twitter_x=data.twitter_x,
            custom_links=[link.model_dump() for link in data.custom_links],
        )
        await self.business_repo.create(business_doc)

        if logo is not None and logo.filename:
            logo_path = await self._save_logo(business_doc["_id"], logo)
            business_doc = await self.business_repo.update(
                business_doc["_id"], {"logo_path": logo_path}
            )

        # New businesses only get the combined QR (review + social both
        # live on /c/{slug} now, gated by is_active/social_is_active) —
        # the separate review-only and social-only QR codes are legacy,
        # kept only for businesses that already have them.
        await self.qr_service.generate_combined_qr_for_business(
            business_id=business_doc["_id"],
            slug=business_doc["combined_slug"],
            business_name=business_doc["business_name"],
            logo_path=business_doc.get("logo_path"),
        )
        logger.info("Created business '%s' for owner %s", data.business_name, owner_id)

        return serialize_doc(business_doc)

    async def list_businesses(self, owner_id: str) -> list[dict]:
        docs = await self.business_repo.list_by_owner(owner_id)
        return [serialize_doc(d) for d in docs]

    async def count_businesses(self, owner_id: str) -> int:
        return await self.business_repo.count_by_owner(owner_id)

    async def get_business(self, owner_id: str, business_id: str) -> dict:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)
        return serialize_doc(doc)

    async def update_business(
        self,
        owner_id: str,
        business_id: str,
        data: BusinessUpdateRequest,
        logo: UploadFile | None = None,
    ) -> dict:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)

        updates = {
            k: v
            for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None or k in _CLEARABLE_UPDATE_FIELDS
        }

        if logo is not None and logo.filename:
            updates["logo_path"] = await self._save_logo(business_id, logo)

        updated = await self.business_repo.update(business_id, updates)
        return serialize_doc(updated)

    async def delete_business(self, owner_id: str, business_id: str) -> None:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)

        await self.qr_service.delete_qr_for_business(business_id)
        await self.business_repo.delete(business_id)
        logger.info("Deleted business %s for owner %s", business_id, owner_id)

    async def set_business_status(self, owner_id: str, business_id: str, is_active: bool) -> dict:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)

        updated = await self.business_repo.update(business_id, {"is_active": is_active})
        logger.info("Business %s is_active set to %s by owner %s", business_id, is_active, owner_id)
        return serialize_doc(updated)

    async def set_social_status(self, owner_id: str, business_id: str, is_active: bool) -> dict:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)

        updated = await self.business_repo.update(business_id, {"social_is_active": is_active})
        logger.info("Business %s social_is_active set to %s by owner %s", business_id, is_active, owner_id)
        return serialize_doc(updated)

    async def set_combined_status(self, owner_id: str, business_id: str, is_active: bool) -> dict:
        doc = await self.business_repo.get_by_id(business_id)
        self._ensure_owned(doc, owner_id)

        updated = await self.business_repo.update(business_id, {"combined_is_active": is_active})
        logger.info("Business %s combined_is_active set to %s by owner %s", business_id, is_active, owner_id)
        return serialize_doc(updated)

    async def generate_review_aspects(self,service_type: str,business_description: str | None = None,) -> list[str]:
        return await self.review_generator.generate_review_aspects(
        service_type=service_type,
        business_description=business_description,
    )
    
    
    @staticmethod
    def _ensure_owned(doc: dict | None, owner_id: str) -> None:
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")
        if doc["owner_id"] != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
