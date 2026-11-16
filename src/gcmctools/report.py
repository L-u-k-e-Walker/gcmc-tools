"""Plots (static PNG, light surface) for isotherms and comparisons.

Colors: the fixed categorical order of the dataviz reference palette (slot 1 blue,
slot 2 orange, slot 3 aqua), never cycled. Identity is also carried by marker shape,
the legend and a direct label, so it does not rely on color alone.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE = "#fcfcfb"
TEXT = "#1f1f1e"
MUTED = "#6b6a63"
GRID = "#e4e3de"


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=TEXT)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_isotherm(csv_path, out_path=None):
    """Excess and absolute loading vs pressure with error bars and the DSL fit (excess)."""
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    meta = json.loads(csv_path.with_suffix(".json").read_text())
    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    for i, (basis, marker) in reversed(list(enumerate((("excess", "o"), ("absolute", "s"))))):
        d = df[df.basis == basis].sort_values("P_bar")  # absolute drawn first so excess sits on top
        ax.errorbar(d.P_bar, d.loading_mmol_g, yerr=d.loading_err_mmol_g, color=SERIES[i], marker=marker,
                    markersize=6, linewidth=2, capsize=2.5, elinewidth=1.2, label=f"GCMC {basis}",
                    markeredgecolor=SURFACE, markeredgewidth=1.0)
        last = d.iloc[-1]
        ax.annotate(basis, (last.P_bar, last.loading_mmol_g), xytext=(6, -3 if i == 0 else 6),
                    textcoords="offset points", color=TEXT, fontsize=9)
    fits = {k: v for k, v in meta.get("fits_excess", {}).items() if k != "Henry" and v.get("ok")}
    if fits:
        from . import fit as fitmod
        name, f = min(fits.items(), key=lambda kv: kv[1]["aic"])
        p = np.logspace(np.log10(df.P_bar.min()), np.log10(df.P_bar.max()), 200)
        ax.plot(p, fitmod.MODELS[name][0](p, *f["params"].values()), color=MUTED, linewidth=1.2, linestyle="--",
                label=f"{name} fit to excess (lowest AIC; reduced chi2 {f['chi2_reduced']:.2g})")
    ax.set_xscale("log")
    ax.set_xlabel("Pressure (bar)", color=TEXT)
    ax.set_ylabel("Loading (mmol/g)", color=TEXT)
    vf = meta["options"].get("void_fraction")
    gasmode = "ideal gas" if meta["options"].get("ideal_gas") else "Peng-Robinson"
    ax.set_title(f"{meta['gas']} in {meta['case']}, {meta['T_K']:g} K  ({meta['label']})", color=TEXT,
                 fontsize=11, loc="left")
    ax.text(0.99, 0.02, f"fugacity: {gasmode}; He void fraction: {vf if vf is not None else '1.0 (default)'}",
            transform=ax.transAxes, fontsize=8, color=MUTED, va="bottom", ha="right")
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT, loc="upper left")
    fig.tight_layout()
    out = Path(out_path or csv_path.with_suffix(".png"))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out
