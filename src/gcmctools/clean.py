"""Clean ISODB candidates into the tidy table, with a ledger row for every candidate.

Rules are applied in a fixed order; the first failure is the rejection reason. Nothing is
dropped silently: dropped points are counted in the ledger notes.

Exp/sim rule (ISODB per-isotherm `category` is usually empty, docs/RECON.md section 5):
accept if the isotherm category is 'exp', or it is empty and the paper's categories are exactly
['exp']. Anything else (sim/mod/qua, or an empty category in a mixed paper) is rejected.

Sample flags: ISODB gives modified samples their own material entries, so a record on the case
hashkey is normally the pristine reference sample. Flags that exclude a record from the
pristine consensus come from the adsorbent name (any category below), or from the paper title
for sample-state words only (SHAPED, AGED_HUMID), which ISODB does not split into materials.
Composite/functionalized/doped/mixed-metal/defect words in the title are recorded as
`title_mentions` for review but do not exclude.
"""

import json
import math
import re

import numpy as np
import pandas as pd

from . import raspa, units

FLAG_WORDS = {
    "composite": [r"composite", r"@", r"hybrid", r"graphene", r"graphite oxide", r"nanotube", r"\bcnt",
                  r"polymer", r"mixed[- ]matrix", r"membrane"],
    "shaped": [r"pellet", r"shaped", r"shaping", r"granul", r"extrud", r"monolith", r"tablet", r"\bbeads?\b",
               r"binder", r"compact", r"thin film", r"\bfilms?\b", r"coating", r"foam"],
    "functionalized": [r"functionali", r"grafted", r"amine", r"modified", r"impregnat", r"encapsulat",
                       r"post-synthetic"],
    "doped": [r"\bdop(ed|ing|ant)"],
    "mixed-metal": [r"mixed[- ]metal", r"bimetallic", r"heterometal"],
    "defect-engineered": [r"defect", r"missing[- ]linker", r"modulat"],
    "aged_humid": [r"humid", r"moisture", r"water vapou?r", r"\bag(ed|eing|ing)\b", r"steam", r"hydrated"],
}
TITLE_EXCLUDING = {"shaped", "aged_humid"}


def find_flags(text, categories=FLAG_WORDS):
    t = (text or "").lower()
    return sorted(k for k, pats in categories.items() if any(re.search(p, t) for p in pats))


def exp_status(iso_cat, paper_cats):
    pc = sorted(paper_cats or [])
    if iso_cat == "exp":
        return True, ""
    if iso_cat:
        return False, f"category '{iso_cat}' (isotherm)"
    if pc == ["exp"]:
        return True, ""
    if "exp" not in pc:
        return False, f"not experimental (paper categories {'+'.join(pc) or 'none'}, isotherm unlabeled)"
    return False, f"ambiguous exp/non-exp (paper categories {'+'.join(pc)}, isotherm unlabeled)"


def points(record):
    """[(P, q)] in original units with null handling; returns (pts, notes)."""
    pts, notes = [], []
    n_null, n_species = 0, 0
    for p in record.get("isotherm_data", []):
        q = p.get("total_adsorption")
        if q is None:
            sd = p.get("species_data") or []
            if len(sd) == 1 and sd[0].get("adsorption") is not None:
                q = sd[0]["adsorption"]
                n_species += 1
        if q is None or p.get("pressure") is None:
            n_null += 1
            continue
        pts.append((float(p["pressure"]), float(q)))
    if n_species:
        notes.append(f"{n_species} pts: total_adsorption null, used species_data")
    if n_null:
        notes.append(f"dropped {n_null} pts with null values")
    return pts, notes


def clean_record(rec, paper, case_hashkeys, gas, T, T_window, molar_mass):
    """Return (ledger_row, accepted_points_or_None). Points are (P_bar, q_mmol_g)."""
    hk = rec.get("adsorbent", {}).get("hashkey")
    ads = [a.get("InChIKey") for a in rec.get("adsorbates", [])]
    row = {"filename": rec["filename"], "doi": rec.get("DOI", ""), "adsorbent_hashkey": hk,
           "adsorbent_name": rec.get("adsorbent", {}).get("name"),
           "adsorbates": "+".join(a.get("name", "?") for a in rec.get("adsorbates", [])),
           "T_K": rec.get("temperature"), "category_isotherm": rec.get("category", ""),
           "categories_paper": "+".join(paper.get("categories", [])) if paper else "?",
           "adsorption_units": rec.get("adsorptionUnits"), "pressure_units": rec.get("pressureUnits"),
           "isotherm_type": rec.get("isotherm_type", ""), "n_points_raw": len(rec.get("isotherm_data", [])),
           "paper_title": (paper or {}).get("title", ""), "year": (paper or {}).get("year")}
    name_flags = find_flags(row["adsorbent_name"])
    title_flags = find_flags(row["paper_title"])
    row["sample_flags"] = ";".join(sorted(set(name_flags) | (set(title_flags) & TITLE_EXCLUDING)))
    row["title_mentions"] = ";".join(sorted(set(title_flags) - TITLE_EXCLUDING))
    basis = rec.get("isotherm_type") if rec.get("isotherm_type") in ("excess", "absolute") else "unknown"
    row["basis"] = basis

    def reject(reason, notes=()):
        row.update(status="rejected", reason=reason, notes="; ".join(notes), n_points_used=0)
        return row, None

    from .isodb import GAS_INCHIKEY
    if hk not in case_hashkeys:
        return reject("adsorbent hashkey not in case")
    if ads != [GAS_INCHIKEY[gas]]:
        return reject("multicomponent or different adsorbate")
    if rec.get("temperature") is None or abs(float(rec["temperature"]) - T) > T_window + 1e-9:
        return reject(f"temperature outside {T:g} +/- {T_window:g} K")
    ok, why = exp_status(rec.get("category", ""), paper.get("categories", []) if paper else [])
    if not ok:
        return reject(why)
    try:
        punit = rec.get("pressureUnits")
        units.pressure_to_bar(1.0, punit)
        units.loading_to_mmol_g(1.0, rec.get("adsorptionUnits"), molar_mass)
    except units.UnitError as e:
        return reject(f"unit: {e}")
    pts, notes = points(rec)
    if any(p <= 0 for p, _ in pts):
        n = sum(p <= 0 for p, _ in pts)
        pts = [(p, q) for p, q in pts if p > 0]
        notes.append(f"dropped {n} pts with P <= 0")
    if any(p == q for p, q in pts):
        n = sum(p == q for p, q in pts)
        pts = [(p, q) for p, q in pts if p != q]
        notes.append(f"dropped {n} pts with adsorption == pressure (digitizer artifact)")
    for k in range(1, len(pts)):
        if pts[k][0] < pts[k - 1][0]:
            notes.append(f"pressure decreases after point {k}: kept adsorption branch, dropped {len(pts) - k} pts")
            pts = pts[:k]
            break
    if len(pts) < 3:
        return reject("fewer than 3 usable points", notes)
    conv = [(units.pressure_to_bar(p, punit),
             units.loading_to_mmol_g(q, rec["adsorptionUnits"], molar_mass)) for p, q in pts]
    row.update(status="accepted", reason="", notes="; ".join(notes), n_points_used=len(conv))
    return row, conv


def clean_case(case_id, gas, T, T_window, case_hashkeys, records, papers):
    """records: [(record, cached_path)]. Returns (ledger DataFrame, tidy DataFrame)."""
    mm = raspa.load_recipe()["gases"][gas]["molar_mass"]
    by_doi = {p["DOI"]: p for p in papers}
    ledger, tidy, sigs = [], [], {}
    # deterministic order; prefer real DOI prefixes over the bogus 10.8888 duplicates
    order = sorted(records, key=lambda r: (r[0].get("DOI", "").startswith("10.8888"), r[0]["filename"]))
    for rec, path in order:
        row, pts = clean_record(rec, by_doi.get(rec.get("DOI")), set(case_hashkeys), gas, T, T_window, mm)
        row["raw_file"] = str(path.relative_to(path.parents[3]))
        if pts is not None:
            sig = tuple((round(p, 6), round(q, 6)) for p, q in pts)
            if sig in sigs:
                row.update(status="rejected", reason=f"duplicate data of {sigs[sig]}", n_points_used=0)
                pts = None
            else:
                sigs[sig] = rec["filename"]
        ledger.append(row)
        if pts is not None:
            for p, q in pts:
                tidy.append({"material_id": case_id, "adsorbate": gas, "T_K": float(rec["temperature"]),
                             "P_bar": p, "loading_mmol_g": q, "loading_err_mmol_g": float("nan"),
                             "basis": row["basis"], "source": "exp", "source_id": rec["filename"],
                             "doi": rec.get("DOI", ""), "notes": row["sample_flags"]})
    return pd.DataFrame(ledger), pd.DataFrame(tidy)


# ------------------------------------------------------------------ consensus

def default_grid(p_min=0.01, p_max=10.0, n=31):
    return np.logspace(math.log10(p_min), math.log10(p_max), n)


def interp_isotherm(p, q, grid):
    """Interpolate in log(P) (and log(q) when all q > 0) inside the measured range only; NaN outside."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    o = np.argsort(p)
    p, q = p[o], q[o]
    lp, lg = np.log(p), np.log(grid)
    inside = (lg >= lp[0] - 1e-12) & (lg <= lp[-1] + 1e-12)
    out = np.full(len(grid), np.nan)
    if np.all(q > 0):
        out[inside] = np.exp(np.interp(lg[inside], lp, np.log(q)))
    else:
        out[inside] = np.interp(lg[inside], lp, q)
    return out


def consensus(tidy, grid=None):
    """Median/IQR across DOIs (one vote per paper: within-paper median first) on a log-P grid.

    Returns (consensus DataFrame, per-isotherm interpolated matrix DataFrame).
    """
    grid = default_grid() if grid is None else grid
    curves = {}
    for sid, g in tidy.groupby("source_id"):
        curves[sid] = (g.doi.iloc[0], interp_isotherm(g.P_bar, g.loading_mmol_g, grid))
    mat = pd.DataFrame({sid: c for sid, (_, c) in curves.items()}, index=grid)
    dois = {sid: d for sid, (d, _) in curves.items()}
    per_doi = pd.DataFrame({d: mat[[s for s in mat if dois[s] == d]].median(axis=1, skipna=True)
                            for d in sorted(set(dois.values()))}, index=grid)
    rows = []
    for p in grid:
        v = per_doi.loc[p].dropna().values
        n_iso = int(mat.loc[p].notna().sum())
        if len(v) == 0:
            rows.append({"P_bar": p, "median": np.nan, "q25": np.nan, "q75": np.nan, "n_dois": 0, "n_isotherms": 0})
            continue
        rows.append({"P_bar": p, "median": float(np.median(v)), "q25": float(np.percentile(v, 25)),
                     "q75": float(np.percentile(v, 75)), "n_dois": len(v), "n_isotherms": n_iso})
    return pd.DataFrame(rows), mat


def flag_outliers(mat, cons, min_points=3):
    """Per isotherm: median log10(q/consensus median) over its grid points; Tukey fences across isotherms."""
    med = cons.set_index("P_bar")["median"]
    score = {}
    for sid in mat:
        r = np.log10(mat[sid] / med)
        r = r[np.isfinite(r)]
        if len(r) >= min_points:
            score[sid] = float(np.median(r))
    s = pd.Series(score)
    if len(s) < 4:
        return s, pd.Series(False, index=s.index), (np.nan, np.nan)
    q1, q3 = np.percentile(s, [25, 75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    return s, (s < lo) | (s > hi), (lo, hi)


def henry_low_pressure(p, q, p_max=0.1, min_points=3):
    """Slope through the origin from points with P <= p_max (unweighted). None if too few points."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    m = p <= p_max
    if m.sum() < min_points:
        return None
    return float(np.sum(p[m] * q[m]) / np.sum(p[m] ** 2))


def isosteric_heat(cons_lo, T_lo, cons_hi, T_hi, loadings):
    """Clausius-Clapeyron Qst (kJ/mol, positive) at fixed loading from two consensus medians."""
    out = []
    for n in loadings:
        ps = []
        for c in (cons_lo, cons_hi):
            c = c.dropna(subset=["median"]).sort_values("P_bar")
            q = c["median"].values
            if len(q) < 2 or q.min() <= 0 or not (q.min() <= n <= q.max()) or np.any(np.diff(q) <= 0):
                ps.append(np.nan)
                continue
            # log-log interpolation: exact for Henry-law and power-law segments
            ps.append(float(np.exp(np.interp(math.log(n), np.log(q), np.log(c.P_bar.values)))))
        p_lo, p_hi = ps
        qst = (units.R_J_PER_MOL_K * math.log(p_hi / p_lo) / (1 / T_lo - 1 / T_hi) / 1000.0
               if np.isfinite(p_lo) and np.isfinite(p_hi) else np.nan)
        out.append({"loading_mmol_g": n, "P_lo_bar": p_lo, "P_hi_bar": p_hi, "Qst_kj_mol": qst})
    return pd.DataFrame(out)


def write_outputs(case_id, gas, T, ledger, tidy, commit, out_dir, extra_meta=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{case_id}_{gas}_{T:g}K"
    ledger.to_csv(out_dir / f"{stem}_ledger.csv", index=False)
    tidy.to_csv(out_dir / f"{stem}.csv", index=False)
    meta = {"case": case_id, "gas": gas, "T_K": T, "isodb_mirror_commit": commit,
            "n_candidates": len(ledger), "n_accepted": int((ledger.status == "accepted").sum()),
            "rules": __doc__, **(extra_meta or {})}
    (out_dir / f"{stem}_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    return out_dir / f"{stem}.csv"
