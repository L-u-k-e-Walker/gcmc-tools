"""Run folders, manifests, resume logic and the job pool.

A run folder is fully determined by its inputs: the folder name ends in a hash of every
input file and every setting, so changing anything gives a new folder and nothing is
overwritten. A point counts as complete only if its output parses, finished, and passes
the framework sanity check (atom count, net charge). Anything else is re-run; the old
output is kept as output.failed-<n>.
"""

import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from . import parse

MAX_JOBS_HARD = 16
RASPA_VERSION = "3.0.29"


def sha256_text(s):
    return hashlib.sha256(s.encode()).hexdigest()


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_hash(files, settings):
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(name.encode() + b"\0" + sha256_text(files[name]).encode() + b"\n")
    h.update(json.dumps(settings, sort_keys=True).encode())
    return h.hexdigest()


def prepare_run_folder(parent, label, files, settings):
    """Create parent/<label>_<hash10>/ with `files` (name -> text) and run.json."""
    digest = run_hash(files, settings)
    d = Path(parent) / f"{label}_{digest[:10]}"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        p = d / name
        if not p.exists():
            p.write_text(text)
        elif p.read_text() != text:
            raise RuntimeError(f"{p} exists with different content (hash collision?)")
    manifest = d / "run.json"
    if not manifest.exists():
        manifest.write_text(json.dumps({
            "hash": digest, "label": label, "created": datetime.now(timezone.utc).isoformat(),
            "raspa3_version": RASPA_VERSION, "settings": settings,
            "files": {n: sha256_text(t) for n, t in files.items()}}, indent=2))
    return d


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
        return b"raspa3" in cmd
    except OSError:
        return False


def validate(result, settings):
    """Return a list of problems with a parsed run (empty list means OK)."""
    if result is None:
        return ["no output file"]
    problems = []
    if not result.get("finished"):
        problems.append("output not finished (truncated or crashed)")
    exp_atoms = settings.get("expected_framework_atoms")
    if result.get("framework_atoms") in (None, 0):
        problems.append("framework has 0 atoms (CIF not read)")
    elif exp_atoms and result["framework_atoms"] != exp_atoms:
        problems.append(f"framework atoms {result['framework_atoms']} != expected {exp_atoms}")
    q = result.get("framework_net_charge")
    if q is None or abs(q) > 1e-3:
        problems.append(f"framework net charge {q}")
    kind = settings["kind"]
    need = {"gcmc": ["exc_mol_kg", "abs_mol_kg"], "widom": ["henry_mol_kg_pa"],
            "nvt1": ["framework_molecule_energy_K"]}[kind]
    for k in need:
        v = result.get(k)
        if v is None or not math.isfinite(v):
            problems.append(f"{k} missing or not finite: {v}")
    if kind == "gcmc" and result.get("production_cycles_total") != settings["cycles"]:
        problems.append("production cycle count does not match settings")
    return problems


def status(run_dir):
    """'running', 'complete' or 'incomplete'."""
    d = Path(run_dir)
    pidf = d / "pid"
    if pidf.exists():
        try:
            if _pid_alive(int(pidf.read_text().strip())):
                return "running"
        except ValueError:
            pass
    settings = json.loads((d / "run.json").read_text())["settings"]
    return "complete" if not validate(parse.parse_run(d), settings) else "incomplete"


def _archive_old_output(d):
    out = d / "output"
    if out.exists():
        n = 1
        while (d / f"output.failed-{n}").exists():
            n += 1
        out.rename(d / f"output.failed-{n}")


def run_pool(run_dirs, jobs=8, poll=10.0, log=print, exe=None):
    """Run every folder that is not complete, at most `jobs` at a time. Blocks until done."""
    jobs = min(int(jobs), MAX_JOBS_HARD)
    exe = exe or shutil.which("raspa3")
    if exe is None:
        raise RuntimeError("raspa3 not on PATH; run inside `conda run -n ads`")
    todo = []
    for d in map(Path, run_dirs):
        st = status(d)
        if st == "complete":
            log(f"skip (complete): {d}")
        elif st == "running":
            log(f"skip (already running elsewhere): {d}")
        else:
            todo.append(d)
    active = {}
    while todo or active:
        while todo and len(active) < jobs:
            d = todo.pop(0)
            _archive_old_output(d)
            logf = open(d / "log.txt", "w")
            p = subprocess.Popen([exe], cwd=d, stdout=logf, stderr=subprocess.STDOUT)
            (d / "pid").write_text(str(p.pid))
            (d / "started").write_text(str(time.time()))
            active[d] = (p, logf)
            log(f"start: {d}")
        time.sleep(poll)
        for d, (p, logf) in list(active.items()):
            # wait4 reaps the child and returns its own CPU time and peak memory. CPU time does not
            # depend on other load on the machine, so it is the cost measure used for budgets.
            pid, wstatus, ru = os.wait4(p.pid, os.WNOHANG)
            if pid == 0:
                continue
            p.returncode = os.waitstatus_to_exitcode(wstatus)
            logf.close()
            (d / "pid").unlink(missing_ok=True)
            settings = json.loads((d / "run.json").read_text())["settings"]
            probs = validate(parse.parse_run(d), settings)
            wall = time.time() - float((d / "started").read_text())
            (d / "status.json").write_text(json.dumps(
                {"returncode": p.returncode, "problems": probs, "wall_s": wall,
                 "cpu_user_s": ru.ru_utime, "cpu_sys_s": ru.ru_stime,
                 "max_rss_mb": ru.ru_maxrss / 1024.0}, indent=2))
            log(f"done ({'OK' if not probs else 'PROBLEM: ' + '; '.join(probs)}, "
                f"{wall:.0f} s wall, {ru.ru_utime:.0f} s cpu, {ru.ru_maxrss / 1024:.0f} MB): {d}")
            del active[d]


# ------------------------------------------------------------- void fraction

def helium_void_fraction(parent, cif_name, cif_text, ff_with_he, iterations=1000, inner=1000,
                         replicas=2, log=print):
    """Helium void fraction with raspa3-cli (energy method, probe-He, 298 K hard-coded).

    Runs `replicas` independent estimates of iterations*inner samples each; returns
    (mean, half-range, values). Results are cached in the folder (hash of inputs).
    """
    exe = shutil.which("raspa3-cli")
    if exe is None:
        raise RuntimeError("raspa3-cli not on PATH")
    files = {f"{cif_name}.cif": cif_text, "force_field.json": json.dumps(ff_with_he, indent=2)}
    settings = {"kind": "voidfraction", "iterations": iterations, "inner": inner,
                "replicas": replicas, "method": "raspa3-cli --void-fraction --energy (probe-He)"}
    d = prepare_run_folder(parent, "voidfraction", files, settings)
    res = d / "result.json"
    if res.exists():
        r = json.loads(res.read_text())
        return r["mean"], r["half_range"], r["values"]
    values = []
    for k in range(replicas):
        sub = d / f"rep{k}"
        sub.mkdir(exist_ok=True)
        for n, t in files.items():
            (sub / n).write_text(t)
        with open(sub / "log.txt", "w") as lf:
            subprocess.run([exe, "--void-fraction", "--energy", "-N", str(iterations), "-M", str(inner),
                            "-f", "force_field.json", f"{cif_name}.cif"], cwd=sub, stdout=lf,
                           stderr=subprocess.STDOUT, check=True)
        out = (sub / f"{cif_name}.energy.vf.cpu.txt").read_text().splitlines()
        values.append(float(out[-1]))
        log(f"void fraction rep{k}: {values[-1]}")
    mean = sum(values) / len(values)
    half = (max(values) - min(values)) / 2
    res.write_text(json.dumps({"mean": mean, "half_range": half, "values": values}, indent=2))
    return mean, half, values
