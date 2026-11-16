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
results/HKUST-1/compare/CO2_298K_regression_corrected_vs_isodb_*.
- F2.1 Of 256 ISODB candidate isotherms (CuBTC hashkey, containing CO2), 51 pass at 298 ± 2 K,
  from 21 papers (50 pristine, 1 flagged for humidity). The main rejection reasons are temperature (118),
  not experimental (53 = 33 sim + 17 qua+sim + 3 mod+sim), ambiguous exp/sim labelling (14),
  mixtures (10), isotherm category 'sim' (8), and unit strings (2: mol/mol, kg/mol). Only 1/51 accepted
  records states a basis (absolute). The other 50 are 'unknown'.
- F2.2 9 of 50 pristine isotherms are low outliers (median uptake 6–32x below the consensus).
  Their sources include a paper whose title is unrelated to adsorption, a multicomponent study that also
  covers carbons and zeolites, bench-scale/ethanol-reflux syntheses, a doping study, and two isotherms from a
  CO2/H2O paper. MEASURED: they are outliers. HYPOTHESIS (untested): degraded/partially activated samples,
  water preloading, or misattributed records.
- F2.3 Experimental spread (IQR across papers, as a ratio q75/q25): about 1.34x below 0.1 bar, 1.54x
  at 0.1–1 bar, 2.67x above 1 bar with outliers. Without outliers: 1.21x, 1.37x, 1.22x. Below 0.016 bar
  only 1 paper contributes.
- F2.4 The example-11 model (Peng–Robinson, φ_He 0.7458) sits on the experimental median: ratio sim/exp
  median 1.04 (low), 1.07 (mid), 1.03 (high), with 80%, 91% and 67% of grid points inside the IQR (excess
  vs 'unknown' treated as excess). Without outliers: 1.01, 1.06, 0.99. This is the example-11 model with
  its undocumented charges, NOT the project recipe (DDEC charges, FIQCEN), which runs in Phase 4.
- F2.5 Henry coefficient: simulation (Widom) 6.32 ± 0.16 mmol/g/bar vs experiment 5.63 (IQR 5.16–5.76)
  from only 5 isotherms in 2 papers, 4 of them from one paper. Ratio 1.12. Weak experimental basis.
- F2.6 Clausius–Clapeyron: only one paper has one isotherm at each of 273 and 298 K, and it is the
  suspicious bio-oil record (Qst 46 → 20 kJ/mol over 0.25–3.25 mmol/g). Experimental heats for
  HKUST-1 CO2 cannot be judged from this ISODB set. The simulated ΔH₀ is 25.4 kJ/mol (F1.3).
