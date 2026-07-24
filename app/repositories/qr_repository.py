"""Data access layer for the `qrcodes` collection."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helper import utc_now

COLLECTION = "qrcodes"


class QRRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[COLLECTION]

    async def create(self, qr_doc: dict[str, Any]) -> dict[str, Any]:
        await self.collection.insert_one(qr_doc)
        return qr_doc

    async def get_by_business_id(self, business_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"business_id": business_id})

    async def upsert_for_business(self, business_id: str, qr_doc: dict[str, Any]) -> dict[str, Any]:
        """Replace any existing QR record for a business (used on regeneration)."""
        qr_doc["updated_at"] = utc_now()
        await self.collection.update_one(
            {"business_id": business_id}, {"$set": qr_doc}, upsert=True
        )
        return await self.get_by_business_id(business_id)

    async def delete_by_business_id(self, business_id: str) -> bool:
        result = await self.collection.delete_one({"business_id": business_id})
        return result.deleted_count > 0
