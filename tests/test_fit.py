import importlib.util  # noqa: F401  (pyGAPS 4.5.0 on Python 3.14 needs this imported first)

import numpy as np
import pytest

from gcmctools import fit

P = np.logspace(-2, 1, 10)


def test_langmuir_recovers_parameters():
    q = fit.langmuir(P, 8.0, 2.0)
    r = fit.fit_model("Langmuir", P, q, 0.01 * q)
    assert r["ok"]
    assert r["params"]["n_m_mmol_g"] == pytest.approx(8.0, rel=1e-6)
    assert r["params"]["K_1_bar"] == pytest.approx(2.0, rel=1e-6)
    assert r["chi2_reduced"] < 1e-8


def test_dsl_recovers_parameters():
    q = fit.dslangmuir(P, 2.0, 30.0, 10.0, 0.3)
    r = fit.fit_model("DSLangmuir", P, q, 0.005 * q)
    assert r["ok"]
    got = sorted([(r["params"]["K1_1_bar"], r["params"]["n1_mmol_g"]),
                  (r["params"]["K2_1_bar"], r["params"]["n2_mmol_g"])])
    assert got[0] == pytest.approx((0.3, 10.0), rel=1e-4)
    assert got[1] == pytest.approx((30.0, 2.0), rel=1e-4)


def test_henry_on_low_pressure_points():
    q = fit.langmuir(P, 8.0, 2.0)
    r = fit.fit_all(P, q, 0.01 * q)["Henry"]
    assert r["n_points"] == 3
    # initial slope is n_m*K = 16; fit over 0.01-0.046 bar sits a little below it
    assert 14.5 < r["params"]["K_mmol_g_bar"] < 16.0


def test_uncertainty_scales_with_errors():
    rng = np.random.default_rng(0)
    q = fit.langmuir(P, 8.0, 2.0)
    noisy = q + rng.normal(0, 0.02 * q)
    a = fit.fit_model("Langmuir", P, noisy, 0.02 * q)
    b = fit.fit_model("Langmuir", P, noisy, 0.08 * q)
    assert b["stderr"]["n_m_mmol_g"] == pytest.approx(4 * a["stderr"]["n_m_mmol_g"], rel=1e-3)


def test_model_forms_match_pygaps():
    import pygaps.modelling as pm
    lm = pm.get_isotherm_model("Langmuir")
    lm.params = {"n_m": 8.0, "K": 2.0}
    dsl = pm.get_isotherm_model("DSLangmuir")
    dsl.params = {"n_m1": 2.0, "K1": 30.0, "n_m2": 10.0, "K2": 0.3}
    for p in (0.01, 0.5, 7.0):
        assert lm.loading(p) == pytest.approx(fit.langmuir(p, 8.0, 2.0))
        assert dsl.loading(p) == pytest.approx(fit.dslangmuir(p, 2.0, 30.0, 10.0, 0.3))


def test_too_few_points():
    assert not fit.fit_model("DSLangmuir", P[:4], P[:4], P[:4])["ok"]
