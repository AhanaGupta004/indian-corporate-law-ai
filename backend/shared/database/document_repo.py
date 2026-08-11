from typing import Optional
from datetime import datetime, timezone
from bson.objectid import ObjectId
from shared.database.mongo import DatabaseManager

class DocumentRepository:
    @staticmethod
    def get_collection():
        return DatabaseManager.get_db().documents

    @classmethod
    async def create_document(cls, user_id: str, filename: str, filepath: str) -> dict:
        doc = {
            "user_id":    ObjectId(user_id),
            "filename":   filename,
            "filepath":   filepath,
            "status":     "UPLOADED",
            "result":     None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = await cls.get_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    async def get_document(cls, doc_id: str) -> Optional[dict]:
        try:
            return await cls.get_collection().find_one({"_id": ObjectId(doc_id)})
        except Exception:
            return None

    @classmethod
    async def get_user_documents(cls, user_id: str) -> list:
        cursor = cls.get_collection().find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        return await cursor.to_list(length=200)

    @classmethod
    async def update_document_status(cls, doc_id: str, status: str) -> None:
        await cls.get_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        )

    @classmethod
    async def store_document_result(cls, doc_id: str, result: dict) -> None:
        """Persist analysis result + mark done in a single atomic write."""
        await cls.get_collection().update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "status":     "COMPLETED",
                    "result":     result,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    @classmethod
    async def delete_document(cls, doc_id: str) -> None:
        await cls.get_collection().delete_one({"_id": ObjectId(doc_id)})
