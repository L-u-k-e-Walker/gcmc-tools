# Log

## 2026-11-15: Phase 0 recon
Did:
- Read MISSION.md. Inspected raspa3-src v3.0.29 examples (6, 10, 11, 12), molecule and FF files,
  docs/manual/commands.md, and source for EOS, void fraction, enthalpy, Widom, CIF reader, input reader.
- Inspected the old cubtc_isotherm run folders (text + JSON output), run_isotherm.py and git history.
- Computed the Cu-BTC helium void fraction with `raspa3-cli --void-fraction --energy` (scratch): 0.7463.
- Fetched ISODB materials.json, gases.json and 5 isotherm records into `data/isodb_raw/api/` (raw,
  unmodified). Shallow, blobless, sparse clone of NIST-ISODB/isodb-library in the scratchpad
  (bibliography + 99 HKUST-1/CO2 paper folders) for a schema/unit survey.
- Downloaded CoRE MOF 2014-DDEC tar from Zenodo (md5 verified) into the scratchpad. Inventoried candidates.
- Found and reproduced a silent failure: CIF without `_atom_site_type_symbol` → RASPA3 reads 0 atoms, exit 0.
- Installed pytest 9.2.0 and pygaps 4.5.0 into `ads` with mamba (raspa3 still 3.0.29). pip is not in `ads`.
Verified: see RECON.md §1 (all UNVERIFIED items resolved).
Open questions: RECON.md §2 (D1–D5): regression target provenance, UiO-66 structure, Mg-MOF-74 choice,
whether to edit ~/projects/CLAUDE.md.
Mistake noted: `git ls-tree -l` on a blobless clone fetches every blob. Stopped after ~5 min, no harm.

## 2026-11-15: Gate 0 approved; structure and FF decisions
User decisions are recorded in RECON.md §2. My decisions:
- Mg-MOF-74 = CoRE 2014-DDEC `Mg-DOBDC.cif`. Its cell is the closest to the CSD-derived VOGTIV cell
  (CoRE 2019, `VOGTIV_clean_h_pacman.cif`): V 1311.6 vs 1321.6 Å³ (−0.8%), c 6.786 vs 6.759 Å.
  `MgMOF-74.cif` is V 1368.9 Å³ (+3.6%), c 6.942 Å (+2.7%), probably DFT-relaxed. Not used.
- UiO-66 = CoRE 2019 v2 (Zenodo 10.5281/zenodo.14184621, zip md5 f0af5f8c…) `CR/ASR/RUBTAK01_SL_pacman.cif`:
  computation-ready, manually curated ("SL"), formula Zr6 H28 C48 O32 = ideal Zr6O4(OH)4(BDC)6, PACMAN
  ML-DDEC6 charges, net charge 0. Alternative `RUBTAK03_auto` (conventional cell, a = 20.7465 Å, about 1%
  smaller lattice) is kept as a possible geometry-sensitivity check.
- Zn LJ: RASPA3's built-in MOF table (`forcefield.cpp`, labeled UFF) has Zn = 27.677 K / 4.04 Å. That is
  NOT UFF: Rappé 1992 Zn3+2 has x1 = 2.763 Å and D1 = 0.124 kcal/mol (checked in Open Babel UFF.prm and
  CP2K uff_table), i.e. 62.40 K / 2.4616 Å, matching the all-UFF example
  `advanced/5_tmmc_methane_in_tobacco_667` (62.39 / 2.46). The recipe uses the UFF value.

## 2026-11-15: Phase 1, Tool 1 and the HKUST-1 regression
Did:
- Built Tool 1 (raspa.py, runner.py, parse.py, fit.py, workflow.py, cli.py, report.py, units.py),
  prepared the 6 structures (scripts/prepare_structures.py) and wrote FORCEFIELD.md. 54 tests pass.
- Regression, old settings (example 11 unchanged, φ = 1.0, void fraction default 1.0, 1×1×1, Coulomb
  cutoff auto, 20k + 5k cycles, PrintEvery 1000). Inputs verified identical to the old run except
  `FugacityCoefficient: 1.0`. All 8 points pass vs the MISSION targets AND vs the on-disk PR numbers
  (results/HKUST-1/regression_table.csv).
- Corrected settings (Peng–Robinson, void fraction from raspa3-cli = 0.74575 ± 0.00051, 2 replicas
  of 10⁶ samples; everything else unchanged), plus a Widom-only run and a 1-molecule NVT run.
  Results in results/HKUST-1/regression_corrected_vs_old.csv.
Verified:
- Every run passed validation (624 framework atoms, net charge 0, finished, cycle count).
- Measured changes corrected − old are all within ±0.5 combined SE. The expected deterministic changes
  are −0.19 mmol/g (−1.5%) at 5 bar and < 0.5% below 2 bar, so 20k cycles cannot resolve them per point.
- ΔH₀ from 1-molecule NVT (−25.42 ± 0.31 kJ/mol) matches the GCMC fluctuation value at 0.01 bar
  (−25.45 ± 0.23). Widom K_H = 6.32 ± 0.16 mmol/g/bar vs Henry fit on 0.01–0.1 bar 6.00 ± 0.13.
  The fit is lower, as expected from curvature already present by 0.1 bar.
Observations for Phase 3:
- RASPA3 uses 5 blocks. The same 0.01 bar point gave rel. error 9.5% (old) and 2.7% (corrected), so the
  block error estimate is itself uncertain by tens of percent. 7 of 16 points exceed the 5% limit at 20k
  cycles; with auto-extension these would be re-run.
- Drift flag (2σ, halves of the production series) fired on 1/16 points (old, 2 bar), consistent
  with the expected false-positive rate of about 5%.
- Wall time per point (8 concurrent): 2 min (0.01 bar) to 19 min (5 bar) for 25k cycles, 624 atoms.

## 2026-11-15: Phase 2, Tool 2 on HKUST-1 CO2
Did:
- isodb.py (mirror at 9e1ee47, sparse checkout), clean.py (rules, ledger, consensus, outliers, Henry,
  Clausius–Clapeyron), compare.py, CLI `gcmc isodb` and `gcmc compare`. 80 tests pass.
- Ran: `bin/gcmc isodb --case HKUST-1 --gas CO2` (298 and 273 K) and
  `bin/gcmc compare --case HKUST-1 --gas CO2 --T 298 --T-second 273 --sim results/HKUST-1/CO2_298K_regression_corrected.csv`.
Bugs found and fixed on the way:
- Mirror folder names are lower-cased bibliography file stems, not "DOI without slash" (12 of 99
  HKUST-1/CO2 papers differ, e.g. 10.1007/s10450-015-9684-6 → 10.1007s1045001596846). With the fix:
  256 candidates, matching the Phase 0 survey (246 single-component + 10 mixtures). Papers that list
  no isotherms (18) have no folder and are skipped.
- A (0, 0) origin point was counted as a digitizer artifact (P == q). Now P ≤ 0 is dropped first.
- The first Clausius–Clapeyron attempt mixed the 273 K papers with the 298 K consensus of other
  papers and gave a physically impossible −72 kJ/mol. It is now computed per paper (same sample),
  only when a paper has exactly one isotherm at each temperature.
- Log–log interpolation in Clausius–Clapeyron (exact for Henry-law segments; the old version was off by 0.1%).
Decisions:
- The sample-flag rule (excluding only name flags and sample-state title words) is documented in
  clean.py. A record on the pristine hashkey inside a composite paper is that paper's reference sample.
- No API calls were needed beyond Phase 0. The mirror equals the API (Phase 0 check).
Open:
- 15 of the 50 pristine 298 K isotherms come from one paper (10.1021/La102359q, CO2/H2O on HKUST-1).
  Two of them are outliers at about 0.1 mmol/g at 1 bar, which may be water-preloaded samples. The records do not say.
- 10.1007/s10973-013-3497-1 ("Hydrogen production from bio-oil by chemical looping reforming") is
  filed under CuBTC in ISODB. The title does not fit and its isotherms are outliers. Possibly a misattributed DOI.

## 2026-11-15: Gate 2 approved; Phase 3 preparation
- User: keep the strict exp/sim rule; "safe option" for H2O in titles; bio-oil record stays (default).
- Safe option chosen: water/H2O words in titles flag aged_humid (excluded from the pristine consensus,
  kept and plotted). Effect for HKUST-1 CO2 298 K: pristine 50 → 34 isotherms (21 → 18 papers); the
  experimental Henry coefficient now rests on 1 isotherm. FINDINGS Phase 2 numbers updated.
- User is gaming: no RASPA3 runs until they say so. Only light work (ISODB fetch, setup, scripts).
- IRMOF-1 CO2 ISODB: 217 candidates; 298 K: 30 accepted (30 pristine); 273 K: 4 accepted.
- runner: per-run CPU time and peak memory via os.wait4 (status.json, points CSV). CPU seconds are the
  budget measure because they do not depend on other load (e.g. gaming). `--dry-run` added. 82 tests.
- Pilot ready to launch (not started): IRMOF-1 CO2 298 K, 10 points 0.01–10 bar, 2×2×2 primitive
  (848 atoms), 20k + 5k cycles, auto-extension on, Widom + NVT1. Waiting for the user's go-ahead.

## 2026-11-15: Phase 3, IRMOF-1 CO2 pilot and budget
Did:
- User gave the go-ahead (games done). Pilot: `bin/gcmc isotherm --case IRMOF-1 --gas CO2 --T 298 --label pilot`
  (20:36–21:17, 41 min wall on 8 jobs). Void fraction 0.80361 ± 0.00001. 2×2×2 primitive (848 atoms).
  Auto-extension re-ran 3 points (0.0215 bar ×3 for rel. error 7.5%; 1 and 2.15 bar ×2 for drift,
  3.3σ and 2.4σ). After extension: no drift flags, all rel. errors ≤ 4.1%.
- Cost: CPU per 25k-cycle point 66 s (0.01 bar) to 1939 s (10 bar). Isotherm total 4844 s GCMC + 368 s
  Widom/NVT1. Peak memory 75–76 MB per job. Wall ≈ CPU for every job (machine otherwise idle).
- Calibration (scripts/calibrate_cost.py): one 500+1000-cycle run at 10 bar for all 24 case/gas/T.
  All passed validation (MFI expands to 288 atoms as set in cases.yaml). results/budget/calibration.json.
  IRMOF-1 calibration predicts 2350 s for the 10-bar point vs 1939 s measured (20% high, conservative).
- Budget (scripts/budget.py → results/budget/budget.json): 20k+5k cycles: 53 CPU h, wall ~6.7 h at 8 jobs;
  longest single point (HKUST-1 CO2 273 K, 10 bar, if extended ×2) 3.7 h. 10k+5k: 31.5 CPU h (~3.9 h).
  40k+10k: 106 CPU h (~13 h).
Observations:
- Low-loading points (CH4/N2 at ≤ 0.1 bar, < 1 molecule in the box) cannot reach 5% relative error in
  any affordable run; under the current rule they all go to ×4. That is not in the 53 h (adds ~15 CPU h).
- Langmuir and DSL cannot fit the IRMOF-1 CO2 isotherm (convex, with an inflection toward 10 bar);
  the DSL fit fails to converge. Henry fit OK.
- Running isotherms one after another wastes cores (each waits for its 10-bar point). Phase 4 needs a
  single shared pool over all points, longest first.

## 2026-11-15/16 Phase 4: full matrix (branch phase4-matrix)
- Approved changes from Gate 3 implemented and tested before launch: no extension when < 1 molecule in the box
  (flagged "low loading"), rel_err = max(block SE, series SE), Quadratic fit model, one shared longest-first pool.
- First launch at 22:2x was stopped within 2 min: the helium void fraction was computed per gas (gas-dependent
  force field). Fixed to one framework-only calculation per structure (runs/_voidfraction/), relaunched 22:30.
- `gcmc matrix --label main --jobs 8`: 24 isotherms, 288 runs (240 GCMC points + 24 Widom + 24 NVT1).
  First pass estimated 38.3 CPU h; extension pass 100 runs (est. 28.1 CPU h) started 04:24; matrix done 07:52.
  Wall 9.4 h. GCMC points used 60.7 CPU h. 0 PROBLEM / COLLECT PROBLEM lines. 24/24 isotherms collected.
- Phase 5 sensitivity runs (scripts/phase5_runs.py, 63 runs) started automatically at 07:52 in tmux gcmc_phase5.

## 2026-11-16 Phase 5: section 7 tests (branch phase5-causes)
- phase5_analysis.py on `main` showed implausible experimental values (exp Henry 876, 281, 95 mmol/g/bar;
  HKUST-1 CO2 273 K sim/exp ≈ 11). Raw-record inspection: cryogenic-shaped isotherms labelled 298 K and 273 K
  isotherms below the 298 K data. Added clean.plausibility_flags (R1 supercritical apparent q/P > 20 mmol/g/bar
  below 0.1 bar; R2 temperature order vs the better-sampled other T) with 2 tests; 90 tests pass. Post hoc and
  disclosed; uses no simulation result. Headline (Gate-2) numbers are kept next to the screened ones.
- Added: low-pressure log-log slope test, abs/excess basis effect, sample-quality between/within split,
  GCMC-vs-Widom consistency at the lowest pressures, data-cleaning table, per-case 2x2 figures, overview figure.
- Findings drafted as F5.1–F5.14 (Gate 5 draft; user granted autonomy).
- Sensitivity runs: 63/63 OK, finished 11:26 (longest MFI bigcell 1 bar, 3.6 h). phase5_analysis.py rerun wrote
  sensitivity.csv; oms_snapshots.py wrote oms_snapshots.csv (MFI skipped: structure not P1). Findings F5.15–F5.18
  added (cause 4 rejected; cause 7 tested, no variant reconciles a disagreeing set; Mg-MOF-74 CO2 sits at Mg).

## 2026-11-16 Phase 6: report (branch phase5-causes)
- reports/REPORT.md completed (no pending items); README gains a report summary and full usage. 90 tests pass.
- Phase branches merged into main and pushed to origin (user approved push at the end of the work).
