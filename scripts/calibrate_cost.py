"""Phase 3 cost calibration: one short GCMC run at the highest pressure for every case/gas/T.

Purpose: (1) measure loading and CPU cost per cycle where it is largest, to budget the full matrix;
(2) check that every structure + gas combination runs and passes validation before the long run.
Settings: 500 initialization + 1000 production cycles, void fraction key omitted (cost does not
depend on it), everything else as in production. Results are NOT used as isotherm data.

Usage: conda run -n ads python scripts/calibrate_cost.py [--jobs 8] [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import parse, raspa, runner, workflow  # noqa: E402

INIT, PROD = 500, 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cases = workflow.load_cases()
    d = cases["defaults"]
    p_max = max(d["pressures_bar"])
    jobs = []
    for cid in cases["cases"]:
        for gas in d["gases"]:
            for T in d["temperatures_K"][gas]:
                model = workflow.build_model(cid, gas, cases=cases)
                cells = raspa.choose_unit_cells(model["cell"], float(model["ff"].get("CutOffVDW", 12.0)))
                opts = {"cycles": PROD, "init_cycles": INIT, "unit_cells": cells, "void_fraction": None,
                        "ideal_gas": False, "coulomb_cutoff": 12.0, "print_every": 100}
                parent = ROOT / "runs" / "_calibration" / cid / f"{gas}_{T:g}K"
                if a.dry_run:
                    print(cid, gas, T, cells, model["expected_framework_atoms"])
                    continue
                dd = workflow.setup_point(model, "gcmc", gas, T, p_max * 1e5, opts, parent)
                jobs.append((cid, gas, T, cells, model["expected_framework_atoms"], dd))
    if a.dry_run:
        return
    runner.run_pool([j[-1] for j in jobs], jobs=a.jobs)
    rows = []
    for cid, gas, T, cells, atoms, dd in jobs:
        r = parse.parse_run(dd)
        st = json.loads((dd / "status.json").read_text()) if (dd / "status.json").exists() else {}
        n_box = r["abs_molec_uc"] * cells[0] * cells[1] * cells[2] if r and r["abs_molec_uc"] is not None else None
        rows.append({"case": cid, "gas": gas, "T_K": T, "P_bar": p_max, "unit_cells": cells,
                     "framework_atoms_box": atoms * cells[0] * cells[1] * cells[2],
                     "abs_mmol_g": r and r["abs_mol_kg"], "molecules_box": n_box,
                     "cpu_s": st.get("cpu_user_s"), "cycles": INIT + PROD,
                     "cpu_s_per_cycle": st.get("cpu_user_s") / (INIT + PROD) if st.get("cpu_user_s") else None,
                     "problems": st.get("problems"), "framework_atoms_reported": r and r["framework_atoms"],
                     "run_dir": str(dd.relative_to(ROOT))})
    out = ROOT / "results" / "budget"
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(f"{r['case']:10s} {r['gas']:4s} {r['T_K']:5.0f}K cells {r['unit_cells']} atoms {r['framework_atoms_box']:5d} "
              f"N {r['molecules_box'] or 0:7.1f} q {r['abs_mmol_g'] or 0:6.2f} cpu/cycle {r['cpu_s_per_cycle'] or 0:.3f} "
              f"problems {r['problems']}")


if __name__ == "__main__":
    main()
