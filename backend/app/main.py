from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.core.supabase_client import get_supabase_admin
from app.schemas.solve import QuotaStatus, SolveRequest, SolveResponse
from app.services.problem_service import solve_problem
from app.services.quota_service import get_quota_status

settings = get_settings()

app = FastAPI(
    title="Axioma Scientific API",
    version="0.1.0",
    description="Hybrid AI + Deterministic Scientific Solver (Math, Physics, Chemistry, Engineering)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "axioma-api"}


@app.get("/api/v1/me/quota", response_model=QuotaStatus)
def read_my_quota(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
) -> QuotaStatus:
    """Return the authenticated user's plan tier and remaining daily quota."""
    return get_quota_status(user, supabase)


@app.post("/api/v1/solve", response_model=SolveResponse)
def solve_endpoint(
    payload: SolveRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
) -> SolveResponse:
    """Analyze a problem with Gemini and verify with SymPy/Pint/ChemPy."""
    return solve_problem(payload, user, supabase)
