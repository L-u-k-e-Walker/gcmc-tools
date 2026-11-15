"""Isotherm fits with parameter uncertainties.

pyGAPS model fits are unweighted and return no covariance (docs/RECON.md section 6), so we
fit with scipy.optimize.curve_fit, weighted by the GCMC standard errors (absolute_sigma).
Model forms are the same as pyGAPS' Henry, Langmuir and DSLangmuir; tests cross-check them.
Pressure in bar, loading in mmol/g.
"""

import math

import numpy as np
from scipy.optimize import curve_fit


def henry(p, k):
    return k * p


def langmuir(p, n_m, k):
    return n_m * k * p / (1.0 + k * p)


def dslangmuir(p, n1, k1, n2, k2):
    return n1 * k1 * p / (1.0 + k1 * p) + n2 * k2 * p / (1.0 + k2 * p)


MODELS = {
    "Henry": (henry, ["K_mmol_g_bar"]),
    "Langmuir": (langmuir, ["n_m_mmol_g", "K_1_bar"]),
    "DSLangmuir": (dslangmuir, ["n1_mmol_g", "K1_1_bar", "n2_mmol_g", "K2_1_bar"]),
}


def _sigma(q, err):
    """Use reported errors; floor at 1% of the value (or a tiny absolute value) to avoid zero weights."""
    q, err = np.asarray(q, float), np.asarray(err, float)
    floor = np.maximum(0.01 * np.abs(q), 1e-6)
    return np.where(np.isfinite(err) & (err > 0), np.maximum(err, floor), floor)


def fit_model(name, p, q, err, p_max=None):
    """Fit one model. Returns dict with params, stderr, residuals, reduced chi^2, or an error."""
    f, names = MODELS[name]
    p, q = np.asarray(p, float), np.asarray(q, float)
    s = _sigma(q, err)
    mask = np.ones_like(p, bool) if p_max is None else p <= p_max
    p, q, s = p[mask], q[mask], s[mask]
    if len(p) < len(names) + (1 if name != "Henry" else 0):
        return {"model": name, "ok": False, "error": f"too few points ({len(p)})"}
    qmax = float(np.max(q))
    if name == "Henry":
        guess, bounds = [q[0] / p[0]], ([0.0], [np.inf])
    elif name == "Langmuir":
        guess, bounds = [1.2 * qmax, (q[0] / p[0]) / (1.2 * qmax)], ([0, 0], [np.inf, np.inf])
    else:
        k0 = (q[0] / p[0]) / qmax
        guess, bounds = [0.3 * qmax, 10 * k0, 0.9 * qmax, 0.3 * k0], ([0] * 4, [np.inf] * 4)
    try:
        popt, pcov = curve_fit(f, p, q, p0=guess, sigma=s, absolute_sigma=True, bounds=bounds,
                               maxfev=20000)
    except (RuntimeError, ValueError) as e:
        return {"model": name, "ok": False, "error": str(e)}
    resid = q - f(p, *popt)
    dof = max(1, len(p) - len(popt))
    chi2 = float(np.sum((resid / s) ** 2))
    perr = np.sqrt(np.diag(pcov)) if np.all(np.isfinite(pcov)) else np.full(len(popt), np.nan)
    n = len(p)
    return {"model": name, "ok": True, "n_points": int(n), "p_max_bar": float(p.max()),
            "params": dict(zip(names, map(float, popt))),
            "stderr": dict(zip(names, map(float, perr))),
            "residuals_mmol_g": [float(x) for x in resid],
            "chi2_reduced": chi2 / dof,
            "aic": float(n * math.log(max(chi2, 1e-300) / n) + 2 * len(popt))}


def fit_all(p, q, err, henry_points=3):
    """Henry on the lowest `henry_points` pressures; Langmuir and DSL on all points."""
    order = np.argsort(p)
    p_h = float(np.asarray(p)[order][min(henry_points, len(p)) - 1])
    return {"Henry": fit_model("Henry", p, q, err, p_max=p_h),
            "Langmuir": fit_model("Langmuir", p, q, err),
            "DSLangmuir": fit_model("DSLangmuir", p, q, err)}
