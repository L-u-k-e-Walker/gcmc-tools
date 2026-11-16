"""Cleaning rules, consensus and comparison helpers on synthetic ISODB-shaped records."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gcmctools import clean, isodb, units

HK = "NIST-MATDB-991daf7313251e7e607e2bab2da57e33"
CO2 = isodb.GAS_INCHIKEY["CO2"]


def rec(fn="10.1/x.Isotherm1", T=298, cat="", units_="mmol/g", punits="bar", data=None, ads=None,
        name="CuBTC", itype=""):
    data = data or [(0.1, 0.5), (0.5, 2.0), (1.0, 3.5)]
    return {"filename": fn, "DOI": "10.1/x", "adsorbent": {"hashkey": HK, "name": name},
            "adsorbates": ads or [{"InChIKey": CO2, "name": "Carbon Dioxide"}], "category": cat,
            "temperature": T, "isotherm_type": itype, "adsorptionUnits": units_, "pressureUnits": punits,
            "isotherm_data": [{"pressure": p, "total_adsorption": q,
                               "species_data": [{"InChIKey": CO2, "composition": 1, "adsorption": q}]}
                              for p, q in data]}


PAPER = {"DOI": "10.1/x", "categories": ["exp"], "title": "CO2 adsorption on HKUST-1", "year": 2010}


def run(r, paper=PAPER, T=298, window=2.0):
    return clean.clean_record(r, paper, {HK}, "CO2", T, window, 44.0095)


@pytest.mark.parametrize("iso,paper_cats,ok", [
    ("exp", ["exp", "sim"], True), ("", ["exp"], True), ("sim", ["exp"], False),
    ("", ["sim"], False), ("", ["exp", "sim"], False), ("", ["mod", "exp"], False), ("", ["qua", "sim"], False),
])
def test_exp_status(iso, paper_cats, ok):
    assert clean.exp_status(iso, paper_cats)[0] is ok


def test_accept_and_units():
    row, pts = run(rec(units_="cm3(STP)/g", data=[(0.1, 22.414), (0.5, 44.828), (1.0, 67.242)]))
    assert row["status"] == "accepted" and row["basis"] == "unknown"
    assert [q for _, q in pts] == pytest.approx([1.0, 2.0, 3.0])


def test_temperature_window_inclusive():
    assert run(rec(T=300))[0]["status"] == "accepted"
    assert run(rec(T=301))[0]["reason"].startswith("temperature")


@pytest.mark.parametrize("u", ["kg/mol", "wt%", "molecules/unitcell", "mol/mol", "cm3(STP)/cm3"])
def test_unit_rejections(u):
    row, pts = run(rec(units_=u))
    assert pts is None and row["reason"].startswith("unit:")


def test_multicomponent_rejected():
    ads = [{"InChIKey": CO2, "name": "CO2"}, {"InChIKey": isodb.GAS_INCHIKEY["N2"], "name": "N2"}]
    assert run(rec(ads=ads))[0]["reason"].startswith("multicomponent")


def test_null_total_uses_species_and_drops_artifacts():
    r = rec(data=[(0.0, 0.0), (0.05, 0.05), (0.1, 0.5), (0.5, 2.0), (1.0, 3.5)])
    r["isotherm_data"][2]["total_adsorption"] = None
    row, pts = run(r)
    assert row["status"] == "accepted"
    assert pts == [(0.1, 0.5), (0.5, 2.0), (1.0, 3.5)]     # P<=0 point and P==q point dropped
    assert "species_data" in row["notes"] and "digitizer" in row["notes"] and "P <= 0" in row["notes"]


def test_desorption_branch_removed():
    row, pts = run(rec(data=[(0.1, 0.5), (0.5, 2.0), (1.0, 3.5), (0.6, 2.4), (0.2, 1.0)]))
    assert len(pts) == 3 and "adsorption branch" in row["notes"]


def test_too_few_points():
    assert run(rec(data=[(0.1, 0.5), (0.5, 2.0)]))[0]["reason"].startswith("fewer than 3")


def test_flags():
    assert run(rec(name="CuBTC pellet"))[0]["sample_flags"] == "shaped"
    paper = {**PAPER, "title": "CuBTC/graphite oxide composites under humid conditions"}
    row, _ = run(rec(), paper)
    assert row["sample_flags"] == "aged_humid"              # sample-state words from the title exclude
    assert row["title_mentions"] == "composite"             # composite words are only recorded


def test_duplicates_rejected_and_bogus_doi_loses(tmp_path):
    d = tmp_path / "a" / "b" / "c"
    d.mkdir(parents=True)
    r1, r2 = rec(fn="10.1021x.Isotherm1"), rec(fn="10.8888x.Isotherm1")
    r2["DOI"] = "10.8888/x"
    recs = [(r2, d / "r2.json"), (r1, d / "r1.json")]
    papers = [PAPER, {**PAPER, "DOI": "10.8888/x"}]
    ledger, tidy = clean.clean_case("HKUST-1", "CO2", 298, 2, [HK], recs, papers)
    st = ledger.set_index("filename")
    assert st.loc["10.1021x.Isotherm1", "status"] == "accepted"
    assert st.loc["10.8888x.Isotherm1", "reason"] == "duplicate data of 10.1021x.Isotherm1"
    assert set(tidy.source_id) == {"10.1021x.Isotherm1"}


def test_interp_no_extrapolation_and_loglog():
    g = np.array([0.05, 0.1, 0.4, 1.0, 2.0])
    out = clean.interp_isotherm([0.1, 1.0], [1.0, 10.0], g)
    assert np.isnan(out[0]) and np.isnan(out[-1])
    assert out[2] == pytest.approx(10 ** (math.log10(0.4) + 1))   # q = 10 P exactly in log-log


def _tidy(curves):
    rows = []
    for sid, doi, k in curves:
        for p in np.logspace(-2, 1, 12):
            rows.append({"source_id": sid, "doi": doi, "P_bar": p, "loading_mmol_g": k * p / (1 + 0.1 * p)})
    return pd.DataFrame(rows)


def test_consensus_one_vote_per_paper():
    # paper A has 5 identical isotherms at k=1, papers B and C one each at k=2 and k=3
    t = _tidy([(f"A{i}", "A", 1.0) for i in range(5)] + [("B1", "B", 2.0), ("C1", "C", 3.0)])
    cons, mat = clean.consensus(t, np.array([0.1, 1.0]))
    assert cons.n_dois.tolist() == [3, 3] and cons.n_isotherms.tolist() == [7, 7]
    lm = 2.0 * 0.1 / 1.01
    assert cons["median"].iloc[0] == pytest.approx(lm, rel=1e-3)       # median of papers (1,2,3)x, not of 7 curves


def test_outlier_flagged_not_removed():
    t = _tidy([(f"P{i}", f"D{i}", k) for i, k in enumerate([1.0, 1.1, 0.9, 1.05, 0.95, 0.05])])
    cons, mat = clean.consensus(t)
    score, out, _ = clean.flag_outliers(mat, cons)
    assert out["P5"] and not out[["P0", "P1", "P2", "P3", "P4"]].any()
    assert "P5" in mat.columns


def test_henry_low_pressure():
    p = np.array([0.01, 0.02, 0.05, 0.1, 1.0])
    assert clean.henry_low_pressure(p, 6.0 * p) == pytest.approx(6.0)
    assert clean.henry_low_pressure(p[3:], 6.0 * p[3:]) is None


def test_isosteric_heat_recovers_vant_hoff():
    # Henry-law isotherms q = K(T) P with K = K0 exp(Q/RT): Clausius-Clapeyron gives Q exactly
    Q = 25000.0
    K = lambda T: 1e-4 * math.exp(Q / (units.R_J_PER_MOL_K * T))
    grid = np.logspace(-3, 1, 50)
    c = lambda T: pd.DataFrame({"P_bar": grid, "median": K(T) * grid})
    r = clean.isosteric_heat(c(273.0), 273.0, c(298.0), 298.0, [0.5, 1.0])
    assert r.Qst_kj_mol.tolist() == pytest.approx([25.0, 25.0], rel=1e-6)


def test_paper_folder_uses_bibliography_stem():
    assert isodb.paper_folder({"_bib_stem": "10.1007s1045001596846", "DOI": "10.1007/s10450-015-9684-6"}) \
        == "10.1007s1045001596846"


def test_water_in_title_flags_sample_state():
    for title in ("CO2/H2O Adsorption Equilibrium on HKUST-1", "Effect of water on CO2 uptake"):
        assert run(rec(), {**PAPER, "title": title})[0]["sample_flags"] == "aged_humid"


def _iso(sid, doi, p, q):
    return pd.DataFrame({"source_id": sid, "doi": doi, "P_bar": p, "loading_mmol_g": q})


def test_plausibility_r1_cryogenic_shape():
    p = np.array([0.005, 0.01, 0.05, 0.5, 1.0])
    tidy = pd.concat([_iso("cryo", "d1", p, [10, 12, 14, 16, 17]),     # 2000 mmol/g/bar: 77 K shape
                      _iso("ok", "d2", p, 0.4 * p)])                    # linear, K = 0.4
    f = clean.plausibility_flags(tidy, "N2", 298.0)
    assert set(f) == {"cryo"} and f["cryo"].startswith("R1")
    assert clean.plausibility_flags(tidy, "CO2", 298.0) == {}          # R1 not applied to CO2


def test_plausibility_r2_temperature_order():
    p = np.logspace(-2, 1, 8)
    warm = pd.concat([_iso("w1", "a", p, 2 * p / (1 + p)), _iso("w2", "b", p, 2.2 * p / (1 + p))])
    cold = pd.concat([_iso("c_ok", "c", p, 4 * p / (1 + p)), _iso("c_bad", "d", p, 0.2 * p / (1 + p))])
    f = clean.plausibility_flags(cold, "CO2", 273.0, warm, 298.0)
    assert set(f) == {"c_bad"} and f["c_bad"].startswith("R2")
    assert clean.plausibility_flags(warm, "CO2", 298.0, cold[cold.source_id == "c_ok"], 273.0) == {}
