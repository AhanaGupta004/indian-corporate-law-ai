from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from shared.config.settings import get_settings


def create_access_token(data: dict) -> str:
    """Mint a JWT with expiry."""
    settings = get_settings()
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_otp_token(user_id: str) -> str:
    """Mint a short-lived JWT for OTP verification."""
    settings = get_settings()
    payload = {"sub": user_id, "type": "otp"}
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=10)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode & verify JWT; raises 401 on failure."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def extract_user_from_token(token: str) -> str:
    """Return user_id (sub) from token."""
    payload = verify_token(token)
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing subject")
    return uid


def extract_user_from_otp_token(token: str) -> str:
    """Return user_id specifically for OTP tokens."""
    payload = verify_token(token)
    if payload.get("type") != "otp":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing subject")
    return uid
