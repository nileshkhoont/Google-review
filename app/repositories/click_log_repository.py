"""Data access layer for the `click_logs` collection."""

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "click_logs"


class ClickLogRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[COLLECTION]

    async def create(self, click_log_doc: dict[str, Any]) -> dict[str, Any]:
        await self.collection.insert_one(click_log_doc)
        return click_log_doc

    async def list_recent(
        self, limit: int = 50, skip: int = 0, business_id: str | None = None
    ) -> list[dict[str, Any]]:
        query = {"business_id": business_id} if business_id else {}
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def count(self, business_id: str | None = None) -> int:
        query = {"business_id": business_id} if business_id else {}
        return await self.collection.count_documents(query)

    async def aggregate_action_counts(
        self,
        business_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Per-button click counts + last-clicked time for one business.

        Grouped by (page, action) rather than action alone: "qr_scan" is
        recorded on both the review and social landing pages, so grouping
        by action only would silently merge Review-QR scans and Social-QR
        scans into one combined count.

        If `start`/`end` are given, only clicks with `start <= created_at < end`
        are counted (used to scope the summary to a single calendar day).
        """
        match: dict[str, Any] = {"business_id": business_id}
        if start is not None or end is not None:
            created_at_range: dict[str, Any] = {}
            if start is not None:
                created_at_range["$gte"] = start
            if end is not None:
                created_at_range["$lt"] = end
            match["created_at"] = created_at_range

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"page": "$page", "action": "$action"},
                    "count": {"$sum": 1},
                    "last_clicked_at": {"$max": "$created_at"},
                }
            },
            {"$sort": {"count": -1}},
        ]
        return [doc async for doc in self.collection.aggregate(pipeline)]

    async def aggregate_business_totals(self) -> list[dict[str, Any]]:
        """Total click counts + last activity, grouped by business ("company")."""
        pipeline = [
            # Sort by created_at first so $last below yields the most recent
            # business_name (business names can change; group order is
            # otherwise unspecified).
            {"$sort": {"created_at": 1}},
            {
                "$group": {
                    "_id": "$business_id",
                    "business_name": {"$last": "$business_name"},
                    "total_clicks": {"$sum": 1},
                    "last_activity_at": {"$max": "$created_at"},
                }
            },
            {"$sort": {"total_clicks": -1}},
        ]
        return [doc async for doc in self.collection.aggregate(pipeline)]
