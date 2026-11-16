"""Extension rules and the matrix cost ordering."""

from gcmctools import workflow


def r(exc, err, n_uc, series=None):
    return {"exc_mol_kg": exc, "exc_err_mol_kg": err, "abs_molec_uc": n_uc,
            "production_series_exc_mol_kg": series or [(i, exc) for i in range(21)]}


def test_extension_factor_from_relative_error():
    assert workflow.extension_factor(r(1.0, 0.04, 5.0), unit_cells=[2, 2, 2]) == 1
    assert workflow.extension_factor(r(1.0, 0.075, 5.0), unit_cells=[2, 2, 2]) == 3   # (0.075/0.05)^2 = 2.25
    assert workflow.extension_factor(r(1.0, 0.5, 5.0), unit_cells=[2, 2, 2]) == 4     # capped


def test_low_loading_points_not_extended():
    # 0.1 molecules per unit cell x 8 cells = 0.8 molecules in the box (< 1)
    assert workflow.extension_factor(r(0.01, 0.005, 0.1), unit_cells=[2, 2, 2]) == 1
    assert workflow.extension_factor(r(0.01, 0.005, 0.2), unit_cells=[2, 2, 2]) == 4


def test_series_error_can_trigger_extension():
    noisy = [(0, 1.0)] + [(i, 1.0 + (0.6 if i % 2 else -0.6)) for i in range(1, 21)]
    # block error says 1%, series SE = 0.6*sqrt(20/19)/sqrt(20) ~ 0.138 -> 13.8% -> x4
    assert workflow.extension_factor(r(1.0, 0.01, 5.0, noisy), unit_cells=[1, 1, 1]) == 4


def test_cost_estimate_orders_high_pressure_first():
    cal = [{"case": "X", "gas": "CO2", "T_K": 298.0, "molecules_box": 200.0, "cpu_s_per_cycle": 0.2}]
    hi = workflow.cost_estimate("X", "CO2", 298.0, "gcmc", 10.0, 25000, cal)
    lo = workflow.cost_estimate("X", "CO2", 298.0, "gcmc", 0.01, 25000, cal)
    assert hi == 0.2 * 25000 and lo == 0.2 / 200 * 20 * 25000
    assert workflow.cost_estimate("Y", "CO2", 298.0, "gcmc", 10.0, 25000, cal) == 0.0
