from typing import Optional
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect_db(cls):
        settings = get_settings()
        url = settings.MONGODB_URL

        cls.client = AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=8000,
            retryWrites=True,
        )
        await cls.client.admin.command("ping")
        cls.db = cls.client[settings.MONGODB_DB]
        logger.info(f"[OK] MongoDB connected -> db={settings.MONGODB_DB}")

        # Ensure Indexes
        await cls.db.users.create_index("email", unique=True)
        await cls.db.documents.create_index("user_id")
        await cls.db.documents.create_index("created_at")
        logger.info("[OK] Database indexes ensured")

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("[OK] MongoDB disconnected")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            raise RuntimeError("Database not initialised — call connect_db() first")
        return cls.db
