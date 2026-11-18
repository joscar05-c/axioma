from app.engines.chemistry_engine import run_chemistry_engine


def test_balance_water_formation() -> None:
    res = run_chemistry_engine(reactants=["H2", "O2"], products=["H2O"])
    assert res.verified is True
    assert res.metadata["reactants"]["H2"] == 2
    assert res.metadata["reactants"]["O2"] == 1
    assert res.metadata["products"]["H2O"] == 2


def test_molar_mass_sulfuric_acid() -> None:
    res = run_chemistry_engine(formula="H2SO4")
    assert res.verified is True
    assert 98.0 < res.metadata["molar_mass"] < 98.2
