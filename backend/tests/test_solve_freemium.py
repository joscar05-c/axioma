from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.supabase_client import get_supabase_admin
from app.main import app
from app.schemas.solve import AIPlanOutput, SolveStep
import app.services.problem_service as problem_service


class _FakeQuery:
    def __init__(self, store: dict, table_name: str):
        self.store = store
        self.table_name = table_name
        self._payload = None

    def insert(self, payload: dict):
        self._payload = payload
        return self

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        if self.table_name == "problems" and self._payload is not None:
            record = {"id": "prob-123", **self._payload}
            self.store["problems"].append(record)
            return SimpleNamespace(data=[record])
        if self.table_name == "daily_usage":
            count = self.store["usage_count"]
            return SimpleNamespace(data=[{"solve_count": count}])
        return SimpleNamespace(data=[])


class _FakeRpc:
    def __init__(self, store: dict, fn_name: str, params: dict):
        self.store = store
        self.fn_name = fn_name
        self.params = params

    def execute(self):
        if self.fn_name == "consume_daily_solve":
            limit = int(self.params["p_limit"])
            if self.store["usage_count"] >= limit:
                return SimpleNamespace(
                    data=[{"allowed": False, "current_count": limit, "remaining": 0}]
                )
            self.store["usage_count"] += 1
            used = self.store["usage_count"]
            return SimpleNamespace(
                data=[{"allowed": True, "current_count": used, "remaining": limit - used}]
            )
        if self.fn_name == "refund_daily_solve":
            self.store["usage_count"] = max(self.store["usage_count"] - 1, 0)
        return SimpleNamespace(data=[])


class _FakeSupabase:
    def __init__(self, initial_usage: int = 0):
        self.store = {"usage_count": initial_usage, "problems": []}

    def table(self, name: str):
        return _FakeQuery(self.store, name)

    def rpc(self, fn_name: str, params: dict):
        return _FakeRpc(self.store, fn_name, params)


def _fake_gemini_plan(**_kwargs) -> AIPlanOutput:
    return AIPlanOutput(
        subject="math",
        engine="math",
        extracted_problem="Derivada de x^2",
        summary="La derivada de x^2 respecto a x es 2x.",
        steps=[
            SolveStep(
                title="Regla de la potencia",
                explanation="Aplicamos d/dx(x^n) = n*x^(n-1).",
                expression_latex="2x",
            )
        ],
        math_operation="derivative",
        expression="x**2",
        variable="x",
    )


def test_free_user_hides_steps_and_plot(monkeypatch) -> None:
    monkeypatch.setattr(problem_service, "analyze_problem_with_gemini", _fake_gemini_plan)
    fake_db = _FakeSupabase(initial_usage=0)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="user-1", email="free@axioma.test", plan_tier="free"
    )
    app.dependency_overrides[get_supabase_admin] = lambda: fake_db

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/solve", json={"raw_input": "d/dx x^2"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["verified"] is True
        assert body["verified_result_latex"] == "2 x"
        assert body["steps"] == []
        assert body["steps_locked"] is True
        assert body["plot_data"] is None
        assert body["plot_locked"] is True
        assert body["quota"]["remaining_today"] == 4
    finally:
        app.dependency_overrides.clear()


def test_free_user_blocked_after_daily_limit(monkeypatch) -> None:
    monkeypatch.setattr(problem_service, "analyze_problem_with_gemini", _fake_gemini_plan)
    fake_db = _FakeSupabase(initial_usage=5)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="user-1", email="free@axioma.test", plan_tier="free"
    )
    app.dependency_overrides[get_supabase_admin] = lambda: fake_db

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/solve", json={"raw_input": "d/dx x^2"})
        assert resp.status_code == 402
        assert resp.json()["detail"]["code"] == "UPGRADE_REQUIRED"
    finally:
        app.dependency_overrides.clear()


def test_pro_user_receives_steps_and_plot(monkeypatch) -> None:
    monkeypatch.setattr(problem_service, "analyze_problem_with_gemini", _fake_gemini_plan)
    fake_db = _FakeSupabase(initial_usage=20)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="user-pro", email="pro@axioma.test", plan_tier="pro"
    )
    app.dependency_overrides[get_supabase_admin] = lambda: fake_db

    try:
        client = TestClient(app)
        resp = client.post("/api/v1/solve", json={"raw_input": "d/dx x^2"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["steps_locked"] is False
        assert len(body["steps"]) == 1
        assert body["plot_locked"] is False
        assert body["plot_data"] is not None
    finally:
        app.dependency_overrides.clear()


def test_auth_confirmed_page() -> None:
    client = TestClient(app)
    resp = client.get("/auth/confirmed")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "¡Correo confirmado!" in resp.text
