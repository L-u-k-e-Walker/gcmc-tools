"""Unit conversions shared by the simulation and experiment tools.

Every factor is explicit and covered by tests with hand-computed values.
Conventions:
- Pressure is reported in bar (1 bar = 1e5 Pa).
- Loading is reported in mmol per gram of adsorbent (mmol/g == mol/kg).
- STP for cm3(STP): 273.15 K and 101.325 kPa, so the ideal-gas molar volume is
  22.414 cm3/mmol (22414 cm3/mol). pyGAPS uses 22.416; we deliberately follow MISSION.md.
"""

R_J_PER_MOL_K = 8.314462618  # CODATA 2018, exact by SI definition (kB * NA)
STP_CM3_PER_MMOL = 22.414

# Pressure units -> bar. Strict allowlist; anything else raises.
_PRESSURE_TO_BAR = {
    "bar": 1.0,
    "mbar": 1e-3,
    "Pa": 1e-5,
    "kPa": 1e-2,
    "MPa": 10.0,
    "atm": 1.01325,
    "torr": 1.01325 / 760.0,
    "mmHg": 1.01325 / 760.0,  # 1 mmHg = 133.322 Pa; equal to torr within 1.4e-7 relative
}


class UnitError(ValueError):
    """Raised for unit strings that are not on the allowlist or need missing information."""


def pressure_to_bar(value, unit):
    if unit not in _PRESSURE_TO_BAR:
        raise UnitError(f"pressure unit not on allowlist: {unit!r}")
    return value * _PRESSURE_TO_BAR[unit]


def pa_to_bar(p_pa):
    return p_pa * 1e-5


def bar_to_pa(p_bar):
    return p_bar * 1e5


def mol_per_kg_to_mmol_per_g(value):
    """RASPA3 reports [mol/kg-framework]; 1 mol/kg = 1 mmol/g exactly."""
    return value


def henry_mol_kg_pa_to_mmol_g_bar(k):
    """Henry coefficient: mol/kg/Pa -> mmol/g/bar (x 1e5)."""
    return k * 1e5


def kelvin_energy_to_kj_mol(e_kelvin):
    """Energy expressed as E/kB in K -> kJ/mol (multiply by R)."""
    return e_kelvin * R_J_PER_MOL_K / 1000.0


# Loading units -> mmol/g. Conversions that need a molar mass take it as an argument.
# Units needing a density, a unit-cell mass or an unstated wt% basis are rejected.
_LOADING_FACTORS = {
    "mmol/g": 1.0,
    "mol/kg": 1.0,
    "mmol/kg": 1e-3,
    "mol/g": 1e3,
    "cm3(STP)/g": 1.0 / STP_CM3_PER_MMOL,
    "ml(STP)/g": 1.0 / STP_CM3_PER_MMOL,
}
_LOADING_NEEDS_MOLAR_MASS = {
    "mg/g": 1.0,   # mg gas per g sorbent / (g/mol) = mmol/g
    "g/g": 1e3,
    "g/kg": 1.0,
}


def loading_to_mmol_g(value, unit, molar_mass=None):
    """Convert an uptake to mmol/g. `molar_mass` is the adsorbate molar mass in g/mol."""
    if unit in _LOADING_FACTORS:
        return value * _LOADING_FACTORS[unit]
    if unit in _LOADING_NEEDS_MOLAR_MASS:
        if not molar_mass:
            raise UnitError(f"{unit!r} needs the adsorbate molar mass")
        return value * _LOADING_NEEDS_MOLAR_MASS[unit] / molar_mass
    raise UnitError(f"loading unit not on allowlist: {unit!r}")


def allowed_loading_units():
    return sorted(set(_LOADING_FACTORS) | set(_LOADING_NEEDS_MOLAR_MASS))
