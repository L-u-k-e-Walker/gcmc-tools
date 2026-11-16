"""Phase 1 regression tables for HKUST-1 CO2 298 K.

Reads results/HKUST-1/CO2_298K_regression_old.csv and ..._regression_corrected(_points).csv,
the MISSION targets (cases.yaml) and the on-disk old isotherm.csv. Writes
results/HKUST-1/regression_table.csv and regression_corrected_vs_old.csv and prints markdown.
Pass = |sim - ref| <= max(3 * combined standard error, 10% of ref).
"""

import math
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "HKUST-1"


def passes(v, e, ref, ref_e):
    se = math.sqrt(e ** 2 + ref_e ** 2)
    tol = max(3 * se, 0.10 * abs(ref))
    return abs(v - ref) <= tol, tol


def main():
    reg = yaml.safe_load((ROOT / "cases/cases.yaml").read_text())["cases"]["HKUST-1"]["regression"]
    targets = {float(k): v for k, v in reg["targets_excess_mmol_g"].items()}
    ondisk = pd.read_csv(Path(reg["ondisk_csv"]).expanduser())
    old = pd.read_csv(RES / "CO2_298K_regression_old.csv")
    old = old[old.basis == "excess"].set_index("P_bar")
    rows = []
    for p, (t, te) in sorted(targets.items()):
        v, e = old.loc[p, "loading_mmol_g"], old.loc[p, "loading_err_mmol_g"]
        ok_t, tol_t = passes(v, e, t, te)
        od = ondisk[ondisk.P_bar == p].iloc[0]
        ok_d, tol_d = passes(v, e, od.exc_mmol_g, od.exc_err)
        rows.append({"P_bar": p, "sim_excess": v, "sim_err": e, "target": t, "target_err": te,
                     "diff_vs_target": v - t, "tol_vs_target": tol_t, "pass_vs_target": ok_t,
                     "ondisk_PR": od.exc_mmol_g, "ondisk_err": od.exc_err, "diff_vs_ondisk": v - od.exc_mmol_g,
                     "tol_vs_ondisk": tol_d, "pass_vs_ondisk": ok_d})
    tab = pd.DataFrame(rows)
    tab.to_csv(RES / "regression_table.csv", index=False)
    print("## Regression (old settings: ideal gas, void fraction 1.0, 1x1x1, 20k+5k cycles)\n")
    print("| P (bar) | sim excess | MISSION target | pass | on-disk (PR) | pass |")
    print("|---:|---:|---:|:-:|---:|:-:|")
    for r in rows:
        print(f"| {r['P_bar']:g} | {r['sim_excess']:.3f} ± {r['sim_err']:.3f} | {r['target']:.3f} ± {r['target_err']:.3f} "
              f"| {'yes' if r['pass_vs_target'] else 'NO'} | {r['ondisk_PR']:.3f} ± {r['ondisk_err']:.3f} "
              f"| {'yes' if r['pass_vs_ondisk'] else 'NO'} |")

    cpath = RES / "CO2_298K_regression_corrected_points.csv"
    if not cpath.exists():
        return
    opts = pd.read_csv(RES / "CO2_298K_regression_old_points.csv").set_index("P_bar")
    cor = pd.read_csv(cpath).set_index("P_bar")
    # Expected (deterministic) effects. The old run used phi = 1, so its absolute loading is a
    # function of fugacity f = P; the real-gas run sees f = phi*P. Use the old absolute DSL fit.
    import json
    from gcmctools.fit import dslangmuir
    fa = json.loads((RES / "CO2_298K_regression_old.json").read_text())["fits_absolute"]["DSLangmuir"]
    rows = []
    for p in sorted(targets):
        o, c = opts.loc[p], cor.loc[p]
        d = c.exc_mmol_g - o.exc_mmol_g
        se = math.sqrt(c.exc_err ** 2 + o.exc_err ** 2)
        fug = dslangmuir(c.fugacity_coefficient * p, *fa["params"].values()) - dslangmuir(p, *fa["params"].values())
        vfterm = (o.abs_mmol_g - o.exc_mmol_g) - (c.abs_mmol_g - c.exc_mmol_g)
        rows.append({"P_bar": p, "expected_fugacity_effect": fug, "expected_voidfraction_effect": vfterm,
                     "expected_total": fug + vfterm, "old_exc": o.exc_mmol_g, "old_err": o.exc_err, "phi_old": o.fugacity_coefficient,
                     "vf_old": o.helium_void_fraction, "new_exc": c.exc_mmol_g, "new_err": c.exc_err,
                     "new_abs": c.abs_mmol_g, "phi_new": c.fugacity_coefficient, "vf_new": c.helium_void_fraction,
                     "delta": d, "delta_se": se, "delta_rel": d / o.exc_mmol_g,
                     "abs_minus_exc_new": c.abs_mmol_g - c.exc_mmol_g,
                     "abs_minus_exc_old": o.abs_mmol_g - o.exc_mmol_g})
    t2 = pd.DataFrame(rows)
    t2.to_csv(RES / "regression_corrected_vs_old.csv", index=False)
    print("\n## Corrected (Peng-Robinson, computed void fraction) vs old\n")
    print("| P (bar) | phi | old excess | corrected excess | measured change | change/SE | expected: fugacity | expected: void fraction | expected total |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['P_bar']:g} | {r['phi_new']:.4f} | {r['old_exc']:.3f} ± {r['old_err']:.3f} | "
              f"{r['new_exc']:.3f} ± {r['new_err']:.3f} | {r['delta']:+.3f} ({r['delta_rel']:+.1%}) | "
              f"{r['delta'] / r['delta_se']:+.1f} | {r['expected_fugacity_effect']:+.3f} | {r['expected_voidfraction_effect']:+.4f} | "
              f"{r['expected_total']:+.3f} ({r['expected_total'] / r['old_exc']:+.1%}) |")


if __name__ == "__main__":
    sys.exit(main())
