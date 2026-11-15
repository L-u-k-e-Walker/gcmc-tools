import json
import math
from pathlib import Path

import pytest

from gcmctools import raspa

ROOT = Path(__file__).resolve().parents[1]

CORE_LIKE = """{'_ref': 'TBD', '_srcid': 'X'}
data_test
_symmetry_space_group_name_H-M   'P 1'
_cell_length_a   10.0
_cell_length_b   10.0
_cell_length_c   10.0
_cell_angle_alpha   90.0
_cell_angle_beta   90.0
_cell_angle_gamma   90.0
loop_
 _atom_site_label
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
 _atom_site_charge
 Zn 0.1 0.2 0.3   1.25
 O 0.5 0.5 0.5   -0.625
 O1 0.0 0.0 0.75   -0.625
"""


def test_widths_cubic_and_hexagonal():
    assert raspa.perpendicular_widths([26.343, 26.343, 26.343, 90, 90, 90]) == pytest.approx([26.343] * 3)
    # hexagonal a=b=10, gamma=120: width perpendicular to a (and b) is a*sin(60)
    w = raspa.perpendicular_widths([10, 10, 5, 90, 90, 120])
    assert w[0] == pytest.approx(10 * math.sqrt(3) / 2)
    assert w[2] == pytest.approx(5)


@pytest.mark.parametrize("cell,cutoff,expected", [
    ([26.343, 26.343, 26.343, 90, 90, 90], 12.0, [1, 1, 1]),   # Cu-BTC conventional (old runs)
    ([24.0, 24.0, 24.0, 90, 90, 90], 12.0, [1, 1, 1]),          # exactly 2 x cutoff is allowed
    ([23.99, 24.0, 24.0, 90, 90, 90], 12.0, [2, 1, 1]),
    ([20.022, 19.899, 13.383, 90, 90, 90], 12.0, [2, 2, 2]),    # MFI (example 10 uses 2x2x2)
    ([16.991, 16.991, 16.991, 90, 90, 90], 12.0, [2, 2, 2]),    # ZIF-8
    ([18.6273, 18.6273, 18.6273, 60, 60, 60], 12.0, [2, 2, 2]), # FIQCEN primitive, widths 15.21
])
def test_choose_unit_cells(cell, cutoff, expected):
    n = raspa.choose_unit_cells(cell, cutoff)
    assert n == expected
    assert all(k * w >= 2 * cutoff - 1e-9 for k, w in zip(n, raspa.perpendicular_widths(cell)))


def test_prepared_structures_supercells():
    for cid, exp in {"HKUST-1": [2, 2, 2], "Mg-MOF-74": [4, 2, 2], "IRMOF-1": [2, 2, 2]}.items():
        info = json.loads((ROOT / "data/structures" / cid / "structure.json").read_text())
        assert raspa.choose_unit_cells(info["cell"], 12.0) == exp


def test_prepare_cif_adds_type_symbol_and_keeps_atoms():
    new, changes, atoms = raspa.prepare_cif(CORE_LIKE)
    assert new.startswith("data_test")
    assert "_atom_site_type_symbol" in new
    assert len(changes) == 2
    assert [(a["label"], a["element"], a["charge"]) for a in atoms] == [
        ("Zn", "Zn", 1.25), ("O", "O", -0.625), ("O1", "O", -0.625)]
    # idempotent: a prepared file needs no further changes
    again, changes2, _ = raspa.prepare_cif(new)
    assert changes2 == [] and again.strip() == new.strip()


def test_prepare_cif_on_shipped_structures_is_lossless():
    for cid in ("HKUST-1", "IRMOF-1", "Mg-MOF-74", "ZIF-8", "UiO-66"):
        d = ROOT / "data/structures" / cid
        orig = next((d / "original").glob("*.cif")).read_text()
        prepared = (d / f"{cid}.cif").read_text()
        a = raspa.atom_table(raspa.src_text_without_junk(orig))
        b = raspa.atom_table(prepared)
        assert [(x["x"], x["y"], x["z"], x["charge"]) for x in a] == [(x["x"], x["y"], x["z"], x["charge"]) for x in b]
        assert abs(sum(x["charge"] for x in b)) < 1e-4


def test_simulation_json_real_vs_ideal():
    kw = dict(kind="gcmc", framework_name="F", gas="CO2", T=298.0, P_pa=1e5, cycles=1000,
              init_cycles=100, unit_cells=[1, 1, 1], void_fraction=0.75)
    real = raspa.simulation_json(**kw)
    ideal = raspa.simulation_json(ideal_gas=True, **kw)
    assert "FugacityCoefficient" not in real["Components"][0]       # -> Peng-Robinson
    assert ideal["Components"][0]["FugacityCoefficient"] == 1.0
    assert isinstance(ideal["Components"][0]["FugacityCoefficient"], float)
    assert real["Systems"][0]["HeliumVoidFraction"] == 0.75
    assert real["Systems"][0]["UseChargesFrom"] == "CIF_File"
    assert real["Systems"][0]["CutOffCoulomb"] == 12.0
    assert real["PrintEvery"] == 50
    default_vf = raspa.simulation_json(**{**kw, "void_fraction": None})
    assert "HeliumVoidFraction" not in default_vf["Systems"][0]


def test_legacy_example11_matches_old_input():
    old = json.loads((Path(__file__).parent / "data/cubtc_old_simulation.json").read_text())
    new = raspa.simulation_json(kind="gcmc", framework_name="Cu-BTC", gas="CO2", T=298.0, P_pa=1e5,
                                cycles=20000, init_cycles=5000, unit_cells=[1, 1, 1], void_fraction=None,
                                ideal_gas=False, coulomb_cutoff=None, charges_from_cif=False,
                                print_every=1000, legacy_example11=True)
    assert new == old


def test_float_guard():
    sim = {"Components": [{"FugacityCoefficient": 1}]}
    with pytest.raises(TypeError):
        raspa._assert_float_keys(sim)


def test_force_field_has_gas_sites_and_sources():
    ff = raspa.build_force_field(["Zn", "O", "C", "H"], ["N2"])
    names = [p["name"] for p in ff["PseudoAtoms"]]
    assert {"Zn", "O", "C", "H", "N_n2", "N_com", "probe-He"} <= set(names)
    assert "C_co2" not in names
    zn = next(s for s in ff["SelfInteractions"] if s["name"] == "Zn")
    assert zn["parameters"] == pytest.approx([0.124 * 4184 / 8.314462618, 2.763 / 2 ** (1 / 6)], rel=1e-4)
    with pytest.raises(KeyError):
        raspa.build_force_field(["Xe"], ["CO2"])
