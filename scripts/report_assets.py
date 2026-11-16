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
from gcmctools import report  # noqa: E402

P5 = ROOT / "results" / "phase5"
REP = ROOT / "reports"
ORDER = ["MFI", "IRMOF-1", "HKUST-1", "Mg-MOF-74", "UiO-66", "ZIF-8"]


def fmt(x, nd=2):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{nd}f}"


def table_comparisons(c):
    lines = ["| Case | Gas | T (K) | exp isotherms (papers) | sim/exp < 0.1 bar | 0.1–1 bar | > 1 bar | "
             "inside exp IQR (low/mid/high) | exp IQR ratio (low/mid/high) | without outliers (low/mid/high) | strict filters (low/mid/high) |",
             "|---|---|---:|---:|---:|---:|---:|---|---|---|---|"]
    for _, r in c.iterrows():
        if not r.get("n_exp_pristine"):
            lines.append(f"| {r.case} | {r.gas} | {r.T_K:g} | 0 | no experimental data | | | | | | |")
            continue
        g = lambda p, k: r.get(f"{p}_{k}")
        lines.append(
            f"| {r.case} | {r.gas} | {r.T_K:g} | {int(r.n_exp_pristine)} ({int(r.n_exp_papers)}) | "
            f"{fmt(g('head', 'low_ratio'))} | {fmt(g('head', 'mid_ratio'))} | {fmt(g('head', 'high_ratio'))} | "
            + "/".join(fmt(g('head', f'{k}_inside_iqr') * 100 if pd.notna(g('head', f'{k}_inside_iqr')) else None, 0)
                       for k in ('low', 'mid', 'high')) + "% | "
            + "/".join(fmt(g('head', f'{k}_exp_iqr_ratio'), 1) for k in ('low', 'mid', 'high')) + " | "
            + "/".join(fmt(g('noout', f'{k}_ratio')) for k in ('low', 'mid', 'high')) + " | "
            + "/".join(fmt(g('strict', f'{k}_ratio')) for k in ('low', 'mid', 'high')) + " |")
    return "\n".join(lines)


def overview_figure(c, out):
    c = c[c.n_exp_pristine.fillna(0) > 0].copy()
    c["label"] = c.case + "  " + c.gas + " " + c.T_K.map(lambda t: f"{t:g} K")
    c["o"] = c.case.map({k: i for i, k in enumerate(ORDER)})
    c = c.sort_values(["o", "gas", "T_K"], ascending=[False, False, False])
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(c) + 1.4), dpi=150)
    fig.patch.set_facecolor(report.SURFACE)
    report._style(ax)
    y = np.arange(len(c))
    for i, (reg, marker, name) in enumerate((("low", "o", "< 0.1 bar"), ("mid", "s", "0.1–1 bar"),
                                             ("high", "D", "> 1 bar"))):
        v = np.log10(c[f"head_{reg}_ratio"].astype(float))
        iqr = c[f"head_{reg}_exp_iqr_ratio"].astype(float)
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
    ax.legend(frameon=False, fontsize=7.5, loc="lower right", labelcolor=report.TEXT)
    ax.set_title("Simulation vs ISODB consensus by pressure regime", color=report.TEXT, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(out, facecolor=report.SURFACE)
    plt.close(fig)


def main():
    REP.mkdir(exist_ok=True)
    c = pd.read_csv(P5 / "comparisons.csv")
    c["o"] = c.case.map({k: i for i, k in enumerate(ORDER)})
    c = c.sort_values(["o", "gas", "T_K"]).drop(columns="o")
    parts = ["# Generated tables (scripts/report_assets.py)\n", "## Simulation vs experiment\n",
             "Excess simulated uptake vs the per-paper experimental median ('unknown' basis treated as excess).\n",
             table_comparisons(c)]
    for name, title in (("henry", "Henry coefficients (mmol/g/bar)"), ("ideal_gas", "Computed ideal-gas effect"),
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
    print(REP / "tables.md", REP / "fig_overview.png")


if __name__ == "__main__":
    main()
