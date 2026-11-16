# Findings

Each finding lists its evidence. Method-level facts are in RECON.md.

## Phase 0 (data and method facts)
- F0.1 Old HKUST-1 runs used helium void fraction 1.0 (the default). Evidence: output line
  `Helium void fraction: 1`, `Excess molecules: 0.44677` = PV/(ZkT) for the full cell.
- F0.2 Most ISODB records do not state excess vs absolute (240/246 HKUST-1 CO2 records empty).
  Evidence: survey in RECON.md §5.
- F0.3 Per-isotherm exp/sim labels are mostly missing in ISODB (192/246 empty). Paper-level labels
  must be used, and mixed papers are ambiguous. Evidence: RECON.md §5.

## Phase 1 (simulation method, HKUST-1 CO2 298 K, example-11 model)
- F1.1 Tool 1 reproduces the old isotherm. All 8 points are within 3 combined SE or 10% of both the
  MISSION targets and the on-disk values. Evidence: results/HKUST-1/regression_table.csv.
- F1.2 Gas non-ideality and the helium void fraction together change the excess loading by
  about −1.5% at 5 bar (fugacity −0.25 mmol/g, void fraction +0.06 mmol/g) and < 0.5% at ≤ 2 bar.
  These are computed from the deterministic terms and are not resolvable in the 20k-cycle runs (measured changes
  within ±0.5 SE). At 298 K, neither correction can explain sim-vs-exp differences larger than a few
  percent for CO2 in HKUST-1 up to 5 bar (10 bar not yet measured; φ ≈ 0.95 there). Evidence:
  results/HKUST-1/regression_corrected_vs_old.csv.
- F1.3 Zero-loading ΔH for CO2 in this model is −25.4 kJ/mol from two independent routes (1-molecule
  NVT −25.42 ± 0.31; GCMC fluctuation at 0.01 bar −25.45 ± 0.23). Evidence:
  results/HKUST-1/CO2_298K_regression_corrected.json, ..._points.csv.

## Phase 2 (experimental data, HKUST-1 CO2 298 K)
All numbers are from data/isodb_clean/HKUST-1_CO2_298K_ledger.csv and
results/HKUST-1/compare/CO2_298K_regression_corrected_vs_isodb_*. They use the cleaning rules as of
2026-11-15 19:37: strict exp/sim, and water/H2O/humid/aged words in titles flag a sample as non-pristine.
- F2.1 Of 256 ISODB candidate isotherms (CuBTC hashkey, containing CO2), 51 pass at 298 ± 2 K,
  from 21 papers. 34 are pristine (18 papers) and 17 flagged (aged_humid, mostly the 15 isotherms of
  10.1021/La102359q, a CO2/H2O paper). The main rejection reasons are temperature (118), not
  experimental (53 = 33 sim + 17 qua+sim + 3 mod+sim), ambiguous exp/sim labelling (14), mixtures (10),
  isotherm category 'sim' (8), and unit strings (2: mol/mol, kg/mol). Only 1/51 accepted records states
  a basis (absolute). The other 50 are 'unknown'.
- F2.2 7 of 34 pristine isotherms are low outliers (median uptake 6–28x below the consensus,
  log10 scores −0.77 to −1.44). Their sources include a paper whose title is unrelated to adsorption
  (bio-oil chemical looping), a multicomponent study that also covers carbons and zeolites, bench-scale
  ethanol-reflux syntheses, a doping study, and a semiconductor-MOF paper. MEASURED: they are outliers.
  HYPOTHESIS (untested): degraded/partially activated samples or misattributed records.
- F2.3 Experimental spread (IQR across papers, q75/q25): 1.99x below 0.1 bar, 1.79x at 0.1–1 bar,
  2.67x above 1 bar. Without outliers: 1.32x, 1.40x, 1.22x. Below 0.1 bar only 1–few papers
  contribute (min 1 at the lowest grid points).
- F2.4 The example-11 model (Peng–Robinson, φ_He 0.7458) is close to the experimental median: sim/exp
  median 1.07 (low), 1.05 (mid), 1.03 (high), with 88%, 100% and 67% of grid points inside the IQR
  (excess vs 'unknown' treated as excess). Without outliers: 0.89, 0.90, 0.99. This is the example-11
  model with its undocumented charges, NOT the project recipe (DDEC charges, FIQCEN), which runs in Phase 4.
- F2.5 Henry coefficient: after the water flag, only 1 pristine isotherm (1 paper) has >= 3 points
  at P <= 0.1 bar (6.31 mmol/g/bar vs simulated 6.32 ± 0.16). Before the flag it was 5 isotherms from
  2 papers (median 5.63). The experimental Henry coefficient for HKUST-1 CO2 is too thinly sampled in
  ISODB to test the simulation.
- F2.6 Clausius–Clapeyron: only one paper has one isotherm at each of 273 and 298 K, and it is the
  suspicious bio-oil record (Qst 46 → 20 kJ/mol over 0.25–3.25 mmol/g). Experimental heats for
  HKUST-1 CO2 cannot be judged from this ISODB set. The simulated ΔH₀ is 25.4 kJ/mol (F1.3).

## Phase 3 (IRMOF-1 CO2 298 K, project recipe: DDEC charges, UFF/DREIDING)
Numbers from results/IRMOF-1/CO2_298K_pilot*.csv/json and results/IRMOF-1/compare/CO2_298K_pilot_vs_isodb_*.
- F3.1 Simulated vs experimental consensus (30 pristine isotherms, 8 papers; 2 outliers): sim/exp median
  0.36 (< 0.1 bar), 0.70 (0.1–1 bar), 1.00 (> 1 bar); inside the IQR at 0%, 18%, 60% of grid points.
  Without outliers: 0.36, 0.61, 1.00. MEASURED: the simulation is below experiment at low pressure
  in a MOF without open metal sites, and agrees above 1 bar. Below ~0.05 bar the consensus rests on
  1–2 papers. Not yet interpreted (Phase 5).
- F3.2 The simulated Henry coefficient (Widom) is 0.814 ± 0.008 mmol/g/bar vs 0.61 from the only experimental
  isotherm with >= 3 points below 0.1 bar (ratio 1.34). This is the opposite direction from F3.1's low-pressure ratio,
  so the low-pressure experimental data disagree among themselves; the experimental side is too thin to resolve it.
- F3.3 Simulated ΔH0 = −14.6 ± 0.6 kJ/mol (1-molecule NVT), consistent with the fluctuation value at
  0.01 bar (−14.4). No paper has exactly one isotherm at each of 273 and 298 K, so no experimental
  Clausius–Clapeyron value.
- F3.4 The simulated isotherm is convex up to 10 bar (0.78 → 11.8 mmol/g from 1 to 10 bar). Langmuir and
  dual-site Langmuir cannot represent it; only the Henry fit is usable.
