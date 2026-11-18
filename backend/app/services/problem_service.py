from fastapi import HTTPException, status
from supabase import Client
from app.core.auth import AuthenticatedUser
from app.engines.chemistry_engine import run_chemistry_engine
from app.engines.math_engine import run_math_engine
from app.engines.physics_engine import run_physics_engine
from app.schemas.solve import (
    AIPlanOutput,
    EngineResult,
    SolveRequest,
    SolveResponse,
)
from app.services.ai_parser import analyze_problem_with_gemini
from app.services.quota_service import consume_quota_or_raise, refund_quota


def _load_user_image_bytes(
    image_path: str,
    user: AuthenticatedUser,
    supabase: Client,
) -> bytes:
    """Download an uploaded problem image after verifying folder ownership."""
    expected_prefix = f"{user.id}/"
    if not image_path.startswith(expected_prefix) or ".." in image_path:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Image path does not belong to the authenticated user.",
        )
    try:
        return supabase.storage.from_("problem-images").download(image_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not download problem image from storage.",
        ) from exc


def _execute_deterministic_engine(plan: AIPlanOutput) -> EngineResult:
    """Route the AI plan to the corresponding deterministic Python engine."""
    try:
        if plan.engine == "math" and plan.math_operation is not None:
            return run_math_engine(
                operation=plan.math_operation,
                expression=plan.expression,
                variable=plan.variable,
                order=plan.order,
                lower_limit=plan.lower_limit,
                upper_limit=plan.upper_limit,
                limit_point=plan.limit_point,
                limit_direction=plan.limit_direction,
                matrix_rows=plan.matrix_rows,
            )
        if plan.engine == "physics" and plan.physics_equation and plan.physics_target:
            return run_physics_engine(
                equation=plan.physics_equation,
                target=plan.physics_target,
                knowns=plan.physics_knowns,
                output_unit=plan.physics_output_unit,
            )
        if plan.engine == "chemistry":
            return run_chemistry_engine(
                reactants=plan.chem_reactants or None,
                products=plan.chem_products or None,
                formula=plan.chem_formula,
            )
    except Exception as exc:
        return EngineResult(
            verified=False,
            result_latex=plan.ai_result_latex or "\\text{Verificación simbólica no disponible}",
            result_text=plan.summary,
            metadata={"engine_error": str(exc)},
        )

    return EngineResult(
        verified=False,
        result_latex=plan.ai_result_latex or "\\text{Revisar resumen}",
        result_text=plan.summary,
        metadata={"engine": "ai_only"},
    )


def solve_problem(
    payload: SolveRequest,
    user: AuthenticatedUser,
    supabase: Client,
) -> SolveResponse:
    """Orchestrate quota gating, Gemini parsing, Python engine verification, and persistence."""
    if not payload.raw_input and not payload.image_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide raw_input or image_path.",
        )

    image_bytes: bytes | None = None
    if payload.image_path:
        image_bytes = _load_user_image_bytes(payload.image_path, user, supabase)

    quota = consume_quota_or_raise(user, supabase)

    try:
        plan = analyze_problem_with_gemini(
            raw_input=payload.raw_input,
            subject_hint=payload.subject_hint,
            image_bytes=image_bytes,
            image_path=payload.image_path,
        )
        engine_result = _execute_deterministic_engine(plan)
    except Exception as exc:
        refund_quota(user, supabase)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Problem solving failed: {exc}",
        ) from exc

    is_pro = user.plan_tier == "pro"
    steps_payload = [step.model_dump() for step in plan.steps]
    plot_payload = engine_result.plot_data.model_dump() if engine_result.plot_data else None

    saved_id: str | None = None
    insert_resp = (
        supabase.table("problems")
        .insert(
            {
                "user_id": user.id,
                "subject": plan.subject,
                "input_type": payload.input_type,
                "raw_input": payload.raw_input or plan.extracted_problem,
                "image_path": payload.image_path,
                "verified_result_latex": engine_result.result_latex,
                "solution_summary": plan.summary,
                "steps_json": steps_payload,
                "plot_data": plot_payload,
                "engine_metadata": {
                    **engine_result.metadata,
                    "verified": engine_result.verified,
                },
            }
        )
        .execute()
    )
    if insert_resp.data:
        saved_id = insert_resp.data[0].get("id")

    # Apply Freemium gating on response: free users get final verified answer + summary only
    return SolveResponse(
        problem_id=saved_id,
        subject=plan.subject,
        extracted_problem=plan.extracted_problem,
        verified=engine_result.verified,
        verified_result_latex=engine_result.result_latex,
        solution_summary=plan.summary,
        steps=plan.steps if is_pro else [],
        steps_locked=not is_pro and len(plan.steps) > 0,
        plot_data=engine_result.plot_data if is_pro else None,
        plot_locked=not is_pro and engine_result.plot_data is not None,
        quota=quota,
    )
