"""
MongoDB connection management using Motor (async driver).

Exposes a single `Database` helper that FastAPI's lifespan hook uses to
open/close the connection, plus a `get_db()` accessor that repositories
use to reach collections.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings
from app.utils.logger import logger


class Database:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    @classmethod
    async def connect(cls) -> None:
        # tz_aware=True: without it, Motor returns naive datetimes for every
        # BSON date field (they're UTC internally but arrive with no tzinfo),
        # which then serialize to JSON with no UTC offset — the browser then
        # misreads them as local time instead of UTC, corrupting any
        # timezone conversion (e.g. IST) done client-side.
        cls.client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
        cls.db = cls.client[settings.mongo_db_name]
        await cls._ensure_indexes()
        logger.info("Connected to MongoDB database '%s'", settings.mongo_db_name)

    @classmethod
    async def disconnect(cls) -> None:
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")

    @classmethod
    async def _ensure_indexes(cls) -> None:
        """Create indexes required for uniqueness / lookup performance."""
        await cls.db["businesses"].create_index("owner_id")
        await cls.db["businesses"].create_index(
          "slug",
          unique=True,
          sparse=True
        )
        # social_slug is a second, distinct identifier used only by the
        # social-media QR code, kept deliberately separate from `slug` (the
        # review QR's identifier) so the two QR codes encode two different,
        # unguessable URLs. sparse=True because businesses created before
        # this field existed are backfilled separately (see main.py).
        await cls.db["businesses"].create_index(
          "social_slug",
          unique=True,
          sparse=True
        )

        # combined_slug is a third, distinct identifier used only by the
        # combined (review + social) QR code — same rationale as social_slug
        # above. sparse=True because businesses created before this field
        # existed are backfilled separately (see main.py).
        await cls.db["businesses"].create_index(
          "combined_slug",
          unique=True,
          sparse=True
        )

        # Each business now has one QR document per qr_type ("review" and
        # "social"), so the old single-field unique index on business_id
        # alone is too strict. Docs created before this existed have no
        # qr_type at all — backfill them as "review" (the only type that
        # used to exist) before swapping the index, so their review QR
        # keeps resolving under the new qr_type-filtered lookups.
        await cls.db["qrcodes"].update_many(
            {"qr_type": {"$exists": False}}, {"$set": {"qr_type": "review"}}
        )
        try:
            await cls.db["qrcodes"].drop_index("business_id_1")
        except Exception:
            pass
        await cls.db["qrcodes"].create_index(
            [("business_id", 1), ("qr_type", 1)], unique=True
        )

        await cls.db["reviews"].create_index("business_id")

        await cls.db["click_logs"].create_index([("business_id", 1), ("created_at", -1)])
        await cls.db["click_logs"].create_index("created_at")


def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency-friendly accessor for the active database."""
    if Database.db is None:
        raise RuntimeError("Database has not been initialized yet.")
    return Database.db
