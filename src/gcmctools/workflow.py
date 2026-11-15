"""Isotherm workflow: build the model, set up runs, run them, extend unconverged points, collect."""

import json
import math
from pathlib import Path

import yaml

from . import fit, parse, raspa, runner, units

ROOT = Path(__file__).resolve().parents[2]
REL_ERR_LIMIT = 0.05


def load_cases():
    return yaml.safe_load((ROOT / "cases" / "cases.yaml").read_text())


# ------------------------------------------------------------------ models

def build_model(case_id, gas, recipe_override=None, cases=None):
    """Everything that defines the physical model of one case/gas (files + flags)."""
    cases = cases or load_cases()
    c = cases["cases"][case_id]
    recipe = recipe_override or c["recipe"]
    r = raspa.load_recipe()
    mol_name = r["gases"][gas]["molecule_file"]
    mol_text = (raspa.TEMPLATES / "molecules" / mol_name).read_text()
    if recipe == "example11":
        reg = c["regression"]
        d = ROOT / reg["structure_dir"]
        if gas != "CO2":
            raise ValueError("example11 model only defines CO2")
        return {"recipe": recipe, "framework_name": reg["framework_name"],
                "cif_text": (d / "Cu-BTC.cif").read_text(),
                "ff": json.loads((d / "force_field.json").read_text()),
                "molecule_file": "CO2.json", "molecule_text": (d / "CO2.json").read_text(),
                "charges_from_cif": False, "expected_framework_atoms": reg["expected_framework_atoms"],
                "cell": raspa.read_cell((d / "Cu-BTC.cif").read_text())}
    cif_path = ROOT / c["structure"]
    cif_text = cif_path.read_text()
    info = json.loads((cif_path.parent / "structure.json").read_text())
    if recipe == "mof":
        ff = raspa.build_force_field(info["elements"], [gas], r)
        charges_from_cif = True
        expected = c.get("expected_framework_atoms") or (info["natoms_cif_rows"] if info["p1"] else None)
    elif recipe == "example10":
        ex10 = json.loads((cif_path.parent / "original" / "example10_force_field.json").read_text())
        ads = raspa.build_force_field([], [gas], r)
        ff = {"MixingRule": ex10["MixingRule"], "TruncationMethod": ex10["TruncationMethod"],
              "TailCorrections": ex10["TailCorrections"], "CutOffVDW": r["CutOffVDW"],
              "PseudoAtoms": [p for p in ex10["PseudoAtoms"] if p["framework"]] + ads["PseudoAtoms"],
              "SelfInteractions": [s for s in ex10["SelfInteractions"] if s["name"] in ("O", "Si")]
              + ads["SelfInteractions"]}
        charges_from_cif = False
        expected = c["expected_framework_atoms"]
    else:
        raise ValueError(f"unknown recipe {recipe}")
    if expected is None:
        raise ValueError(f"{case_id}: expected_framework_atoms needed for a non-P1 CIF")
    return {"recipe": recipe, "framework_name": c["framework_name"], "cif_text": cif_text, "ff": ff,
            "molecule_file": mol_name, "molecule_text": mol_text, "charges_from_cif": charges_from_cif,
            "expected_framework_atoms": expected, "cell": raspa.read_cell(cif_text)}


# ------------------------------------------------------------------ setup

def isotherm_dir(case_id, gas, T, label):
    return ROOT / "runs" / case_id / f"{gas}_{T:g}K" / label


def setup_point(model, kind, gas, T, P_pa, opts, parent, cycles=None, init_cycles=None):
    cycles = cycles or opts["cycles"]
    init_cycles = opts["init_cycles"] if init_cycles is None else init_cycles
    sim = raspa.simulation_json(
        kind=kind, framework_name=model["framework_name"], gas=gas, T=T, P_pa=P_pa, cycles=cycles,
        init_cycles=init_cycles, unit_cells=opts["unit_cells"], void_fraction=opts["void_fraction"],
        ideal_gas=opts["ideal_gas"], coulomb_cutoff=opts["coulomb_cutoff"],
        charges_from_cif=model["charges_from_cif"], print_every=opts.get("print_every"),
        legacy_example11=(model["recipe"] == "example11"))
    files = {"simulation.json": json.dumps(sim, indent=2),
             "force_field.json": json.dumps(model["ff"], indent=2),
             f"{model['framework_name']}.cif": model["cif_text"],
             model["molecule_file"]: model["molecule_text"]}
    settings = {"kind": kind, "gas": gas, "T_K": T, "P_Pa": P_pa, "cycles": cycles,
                "init_cycles": init_cycles, "unit_cells": opts["unit_cells"],
                "void_fraction": opts["void_fraction"], "ideal_gas": opts["ideal_gas"],
                "coulomb_cutoff": opts["coulomb_cutoff"], "recipe": model["recipe"],
                "expected_framework_atoms": model["expected_framework_atoms"]}
    label = {"gcmc": f"gcmc_{P_pa:g}Pa", "widom": "widom", "nvt1": "nvt1"}[kind]
    return runner.prepare_run_folder(parent / kind, label, files, settings)


def resolve_options(model, opts, parent, log=print):
    """Fill in automatic unit cells and void fraction. Logs every automatic choice."""
    opts = dict(opts)
    cutoff = float(model["ff"].get("CutOffVDW", 12.0))
    auto_cells = raspa.choose_unit_cells(model["cell"], cutoff)
    widths = raspa.perpendicular_widths(model["cell"])
    if opts.get("unit_cells") in (None, "auto"):
        opts["unit_cells"] = auto_cells
        log(f"unit cells: {auto_cells} (perpendicular widths {[round(w, 3) for w in widths]} A, "
            f"cutoff {cutoff} A, rule width*n >= 2*cutoff)")
    else:
        bad = [n * w < 2 * cutoff - 1e-9 for n, w in zip(opts["unit_cells"], widths)]
        log(f"unit cells: {opts['unit_cells']} (user); minimum-image OK: {not any(bad)}")
        if any(bad):
            raise ValueError("requested unit cells violate the minimum-image rule")
    vf = opts.get("void_fraction", "auto")
    if vf == "auto":
        mean, half, vals = runner.helium_void_fraction(
            parent, model["framework_name"], model["cif_text"], raspa.add_helium_probe(model["ff"]), log=log)
        opts["void_fraction"] = round(mean, 5)
        opts["void_fraction_detail"] = {"mean": mean, "half_range": half, "values": vals}
        log(f"helium void fraction: {mean:.5f} +/- {half:.5f} (raspa3-cli, {len(vals)} replicas)")
    elif vf == "default":
        opts["void_fraction"] = None
        log("helium void fraction: key omitted (RASPA3 default 1.0)")
    else:
        opts["void_fraction"] = float(vf)
    return opts


# ------------------------------------------------------------------ run

def adhoc_case(cif_path):
    """Register an explicit --cif structure (charged CIF, MOF recipe) under runs/adhoc/<stem>/."""
    cif_path = Path(cif_path).resolve()
    stem = cif_path.stem
    d = ROOT / "runs" / "adhoc" / stem
    d.mkdir(parents=True, exist_ok=True)
    text, changes, atoms = raspa.prepare_cif(cif_path.read_text())
    if any(a["charge"] is None for a in atoms):
        raise ValueError("ad-hoc CIF must carry _atom_site_charge (charges are never invented)")
    (d / f"{stem}.cif").write_text(text)
    cell = raspa.read_cell(text)
    (d / "structure.json").write_text(json.dumps({
        "id": stem, "source_file": str(cif_path), "sha256_original": runner.sha256_file(cif_path),
        "p1": raspa.is_p1(text), "natoms_cif_rows": len(atoms),
        "elements": sorted({a["element"] for a in atoms}), "net_charge": sum(a["charge"] for a in atoms),
        "cell": cell, "format_changes": changes}, indent=2))
    cases = load_cases()
    cases["cases"]["adhoc-" + stem] = {"structure": str((d / f"{stem}.cif").relative_to(ROOT)),
                                       "framework_name": stem, "recipe": "mof"}
    return "adhoc-" + stem, cases


def run_isotherm(case_id, gas, T, pressures_bar, opts, label, jobs=8, extend=True, log=print,
                 widom=True, nvt1=True, recipe_override=None, cases=None):
    model = build_model(case_id, gas, recipe_override, cases)
    parent = isotherm_dir(case_id, gas, T, label)
    parent.mkdir(parents=True, exist_ok=True)
    opts = resolve_options(model, opts, parent, log)
    dirs = [setup_point(model, "gcmc", gas, T, units.bar_to_pa(p), opts, parent) for p in pressures_bar]
    extra = []
    if widom:
        extra.append(setup_point(model, "widom", gas, T, 1e5, opts, parent, init_cycles=0))
    if nvt1:
        extra.append(setup_point(model, "nvt1", gas, T, 1e5, opts, parent))
    (parent / "isotherm.json").write_text(json.dumps(
        {"case": case_id, "gas": gas, "T_K": T, "pressures_bar": pressures_bar, "label": label,
         "options": opts, "gcmc_dirs": [str(d) for d in dirs], "extra_dirs": [str(d) for d in extra]},
        indent=2))
    runner.run_pool(dirs + extra, jobs=jobs, log=log)

    if extend:
        final = []
        ext = []
        for d, p in zip(dirs, pressures_bar):
            r = parse.parse_run(d)
            factor = extension_factor(r)
            if factor > 1:
                log(f"extend {p} bar by x{factor}: {d.name}")
                ext.append(setup_point(model, "gcmc", gas, T, units.bar_to_pa(p), opts, parent,
                                       cycles=opts["cycles"] * factor, init_cycles=opts["init_cycles"] * 2))
                final.append(ext[-1])
            else:
                final.append(d)
        if ext:
            runner.run_pool(ext, jobs=jobs, log=log)
        meta = json.loads((parent / "isotherm.json").read_text())
        meta["gcmc_dirs_first_pass"] = meta["gcmc_dirs"]
        meta["gcmc_dirs"] = [str(d) for d in final]
        (parent / "isotherm.json").write_text(json.dumps(meta, indent=2))
    return parent


def extension_factor(r, max_factor=4):
    """Cycle multiplier for an unconverged point (1 = fine).

    Statistical error scales as 1/sqrt(cycles), so the factor to reach 5% relative error is
    (relerr/0.05)^2, capped. A drift flag alone gives x2 (and the init cycles are doubled).
    """
    rel = rel_err(r)
    drift = parse.drift_check(r["production_series_exc_mol_kg"])[2]
    f = 1
    if rel is not None and rel > REL_ERR_LIMIT:
        f = math.ceil((rel / REL_ERR_LIMIT) ** 2)
    if drift:
        f = max(f, 2)
    return min(f, max_factor)


def rel_err(r):
    if not r or not r.get("exc_mol_kg"):
        return None
    return abs(r["exc_err_mol_kg"] / r["exc_mol_kg"])


# ------------------------------------------------------------------ collect

def collect(parent, results_dir=None):
    """Write tidy CSV, point details, metadata JSON and fits for one isotherm folder."""
    import pandas as pd
    parent = Path(parent)
    meta = json.loads((parent / "isotherm.json").read_text())
    rows, detail = [], []
    for d in map(Path, meta["gcmc_dirs"]):
        run = json.loads((d / "run.json").read_text())
        r = parse.parse_run(d)
        probs = runner.validate(r, run["settings"])
        if probs:
            raise RuntimeError(f"{d}: {probs}")
        p_bar = units.pa_to_bar(run["settings"]["P_Pa"])
        drift, drift_se, drift_flag = parse.drift_check(r["production_series_exc_mol_kg"])
        rel = rel_err(r)
        flags = []
        if drift_flag:
            flags.append("drift")
        if rel is not None and rel > REL_ERR_LIMIT:
            flags.append(f"relerr>{REL_ERR_LIMIT:.0%}")
        for basis in ("excess", "absolute"):
            k = "exc" if basis == "excess" else "abs"
            rows.append({"material_id": meta["case"], "adsorbate": meta["gas"], "T_K": meta["T_K"],
                         "P_bar": p_bar, "loading_mmol_g": units.mol_per_kg_to_mmol_per_g(r[f"{k}_mol_kg"]),
                         "loading_err_mmol_g": r[f"{k}_err_mol_kg"], "basis": basis, "source": "sim",
                         "source_id": run["hash"][:10], "doi": "",
                         "notes": ";".join([meta["label"]] + flags)})
        detail.append({"P_bar": p_bar, "fugacity_coefficient": r["fugacity_coefficient"],
                       "helium_void_fraction": r["helium_void_fraction"],
                       "exc_mmol_g": r["exc_mol_kg"], "exc_err": r["exc_err_mol_kg"],
                       "abs_mmol_g": r["abs_mol_kg"], "abs_err": r["abs_err_mol_kg"],
                       "rel_err": rel, "drift_mmol_g": drift, "drift_se": drift_se, "drift_flag": drift_flag,
                       "enthalpy_kj_mol": r["enthalpy_kj_mol"], "enthalpy_err_kj_mol": r["enthalpy_err_kj_mol"],
                       "cycles": run["settings"]["cycles"], "framework_atoms": r["framework_atoms"],
                       "unit_cells": run["settings"]["unit_cells"], "coulomb_cutoff_A": r["coulomb_cutoff_A"],
                       "wall_s": _wall(d), "run_hash": run["hash"], "run_dir": str(d.relative_to(ROOT))})
    tidy = pd.DataFrame(rows)
    det = pd.DataFrame(detail)
    summary = {"case": meta["case"], "gas": meta["gas"], "T_K": meta["T_K"], "label": meta["label"],
               "options": meta["options"]}
    for d in map(Path, meta.get("extra_dirs", [])):
        run = json.loads((d / "run.json").read_text())
        r = parse.parse_run(d)
        if runner.validate(r, run["settings"]):
            continue
        if run["settings"]["kind"] == "widom":
            summary["henry_widom_mmol_g_bar"] = units.henry_mol_kg_pa_to_mmol_g_bar(r["henry_mol_kg_pa"])
            summary["henry_widom_err_mmol_g_bar"] = units.henry_mol_kg_pa_to_mmol_g_bar(r["henry_err_mol_kg_pa"])
        if run["settings"]["kind"] == "nvt1":
            # rigid molecule, 1 molecule: dH0 = <U_host-guest> - kT
            dh_K = r["framework_molecule_energy_K"] - meta["T_K"]
            summary["dH0_nvt1_kj_mol"] = units.kelvin_energy_to_kj_mol(dh_K)
            summary["dH0_nvt1_err_kj_mol"] = units.kelvin_energy_to_kj_mol(r["framework_molecule_energy_err_K"])
    summary["fits_excess"] = fit.fit_all(det.P_bar, det.exc_mmol_g, det.exc_err)
    summary["fits_absolute"] = fit.fit_all(det.P_bar, det.abs_mmol_g, det.abs_err)
    out = Path(results_dir or ROOT / "results" / meta["case"])
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{meta['gas']}_{meta['T_K']:g}K_{meta['label']}"
    tidy.to_csv(out / f"{stem}.csv", index=False)
    det.to_csv(out / f"{stem}_points.csv", index=False)
    (out / f"{stem}.json").write_text(json.dumps(summary, indent=2, default=float))
    return out / f"{stem}.csv", tidy, det, summary


def _wall(d):
    s = Path(d) / "status.json"
    return json.loads(s.read_text()).get("wall_s") if s.exists() else None
