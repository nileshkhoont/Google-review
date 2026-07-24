"""Data access layer for the `businesses` collection."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helper import utc_now

COLLECTION = "businesses"


class BusinessRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[COLLECTION]

    async def create(self, business_doc: dict[str, Any]) -> dict[str, Any]:
        await self.collection.insert_one(business_doc)
        return business_doc

    async def get_by_id(self, business_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": business_id})

    async def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"slug": slug})

    async def list_by_owner(self, owner_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find({"owner_id": owner_id}).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def count_by_owner(self, owner_id: str) -> int:
        return await self.collection.count_documents({"owner_id": owner_id})

    async def update(self, business_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        updates["updated_at"] = utc_now()
        await self.collection.update_one({"_id": business_id}, {"$set": updates})
        return await self.get_by_id(business_id)

    async def delete(self, business_id: str) -> bool:
        result = await self.collection.delete_one({"_id": business_id})
        return result.deleted_count > 0
