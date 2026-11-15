"""Unit conversions with hand-computed expected values."""

import pytest

from gcmctools import units


def test_pressure():
    assert units.pressure_to_bar(100.0, "kPa") == pytest.approx(1.0)
    assert units.pressure_to_bar(1.0, "atm") == pytest.approx(1.01325)
    assert units.pressure_to_bar(760.0, "torr") == pytest.approx(1.01325)
    assert units.pressure_to_bar(1e5, "Pa") == pytest.approx(1.0)
    assert units.pressure_to_bar(2.5, "MPa") == pytest.approx(25.0)
    assert units.pressure_to_bar(500.0, "mbar") == pytest.approx(0.5)
    with pytest.raises(units.UnitError):
        units.pressure_to_bar(1.0, "psi")


def test_loading_simple():
    assert units.loading_to_mmol_g(3.0, "mmol/g") == 3.0
    assert units.loading_to_mmol_g(3.0, "mol/kg") == 3.0
    assert units.loading_to_mmol_g(0.002, "mol/g") == pytest.approx(2.0)
    assert units.loading_to_mmol_g(2500.0, "mmol/kg") == pytest.approx(2.5)


def test_cm3_stp_uses_22414():
    # 22.414 cm3(STP)/g of an ideal gas at 273.15 K, 101.325 kPa is exactly 1 mmol/g
    assert units.loading_to_mmol_g(22.414, "cm3(STP)/g") == pytest.approx(1.0)
    assert units.loading_to_mmol_g(100.0, "cm3(STP)/g") == pytest.approx(4.461497)


def test_mass_based_needs_molar_mass():
    # 44.0095 mg CO2 per g = 1 mmol/g;  0.0440095 g/g = 1 mmol/g
    assert units.loading_to_mmol_g(44.0095, "mg/g", molar_mass=44.0095) == pytest.approx(1.0)
    assert units.loading_to_mmol_g(0.0440095, "g/g", molar_mass=44.0095) == pytest.approx(1.0)
    assert units.loading_to_mmol_g(160.4246, "mg/g", molar_mass=16.04246) == pytest.approx(10.0)
    with pytest.raises(units.UnitError):
        units.loading_to_mmol_g(10.0, "mg/g")


@pytest.mark.parametrize("unit", ["wt%", "kg/mol", "molecules/unitcell", "cm3(STP)/cm3", "mmol/cm3",
                                  "mol/l", "mol/m3", "mol/m2", "cm3/m2", "mol/mol", "", "mmol/G"])
def test_rejected_units(unit):
    with pytest.raises(units.UnitError):
        units.loading_to_mmol_g(1.0, unit, molar_mass=44.0)


def test_henry_and_energy():
    assert units.henry_mol_kg_pa_to_mmol_g_bar(6.558276e-05) == pytest.approx(6.558276)
    assert units.kelvin_energy_to_kj_mol(-2716.869) == pytest.approx(-22.5893, rel=1e-4)  # RASPA prints -22.58931
