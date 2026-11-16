"""Cause 6 (open metal sites): where do CO2 molecules sit relative to the framework metal?

Reads the production snapshots of the phase5 'movie' runs (CO2, 298 K, 0.1 bar), rebuilds the
metal positions of the simulation box from the prepared CIF, and computes for every CO2 molecule the
minimum-image distance from its O atoms and its C atom to the nearest metal. MFI has no metal; Si is
used as a structural reference there. RASPA3 cell convention: a along x, b in the xy plane.

Writes results/phase5/oms_snapshots.csv (one row per case) and oms_distances.csv (all distances).
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import raspa, workflow  # noqa: E402

METAL = {"HKUST-1": "Cu", "Mg-MOF-74": "Mg", "IRMOF-1": "Zn", "ZIF-8": "Zn", "UiO-66": "Zr", "MFI": "Si"}


def cell_matrix(a, b, c, al, be, ga):
    al, be, ga = map(math.radians, (al, be, ga))
    tmp = (math.cos(al) - math.cos(ga) * math.cos(be)) / math.sin(ga)
    return np.array([[a, 0, 0], [b * math.cos(ga), b * math.sin(ga), 0],
                     [c * math.cos(be), c * tmp, c * math.sqrt(1 - math.cos(be) ** 2 - tmp ** 2)]]).T


def read_movie(path):
    frames, cur, cryst = [], [], None
    for line in path.read_text().splitlines():
        if line.startswith("MODEL"):
            cur = []
        elif line.startswith("CRYST1"):
            cryst = [float(line[6:15]), float(line[15:24]), float(line[24:33]),
                     float(line[33:40]), float(line[40:47]), float(line[47:54])]
        elif line.startswith("ATOM"):
            cur.append((line[12:16].strip(), float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif line.startswith("ENDMDL"):
            frames.append(cur)
    if cur and (not frames or frames[-1] is not cur):
        frames.append(cur)
    return cryst, frames


def metal_fractional(case_id, element, cells):
    info = json.loads((ROOT / "data/structures" / case_id / "structure.json").read_text())
    if not info["p1"]:
        return None
    atoms = raspa.atom_table((ROOT / "data/structures" / case_id / f"{case_id}.cif").read_text())
    f = np.array([[a["x"], a["y"], a["z"]] for a in atoms if a["element"] == element]) % 1.0
    reps = [np.array([i, j, k]) for i in range(cells[0]) for j in range(cells[1]) for k in range(cells[2])]
    return np.concatenate([(f + r) / np.array(cells) for r in reps])


def analyse(case_id, run_dir, cells):
    cryst, frames = read_movie(run_dir / "movies" / "movie.s0.pdb")
    frames = frames[len(frames) // 2:]                    # second half only (well into production)
    M = cell_matrix(*cryst)
    Minv = np.linalg.inv(M)
    mf = metal_fractional(case_id, METAL[case_id], cells)
    if mf is None:
        return None, None
    rows = []
    for fr in frames:
        names = [a[0] for a in fr]
        xyz = np.array([a[1:] for a in fr])
        for i in range(0, len(fr) - 2, 3):                # CO2 written as O, C, O
            if not (names[i].startswith("O_co") and names[i + 1].startswith("C_co")):
                continue
            d = []
            for k in (i, i + 1, i + 2):
                df = (Minv @ xyz[k]) - mf
                df -= np.round(df)
                d.append(np.min(np.linalg.norm(df @ M.T, axis=1)))
            rows.append({"case": case_id, "d_O_metal": min(d[0], d[2]), "d_C_metal": d[1]})
    dd = pd.DataFrame(rows)
    if dd.empty:
        return {"case": case_id, "metal": METAL[case_id], "n_molecule_samples": 0}, dd
    return {"case": case_id, "metal": METAL[case_id], "n_frames": len(frames), "n_molecule_samples": len(dd),
            "median_d_O_metal_A": float(dd.d_O_metal.median()),
            "frac_O_metal_lt_3.0A": float((dd.d_O_metal < 3.0).mean()),
            "frac_O_metal_lt_3.5A": float((dd.d_O_metal < 3.5).mean()),
            "median_d_C_metal_A": float(dd.d_C_metal.median())}, dd


def main():
    summ, alld = [], []
    for case_id in METAL:
        runs = sorted((ROOT / "runs" / case_id / "CO2_298K" / "phase5_movie" / "gcmc").glob("gcmc_*"))
        if not runs or not (runs[0] / "movies" / "movie.s0.pdb").exists():
            print(f"{case_id}: no movie")
            continue
        cells = json.loads((runs[0] / "run.json").read_text())["settings"]["unit_cells"]
        s, d = analyse(case_id, runs[0], cells)
        if s:
            summ.append(s)
            alld.append(d)
            print(s)
    out = ROOT / "results" / "phase5"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summ).to_csv(out / "oms_snapshots.csv", index=False)
    if alld:
        pd.concat(alld).to_csv(out / "oms_distances.csv", index=False)


if __name__ == "__main__":
    main()
