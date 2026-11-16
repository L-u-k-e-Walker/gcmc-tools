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
  within ±0.5 SE). For 0.01–10 bar at 298 K, neither correction can explain sim-vs-exp differences larger than a few
  percent for CO2 in HKUST-1. Evidence: results/HKUST-1/regression_corrected_vs_old.csv.
- F1.3 Zero-loading ΔH for CO2 in this model is −25.4 kJ/mol from two independent routes (1-molecule
  NVT −25.42 ± 0.31; GCMC fluctuation at 0.01 bar −25.45 ± 0.23). Evidence:
  results/HKUST-1/CO2_298K_regression_corrected.json, ..._points.csv.
