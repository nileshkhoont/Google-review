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
        cls.client = AsyncIOMotorClient(settings.mongo_uri)
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
        await cls.db["qrcodes"].create_index("business_id", unique=True)
        await cls.db["reviews"].create_index("business_id")


def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency-friendly accessor for the active database."""
    if Database.db is None:
        raise RuntimeError("Database has not been initialized yet.")
    return Database.db
