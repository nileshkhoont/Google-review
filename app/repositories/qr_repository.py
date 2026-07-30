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

    async def get_by_business_id(self, business_id: str, qr_type: str = "review") -> dict[str, Any] | None:
        return await self.collection.find_one({"business_id": business_id, "qr_type": qr_type})

    async def upsert_for_business(
        self, business_id: str, qr_type: str, qr_doc: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Replace any existing QR record of this type for a business (used on
        regeneration). `_id` and `created_at` are only applied on the initial
        insert (`$setOnInsert`) — `$set`-ing them unconditionally would try to
        overwrite an existing document's immutable `_id`, which MongoDB
        rejects outright.
        """
        qr_doc = dict(qr_doc)
        doc_id = qr_doc.pop("_id")
        created_at = qr_doc.pop("created_at", None)
        qr_doc["updated_at"] = utc_now()

        set_on_insert = {"_id": doc_id}
        if created_at is not None:
            set_on_insert["created_at"] = created_at

        await self.collection.update_one(
            {"business_id": business_id, "qr_type": qr_type},
            {"$set": qr_doc, "$setOnInsert": set_on_insert},
            upsert=True,
        )
        return await self.get_by_business_id(business_id, qr_type)

    async def delete_by_business_id(self, business_id: str) -> bool:
        """Delete every QR record (all types) for a business."""
        result = await self.collection.delete_many({"business_id": business_id})
        return result.deleted_count > 0
