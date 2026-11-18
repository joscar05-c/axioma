from chempy import Substance, balance_stoichiometry
from app.schemas.solve import EngineResult


def _format_side_latex(side: dict[str, int]) -> str:
    parts = []
    for formula, coeff in side.items():
        prefix = "" if coeff == 1 else str(coeff)
        parts.append(f"{prefix}\\mathrm{{{formula}}}")
    return " + ".join(parts)


def _format_side_text(side: dict[str, int]) -> str:
    parts = []
    for formula, coeff in side.items():
        prefix = "" if coeff == 1 else str(coeff)
        parts.append(f"{prefix}{formula}")
    return " + ".join(parts)


def run_chemistry_engine(
    reactants: list[str] | None = None,
    products: list[str] | None = None,
    formula: str | None = None,
) -> EngineResult:
    """Balance chemical equations or calculate molar mass deterministically with ChemPy."""
    if reactants and products:
        reac_dict, prod_dict = balance_stoichiometry(set(reactants), set(products))
        result_latex = (
            f"{_format_side_latex(dict(reac_dict))} \\rightarrow "
            f"{_format_side_latex(dict(prod_dict))}"
        )
        result_text = (
            f"{_format_side_text(dict(reac_dict))} -> "
            f"{_format_side_text(dict(prod_dict))}"
        )
        return EngineResult(
            verified=True,
            result_latex=result_latex,
            result_text=result_text,
            metadata={
                "reactants": dict(reac_dict),
                "products": dict(prod_dict),
            },
        )

    if formula:
        substance = Substance.from_formula(formula.strip())
        mass = round(float(substance.mass), 4)
        return EngineResult(
            verified=True,
            result_latex=f"M(\\mathrm{{{formula}}}) = {mass}\\,\\mathrm{{g/mol}}",
            result_text=f"M({formula}) = {mass} g/mol",
            metadata={"formula": formula, "molar_mass": mass},
        )

    raise ValueError("Provide reactants and products to balance, or a chemical formula.")
