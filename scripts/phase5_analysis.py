"""Phase 5 analysis: test the candidate causes of MISSION section 7 for every case/gas/T.

Inputs: results/<case>/<gas>_<T>K_<label>.csv (+ _points.csv, .json), data/isodb_clean/*, and
results/phase5/sensitivity_runs.csv (+ oms_snapshots.csv) when present. Nothing here runs RASPA3.

Outputs (results/phase5/):
- comparisons.csv      : sim/exp by regime (headline, without outliers, strict filters), exp spread, n papers
- ideal_gas.csv        : computed ideal-gas vs real-gas loading at 1 and 10 bar (no new simulations)
- sample_quality.csv   : per experimental isotherm, exp/sim ratio at low/high P and the log-ratio slope
- sensitivity.csv      : variant / main at the same P with a z-score (convergence, size, charges, LJ)
- henry.csv            : simulated Henry coefficient vs experimental low-P slopes
- low_p_slopes.csv     : experimental vs simulated log-log slope below 0.1 bar (digitization floor test)\n- plausibility_flags.csv: records removed by the post-hoc screen (clean.plausibility_flags); scr_* columns
Usage: conda run -n ads python scripts/phase5_analysis.py [--label main]
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import clean, compare  # noqa: E402

CLEAN = ROOT / "data" / "isodb_clean"
OUT = ROOT / "results" / "phase5"


def pristine_ids(ledger):
    acc = ledger[ledger.status == "accepted"]
    return set(acc[acc.sample_flags.isna() | (acc.sample_flags == "")].filename)


def strict_files(case, gas, T, tmpdir):
    """Stricter experimental selection: |T - target| <= 0.5 K, no outliers, >= 5 points."""
    stem = f"{case}_{gas}_{T:g}K"
    led = pd.read_csv(CLEAN / f"{stem}_ledger.csv")
    tidy = pd.read_csv(CLEAN / f"{stem}.csv")
    keep = led.status == "accepted"
    keep &= (led.T_K - T).abs() <= 0.5
    keep &= ~led.get("outlier", pd.Series(False, index=led.index)).fillna(False).astype(bool)
    keep &= led.n_points_used >= 5
    led2 = led.copy()
    led2.loc[led.status.eq("accepted") & ~keep, "status"] = "rejected"
    led2.loc[led.status.eq("accepted") & ~keep, "reason"] = "strict filter"
    tmpdir.mkdir(parents=True, exist_ok=True)
    led2.to_csv(tmpdir / f"{stem}_ledger.csv", index=False)
    tidy[tidy.source_id.isin(set(led2[led2.status == "accepted"].filename))].to_csv(tmpdir / f"{stem}.csv", index=False)
    return tmpdir / f"{stem}.csv", tmpdir / f"{stem}_ledger.csv", int(keep.sum())


def pristine_tidy(stem):
    if not (CLEAN / f"{stem}.csv").exists():
        return None, 0
    led = pd.read_csv(CLEAN / f"{stem}_ledger.csv")
    ids = pristine_ids(led)
    tidy = pd.read_csv(CLEAN / f"{stem}.csv")
    return tidy[tidy.source_id.isin(ids)], int(led[led.filename.isin(ids)].doi.nunique())


def screened_files(case, gas, T, tmpdir):
    """Gate-2 selection minus records failing clean.plausibility_flags (R1 always; R2 only for the
    temperature with fewer papers, tested against the better-sampled one, so a bad small set cannot
    remove good records). Returns (exp_csv, ledger_csv, n_kept, flags)."""
    stem = f"{case}_{gas}_{T:g}K"
    tidy, n_pap = pristine_tidy(stem)
    other_T = {298.0: 273.0, 273.0: 298.0}.get(T) if gas == "CO2" else None
    o_tidy, o_pap = pristine_tidy(f"{case}_{gas}_{other_T:g}K") if other_T else (None, 0)
    use_r2 = o_tidy is not None and o_pap > n_pap
    flags = clean.plausibility_flags(tidy, gas, T, o_tidy if use_r2 else None, other_T if use_r2 else None)
    led = pd.read_csv(CLEAN / f"{stem}_ledger.csv")
    hit = led.filename.isin(flags)
    led.loc[hit, "status"] = "rejected"
    led.loc[hit, "reason"] = led.loc[hit, "filename"].map(flags)
    tmpdir.mkdir(parents=True, exist_ok=True)
    led.to_csv(tmpdir / f"{stem}_ledger.csv", index=False)
    full = pd.read_csv(CLEAN / f"{stem}.csv")
    full[~full.source_id.isin(flags)].to_csv(tmpdir / f"{stem}.csv", index=False)
    n = len(pristine_ids(led))
    return tmpdir / f"{stem}.csv", tmpdir / f"{stem}_ledger.csv", n, flags


def regime_row(reg, basis="excess"):
    out = {}
    for _, r in reg[reg.sim_basis == basis].iterrows():
        k = r["regime"]
        out[f"{k}_ratio"] = r.get("ratio_at_median")
        out[f"{k}_inside_iqr"] = r.get("frac_inside_iqr")
        out[f"{k}_min_dois"] = r.get("min_n_dois")
        out[f"{k}_exp_iqr_ratio"] = r.get("median_exp_iqr_ratio")
        out[f"{k}_n_grid"] = r.get("n_grid_points")
    return out


def ideal_gas_effect(points_csv):
    """Ideal-gas loading at P equals the real-gas loading at fugacity P (the real run sees f = phi*P)."""
    d = pd.read_csv(points_csv).sort_values("P_bar")
    f = d.P_bar * d.fugacity_coefficient
    rows = []
    for p in (1.0, 10.0):
        if p < f.min() or p > f.max() and p > d.P_bar.max():
            continue
        q_real = float(np.interp(math.log(p), np.log(d.P_bar), np.log(d.exc_mmol_g.clip(lower=1e-12))))
        if p > f.max():                             # fugacity at the top point is below P: extrapolate in log-log
            sl = (math.log(d.exc_mmol_g.iloc[-1]) - math.log(d.exc_mmol_g.iloc[-2])) / \
                 (math.log(f.iloc[-1]) - math.log(f.iloc[-2]))
            q_ideal = math.log(d.exc_mmol_g.iloc[-1]) + sl * (math.log(p) - math.log(f.iloc[-1]))
            note = "log-log extrapolation over the last segment"
        else:
            q_ideal = float(np.interp(math.log(p), np.log(f), np.log(d.exc_mmol_g.clip(lower=1e-12))))
            note = ""
        phi = float(np.interp(p, d.P_bar, d.fugacity_coefficient))
        rows.append({"P_bar": p, "phi": phi, "q_real": math.exp(q_real), "q_ideal": math.exp(q_ideal),
                     "ideal_over_real": math.exp(q_ideal - q_real), "note": note})
    return rows


def sample_quality(sim_csv, exp_csv, ledger_csv):
    sim = pd.read_csv(sim_csv)
    s = sim[sim.basis == "excess"].sort_values("P_bar")
    exp = pd.read_csv(exp_csv)
    ids = pristine_ids(pd.read_csv(ledger_csv))
    rows = []
    for sid, g in exp[exp.source_id.isin(ids)].groupby("source_id"):
        g = g[(g.P_bar >= s.P_bar.min()) & (g.P_bar <= s.P_bar.max()) & (g.loading_mmol_g > 0)]
        if len(g) < 3:
            continue
        qs = np.exp(np.interp(np.log(g.P_bar), np.log(s.P_bar), np.log(s.loading_mmol_g)))
        lr = np.log10(g.loading_mmol_g.values / qs)
        lp = np.log10(g.P_bar.values)
        slope = float(np.polyfit(lp, lr, 1)[0]) if lp.max() - lp.min() > 0.3 else float("nan")
        lo, hi = lr[g.P_bar.values < 0.1], lr[g.P_bar.values > 1.0]
        rows.append({"source_id": sid, "doi": g.doi.iloc[0], "n": len(g), "P_min": float(g.P_bar.min()),
                     "P_max": float(g.P_bar.max()), "median_log10_exp_over_sim": float(np.median(lr)),
                     "low_P_log10_ratio": float(np.median(lo)) if len(lo) else np.nan,
                     "high_P_log10_ratio": float(np.median(hi)) if len(hi) else np.nan,
                     "slope_dlog_ratio_dlogP": slope, "sd_log10_ratio": float(np.std(lr, ddof=1))})
    return rows


def low_p_slopes(sim_csv, exp_csv, ledger_csv, p_max=0.1):
    """Log-log slope d ln q / d ln P of each pristine experimental isotherm over its points with P <= p_max
    (>= 3 points spanning >= 0.5 decade), next to the simulated slope over the same pressure span.
    In the Henry regime the slope is 1; digitization error near the origin of a linear-axis figure
    flattens it (positive, roughly constant absolute error)."""
    sim = pd.read_csv(sim_csv)
    s = sim[sim.basis == "excess"].sort_values("P_bar")
    exp = pd.read_csv(exp_csv)
    ids = pristine_ids(pd.read_csv(ledger_csv))
    rows = []
    for sid, g in exp[exp.source_id.isin(ids)].groupby("source_id"):
        g = g[(g.P_bar <= p_max) & (g.P_bar > 0) & (g.loading_mmol_g > 0)]
        if len(g) < 3 or math.log10(g.P_bar.max() / g.P_bar.min()) < 0.5:
            continue
        sl = float(np.polyfit(np.log(g.P_bar), np.log(g.loading_mmol_g), 1)[0])
        lo, hi = max(g.P_bar.min(), s.P_bar.min()), g.P_bar.max()
        ss = s[(s.P_bar >= lo * 0.999) & (s.P_bar <= hi * 1.001)]
        if len(ss) < 2:
            ss = s.head(3)
        sim_sl = float(np.polyfit(np.log(ss.P_bar), np.log(ss.loading_mmol_g), 1)[0])
        rows.append({"source_id": sid, "doi": g.doi.iloc[0], "n": len(g), "P_min": float(g.P_bar.min()),
                     "P_max": float(g.P_bar.max()), "q_min": float(g.loading_mmol_g.min()), "exp_slope": sl,
                     "sim_slope": sim_sl})
    return rows


def basis_effect(sim_csv):
    """Absolute / excess simulated loading at 1 and 10 bar (cause 2)."""
    d = pd.read_csv(sim_csv)
    e = d[d.basis == "excess"].set_index("P_bar").loading_mmol_g
    a = d[d.basis == "absolute"].set_index("P_bar").loading_mmol_g
    out = {}
    for p in (1.0, 10.0):
        k = min(e.index, key=lambda x: abs(math.log(x / p)))
        out[f"abs_over_exc_{p:g}bar"] = float(a[k] / e[k])
    return out


def sample_quality_summary(sq):
    """Per case/gas/T: between-isotherm spread of the median log ratio (constant-factor part) vs the
    median within-isotherm spread (shape part). Cause-5 signature: between >> within and high-P ratio < 1."""
    rows = []
    for (c, g, t), d in pd.DataFrame(sq).groupby(["case", "gas", "T_K"]):
        if len(d) < 3:
            continue
        rows.append({"case": c, "gas": g, "T_K": t, "n_isotherms": len(d),
                     "between_sd_log10": float(d.median_log10_exp_over_sim.std(ddof=1)),
                     "within_sd_log10_median": float(d.sd_log10_ratio.median()),
                     "median_high_P_exp_over_sim": float(10 ** d.high_P_log10_ratio.median())
                     if d.high_P_log10_ratio.notna().any() else np.nan,
                     "median_low_P_exp_over_sim": float(10 ** d.low_P_log10_ratio.median())
                     if d.low_P_log10_ratio.notna().any() else np.nan,
                     "median_slope": float(d.slope_dlog_ratio_dlogP.median())})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="main")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    comps, ideal, sq, henry, plaus, slopes = [], [], [], [], [], []
    for sim_csv in sorted(ROOT.glob(f"results/*/*K_{a.label}.csv")):
        case = sim_csv.parent.name
        gas, Tk = sim_csv.stem.split("_")[:2]
        T = float(Tk[:-1])
        stem = f"{case}_{gas}_{T:g}K"
        exp_csv, led_csv = CLEAN / f"{stem}.csv", CLEAN / f"{stem}_ledger.csv"
        row = {"case": case, "gas": gas, "T_K": T}
        sim_meta = json.loads(sim_csv.with_suffix(".json").read_text())
        row["sim_henry_mmol_g_bar"] = sim_meta.get("henry_widom_mmol_g_bar")
        row["sim_dH0_kj_mol"] = sim_meta.get("dH0_nvt1_kj_mol")
        row.update(basis_effect(sim_csv))
        for r in ideal_gas_effect(sim_csv.with_name(sim_csv.stem + "_points.csv")):
            ideal.append({"case": case, "gas": gas, "T_K": T, **r})
        if not exp_csv.exists():
            row["n_exp_pristine"] = 0
            comps.append(row)
            continue
        led = pd.read_csv(led_csv)
        ids = pristine_ids(led)
        row["n_exp_pristine"] = len(ids)
        row["n_exp_papers"] = int(led[led.filename.isin(ids)].doi.nunique())
        if len(ids) == 0:
            comps.append(row)
            continue
        t2 = None
        other = {298.0: 273.0, 273.0: 298.0}.get(T) if gas == "CO2" else None
        if other is not None and (CLEAN / f"{case}_{gas}_{other:g}K.csv").exists():
            l2 = pd.read_csv(CLEAN / f"{case}_{gas}_{other:g}K_ledger.csv")
            e2 = pd.read_csv(CLEAN / f"{case}_{gas}_{other:g}K.csv")
            t2 = (e2[e2.source_id.isin(pristine_ids(l2))], other)
        res = compare.compare(sim_csv, exp_csv, led_csv, exp_lo=t2 if (t2 is not None and T == 298.0) else None)
        out_dir = ROOT / "results" / case / "compare"
        cstem = f"{sim_csv.stem}_vs_isodb"
        compare.write(res, out_dir, cstem, sim_csv)
        compare.plot_compare(res, sim_csv, f"{gas} in {case}, {T:g} K: simulation vs ISODB", out_dir / f"{cstem}.png")
        row.update({f"head_{k}": v for k, v in regime_row(res["regimes"]).items()})
        row.update({f"noout_{k}": v for k, v in regime_row(res["regimes_no_outliers"]).items()})
        row.update({f"abs_{k}": v for k, v in regime_row(res["regimes"], "absolute").items() if k.endswith("ratio")
                    and "iqr" not in k})
        row["n_outliers"] = int(sum(bool(v) for v in res["outlier"].values))
        h = res["henry"]
        henry.append({"case": case, "gas": gas, "T_K": T, "sim_widom": h["sim_widom_mmol_g_bar"],
                      "sim_widom_err": h["sim_widom_err"], "exp_median": h["exp_median_mmol_g_bar"],
                      "exp_n_isotherms": h["exp_n_isotherms"], "exp_n_papers": h["exp_n_dois"],
                      "sim_over_exp": h.get("sim_over_exp_median")})
        if "qst_exp" in res and len(res["qst_exp"]):
            q = res["qst_exp"]
            row["exp_qst_papers"] = int(q.doi.nunique())
            row["exp_qst_median_kj_mol"] = float(q.Qst_kj_mol.median())
        # strict filters
        se, sl, n = strict_files(case, gas, T, OUT / "strict")
        row["strict_n_isotherms"] = n
        if n > 0:
            rs = compare.compare(sim_csv, se, sl)
            row.update({f"strict_{k}": v for k, v in regime_row(rs["regimes"]).items()})
        # post-hoc plausibility screen (experimental data and physics only)
        se, sl, n, flags = screened_files(case, gas, T, OUT / "screened")
        row["scr_n_isotherms"] = n
        row["scr_n_removed"] = len(flags)
        for sid, why in flags.items():
            plaus.append({"case": case, "gas": gas, "T_K": T, "source_id": sid,
                          "doi": led.set_index("filename").doi.get(sid), "reason": why})
        if n > 0:
            rs = compare.compare(sim_csv, se, sl)
            row.update({f"scr_{k}": v for k, v in regime_row(rs["regimes"]).items()})
            hs = rs["henry"]
            henry[-1].update({"scr_exp_median": hs["exp_median_mmol_g_bar"], "scr_exp_n_isotherms": hs["exp_n_isotherms"],
                              "scr_sim_over_exp": hs.get("sim_over_exp_median")})
        if n > 0:                                   # screened selection only
            for r in low_p_slopes(sim_csv, se, sl):
                slopes.append({"case": case, "gas": gas, "T_K": T, **r})
            for r in sample_quality(sim_csv, se, sl):
                sq.append({"case": case, "gas": gas, "T_K": T, **r})
        comps.append(row)
    pd.DataFrame(comps).to_csv(OUT / "comparisons.csv", index=False)
    pd.DataFrame(ideal).to_csv(OUT / "ideal_gas.csv", index=False)
    pd.DataFrame(sq).to_csv(OUT / "sample_quality.csv", index=False)
    sample_quality_summary(sq).to_csv(OUT / "sample_quality_summary.csv", index=False)
    pd.DataFrame(henry).to_csv(OUT / "henry.csv", index=False)
    pd.DataFrame(slopes).to_csv(OUT / "low_p_slopes.csv", index=False)
    pd.DataFrame(plaus, columns=["case", "gas", "T_K", "source_id", "doi", "reason"]).to_csv(
        OUT / "plausibility_flags.csv", index=False)

    sens_path = OUT / "sensitivity_runs.csv"
    if sens_path.exists():
        sens = pd.read_csv(sens_path)
        rows = []
        for _, r in sens[sens.variant != "movie"].iterrows():
            pts = ROOT / "results" / r.case / f"CO2_298K_{a.label}_points.csv"
            if not pts.exists():
                continue
            m = pd.read_csv(pts)
            m = m.iloc[(m.P_bar - r.P_bar).abs().argsort()[:1]]
            if abs(float(m.P_bar.iloc[0]) - r.P_bar) > 1e-6 * r.P_bar:
                continue
            base, base_err = float(m.exc_mmol_g.iloc[0]), float(max(m.exc_err.iloc[0], m.exc_err_series.iloc[0] or 0))
            err = max(r.exc_err, r.exc_err_series if pd.notna(r.exc_err_series) else 0)
            rows.append({"case": r.case, "variant": r.variant, "P_bar": r.P_bar, "main": base, "main_err": base_err,
                         "variant_value": r.exc_mmol_g, "variant_err": err, "ratio": r.exc_mmol_g / base,
                         "z": (r.exc_mmol_g - base) / math.sqrt(err ** 2 + base_err ** 2)})
        pd.DataFrame(rows).to_csv(OUT / "sensitivity.csv", index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
