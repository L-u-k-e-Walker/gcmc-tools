"""Phase 5 sensitivity runs (MISSION section 7), all CO2 at 298 K, one shared longest-first pool.

Variants (each compared with the 'main' matrix result at the same pressure):
- cycles4x     : 4x production and initialization cycles, P = 0.1, 1 bar          (cause 4: convergence)
- bigcell      : unit cells +1 in every direction, P = 0.1, 1 bar                 (cause 4: system size)
- charges_off  : framework charges zero (pseudo-atom charges), P = 0.01, 0.1, 1 bar (cause 7: charges)
- uff          : all-UFF framework LJ (MOFs only), P = 0.01, 0.1, 1 bar           (cause 7: LJ set)
- movie        : production snapshots at 0.1 bar for the nearest-metal analysis    (cause 6: open metal sites)
Extension is off: every variant uses fixed cycles so the comparison is like for like.

Usage: conda run -n ads python scripts/phase5_runs.py [--jobs 8] [--plan]
Writes results/phase5/sensitivity.csv.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import parse, raspa, runner, units, workflow  # noqa: E402

GAS, T = "CO2", 298.0
BASE = {"cycles": 20000, "init_cycles": 5000, "unit_cells": "auto", "void_fraction": "auto",
        "ideal_gas": False, "coulomb_cutoff": 12.0, "print_every": None}
VARIANTS = {
    "cycles4x": {"pressures": [0.1, 1.0], "opts": {"cycles": 80000, "init_cycles": 20000}},
    "bigcell": {"pressures": [0.1, 1.0], "opts": {}, "bigcell": True},
    "charges_off": {"pressures": [0.01, 0.1, 1.0], "opts": {}, "charges_off": True},
    "uff": {"pressures": [0.01, 0.1, 1.0], "opts": {}, "recipe": "mof-uff"},
    "movie": {"pressures": [0.1], "opts": {"extra_system": {"OutputPDBMovie": True, "SampleMovieEvery": 100}}},
}


def setup_all(log=print):
    cases = workflow.load_cases()
    cal = json.loads((ROOT / "results/budget/calibration.json").read_text())
    jobs = []
    for cid, c in cases["cases"].items():
        for vname, v in VARIANTS.items():
            if vname == "uff" and c["recipe"] != "mof":
                continue
            model = workflow.build_model(cid, GAS, v.get("recipe"), cases)
            if v.get("charges_off"):
                model = {**model, "charges_from_cif": False,
                         "ff": {**model["ff"], "PseudoAtoms": [
                             {**p, "charge": 0.0} if p["framework"] else p for p in model["ff"]["PseudoAtoms"]]}}
            parent = ROOT / "runs" / cid / f"{GAS}_{T:g}K" / f"phase5_{vname}"
            parent.mkdir(parents=True, exist_ok=True)
            opts = workflow.resolve_options(model, {**BASE, **v["opts"]}, parent, log=lambda m: None)
            if v.get("bigcell"):
                opts["unit_cells"] = [n + 1 for n in opts["unit_cells"]]
            for p in v["pressures"]:
                d = workflow.setup_point(model, "gcmc", GAS, T, units.bar_to_pa(p), opts, parent)
                cyc = opts["cycles"] + opts["init_cycles"]
                cost = workflow.cost_estimate(cid, GAS, T, "gcmc", p, cyc, cal)
                if v.get("bigcell"):
                    base_cells = raspa.choose_unit_cells(model["cell"], 12.0)
                    f = (opts["unit_cells"][0] * opts["unit_cells"][1] * opts["unit_cells"][2]) / \
                        (base_cells[0] * base_cells[1] * base_cells[2])
                    cost *= f * f                   # more atoms per step and more molecules per cycle
                jobs.append({"case": cid, "variant": vname, "P_bar": p, "dir": d, "cost": cost,
                             "unit_cells": opts["unit_cells"]})
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--plan", action="store_true")
    a = ap.parse_args()
    jobs = setup_all()
    jobs.sort(key=lambda j: -j["cost"])
    print(f"{len(jobs)} runs, estimated {sum(j['cost'] for j in jobs) / 3600:.1f} CPU h; "
          f"longest {jobs[0]['case']} {jobs[0]['variant']} {jobs[0]['P_bar']} bar {jobs[0]['cost'] / 3600:.2f} h")
    if a.plan:
        return
    runner.run_pool([j["dir"] for j in jobs], jobs=a.jobs)
    rows = []
    for j in jobs:
        r = parse.parse_run(j["dir"])
        run = json.loads((j["dir"] / "run.json").read_text())
        st = json.loads((j["dir"] / "status.json").read_text()) if (j["dir"] / "status.json").exists() else {}
        rows.append({"case": j["case"], "variant": j["variant"], "P_bar": j["P_bar"],
                     "unit_cells": j["unit_cells"], "cycles": run["settings"]["cycles"],
                     "exc_mmol_g": r and r["exc_mol_kg"], "exc_err": r and r["exc_err_mol_kg"],
                     "exc_err_series": r and parse.series_stderr(r["production_series_exc_mol_kg"]),
                     "abs_mmol_g": r and r["abs_mol_kg"], "problems": st.get("problems"),
                     "cpu_s": st.get("cpu_user_s"), "run_dir": str(j["dir"].relative_to(ROOT))})
    out = ROOT / "results" / "phase5"
    out.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    pd.DataFrame(rows).sort_values(["case", "variant", "P_bar"]).to_csv(out / "sensitivity_runs.csv", index=False)
    print(out / "sensitivity_runs.csv")


if __name__ == "__main__":
    main()
