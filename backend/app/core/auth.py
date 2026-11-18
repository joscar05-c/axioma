from typing import Literal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client
from app.core.supabase_client import get_supabase_admin

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Authenticated user context extracted from Supabase Auth + profiles."""

    id: str
    email: str | None = None
    plan_tier: Literal["free", "pro"] = "free"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    supabase: Client = Depends(get_supabase_admin),
) -> AuthenticatedUser:
    """Validate Supabase Bearer JWT and load the user's plan tier."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
        )

    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        user = getattr(user_response, "user", None)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for provided token.",
        )

    plan_tier: Literal["free", "pro"] = "free"
    profile_resp = (
        supabase.table("profiles")
        .select("plan_tier")
        .eq("id", str(user.id))
        .limit(1)
        .execute()
    )
    if profile_resp.data:
        raw_tier = profile_resp.data[0].get("plan_tier")
        if raw_tier in ("free", "pro"):
            plan_tier = raw_tier

    return AuthenticatedUser(
        id=str(user.id),
        email=getattr(user, "email", None),
        plan_tier=plan_tier,
    )
