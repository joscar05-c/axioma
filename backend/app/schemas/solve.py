from typing import Any, Literal
from pydantic import BaseModel, Field

SubjectType = Literal["math", "physics", "chemistry", "engineering"]
InputType = Literal["text", "latex", "image"]
EngineName = Literal["math", "physics", "chemistry", "ai_only"]
MathOperation = Literal[
    "simplify",
    "evaluate",
    "derivative",
    "integral",
    "limit",
    "solve",
    "ode",
    "matrix_det",
    "matrix_inv",
]


class SolveStep(BaseModel):
    """Single pedagogical step returned to the user."""

    title: str
    explanation: str
    expression_latex: str | None = None


class PlotData(BaseModel):
    """2D plot points sampled deterministically for a function."""

    variable: str = "x"
    expression_latex: str
    x: list[float]
    y: list[float]


class SolveRequest(BaseModel):
    """Incoming solve request from the Axioma mobile client."""

    subject_hint: SubjectType | Literal["auto"] = "auto"
    input_type: InputType = "text"
    raw_input: str | None = Field(default=None, max_length=4000)
    image_path: str | None = Field(default=None, max_length=512)


class AIPlanOutput(BaseModel):
    """Structured output produced by Gemini before deterministic verification."""

    subject: SubjectType
    engine: EngineName
    extracted_problem: str
    summary: str
    steps: list[SolveStep] = Field(default_factory=list)
    # Math engine parameters
    math_operation: MathOperation | None = None
    expression: str | None = None
    variable: str = "x"
    order: int = 1
    lower_limit: str | None = None
    upper_limit: str | None = None
    limit_point: str | None = None
    limit_direction: Literal["+", "-", "+-"] = "+-"
    matrix_rows: list[list[str]] | None = None
    # Physics engine parameters
    physics_equation: str | None = None
    physics_target: str | None = None
    physics_knowns: dict[str, str] = Field(default_factory=dict)
    physics_output_unit: str | None = None
    # Chemistry engine parameters
    chem_reactants: list[str] = Field(default_factory=list)
    chem_products: list[str] = Field(default_factory=list)
    chem_formula: str | None = None
    # Fallback answer when engine == "ai_only"
    ai_result_latex: str | None = None


class EngineResult(BaseModel):
    """Deterministic calculation output from Python engines."""

    verified: bool
    result_latex: str
    result_text: str
    plot_data: PlotData | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuotaStatus(BaseModel):
    """Current daily quota status for the authenticated user."""

    plan_tier: Literal["free", "pro"]
    daily_limit: int | None
    used_today: int
    remaining_today: int | None


class SolveResponse(BaseModel):
    """Final response returned to the mobile app after gating."""

    problem_id: str | None = None
    subject: SubjectType
    extracted_problem: str
    verified: bool
    verified_result_latex: str
    solution_summary: str
    steps: list[SolveStep] = Field(default_factory=list)
    steps_locked: bool = False
    plot_data: PlotData | None = None
    plot_locked: bool = False
    quota: QuotaStatus
