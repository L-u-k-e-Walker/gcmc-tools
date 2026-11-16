"""Compare a simulated isotherm with the cleaned experimental isotherms of the same case/gas/T.

Basis: experimental records are mostly 'unknown' basis. The headline comparison uses the
simulated EXCESS loading and treats 'unknown' as excess; this is labeled in every output.
The simulated absolute loading is reported alongside.
Regimes (MISSION 5.9): low P < 0.1 bar, mid 0.1-1 bar, high > 1 bar.
"""

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import clean, report  # noqa: E402

REGIMES = [("low", 0.0, 0.1), ("mid", 0.1, 1.0), ("high", 1.0, np.inf)]


def regime_of(p):
    for name, lo, hi in REGIMES:
        if lo <= p < hi or (name == "mid" and p == 1.0):
            return name
    return "high"


def compare(sim_csv, exp_csv, ledger_csv, grid=None, exp_lo=None):
    """Return dict of tables and summary metrics.

    exp_lo: optional (pristine tidy DataFrame, T) at a second temperature. Clausius-Clapeyron heats
    are computed per paper (same sample at both temperatures), never across papers.
    """
    sim = pd.read_csv(sim_csv)
    exp = pd.read_csv(exp_csv)
    ledger = pd.read_csv(ledger_csv)
    acc = ledger[ledger.status == "accepted"]
    pristine_ids = set(acc[acc.sample_flags.isna() | (acc.sample_flags == "")].filename)
    pristine = exp[exp.source_id.isin(pristine_ids)]
    flagged = exp[~exp.source_id.isin(pristine_ids)]
    grid = clean.default_grid() if grid is None else grid
    cons, mat = clean.consensus(pristine, grid)
    score, is_out, fences = clean.flag_outliers(mat, cons)

    keep = [sid for sid in pristine.source_id.unique() if not bool(is_out.get(sid, False))]
    cons_no_out, _ = clean.consensus(pristine[pristine.source_id.isin(keep)], grid)

    out = {"consensus": cons, "consensus_no_outliers": cons_no_out, "matrix": mat, "outlier_score": score, "outlier": is_out, "fences": fences,
           "pristine": pristine, "flagged": flagged}
    out["points"], out["regimes"] = _regimes(sim, cons, grid)
    out["points_no_outliers"], out["regimes_no_outliers"] = _regimes(sim, cons_no_out, grid)
    return _henry_and_qst(out, sim, sim_csv, pristine, exp_lo)


def _regimes(sim, cons, grid):
    rows = []
    for basis in ("excess", "absolute"):
        s = sim[sim.basis == basis].sort_values("P_bar")
        s_on_grid = clean.interp_isotherm(s.P_bar, s.loading_mmol_g, grid)
        for p, sv, (_, c) in zip(grid, s_on_grid, cons.iterrows()):
            if not np.isfinite(sv) or not np.isfinite(c["median"]):
                continue
            rows.append({"sim_basis": basis, "P_bar": p, "regime": regime_of(p), "sim": sv,
                         "exp_median": c["median"], "exp_q25": c["q25"], "exp_q75": c["q75"],
                         "n_dois": c["n_dois"], "log10_ratio": math.log10(sv / c["median"]),
                         "inside_iqr": bool(c["q25"] <= sv <= c["q75"]),
                         "exp_iqr_log10_width": math.log10(c["q75"] / c["q25"]) if c["q25"] > 0 else np.nan})
    pts = pd.DataFrame(rows)
    reg = []
    for basis in ("excess", "absolute"):
        for name, _, _ in REGIMES:
            g = pts[(pts.sim_basis == basis) & (pts.regime == name)]
            if g.empty:
                reg.append({"sim_basis": basis, "regime": name, "n_grid_points": 0})
                continue
            reg.append({"sim_basis": basis, "regime": name, "n_grid_points": len(g),
                        "median_log10_ratio": float(g.log10_ratio.median()),
                        "ratio_at_median": float(10 ** g.log10_ratio.median()),
                        "min_log10_ratio": float(g.log10_ratio.min()), "max_log10_ratio": float(g.log10_ratio.max()),
                        "frac_inside_iqr": float(g.inside_iqr.mean()), "min_n_dois": int(g.n_dois.min()),
                        "median_exp_iqr_log10_width": float(g.exp_iqr_log10_width.median()),
                        "median_exp_iqr_ratio": float(10 ** g.exp_iqr_log10_width.median())})
    return pts, pd.DataFrame(reg)


def _henry_and_qst(out, sim, sim_csv, pristine, exp_lo):
    # Henry: experiment per pristine isotherm (>= 3 points at P <= 0.1 bar) vs simulation (Widom)
    kh = {sid: clean.henry_low_pressure(g.P_bar, g.loading_mmol_g) for sid, g in pristine.groupby("source_id")}
    kh = pd.Series({k: v for k, v in kh.items() if v is not None}, dtype=float)
    sim_meta = json.loads(Path(sim_csv).with_suffix(".json").read_text())
    out["henry"] = {"exp_n_isotherms": int(len(kh)),
                    "exp_n_dois": int(pristine[pristine.source_id.isin(kh.index)].doi.nunique()),
                    "exp_median_mmol_g_bar": float(kh.median()) if len(kh) else None,
                    "exp_q25": float(kh.quantile(0.25)) if len(kh) else None,
                    "exp_q75": float(kh.quantile(0.75)) if len(kh) else None,
                    "exp_values": {k: float(v) for k, v in kh.items()},
                    "sim_widom_mmol_g_bar": sim_meta.get("henry_widom_mmol_g_bar"),
                    "sim_widom_err": sim_meta.get("henry_widom_err_mmol_g_bar"),
                    "sim_fit_lowP_mmol_g_bar": sim_meta.get("fits_excess", {}).get("Henry", {}).get("params", {}).get("K_mmol_g_bar"),
                    "exp_method": "slope through origin of points with P <= 0.1 bar, >= 3 points, per isotherm"}
    if out["henry"]["exp_median_mmol_g_bar"] and out["henry"]["sim_widom_mmol_g_bar"]:
        out["henry"]["sim_over_exp_median"] = out["henry"]["sim_widom_mmol_g_bar"] / out["henry"]["exp_median_mmol_g_bar"]

    if exp_lo is not None:
        tidy_lo, T_lo = exp_lo
        T_hi = float(sim.T_K.iloc[0])
        loads = np.round(np.linspace(0.25, 8.0, 32), 3)
        rows, skipped = [], {}
        for doi in sorted(set(tidy_lo.doi) & set(pristine.doi)):
            n_lo = tidy_lo[tidy_lo.doi == doi].source_id.nunique()
            n_hi = pristine[pristine.doi == doi].source_id.nunique()
            if n_lo != 1 or n_hi != 1:
                skipped[doi] = f"pairing ambiguous ({n_lo} isotherms at {T_lo:g} K, {n_hi} at {T_hi:g} K)"
                continue
            c_lo, _ = clean.consensus(tidy_lo[tidy_lo.doi == doi], clean.default_grid(0.01, 100, 61))
            c_hi, _ = clean.consensus(pristine[pristine.doi == doi], clean.default_grid(0.01, 100, 61))
            q = clean.isosteric_heat(c_lo, T_lo, c_hi, T_hi, loads).dropna()
            q.insert(0, "doi", doi)
            rows.append(q)
        out["qst_exp"] = pd.concat(rows) if rows else pd.DataFrame(
            columns=["doi", "loading_mmol_g", "P_lo_bar", "P_hi_bar", "Qst_kj_mol"])
        out["qst_skipped"] = skipped
    return out


def plot_compare(res, sim_csv, title, out_path):
    sim = pd.read_csv(sim_csv)
    cons = res["consensus"].dropna(subset=["median"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), dpi=150)
    fig.patch.set_facecolor(report.SURFACE)
    for ax, ylog in zip(axes, (True, False)):
        report._style(ax)
        for sid, g in res["flagged"].groupby("source_id"):
            ax.plot(g.P_bar, g.loading_mmol_g, color="#b9b7ae", linewidth=0.8, linestyle=":", zorder=1)
        for sid, g in res["pristine"].groupby("source_id"):
            out = bool(res["outlier"].get(sid, False))
            ax.plot(g.P_bar, g.loading_mmol_g, color="#8f8d84", linewidth=0.8, alpha=0.8,
                    linestyle="--" if out else "-", zorder=2)
        ax.fill_between(cons.P_bar, cons.q25, cons.q75, color=report.SERIES[1], alpha=0.22, linewidth=0, zorder=3)
        ax.plot(cons.P_bar, cons["median"], color=report.SERIES[1], linewidth=2, zorder=4)
        se = sim[sim.basis == "excess"].sort_values("P_bar")
        sa = sim[sim.basis == "absolute"].sort_values("P_bar")
        ax.plot(sa.P_bar, sa.loading_mmol_g, color=report.SERIES[0], linewidth=1, linestyle="--", zorder=5)
        ax.errorbar(se.P_bar, se.loading_mmol_g, yerr=se.loading_err_mmol_g, color=report.SERIES[0], marker="o",
                    markersize=6, linewidth=2, capsize=2.5, markeredgecolor=report.SURFACE, zorder=6)
        ax.set_xscale("log")
        ax.set_xlim(5e-3, 20)
        if ylog:
            ax.set_yscale("log")
            pos = pd.concat([res["pristine"].loading_mmol_g, se.loading_mmol_g])
            ax.set_ylim(max(pos[pos > 0].min() * 0.5, 1e-3), pos.max() * 2)
        else:
            ax.set_ylim(0, max(se.loading_mmol_g.max(), cons.q75.max()) * 1.15)
        ax.set_xlabel("Pressure (bar)", color=report.TEXT)
        ax.set_ylabel("Uptake (mmol/g)", color=report.TEXT)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Line2D([], [], color=report.SERIES[0], marker="o", linewidth=2, label="GCMC excess"),
               Line2D([], [], color=report.SERIES[0], linestyle="--", linewidth=1, label="GCMC absolute"),
               Line2D([], [], color=report.SERIES[1], linewidth=2, label="exp. consensus median (per-paper)"),
               Patch(color=report.SERIES[1], alpha=0.22, label="exp. interquartile range"),
               Line2D([], [], color="#8f8d84", linewidth=0.8, label="exp. isotherm (pristine)"),
               Line2D([], [], color="#8f8d84", linewidth=0.8, linestyle="--", label="exp. isotherm flagged outlier"),
               Line2D([], [], color="#b9b7ae", linewidth=0.8, linestyle=":", label="exp. isotherm, flagged sample")]
    axes[1].legend(handles=handles, frameon=False, fontsize=7.5, labelcolor=report.TEXT, loc="upper left")
    axes[0].set_title("log scale", color=report.MUTED, fontsize=9, loc="left")
    axes[1].set_title("linear scale", color=report.MUTED, fontsize=9, loc="left")
    fig.suptitle(title, color=report.TEXT, fontsize=11, x=0.01, ha="left")
    fig.text(0.99, 0.005, "experimental 'unknown' basis treated as excess", color=report.MUTED, fontsize=7.5,
             ha="right", va="bottom")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(out_path, facecolor=report.SURFACE)
    plt.close(fig)
    return out_path


def write(res, out_dir, stem, sim_csv):
    out_dir.mkdir(parents=True, exist_ok=True)
    res["points"].to_csv(out_dir / f"{stem}_points.csv", index=False)
    res["regimes"].to_csv(out_dir / f"{stem}_regimes.csv", index=False)
    res["regimes_no_outliers"].to_csv(out_dir / f"{stem}_regimes_no_outliers.csv", index=False)
    res["consensus_no_outliers"].to_csv(out_dir / f"{stem}_consensus_no_outliers.csv", index=False)
    res["consensus"].to_csv(out_dir / f"{stem}_consensus.csv", index=False)
    if "qst_exp" in res:
        res["qst_exp"].to_csv(out_dir / f"{stem}_qst_exp.csv", index=False)
    summ = {"sim_csv": str(sim_csv), "henry": res["henry"],
            "outliers": {k: bool(v) for k, v in res["outlier"].items()},
            "outlier_scores_log10": res["outlier_score"].to_dict(), "outlier_fences_log10": list(res["fences"]),
            "n_pristine_isotherms": int(res["pristine"].source_id.nunique()),
            "n_pristine_dois": int(res["pristine"].doi.nunique()),
            "n_flagged_isotherms": int(res["flagged"].source_id.nunique()),
            "qst_exp_skipped_papers": res.get("qst_skipped", {}),
            "basis_note": "experimental 'unknown' basis treated as excess for the headline comparison"}
    (out_dir / f"{stem}_summary.json").write_text(json.dumps(summ, indent=2, default=float))
