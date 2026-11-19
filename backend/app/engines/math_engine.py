import math
import re
from typing import Any, Literal
import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from app.schemas.solve import EngineResult, MathOperation, PlotData

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

_FORBIDDEN_PATTERN = re.compile(
    r"(__|\bimport\b|\beval\b|\bexec\b|\bopen\b|\blambda\b|\bgetattr\b|\bsetattr\b)"
)

_SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
    "Function": sp.Function,
    "Tuple": sp.Tuple,
}

_BASE_SYMBOLS: dict[str, Any] = {
    "pi": sp.pi,
    "E": sp.E,
    "e": sp.E,
    "oo": sp.oo,
    "inf": sp.oo,
    "I": sp.I,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "factorial": sp.factorial,
    "Eq": sp.Eq,
    "Derivative": sp.Derivative,
    "Integral": sp.Integral,
    "Function": sp.Function,
}


class UnsafeExpressionError(ValueError):
    """Raised when an expression contains forbidden tokens or invalid syntax."""


def safe_parse_expr(
    raw: str,
    extra_locals: dict[str, Any] | None = None,
) -> sp.Basic:
    """Safely parse a mathematical expression string into a SymPy object."""
    text = (raw or "").strip()
    if not text:
        raise UnsafeExpressionError("Expression cannot be empty.")
    if len(text) > 500:
        raise UnsafeExpressionError("Expression exceeds maximum allowed length.")
    if _FORBIDDEN_PATTERN.search(text):
        raise UnsafeExpressionError("Expression contains forbidden keywords.")

    local_dict = dict(_BASE_SYMBOLS)
    if extra_locals:
        local_dict.update(extra_locals)

    try:
        return parse_expr(
            text,
            local_dict=local_dict,
            global_dict=dict(_SAFE_GLOBALS),
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:
        raise UnsafeExpressionError(f"Could not parse expression '{text}': {exc}") from exc


def _parse_equation_or_expr(raw: str, extra_locals: dict[str, Any] | None = None) -> sp.Basic:
    """Parse either 'lhs = rhs' into Eq(lhs, rhs) or a single expression."""
    if "=" in raw and "==" not in raw:
        parts = raw.split("=")
        if len(parts) != 2:
            raise UnsafeExpressionError("Equation must contain exactly one '='.")
        lhs = safe_parse_expr(parts[0], extra_locals)
        rhs = safe_parse_expr(parts[1], extra_locals)
        return sp.Eq(lhs, rhs)
    return safe_parse_expr(raw, extra_locals)


def sample_plot_2d(
    expr: sp.Basic,
    var_name: str,
    x_min: float = -10.0,
    x_max: float = 10.0,
    num_points: int = 120,
) -> PlotData | None:
    """Sample numeric (x, y) points for a single-variable SymPy expression."""
    free = expr.free_symbols
    if not all(sym.name == var_name for sym in free):
        return None
    var_sym = next(iter(free), sp.Symbol(var_name))
    try:
        fn = sp.lambdify(var_sym, expr, modules=["numpy"])
        xs = np.linspace(x_min, x_max, num_points)
        ys_raw = fn(xs)
        if np.isscalar(ys_raw):
            ys = np.full_like(xs, float(ys_raw), dtype=float)
        else:
            ys = np.asarray(ys_raw, dtype=float)
        clean_x: list[float] = []
        clean_y: list[float] = []
        for xv, yv in zip(xs.tolist(), ys.tolist()):
            if math.isfinite(yv) and abs(yv) <= 1e6:
                clean_x.append(round(float(xv), 4))
                clean_y.append(round(float(yv), 4))
        if len(clean_x) < 2:
            return None
        return PlotData(
            variable=var_name,
            expression_latex=sp.latex(expr),
            x=clean_x,
            y=clean_y,
        )
    except Exception:
        return None


def run_math_engine(
    operation: MathOperation,
    expression: str | None = None,
    variable: str = "x",
    order: int = 1,
    lower_limit: str | None = None,
    upper_limit: str | None = None,
    limit_point: str | None = None,
    limit_direction: Literal["+", "-", "+-"] = "+-",
    matrix_rows: list[list[str]] | None = None,
) -> EngineResult:
    """Execute symbolic/numeric mathematics operations using SymPy."""
    var_sym = sp.Symbol(variable)
    plot_target: sp.Basic | None = None

    if operation in ("matrix_det", "matrix_inv"):
        if not matrix_rows:
            raise UnsafeExpressionError("Matrix rows are required for matrix operations.")
        parsed_rows = [[safe_parse_expr(cell) for cell in row] for row in matrix_rows]
        mat = sp.Matrix(parsed_rows)
        result = mat.det() if operation == "matrix_det" else mat.inv()
        return EngineResult(
            verified=True,
            result_latex=sp.latex(result),
            result_text=str(result),
            metadata={"operation": operation},
        )

    if not expression:
        raise UnsafeExpressionError("Expression is required.")

    if operation == "ode":
        y_func = sp.Function("y")
        extra = {variable: var_sym, "y": y_func}
        eq = _parse_equation_or_expr(expression, extra)
        result = sp.dsolve(eq, y_func(var_sym))
    elif operation == "solve":
        eq = _parse_equation_or_expr(expression, {variable: var_sym})
        result = sp.solve(eq, var_sym)
    else:
        expr = safe_parse_expr(expression, {variable: var_sym})
        if operation == "derivative":
            result = sp.diff(expr, var_sym, max(1, min(order, 10)))
            plot_target = result
        elif operation == "integral":
            if lower_limit is not None and upper_limit is not None:
                low = safe_parse_expr(lower_limit, {variable: var_sym})
                high = safe_parse_expr(upper_limit, {variable: var_sym})
                result = sp.integrate(expr, (var_sym, low, high))
                plot_target = expr
            else:
                result = sp.integrate(expr, var_sym)
                plot_target = result
        elif operation == "limit":
            if limit_point is None:
                raise UnsafeExpressionError("limit_point is required for limit operation.")
            pt = safe_parse_expr(limit_point, {variable: var_sym})
            result = sp.limit(expr, var_sym, pt, dir=limit_direction)
            plot_target = expr
        elif operation == "evaluate":
            result = sp.N(expr)
            plot_target = expr if expr.free_symbols else None
        else:
            result = sp.simplify(expr)
            plot_target = result if result.free_symbols else None

    plot_data = sample_plot_2d(plot_target, variable) if plot_target is not None else None

    return EngineResult(
        verified=True,
        result_latex=sp.latex(result),
        result_text=str(result),
        plot_data=plot_data,
        metadata={"operation": operation, "variable": variable},
    )
