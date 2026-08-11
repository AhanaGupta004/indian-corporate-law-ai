from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from services.auth_service import service
from shared.security.jwt import extract_user_from_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    company: Optional[str] = None
    is_new_to_ai: bool = False
    purpose: Optional[str] = None
    source: Optional[str] = None
    captcha_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str

class OTPVerifyRequest(BaseModel):
    temp_token: str
    otp: str


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """Register a new agent account (pending approval)."""
    return await service.signup(req.email, req.company, req.is_new_to_ai, req.purpose, req.source, req.captcha_token)


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate and receive a JWT bearer token."""
    return await service.login(req.email, req.password, req.captcha_token)

@router.post("/verify-otp")
async def verify_otp(req: OTPVerifyRequest):
    """Verify OTP and get final access token."""
    return await service.verify_otp(req.temp_token, req.otp)


@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    """Get the current authenticated user's profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    user_id = extract_user_from_token(authorization.removeprefix("Bearer "))
    user = await service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


@router.get("/admin/agents/pending")
async def get_pending_agents():
    """Admin: Get all pending agents."""
    return await service.get_pending_agents()


@router.get("/admin/agents/all")
async def get_all_agents():
    """Admin: Get all agents (pending & approved)."""
    return await service.get_all_agents()


@router.post("/admin/agents/approve/{agent_id}")
async def approve_agent(agent_id: str):
    """Admin: Approve an agent and generate their password."""
    return await service.approve_agent(agent_id)


@router.post("/admin/agents/reset-limit/{agent_id}")
async def reset_agent_limit(agent_id: str):
    """Admin: Reset an agent's daily document limit count to 0."""
    return await service.reset_agent_limit(agent_id)


@router.get("/admin/stats")
async def get_admin_stats():
    """Admin: Get platform statistics."""
    return await service.get_stats()
