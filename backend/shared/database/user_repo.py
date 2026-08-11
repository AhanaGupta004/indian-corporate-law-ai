from typing import Optional
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId
from shared.database.mongo import DatabaseManager

class UserRepository:
    @staticmethod
    def get_collection():
        return DatabaseManager.get_db().users

    @classmethod
    async def create_user(cls, email: str, password_hash: Optional[str] = None, role: str = "agent", status: str = "pending", company: Optional[str] = None, is_new_to_ai: bool = False, purpose: Optional[str] = None, source: Optional[str] = None) -> dict:
        doc = {
            "email": email,
            "company": company,
            "is_new_to_ai": is_new_to_ai,
            "purpose": purpose,
            "source": source,
            "password_hash": password_hash,
            "role": role,
            "status": status,
            "subscription_tier": "free",
            "subscription_expiry": None,
            "daily_doc_count": 0,
            "last_reset_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc),
        }
        result = await cls.get_collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    async def find_user_by_email(cls, email: str) -> Optional[dict]:
        return await cls.get_collection().find_one({"email": email})

    @classmethod
    async def find_user_by_id(cls, user_id: str) -> Optional[dict]:
        return await cls.get_collection().find_one({"_id": ObjectId(user_id)})

    @classmethod
    async def get_pending_agents(cls) -> list:
        cursor = cls.get_collection().find({"role": "agent", "status": "pending"}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    @classmethod
    async def get_all_agents(cls) -> list:
        cursor = cls.get_collection().find({"role": "agent"}).sort("created_at", -1)
        return await cursor.to_list(length=1000)

    @classmethod
    async def approve_agent(cls, user_id: str, password_hash: str) -> None:
        await cls.get_collection().update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "approved", "password_hash": password_hash}}
        )

    @classmethod
    async def save_otp(cls, user_id: str, otp: str, expiry: datetime) -> None:
        await cls.get_collection().update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"otp": otp, "otp_expiry": expiry}}
        )

    @classmethod
    async def clear_otp(cls, user_id: str) -> None:
        await cls.get_collection().update_one(
            {"_id": ObjectId(user_id)},
            {"$unset": {"otp": "", "otp_expiry": ""}}
        )

    @classmethod
    async def get_all_agents_stats(cls) -> dict:
        coll = cls.get_collection()
        total = await coll.count_documents({"role": "agent"})
        approved = await coll.count_documents({"role": "agent", "status": "approved"})
        pending = await coll.count_documents({"role": "agent", "status": "pending"})
        tiers = {
            "free": await coll.count_documents({"role": "agent", "subscription_tier": "free"}),
            "basic": await coll.count_documents({"role": "agent", "subscription_tier": "basic"}),
            "professional": await coll.count_documents({"role": "agent", "subscription_tier": "professional"}),
        }
        return {"total": total, "approved": approved, "pending": pending, "tiers": tiers}

    @classmethod
    async def increment_daily_doc_count(cls, user_id: str, current_date: str) -> Optional[dict]:
        coll = cls.get_collection()
        user = await coll.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        if user.get("last_reset_date") != current_date:
            update_data = {"$set": {"daily_doc_count": 1, "last_reset_date": current_date}}
        else:
            update_data = {"$inc": {"daily_doc_count": 1}}
        await coll.update_one({"_id": ObjectId(user_id)}, update_data)
        return await coll.find_one({"_id": ObjectId(user_id)})
