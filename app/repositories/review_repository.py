"""Data access layer for the optional `reviews` history collection."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "reviews"


class ReviewRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[COLLECTION]

    async def create(self, review_doc: dict[str, Any]) -> dict[str, Any]:
        await self.collection.insert_one(review_doc)
        return review_doc

    async def list_by_business(self, business_id: str, limit: int = 50) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"business_id": business_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def count_by_business(self, business_id: str) -> int:
        return await self.collection.count_documents({"business_id": business_id})
