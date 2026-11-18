import pint
import sympy as sp
from app.engines.math_engine import UnsafeExpressionError, safe_parse_expr
from app.schemas.solve import EngineResult

ureg = pint.UnitRegistry()


def run_physics_engine(
    equation: str,
    target: str,
    knowns: dict[str, str],
    output_unit: str | None = None,
) -> EngineResult:
    """Solve a physics/engineering formula symbolically and evaluate with Pint units."""
    if "=" not in equation:
        raise UnsafeExpressionError("Physics equation must include '='.")

    lhs_str, rhs_str = equation.split("=", 1)
    symbol_names = set(knowns.keys()) | {target}
    local_syms = {name: sp.Symbol(name) for name in symbol_names}

    lhs = safe_parse_expr(lhs_str, local_syms)
    rhs = safe_parse_expr(rhs_str, local_syms)
    target_sym = local_syms[target]

    solutions = sp.solve(sp.Eq(lhs, rhs), target_sym)
    if not solutions:
        raise ValueError(f"Could not solve equation for target '{target}'.")

    symbolic_formula = solutions[0]

    # Build a Pint-aware local namespace for exact unit propagation
    pint_env: dict[str, object] = {}
    for var_name, raw_qty in knowns.items():
        pint_env[var_name] = ureg.Quantity(raw_qty)

    # Evaluate the solved symbolic expression against Pint Quantities via lambdify
    ordered_vars = [name for name in knowns.keys() if local_syms[name] in symbolic_formula.free_symbols]
    arg_syms = [local_syms[name] for name in ordered_vars]
    fn = sp.lambdify(arg_syms, symbolic_formula, modules="math")
    qty_result = fn(*(pint_env[name] for name in ordered_vars))

    if isinstance(qty_result, pint.Quantity):
        if output_unit:
            qty_result = qty_result.to(output_unit)
        else:
            qty_result = qty_result.to_base_units()
        mag_str = f"{qty_result.magnitude:.6g}"
        unit_latex = f"{qty_result.units:~L}"
        result_latex = (
            f"{sp.latex(target_sym)} = {mag_str}\\,\\mathrm{{{unit_latex}}}"
            if unit_latex
            else f"{sp.latex(target_sym)} = {mag_str}"
        )
        result_text = f"{target} = {qty_result:~P}"
    else:
        numeric_val = float(qty_result)
        result_latex = f"{sp.latex(target_sym)} = {numeric_val:.6g}"
        result_text = f"{target} = {numeric_val:.6g}"

    return EngineResult(
        verified=True,
        result_latex=result_latex,
        result_text=result_text,
        metadata={
            "symbolic_solution": str(symbolic_formula),
            "target": target,
        },
    )
