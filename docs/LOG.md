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
