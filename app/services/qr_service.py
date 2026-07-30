"""Business logic for generating, storing, and regenerating QR codes."""

from fastapi import HTTPException, status

from app.config import settings
from app.models.qr import build_qr_document
from app.repositories.qr_repository import QRRepository
from app.utils.helper import serialize_doc
from app.utils.logger import logger
from app.utils.qr_generator import delete_qr_image, generate_qr_image


class QRService:
    def __init__(self, qr_repo: QRRepository):
        self.qr_repo = qr_repo

    @staticmethod
    def _customer_url(slug: str) -> str:
        return f"{settings.base_url}/r/{slug}"

    @staticmethod
    def _social_url(slug: str) -> str:
        return f"{settings.base_url}/s/{slug}"

    async def generate_qr_for_business(
        self,
        business_id: str,
        slug: str,
        business_name: str,
        logo_path: str | None = None,
    ) -> dict:
        target_url = self._customer_url(slug)
        filename = f"{business_id}.png"
        file_path = generate_qr_image(
            data_url=target_url,
            filename=filename,
            business_name=business_name,
            logo_path=logo_path,
        )

        qr_doc = build_qr_document(
            business_id=business_id, file_path=file_path, target_url=target_url, qr_type="review"
        )
        saved = await self.qr_repo.upsert_for_business(business_id, "review", qr_doc)
        logger.info("Generated QR for business %s", business_id)
        return serialize_doc(saved)

    async def generate_social_qr_for_business(
        self,
        business_id: str,
        slug: str,
        business_name: str,
        logo_path: str | None = None,
    ) -> dict:
        target_url = self._social_url(slug)
        filename = f"{business_id}_social.png"
        file_path = generate_qr_image(
            data_url=target_url,
            filename=filename,
            business_name=business_name,
            logo_path=logo_path,
            subtitle="Scan to Connect With Us",
        )

        qr_doc = build_qr_document(
            business_id=business_id, file_path=file_path, target_url=target_url, qr_type="social"
        )
        saved = await self.qr_repo.upsert_for_business(business_id, "social", qr_doc)
        logger.info("Generated social QR for business %s", business_id)
        return serialize_doc(saved)

    async def get_qr_for_business(self, business_id: str, qr_type: str = "review") -> dict:
        doc = await self.qr_repo.get_by_business_id(business_id, qr_type)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found.")
        return serialize_doc(doc)

    async def delete_qr_for_business(self, business_id: str) -> None:
        for qr_type in ("review", "social"):
            existing = await self.qr_repo.get_by_business_id(business_id, qr_type)
            if existing:
                delete_qr_image(existing.get("file_path"))
        await self.qr_repo.delete_by_business_id(business_id)
