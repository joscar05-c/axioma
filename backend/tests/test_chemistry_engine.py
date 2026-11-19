import pytest
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


def test_balance_propane_combustion() -> None:
    res = run_chemistry_engine(reactants=["C3H8", "O2"], products=["CO2", "H2O"])
    assert res.verified is True
    assert res.metadata["reactants"] == {"C3H8": 1, "O2": 5}
    assert res.metadata["products"] == {"CO2": 3, "H2O": 4}


def test_balance_iron_oxide_and_aluminum_hydroxide() -> None:
    res_fe = run_chemistry_engine(reactants=["Fe2O3", "CO"], products=["Fe", "CO2"])
    assert res_fe.verified is True
    assert res_fe.metadata["reactants"] == {"Fe2O3": 1, "CO": 3}
    assert res_fe.metadata["products"] == {"Fe": 2, "CO2": 3}

    res_al = run_chemistry_engine(
        reactants=["Al(OH)3", "H2SO4"],
        products=["Al2(SO4)3", "H2O"],
    )
    assert res_al.verified is True
    assert res_al.metadata["reactants"] == {"Al(OH)3": 2, "H2SO4": 3}
    assert res_al.metadata["products"] == {"Al2(SO4)3": 1, "H2O": 6}


def test_molar_mass_brackets_and_hydrate() -> None:
    res_ca = run_chemistry_engine(formula="Ca(OH)2")
    assert res_ca.verified is True
    assert 74.0 < res_ca.metadata["molar_mass"] < 74.2

    res_cu = run_chemistry_engine(formula="CuSO4.5H2O")
    assert res_cu.verified is True
    assert 249.6 < res_cu.metadata["molar_mass"] < 249.8


def test_rejects_invalid_formula_and_impossible_reaction() -> None:
    with pytest.raises(ValueError):
        run_chemistry_engine(formula="Zz2O")

    with pytest.raises(ValueError):
        run_chemistry_engine(reactants=["H2"], products=["O2"])
