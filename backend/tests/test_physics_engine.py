from app.engines.physics_engine import run_physics_engine


def test_physics_newton_second_law() -> None:
    res = run_physics_engine(
        equation="F = m * a",
        target="F",
        knowns={"m": "10 kg", "a": "9.81 m/s**2"},
        output_unit="N",
    )
    assert res.verified is True
    assert "98.1" in res.result_text
    assert "N" in res.result_text


def test_physics_solve_for_unknown_with_conversion() -> None:
    res = run_physics_engine(
        equation="v = d / t",
        target="t",
        knowns={"v": "36 km/h", "d": "100 m"},
        output_unit="s",
    )
    assert res.verified is True
    assert "10" in res.result_text
