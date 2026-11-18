import pytest
from app.engines.math_engine import UnsafeExpressionError, run_math_engine


def test_derivative_polynomial_and_plot() -> None:
    res = run_math_engine(operation="derivative", expression="x**3 + 2*x", variable="x")
    assert res.verified is True
    assert "3 x^{2} + 2" in res.result_latex
    assert res.plot_data is not None
    assert len(res.plot_data.x) > 10


def test_definite_integral() -> None:
    res = run_math_engine(
        operation="integral",
        expression="x**2",
        variable="x",
        lower_limit="0",
        upper_limit="3",
    )
    assert res.verified is True
    assert res.result_text == "9"


def test_indefinite_integral() -> None:
    res = run_math_engine(operation="integral", expression="cos(x)", variable="x")
    assert res.verified is True
    assert "sin" in res.result_text


def test_ode_solution() -> None:
    res = run_math_engine(
        operation="ode",
        expression="Derivative(y(x), x) - 2*y(x) = 0",
        variable="x",
    )
    assert res.verified is True
    assert "C1" in res.result_text


def test_matrix_determinant() -> None:
    res = run_math_engine(
        operation="matrix_det",
        matrix_rows=[["2", "1"], ["3", "4"]],
    )
    assert res.verified is True
    assert res.result_text == "5"


def test_rejects_unsafe_expression() -> None:
    with pytest.raises(UnsafeExpressionError):
        run_math_engine(
            operation="evaluate",
            expression="__import__('os').system('echo pwned')",
        )
