from functools import reduce
import math
import re
import sympy as sp
from app.schemas.solve import EngineResult

_ATOMIC_MASSES: dict[str, float] = {
    "H": 1.008,
    "He": 4.0026,
    "Li": 6.94,
    "Be": 9.0122,
    "B": 10.81,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "Ne": 20.180,
    "Na": 22.990,
    "Mg": 24.305,
    "Al": 26.982,
    "Si": 28.085,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "Ar": 39.948,
    "K": 39.098,
    "Ca": 40.078,
    "Sc": 44.956,
    "Ti": 47.867,
    "V": 50.942,
    "Cr": 51.996,
    "Mn": 54.938,
    "Fe": 55.845,
    "Co": 58.933,
    "Ni": 58.693,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.630,
    "As": 74.922,
    "Se": 78.971,
    "Br": 79.904,
    "Kr": 83.798,
    "Rb": 85.468,
    "Sr": 87.62,
    "Y": 88.906,
    "Zr": 91.224,
    "Nb": 92.906,
    "Mo": 95.95,
    "Tc": 98.0,
    "Ru": 101.07,
    "Rh": 102.91,
    "Pd": 106.42,
    "Ag": 107.87,
    "Cd": 112.41,
    "In": 114.82,
    "Sn": 118.71,
    "Sb": 121.76,
    "Te": 127.60,
    "I": 126.90,
    "Xe": 131.29,
    "Cs": 132.91,
    "Ba": 137.33,
    "La": 138.91,
    "Ce": 140.12,
    "Pr": 140.91,
    "Nd": 144.24,
    "Pm": 145.0,
    "Sm": 150.36,
    "Eu": 151.96,
    "Gd": 157.25,
    "Tb": 158.93,
    "Dy": 162.50,
    "Ho": 164.93,
    "Er": 167.26,
    "Tm": 168.93,
    "Yb": 173.05,
    "Lu": 174.97,
    "Hf": 178.49,
    "Ta": 180.95,
    "W": 183.84,
    "Re": 186.21,
    "Os": 190.23,
    "Ir": 192.22,
    "Pt": 195.08,
    "Au": 196.97,
    "Hg": 200.59,
    "Tl": 204.38,
    "Pb": 207.2,
    "Bi": 208.98,
    "Po": 209.0,
    "At": 210.0,
    "Rn": 222.0,
    "Fr": 223.0,
    "Ra": 226.0,
    "Ac": 227.0,
    "Th": 232.04,
    "Pa": 231.04,
    "U": 238.03,
    "Np": 237.0,
    "Pu": 244.0,
    "Am": 243.0,
    "Cm": 247.0,
    "Bk": 247.0,
    "Cf": 251.0,
    "Es": 252.0,
    "Fm": 257.0,
    "Md": 258.0,
    "No": 259.0,
    "Lr": 266.0,
    "Rf": 267.0,
    "Db": 268.0,
    "Sg": 269.0,
    "Bh": 270.0,
    "Hs": 277.0,
    "Mt": 278.0,
    "Ds": 281.0,
    "Rg": 282.0,
    "Cn": 285.0,
    "Nh": 286.0,
    "Fl": 289.0,
    "Mc": 290.0,
    "Lv": 293.0,
    "Ts": 294.0,
    "Og": 294.0,
}

_BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
_CLOSING_TO_OPENING = {v: k for k, v in _BRACKET_PAIRS.items()}
_TOKEN_RE = re.compile(r"([A-Z][a-z]?)|(\d+)|([\(\[\{])|([\)\]\}])")
_CHARGE_RE = re.compile(r"\^(\d*)([+-])$")
_LEADING_MULT_RE = re.compile(r"^(\d+)(.+)$")


def _parse_segment(segment: str) -> dict[str, int]:
    """Parse a single chemical segment (without hydrate separator or charge)."""
    mult = 1
    body = segment
    mult_match = _LEADING_MULT_RE.match(segment)
    if mult_match:
        mult = int(mult_match.group(1))
        body = mult_match.group(2)
        if mult <= 0:
            raise ValueError(f"Invalid stoichiometric multiplier in '{segment}'.")

    stack: list[tuple[str | None, dict[str, int]]] = [(None, {})]
    pos = 0
    tokens = list(_TOKEN_RE.finditer(body))
    idx = 0

    while idx < len(tokens):
        match = tokens[idx]
        if match.start() != pos:
            raise ValueError(f"Invalid chemical formula syntax in '{segment}'.")
        pos = match.end()

        elem, digits, open_b, close_b = match.groups()
        if elem is not None:
            if elem not in _ATOMIC_MASSES:
                raise ValueError(f"Unknown chemical element: '{elem}'.")
            count = 1
            if idx + 1 < len(tokens) and tokens[idx + 1].group(2) is not None:
                next_match = tokens[idx + 1]
                if next_match.start() != pos:
                    raise ValueError(f"Invalid chemical formula syntax in '{segment}'.")
                count = int(next_match.group(2))
                pos = next_match.end()
                idx += 1
            stack[-1][1][elem] = stack[-1][1].get(elem, 0) + count
        elif open_b is not None:
            stack.append((open_b, {}))
        elif close_b is not None:
            expected_open = _CLOSING_TO_OPENING[close_b]
            if len(stack) == 1 or stack[-1][0] != expected_open:
                raise ValueError(f"Unbalanced brackets in formula '{segment}'.")
            _, group_counts = stack.pop()
            if not group_counts:
                raise ValueError(f"Empty bracket group in formula '{segment}'.")
            group_mult = 1
            if idx + 1 < len(tokens) and tokens[idx + 1].group(2) is not None:
                next_match = tokens[idx + 1]
                if next_match.start() != pos:
                    raise ValueError(f"Invalid chemical formula syntax in '{segment}'.")
                group_mult = int(next_match.group(2))
                pos = next_match.end()
                idx += 1
            for el, cnt in group_counts.items():
                stack[-1][1][el] = stack[-1][1].get(el, 0) + cnt * group_mult
        else:
            raise ValueError(f"Unexpected numeric token in formula '{segment}'.")

        idx += 1

    if pos != len(body) or len(stack) != 1:
        raise ValueError(f"Invalid or unbalanced chemical formula '{segment}'.")

    return {el: cnt * mult for el, cnt in stack[0][1].items()}


def parse_chemical_formula(formula: str) -> dict[str, int]:
    """Parse a chemical formula into element counts (and optional net ionic '_charge')."""
    text = (formula or "").strip()
    if not text:
        raise ValueError("Chemical formula cannot be empty.")

    charge = 0
    if "^" in text:
        charge_match = _CHARGE_RE.search(text)
        if not charge_match:
            raise ValueError(f"Invalid ionic charge notation in '{text}'.")
        mag = int(charge_match.group(1)) if charge_match.group(1) else 1
        charge = mag if charge_match.group(2) == "+" else -mag
        text = text[: charge_match.start()].strip()
        if not text:
            raise ValueError(f"Missing formula before charge in '{formula}'.")

    segments = re.split(r"[.·]", text)
    if any(not seg.strip() for seg in segments):
        raise ValueError(f"Invalid hydrate/adduct separator in '{formula}'.")

    total_counts: dict[str, int] = {}
    for seg in segments:
        seg_counts = _parse_segment(seg.strip())
        for el, cnt in seg_counts.items():
            total_counts[el] = total_counts.get(el, 0) + cnt

    if not total_counts:
        raise ValueError(f"No chemical elements found in '{formula}'.")

    if charge != 0:
        total_counts["_charge"] = charge

    return total_counts


def balance_chemical_equation(
    reactants: list[str],
    products: list[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """Balance a chemical equation exactly using SymPy matrix nullspace."""
    clean_reactants = list(dict.fromkeys(r.strip() for r in reactants if r and r.strip()))
    clean_products = list(dict.fromkeys(p.strip() for p in products if p and p.strip()))
    if not clean_reactants or not clean_products:
        raise ValueError("Reactants and products must both be non-empty.")

    parsed_reactants = [parse_chemical_formula(r) for r in clean_reactants]
    parsed_products = [parse_chemical_formula(p) for p in clean_products]

    all_keys: list[str] = []
    seen_keys: set[str] = set()
    for counts in parsed_reactants + parsed_products:
        for k in counts:
            if k not in seen_keys:
                seen_keys.add(k)
                all_keys.append(k)

    rows: list[list[int]] = []
    for key in all_keys:
        row = [counts.get(key, 0) for counts in parsed_reactants]
        row.extend(-counts.get(key, 0) for counts in parsed_products)
        rows.append(row)

    mat = sp.Matrix(rows)
    nullspace = mat.nullspace()
    if len(nullspace) == 0:
        raise ValueError("Could not balance chemical equation.")
    if len(nullspace) > 1:
        raise ValueError("Chemical equation is underdetermined.")

    vec = nullspace[0]
    denominators = [int(sp.fraction(val)[1]) for val in vec]
    lcm_val = reduce(sp.ilcm, denominators, 1)
    ints = [int(val * lcm_val) for val in vec]

    if all(c < 0 for c in ints):
        ints = [-c for c in ints]

    if not all(c > 0 for c in ints):
        raise ValueError("Chemical equation requires positive stoichiometric coefficients.")

    common_gcd = reduce(math.gcd, ints)
    if common_gcd > 1:
        ints = [c // common_gcd for c in ints]

    n_r = len(clean_reactants)
    reac_dict = dict(zip(clean_reactants, ints[:n_r]))
    prod_dict = dict(zip(clean_products, ints[n_r:]))
    return reac_dict, prod_dict


def calculate_molar_mass(formula: str) -> float:
    """Calculate the molar mass (g/mol) of a chemical formula."""
    counts = parse_chemical_formula(formula)
    total = sum(
        cnt * _ATOMIC_MASSES[el]
        for el, cnt in counts.items()
        if el != "_charge"
    )
    return round(float(total), 4)


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
    """Balance chemical equations or calculate molar mass deterministically with SymPy."""
    if reactants and products:
        reac_dict, prod_dict = balance_chemical_equation(reactants, products)
        result_latex = (
            f"{_format_side_latex(reac_dict)} \\rightarrow "
            f"{_format_side_latex(prod_dict)}"
        )
        result_text = (
            f"{_format_side_text(reac_dict)} -> "
            f"{_format_side_text(prod_dict)}"
        )
        return EngineResult(
            verified=True,
            result_latex=result_latex,
            result_text=result_text,
            metadata={
                "reactants": reac_dict,
                "products": prod_dict,
            },
        )

    if formula:
        clean_formula = formula.strip()
        mass = calculate_molar_mass(clean_formula)
        return EngineResult(
            verified=True,
            result_latex=f"M(\\mathrm{{{clean_formula}}}) = {mass}\\,\\mathrm{{g/mol}}",
            result_text=f"M({clean_formula}) = {mass} g/mol",
            metadata={"formula": clean_formula, "molar_mass": mass},
        )

    raise ValueError("Provide reactants and products to balance, or a chemical formula.")
