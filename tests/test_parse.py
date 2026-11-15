"""Parser tests against real RASPA3 3.0.29 output (old Cu-BTC runs, PR fugacity, void fraction 1)."""

from pathlib import Path

import pytest

from gcmctools import parse

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def r1bar():
    return parse.parse_text((DATA / "cubtc_298K_1e5Pa.s0.txt").read_text())


def test_final_loadings_take_mol_kg_line(r1bar):
    # values from the LoadingData section (also in cubtc_isotherm/isotherm.csv)
    assert r1bar["abs_mol_kg"] == pytest.approx(3.400751)
    assert r1bar["abs_err_mol_kg"] == pytest.approx(0.1812488)
    assert r1bar["exc_mol_kg"] == pytest.approx(3.354587)
    assert r1bar["exc_molec_uc"] == pytest.approx(32.46553)


def test_settings_echoed(r1bar):
    assert r1bar["temperature_K"] == 298.0
    assert r1bar["pressure_Pa"] == 1e5
    assert r1bar["helium_void_fraction"] == 1.0
    assert r1bar["fugacity_coefficient"] == pytest.approx(0.9945357132660135)
    assert r1bar["excess_molecules_correction"] == pytest.approx(0.4467715588547444)


def test_framework_fields_not_confused_with_component(r1bar):
    assert r1bar["framework_atoms"] == 624
    assert r1bar["framework_net_charge"] == pytest.approx(0.0, abs=1e-6)
    assert r1bar["framework_mass_amu"] == pytest.approx(9677.9499)


def test_henry_enthalpy_and_energy():
    r = parse.parse_text((DATA / "cubtc_298K_1000Pa.s0.txt").read_text())
    assert r["henry_mol_kg_pa"] == pytest.approx(6.558276e-05)
    assert r["henry_err_mol_kg_pa"] == pytest.approx(1.019934e-05)
    assert r["enthalpy_kj_mol"] == pytest.approx(-25.43456)
    assert r["enthalpy_err_kj_mol"] == pytest.approx(0.3627641)
    assert r["measured_fugacity_Pa"] == pytest.approx(966.8704)
    assert r["framework_molecule_energy_K"] == pytest.approx(-1679.881)
    assert r["finished"]


def test_production_series(r1bar):
    s = r1bar["production_series_exc_mol_kg"]
    assert len(s) == 20                      # 20000 cycles / PrintEvery 1000, initialization excluded
    assert s[0] == (0, pytest.approx(3.673632))
    assert [c for c, _ in s] == list(range(0, 20000, 1000))


def test_zero_atom_framework_is_visible():
    r = parse.parse_text((DATA / "zero_atoms.s0.txt").read_text())
    assert r["framework_atoms"] == 0


def test_truncated_output_not_finished():
    text = (DATA / "cubtc_298K_1e5Pa.s0.txt").read_text()
    r = parse.parse_text(text[: len(text) // 2])
    assert not r["finished"]
    assert r["exc_mol_kg"] is None


def test_drift_check_flags_trend_not_noise():
    flat = [(i, 1.0 + (0.01 if i % 2 else -0.01)) for i in range(21)]
    ramp = [(i, 1.0 + 0.05 * i) for i in range(21)]
    assert parse.drift_check(flat)[2] is False
    assert parse.drift_check(ramp)[2] is True
    assert parse.drift_check(ramp[:4]) == (None, None, False)
