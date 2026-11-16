"""Command-line interface: `gcmc isotherm`, `gcmc collect`, `gcmc regression` (Tool 1).

Run inside the `ads` env, e.g. `bin/gcmc isotherm --case IRMOF-1 --gas CO2 --T 298`.
Long runs: add `--detach` to start the same command in a detached tmux session.
"""

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import workflow

ROOT = workflow.ROOT


def _log_to(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a")

    def log(msg):
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
        print(line, flush=True)
        f.write(line + "\n")
        f.flush()
    return log


def _detach(argv, session):
    cmd = " ".join(shlex.quote(a) for a in argv if a != "--detach")
    full = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(str(ROOT / 'bin' / 'gcmc'))} {cmd}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, full], check=True)
    print(f"started tmux session '{session}': {full}")


def cmd_isotherm(a, argv):
    cases = workflow.load_cases()
    d = cases["defaults"]
    if bool(a.case) == bool(a.cif):
        raise SystemExit("give exactly one of --case or --cif")
    case_id, case_table = a.case, None
    if a.cif:
        case_id, case_table = workflow.adhoc_case(a.cif)
    pressures = a.pressures or d["pressures_bar"]
    label = a.label or ("ideal" if a.ideal_gas else "real") + f"_vf-{a.void_fraction}"
    if a.dry_run:
        print(json.dumps(workflow.plan(case_id, a.gas, a.T, pressures, {
            "cycles": a.cycles, "init_cycles": a.init_cycles, "unit_cells": a.unit_cells or "auto",
            "void_fraction": a.void_fraction, "ideal_gas": a.ideal_gas}, a.recipe, case_table), indent=2))
        return
    if a.detach:
        return _detach(["isotherm"] + argv, f"gcmc_{case_id}_{a.gas}_{a.T:g}_{label}".replace(".", "p"))
    opts = {"cycles": a.cycles, "init_cycles": a.init_cycles, "unit_cells": a.unit_cells or "auto",
            "void_fraction": a.void_fraction, "ideal_gas": a.ideal_gas,
            "coulomb_cutoff": None if a.coulomb_cutoff == "auto" else float(a.coulomb_cutoff),
            "print_every": a.print_every}
    log = _log_to(workflow.isotherm_dir(case_id, a.gas, a.T, label) / "driver.log")
    log(f"gcmc isotherm {' '.join(argv)}")
    parent = workflow.run_isotherm(case_id, a.gas, a.T, pressures, opts, label, jobs=a.jobs,
                                   extend=not a.no_extend, log=log, widom=not a.no_widom,
                                   nvt1=not a.no_nvt1, recipe_override=a.recipe, cases=case_table)
    csv, *_ = workflow.collect(parent)
    log(f"wrote {csv}")
    from . import report
    log(f"plot {report.plot_isotherm(csv)}")


def cmd_collect(a, argv):
    csv, *_ = workflow.collect(Path(a.isotherm_dir))
    print(csv)
    from . import report
    print(report.plot_isotherm(csv))


CLEAN = ROOT / "data" / "isodb_clean"


def cmd_isodb(a, argv):
    import pandas as pd
    from . import clean, isodb
    cases = workflow.load_cases()
    c = cases["cases"][a.case]
    hashkeys = c["isodb_hashkeys"]
    log = _log_to(CLEAN / "isodb.log")
    log(f"gcmc isodb {' '.join(argv)}")
    for m in isodb.registry_matches(c["aliases"], hashkeys + c.get("isodb_hashkeys_conditional", [])):
        log(f"registry match: {m['hashkey']} '{m['name']}' via {m['matched']} in_cases_yaml={m['in_cases_yaml']}")
    if c.get("isodb_hashkeys_conditional"):
        log(f"conditional hashkeys NOT used automatically: {c['isodb_hashkeys_conditional']} ({c.get('aliases_note', '')})")
    commit, papers, records = isodb.fetch(a.case, a.gas, hashkeys, log=log)
    temps = a.T or cases["defaults"]["temperatures_K"][a.gas]
    window = a.T_window if a.T_window is not None else cases["defaults"]["isodb_T_window_K"]
    for T in temps:
        ledger, tidy = clean.clean_case(a.case, a.gas, T, window, hashkeys, records, papers)
        ledger.insert(0, "target_T_K", T)
        ledger.insert(0, "case", a.case)
        ledger.insert(2, "gas", a.gas)
        acc = ledger[ledger.status == "accepted"]
        pristine_ids = set(acc[acc.sample_flags.isna() | (acc.sample_flags == "")].filename)
        if len(pristine_ids):
            cons, mat = clean.consensus(tidy[tidy.source_id.isin(pristine_ids)])
            score, out, _ = clean.flag_outliers(mat, cons)
            ledger["outlier_score_log10"] = ledger.filename.map(score)
            ledger["outlier"] = ledger.filename.map(out).fillna(False).astype(bool)
        csv = clean.write_outputs(a.case, a.gas, T, ledger, tidy, commit, CLEAN,
                                  {"T_window_K": window, "hashkeys": hashkeys,
                                   "n_candidate_papers": len(papers)})
        log(f"T={T:g} K: {len(ledger)} candidates, {len(acc)} accepted "
            f"({len(pristine_ids)} pristine, {len(acc) - len(pristine_ids)} flagged) -> {csv.relative_to(ROOT)}")
        for reason, n in ledger[ledger.status == "rejected"].reason.str.replace(r" of .*", " of ...", regex=True) \
                .value_counts().items():
            log(f"    rejected {n:4d}  {reason}")
    parts = [pd.read_csv(f) for f in sorted(CLEAN.glob("*_ledger.csv"))]
    pd.concat(parts, ignore_index=True).to_csv(CLEAN / "ledger.csv", index=False)
    log(f"combined ledger: {CLEAN / 'ledger.csv'}")


def cmd_compare(a, argv):
    import pandas as pd
    from . import clean, compare
    stem_exp = f"{a.case}_{a.gas}_{a.T:g}K"
    exp_lo = None
    if a.T_second is not None:
        e2 = CLEAN / f"{a.case}_{a.gas}_{a.T_second:g}K"
        led2 = pd.read_csv(f"{e2}_ledger.csv")
        acc2 = led2[led2.status == "accepted"]
        ids2 = set(acc2[acc2.sample_flags.isna() | (acc2.sample_flags == "")].filename)
        t2 = pd.read_csv(f"{e2}.csv")
        exp_lo = (t2[t2.source_id.isin(ids2)], a.T_second)
    res = compare.compare(a.sim, CLEAN / f"{stem_exp}.csv", CLEAN / f"{stem_exp}_ledger.csv", exp_lo=exp_lo)
    sim_label = Path(a.sim).stem
    out = ROOT / "results" / a.case / "compare"
    stem = f"{sim_label}_vs_isodb"
    compare.write(res, out, stem, a.sim)
    png = compare.plot_compare(res, a.sim, f"{a.gas} in {a.case}, {a.T:g} K: simulation ({sim_label}) vs ISODB",
                               out / f"{stem}.png")
    print(res["regimes"].round(3).to_string(index=False))
    print(json.dumps(res["henry"], indent=1, default=float)[:800])
    print(png)


def cmd_matrix(a, argv):
    cases = workflow.load_cases()
    d = cases["defaults"]
    items = [(c, g, T) for c in (a.cases or list(cases["cases"])) for g in (a.gases or d["gases"])
             for T in d["temperatures_K"][g]]
    if a.detach:
        return _detach(["matrix"] + argv, f"gcmc_matrix_{a.label}")
    opts = {"cycles": a.cycles, "init_cycles": a.init_cycles, "unit_cells": "auto", "void_fraction": "auto",
            "ideal_gas": False, "coulomb_cutoff": 12.0, "print_every": None}
    log = _log_to(ROOT / "runs" / f"matrix_{a.label}.log")
    log(f"gcmc matrix {' '.join(argv)}")
    for csv in workflow.run_matrix(items, opts, a.label, jobs=a.jobs, log=log):
        print(csv)
    log("matrix done")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(prog="gcmc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("isotherm", help="run a GCMC isotherm with RASPA3")
    s.add_argument("--case")
    s.add_argument("--cif", help="explicit charged P1 CIF (MOF recipe); prefer adding it to cases.yaml")
    s.add_argument("--gas", required=True, choices=["CO2", "CH4", "N2"])
    s.add_argument("--T", type=float, required=True)
    s.add_argument("--pressures", type=float, nargs="+", help="bar; default from cases.yaml")
    s.add_argument("--cycles", type=int, default=20000)
    s.add_argument("--init-cycles", type=int, default=5000)
    s.add_argument("--print-every", type=int)
    s.add_argument("--jobs", type=int, default=8)
    s.add_argument("--unit-cells", type=int, nargs=3)
    s.add_argument("--void-fraction", default="auto", help="'auto' (raspa3-cli), 'default' (omit, =1.0) or a number")
    s.add_argument("--ideal-gas", action="store_true", help="FugacityCoefficient 1.0 instead of Peng-Robinson")
    s.add_argument("--coulomb-cutoff", default="12.0", help="A, or 'auto' (RASPA: half smallest width)")
    s.add_argument("--recipe", choices=["mof", "example10", "example11"], help="override the case recipe")
    s.add_argument("--label")
    s.add_argument("--no-extend", action="store_true", help="do not re-run unconverged points with more cycles")
    s.add_argument("--no-widom", action="store_true")
    s.add_argument("--no-nvt1", action="store_true")
    s.add_argument("--detach", action="store_true", help="run in a detached tmux session")
    s.add_argument("--dry-run", action="store_true", help="show what would run; create and run nothing")
    c = sub.add_parser("collect", help="(re)write results for an isotherm run folder")
    c.add_argument("isotherm_dir")
    i = sub.add_parser("isodb", help="fetch and clean ISODB isotherms for a case")
    i.add_argument("--case", required=True)
    i.add_argument("--gas", required=True, choices=["CO2", "CH4", "N2"])
    i.add_argument("--T", type=float, nargs="+", help="target temperatures (K); default from cases.yaml")
    i.add_argument("--T-window", type=float, help="K; default from cases.yaml (2 K)")
    k = sub.add_parser("compare", help="compare a simulated isotherm CSV with the cleaned ISODB data")
    k.add_argument("--case", required=True)
    k.add_argument("--gas", required=True, choices=["CO2", "CH4", "N2"])
    k.add_argument("--T", type=float, required=True)
    k.add_argument("--sim", required=True, help="results/<case>/<gas>_<T>K_<label>.csv")
    k.add_argument("--T-second", type=float, help="second experimental temperature for Clausius-Clapeyron")
    m = sub.add_parser("matrix", help="run all case/gas/T isotherms in one longest-first pool")
    m.add_argument("--cases", nargs="+")
    m.add_argument("--gases", nargs="+", choices=["CO2", "CH4", "N2"])
    m.add_argument("--cycles", type=int, default=20000)
    m.add_argument("--init-cycles", type=int, default=5000)
    m.add_argument("--jobs", type=int, default=8)
    m.add_argument("--label", default="main")
    m.add_argument("--detach", action="store_true")
    a = ap.parse_args(argv)
    {"matrix": cmd_matrix, "isotherm": cmd_isotherm, "collect": cmd_collect, "isodb": cmd_isodb,
     "compare": cmd_compare}[a.cmd](a, argv[1:])


if __name__ == "__main__":
    main()
