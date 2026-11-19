from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    allow_credentials=settings.cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root_status() -> dict[str, str]:
    """Root endpoint confirming the Axioma API service is online."""
    return {"status": "ok", "service": "axioma-api", "docs": "/docs"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "axioma-api"}


_AUTH_CONFIRMED_HTML = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Axioma — Correo confirmado</title>
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        background: #020617;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        box-sizing: border-box;
      }
      .card {
        max-width: 420px;
        width: 100%;
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 32px 24px;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
      }
      .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        border-radius: 999px;
        background: rgba(56, 189, 248, 0.14);
        color: #38bdf8;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 16px;
      }
      .brand {
        color: #38bdf8;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 2.5px;
        margin-bottom: 8px;
      }
      h1 {
        margin: 0 0 12px;
        font-size: 24px;
        font-weight: 800;
      }
      p {
        margin: 0 0 24px;
        color: #94a3b8;
        font-size: 15px;
        line-height: 1.5;
      }
      .btn {
        display: inline-block;
        background: #38bdf8;
        color: #020617;
        text-decoration: none;
        font-weight: 700;
        font-size: 15px;
        padding: 13px 22px;
        border-radius: 12px;
      }
    </style>
  </head>
  <body>
    <main class="card">
      <div class="badge">✓</div>
      <div class="brand">AXIOMA</div>
      <h1>¡Correo confirmado!</h1>
      <p>
        Tu cuenta ya está verificada. Puedes cerrar esta pestaña, volver a la
        app móvil de Axioma e iniciar sesión con tu correo y contraseña.
      </p>
      <a class="btn" href="axioma://">Abrir Axioma</a>
    </main>
  </body>
</html>
"""


@app.get("/auth/confirmed", response_class=HTMLResponse)
def auth_confirmed_page() -> HTMLResponse:
    """Landing page shown after Supabase email confirmation redirect."""
    return HTMLResponse(content=_AUTH_CONFIRMED_HTML)


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
    """Analyze a problem with Gemini and verify with SymPy/Pint."""
    return solve_problem(payload, user, supabase)
