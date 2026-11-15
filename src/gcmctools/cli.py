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
    c = sub.add_parser("collect", help="(re)write results for an isotherm run folder")
    c.add_argument("isotherm_dir")
    a = ap.parse_args(argv)
    {"isotherm": cmd_isotherm, "collect": cmd_collect}[a.cmd](a, argv[1:])


if __name__ == "__main__":
    main()
