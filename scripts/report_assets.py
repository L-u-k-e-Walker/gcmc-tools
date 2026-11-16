"""Tables (markdown) and the overview figure for reports/REPORT.md, generated from results files only.

Usage: conda run -n ads python scripts/report_assets.py
Writes reports/tables.md and reports/fig_overview.png.
"""

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import compare, report  # noqa: E402

P5 = ROOT / "results" / "phase5"
REP = ROOT / "reports"
ORDER = ["MFI", "IRMOF-1", "HKUST-1", "Mg-MOF-74", "UiO-66", "ZIF-8"]


def fmt(x, nd=2):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{nd}f}"


def table_comparisons(c):
    """Screened sim/exp ratio per regime with the minimum number of papers behind it, then Gate-2 headline."""
    lines = ["| Case | Gas | T (K) | exp isotherms: Gate 2 → screened | sim/exp < 0.1 bar (papers) | 0.1–1 bar (papers) | "
             "> 1 bar (papers) | exp IQR/median ratio 0.1–1 bar | Gate-2 headline (low/mid/high) | strict (low/mid/high) |",
             "|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for _, r in c.iterrows():
        n0 = int(r.get("n_exp_pristine") or 0)
        if not n0:
            lines.append(f"| {r.case} | {r.gas} | {r.T_K:g} | 0 | no experimental data | | | | | |")
            continue
        g = lambda k: r.get(k)
        def cell(reg):
            v = g(f"scr_{reg}_ratio")
            n = g(f"scr_{reg}_min_dois")
            return "–" if v is None or not np.isfinite(v) else f"{v:.2f} ({int(n)})"
        lines.append(
            f"| {r.case} | {r.gas} | {r.T_K:g} | {n0} → {int(g('scr_n_isotherms') or 0)} | "
            f"{cell('low')} | {cell('mid')} | {cell('high')} | {fmt(g('scr_mid_exp_iqr_ratio'), 1)} | "
            + "/".join(fmt(g(f'head_{k}_ratio')) for k in ('low', 'mid', 'high')) + " | "
            + "/".join(fmt(g(f'strict_{k}_ratio')) for k in ('low', 'mid', 'high')) + " |")
    return "\n".join(lines)


def overview_figure(c, out):
    c = c[c.scr_n_isotherms.fillna(0) > 0].copy()
    c["label"] = c.case + "  " + c.gas + " " + c.T_K.map(lambda t: f"{t:g} K")
    c["o"] = c.case.map({k: i for i, k in enumerate(ORDER)})
    c = c.sort_values(["o", "gas", "T_K"], ascending=[False, False, False])
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(c) + 1.4), dpi=150)
    fig.patch.set_facecolor(report.SURFACE)
    report._style(ax)
    y = np.arange(len(c))
    for i, (reg, marker, name) in enumerate((("low", "o", "< 0.1 bar"), ("mid", "s", "0.1–1 bar"),
                                             ("high", "D", "> 1 bar"))):
        v = np.log10(c[f"scr_{reg}_ratio"].astype(float))
        iqr = c[f"scr_{reg}_exp_iqr_ratio"].astype(float)
        ax.errorbar(v, y + (i - 1) * 0.22, xerr=np.log10(iqr) / 2, fmt=marker, color=report.SERIES[i],
                    markersize=6, elinewidth=1, capsize=0, label=f"{name} (bar: half exp IQR)",
                    markeredgecolor=report.SURFACE)
    ax.axvline(0, color=report.MUTED, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(c.label, fontsize=8, color=report.TEXT)
    ticks = [0.1, 0.2, 0.5, 1, 2, 5]
    ax.set_xticks(np.log10(ticks))
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_xlabel("simulated / experimental median uptake (log scale)", color=report.TEXT)
    ax.grid(False, axis="y")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, labelcolor=report.TEXT)
    ax.set_title("Simulation vs screened ISODB consensus by pressure regime", color=report.TEXT, fontsize=10, loc="left", pad=22)
    fig.tight_layout()
    fig.savefig(out, facecolor=report.SURFACE)
    plt.close(fig)


PANELS = [("CO2", 298.0), ("CO2", 273.0), ("CH4", 298.0), ("N2", 298.0)]


def case_figure(case, label, out):
    """2x2 log-log panels: simulation (excess) vs screened experimental isotherms and consensus."""
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 7.2), dpi=150)
    fig.patch.set_facecolor(report.SURFACE)
    for ax, (gas, T) in zip(axes.flat, PANELS):
        report._style(ax)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"{gas}, {T:g} K", color=report.TEXT, fontsize=9.5, loc="left")
        sim_csv = ROOT / "results" / case / f"{gas}_{T:g}K_{label}.csv"
        if not sim_csv.exists():
            continue
        stem = f"{case}_{gas}_{T:g}K"
        se, sl = P5 / "screened" / f"{stem}.csv", P5 / "screened" / f"{stem}_ledger.csv"
        n_exp = 0
        led = pd.read_csv(sl) if sl.exists() else None
        has_exp = led is not None and bool(((led.status == "accepted") &
                                            (led.sample_flags.isna() | (led.sample_flags == ""))).any())
        if has_exp:
            res = compare.compare(sim_csv, se, sl)
            pr = res["pristine"]
            n_exp = pr.source_id.nunique()
            for i, (sid, g) in enumerate(pr.groupby("source_id")):
                g = g[g.loading_mmol_g > 0].sort_values("P_bar")
                ax.plot(g.P_bar, g.loading_mmol_g, color=report.MUTED, linewidth=0.7, alpha=0.55,
                        label="exp. isotherm (screened)" if i == 0 else None, zorder=1)
            c = res["consensus"].dropna(subset=["median"])
            if len(c):
                ax.fill_between(c.P_bar, c.q25, c.q75, color=report.SERIES[1], alpha=0.18, linewidth=0, zorder=2,
                                label="exp. interquartile range (papers)")
                ax.plot(c.P_bar, c["median"], color=report.SERIES[1], linewidth=2, zorder=3,
                        label="exp. consensus median")
        sim = pd.read_csv(sim_csv)
        s = sim[sim.basis == "excess"].sort_values("P_bar")
        ax.errorbar(s.P_bar, s.loading_mmol_g, yerr=s.loading_err_mmol_g, fmt="o-", color=report.SERIES[0],
                    markersize=4.5, linewidth=2, markeredgecolor=report.SURFACE, zorder=4, label="GCMC excess")
        if n_exp == 0:
            ax.text(0.04, 0.92, "no accepted experimental isotherm", transform=ax.transAxes, fontsize=8,
                    color=report.MUTED)
        else:
            ax.text(0.04, 0.92, f"{n_exp} exp. isotherms", transform=ax.transAxes, fontsize=8, color=report.MUTED)
        ax.set_xlim(5e-3, 20)
        ax.set_xlabel("Pressure (bar)", color=report.TEXT, fontsize=8.5)
        ax.set_ylabel("Uptake (mmol/g)", color=report.TEXT, fontsize=8.5)
    h, l = [], []
    for ax in axes.flat:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l:
                h.append(hh)
                l.append(ll)
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=8, labelcolor=report.TEXT)
    fig.suptitle(f"{case}: simulation vs screened ISODB experiments", x=0.01, ha="left", color=report.TEXT,
                 fontsize=11)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    fig.savefig(out, facecolor=report.SURFACE)
    plt.close(fig)


def main():
    REP.mkdir(exist_ok=True)
    c = pd.read_csv(P5 / "comparisons.csv")
    c["o"] = c.case.map({k: i for i, k in enumerate(ORDER)})
    c = c.sort_values(["o", "gas", "T_K"]).drop(columns="o")
    parts = ["# Generated tables (scripts/report_assets.py)\n", "## Simulation vs experiment\n",
             "Excess simulated uptake / per-paper experimental consensus median, median over grid points in each regime "
             "('unknown' basis treated as excess). (papers) = fewest papers behind any grid point in the regime. "
             "Screened = Gate-2 selection minus results/phase5/plausibility_flags.csv.\n",
             table_comparisons(c)]
    for name, title in (("henry", "Henry coefficients (mmol/g/bar)"), ("ideal_gas", "Computed ideal-gas effect"),
                        ("plausibility_flags", "Records removed by the plausibility screen"),
                        ("sensitivity", "Sensitivity runs (variant / main, z-score)")):
        f = P5 / f"{name}.csv"
        if f.exists():
            d = pd.read_csv(f)
            parts += [f"\n## {title}\n", d.round(3).to_markdown(index=False)]
    for name, title in (("oms_snapshots", "Nearest-metal distances of CO2 at 0.1 bar"),):
        f = P5 / f"{name}.csv"
        if f.exists():
            parts += [f"\n## {title}\n", pd.read_csv(f).round(3).to_markdown(index=False)]
    (REP / "tables.md").write_text("\n".join(parts) + "\n")
    overview_figure(c, REP / "fig_overview.png")
    for case in ORDER:
        case_figure(case, "main", REP / f"fig_{case}.png")
    print(REP / "tables.md", REP / "fig_overview.png")


if __name__ == "__main__":
    main()
