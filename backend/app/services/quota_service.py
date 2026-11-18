from datetime import date
from fastapi import HTTPException, status
from supabase import Client
from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.schemas.solve import QuotaStatus


def get_quota_status(user: AuthenticatedUser, supabase: Client) -> QuotaStatus:
    """Fetch the user's current daily usage without consuming a solve."""
    settings = get_settings()
    today_iso = date.today().isoformat()
    resp = (
        supabase.table("daily_usage")
        .select("solve_count")
        .eq("user_id", user.id)
        .eq("usage_date", today_iso)
        .limit(1)
        .execute()
    )
    used_today = int(resp.data[0]["solve_count"]) if resp.data else 0

    if user.plan_tier == "pro":
        return QuotaStatus(
            plan_tier="pro",
            daily_limit=None,
            used_today=used_today,
            remaining_today=None,
        )

    remaining = max(settings.free_daily_limit - used_today, 0)
    return QuotaStatus(
        plan_tier="free",
        daily_limit=settings.free_daily_limit,
        used_today=used_today,
        remaining_today=remaining,
    )


def consume_quota_or_raise(user: AuthenticatedUser, supabase: Client) -> QuotaStatus:
    """Atomically check and consume 1 daily solve for free users."""
    if user.plan_tier == "pro":
        return QuotaStatus(
            plan_tier="pro",
            daily_limit=None,
            used_today=0,
            remaining_today=None,
        )

    settings = get_settings()
    rpc_resp = supabase.rpc(
        "consume_daily_solve",
        {"p_user_id": user.id, "p_limit": settings.free_daily_limit},
    ).execute()

    if not rpc_resp.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify daily solve quota.",
        )

    row = rpc_resp.data[0]
    if not row.get("allowed"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "UPGRADE_REQUIRED",
                "reason": "daily_limit_reached",
                "message": "Alcanzaste el límite diario de 5 problemas en el plan gratuito.",
                "daily_limit": settings.free_daily_limit,
            },
        )

    return QuotaStatus(
        plan_tier="free",
        daily_limit=settings.free_daily_limit,
        used_today=int(row["current_count"]),
        remaining_today=int(row["remaining"]),
    )


def refund_quota(user: AuthenticatedUser, supabase: Client) -> None:
    """Refund 1 solve if processing fails before returning an answer."""
    if user.plan_tier == "pro":
        return
    try:
        supabase.rpc("refund_daily_solve", {"p_user_id": user.id}).execute()
    except Exception:
        # Best-effort refund; never mask original exception
        pass
