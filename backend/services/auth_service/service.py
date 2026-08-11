from typing import Optional
import logging
import httpx
import bcrypt
import string
import random
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from shared.database.user_repo import UserRepository
from shared.security.jwt import create_access_token, create_otp_token, extract_user_from_otp_token
from shared.config.settings import get_settings
from services.auth_service.notification.service import get_notification_provider

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _get_recaptcha_secret() -> str:
    return get_settings().RECAPTCHA_SECRET


async def verify_captcha(token: str):
    async with httpx.AsyncClient() as client:
        res = await client.post("https://www.google.com/recaptcha/api/siteverify", data={
            "secret": _get_recaptcha_secret(),
            "response": token
        })
        data = res.json()
        if not data.get("success"):
            logger.warning(f"CAPTCHA validation failed: {data}")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid CAPTCHA")


async def signup(email: str, company: Optional[str] = None, is_new_to_ai: bool = False, purpose: Optional[str] = None, source: Optional[str] = None, captcha_token: str = None) -> dict:
    if captcha_token:
        await verify_captcha(captcha_token)
    if await UserRepository.find_user_by_email(email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    role = "admin" if email == "hemabisht14888@gmail.com" else "agent"
    status_str = "approved" if email == "hemabisht14888@gmail.com" else "pending"

    user = await UserRepository.create_user(email, password_hash=None, role=role, status=status_str,
                                             company=company, is_new_to_ai=is_new_to_ai, purpose=purpose, source=source)
    logger.info(f"[OK] New registration: {email} (role: {role})")

    if role == "admin":
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        raw_password = ''.join(random.choice(chars) for _ in range(12))
        hashed = _hash_password(raw_password)
        await UserRepository.approve_agent(str(user["_id"]), hashed)
        provider = get_notification_provider()
        await provider.send_agent_credentials(email, raw_password)
        return {"user_id": str(user["_id"]), "email": email, "status": "approved"}

    return {"user_id": str(user["_id"]), "email": email, "status": "pending"}


async def login(email: str, password: str, captcha_token: str = None) -> dict:
    if captcha_token:
        await verify_captcha(captcha_token)
    user = await UserRepository.find_user_by_email(email)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.get("role") == "agent" and user.get("status") != "approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is pending admin approval")
    if not user.get("password_hash") or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    otp_code = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    await UserRepository.save_otp(str(user["_id"]), otp_code, expiry)

    provider = get_notification_provider()
    await provider.send_otp(email, otp_code)

    temp_token = create_otp_token(str(user["_id"]))
    return {"requires_otp": True, "temp_token": temp_token, "message": "OTP sent to your email."}


async def verify_otp(temp_token: str, otp: str) -> dict:
    user_id = extract_user_from_otp_token(temp_token)
    user = await UserRepository.find_user_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    saved_otp = user.get("otp")
    otp_expiry = user.get("otp_expiry")
    if not saved_otp or saved_otp != otp:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid OTP code")
    if otp_expiry and otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "OTP code has expired")

    await UserRepository.clear_otp(user_id)
    email = user["email"]
    token = create_access_token({"sub": str(user["_id"]), "email": email, "role": user.get("role", "agent")})
    logger.info(f"[OK] Login complete via OTP: {email}")
    return {"access_token": token, "token_type": "bearer", "user_id": str(user["_id"]), "email": email, "role": user.get("role", "agent")}


async def get_user_profile(user_id: str) -> Optional[dict]:
    user = await UserRepository.find_user_by_id(user_id)
    if not user:
        return None
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_count = user.get("daily_doc_count", 0)
    last_reset = user.get("last_reset_date")
    if last_reset != current_date:
        current_count = 0
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "company": user.get("company"),
        "role": user["role"],
        "status": user["status"],
        "subscription_tier": user.get("subscription_tier", "free"),
        "daily_doc_count": current_count
    }


async def get_pending_agents() -> list:
    agents = await UserRepository.get_pending_agents()
    return [{"id": str(a["_id"]), "email": a["email"], "company": a.get("company"), "purpose": a.get("purpose"), "created_at": a["created_at"]} for a in agents]


async def get_all_agents() -> list:
    agents = await UserRepository.get_all_agents()
    return [{
        "id": str(a["_id"]),
        "email": a["email"],
        "company": a.get("company"),
        "purpose": a.get("purpose"),
        "is_new_to_ai": a.get("is_new_to_ai"),
        "source": a.get("source"),
        "status": a.get("status"),
        "subscription_tier": a.get("subscription_tier"),
        "daily_doc_count": a.get("daily_doc_count"),
        "created_at": a["created_at"]
    } for a in agents]


async def approve_agent(agent_id: str) -> dict:
    agent = await UserRepository.find_user_by_id(agent_id)
    if not agent or agent.get("role") != "agent":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    if agent.get("status") == "approved":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Agent already approved")

    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    raw_password = ''.join(random.choice(chars) for _ in range(12))
    hashed = _hash_password(raw_password)
    await UserRepository.approve_agent(agent_id, hashed)

    provider = get_notification_provider()
    await provider.send_agent_credentials(agent["email"], raw_password)
    return {"message": "Agent approved and credentials sent"}


async def reset_agent_limit(agent_id: str) -> dict:
    from bson.objectid import ObjectId
    collection = UserRepository.get_collection()
    try:
        result = await collection.update_one(
            {"_id": ObjectId(agent_id)},
            {"$set": {"daily_doc_count": 0}}
        )
        if result.matched_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
        if result.modified_count == 0:
            return {"success": True, "message": "Agent limit is already at 0"}
        return {"success": True, "message": "Agent limit reset to 0"}
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid agent ID")


async def get_stats() -> dict:
    return await UserRepository.get_all_agents_stats()
