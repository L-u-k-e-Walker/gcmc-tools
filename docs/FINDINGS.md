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

## Phase 4 (full matrix, label `main`) and Phase 5 (section 7 tests) — Gate 5
Numbers from results/phase5/*.csv (scripts/phase5_analysis.py --label main) and results/<case>/*_main*.
"Ratio" = simulated excess / per-paper experimental consensus median, median over grid points in a regime
(low < 0.1 bar, mid 0.1–1 bar, high > 1 bar). "(n)" = fewest papers behind any grid point of that regime.

### Data artifacts (cause 1)
- F5.1 MEASURED: 11 of 188 pristine isotherms fail a post-hoc plausibility screen
  (clean.plausibility_flags; results/phase5/plausibility_flags.csv). R1 (physically impossible for a
  supercritical gas at 298 K, apparent q/P > 20 mmol/g/bar below 0.1 bar): 5 isotherms with q/P 394–2162,
  near-saturation shapes like 77 K isotherms (HKUST-1 CH4 and N2 from 10.1021/la800803w; IRMOF-1 N2 from
  10.1016/j.micromeso.2008.04.033; ZIF-8 N2 from 10.1021/am5028346). R2 (inconsistent with the
  better-sampled other temperature, i.e. loading not falling with T): all 3 HKUST-1 CO2 273 K isotherms, the only
  Mg-MOF-74 CO2 273 K isotherm, and 3 ZIF-8 CO2 298 K isotherms from 10.1039/C4ee01009d. The rule was written after
  inspecting the data; it uses no simulation result. R1 hits are near-certain metadata errors; R2 hits may be
  real sample differences (the ZIF-8 paper reports a series of samples).
- F5.2 MEASURED: these few records dominated several headline ratios. The Gate-2 low-pressure ratios were
  0.00 (IRMOF-1 N2), 0.01 (HKUST-1 CH4, ZIF-8 N2) and 0.19 (HKUST-1 N2); after screening they are –, 2.96 (1),
  0.52 (1) and 0.25 (1). The Gate-2 experimental Henry medians of 876, 281 and 95 mmol/g/bar (IRMOF-1 N2,
  HKUST-1 CH4, ZIF-8 N2) came from single R1 records. HKUST-1 CO2 273 K (Gate-2 ratio 10.7–12.1) has no usable
  experimental isotherm after screening. Cause 1: TESTED-SUPPORTED for these 6 case/gas/T sets.
- F5.3 MEASURED: in the low-pressure regime the consensus rests on 1 paper for 14 of the 17 screened sets that have data
  there (min papers per grid point). The low-pressure ratio is a single-lab comparison in most cases.
- F5.4 MEASURED: experimental log-log slopes below 0.1 bar (results/phase5/low_p_slopes.csv, 26 isotherms
  with >= 3 points over >= 0.5 decade) have median 0.77 (CO2 0.77, N2 0.84, CH4 0.65); 44–50 % are below 0.7.
  The simulated slopes over the same ranges are 0.97–1.01. HYPOTHESIS (not resolved): digitization error near the
  origin of linear-axis figures and real surface heterogeneity (defects, strong sites) both flatten the
  experimental curve; the data cannot separate them. Low slopes also occur at loadings well above any digitization
  floor (Mg-MOF-74 CO2), where they are physical.
- F5.5 MEASURED: the strict filter (|T − target| <= 0.5 K, no Tukey outliers, >= 5 points) changes mid-pressure
  ratios by at most 0.12 (IRMOF-1 CH4 0.48 → 0.60). It does not remove the R1 records (IRMOF-1 N2 stays at 0.00), so
  strictness of the temperature window and point count is not what drives the disagreements; metadata errors are.

### Basis and non-ideality (causes 2, 3)
- F5.6 MEASURED: absolute/excess simulated loading at 1 bar is 1.00–1.07 for CO2 and CH4 except IRMOF-1 CH4 (1.17), and
  1.05–1.39 for N2 (largest IRMOF-1, 1.39 at 1 bar, 1.43 at 10 bar). Only 7 of 207 accepted records state a basis (4 excess, 3 absolute).
  For CO2 the basis cannot explain disagreements larger than ~7 %; for N2 in IRMOF-1, ZIF-8 and HKUST-1 the
  basis ambiguity alone is 11–43 %. Cause 2: TESTED; matters only for N2 (and IRMOF-1 CH4).
- F5.7 MEASURED (computed, no new runs): using the ideal-gas law instead of Peng–Robinson raises the simulated
  loading by <= 0.9 % at 1 bar in every set, and by 0.3–8.7 % at 10 bar (largest IRMOF-1 CO2: 8.4 % at 298 K,
  8.7 % at 273 K; extrapolated over the last segment). Cause 3: TESTED-REJECTED as an explanation for any gap above
  ~10 %.

### Sample quality (cause 5)
- F5.8 MEASURED (results/phase5/sample_quality_summary.csv): between-isotherm spread of log10(exp/sim) exceeds
  the median within-isotherm spread in 14 of 16 sets (exceptions MFI CH4 and Mg-MOF-74 CO2) with >= 3 isotherms; the largest gaps are HKUST-1 CO2 298 K
  (0.50 vs 0.11, i.e. labs differ by ~3x in scale while each curve has roughly the simulated shape), IRMOF-1 CO2
  273 K (0.97 vs 0.06), UiO-66 N2 (0.63 vs 0.03), HKUST-1 N2 (0.28 vs 0.07) and IRMOF-1 CO2 298 K (0.22 vs 0.04).
  Experimental curves differing by a constant factor is the cause-5 signature. Proxy only: no record carries a
  pore volume or BET area, so the rescaling test of section 7 was not possible.
- F5.9 MEASURED: UiO-66 is the only material where experiment is below simulation in every regime for CO2
  (screened ratios 1.98 (1)/1.58 (3) at 298 K; 4.02 (1)/1.86 (3)/2.05 (1) at 273 K) and CH4 (1.92/1.57, 1 paper),
  with a nearly pressure-independent factor (median slope of the log ratio 0.07–0.17). Consistent with lost or
  inaccessible pore volume (cause 5) but equally with model overbinding (charges/LJ); see the sensitivity runs.

### Open metal sites (cause 6)
- F5.10 MEASURED: Mg-MOF-74 CO2 298 K shows the open-metal-site signature: screened ratio 0.09 (2) below 0.1 bar,
  0.54 (2) at 0.1–1 bar, 1.20 (1) above 1 bar; simulated Henry 9.53 ± 0.13 vs experimental median 55.6 mmol/g/bar
  (6 isotherms, 3 papers; ratio 0.17). The experimental curves bend over at < 0.1 bar (Langmuir-like) while the
  simulation is nearly linear up to 0.2 bar; within-isotherm spread (0.35) exceeds between-isotherm spread (0.16),
  i.e. a shape mismatch, not a scale factor. Mg-MOF-74 N2 is also low at all pressures (0.35 (1), 0.30 (3)).
- F5.11 MEASURED: HKUST-1 CO2 does NOT show it: screened ratios 0.94 (1)/0.79 (4)/0.93 (14); Henry 6.12 vs 6.31
  (1 isotherm). IRMOF-1 (no open metal site) is further below experiment at low pressure than HKUST-1 is anywhere
  (0.35 (1)/0.70 (3)/1.00 (3)), resting on 1 paper below 0.1 bar, so a low-pressure deficit alone does not
  identify open-metal-site physics. Cause 6: TESTED-SUPPORTED for Mg-MOF-74
  (CO2, probably N2); TESTED-REJECTED as a large effect for HKUST-1 CO2 with this model.

### Experiment-to-experiment spread
- F5.12 MEASURED: the interquartile range across papers (q75/q25) at 0.1–1 bar is 1.1–1.8x in every set with
  >= 2 papers there, except UiO-66 N2 (6.8x, 3 papers). Where only 1 paper contributes the IQR is undefined, and
  the "inside IQR" metric is 0 by construction; it is reported only where >= 2 papers overlap. A sim/exp ratio
  between 0.7 and 1.4 is within lab-to-lab spread for HKUST-1, IRMOF-1, ZIF-8 (CO2, CH4, N2 mid/high P).

### Heats of adsorption
- F5.13 MEASURED: per-paper Clausius–Clapeyron heats exist for 3 sets only: HKUST-1 CO2 27.0 kJ/mol (1 paper; its
  273 K records fail R2, so this value is not trustworthy), UiO-66 CO2 20.6 (2 papers), ZIF-8 CO2 10.1 (1 paper).
  Simulated −ΔH0: 25.6, 24.2 and 16.1 kJ/mol. Too thin to test the force field.

### Simulation precision (cause 4, part 1)
- F5.14 MEASURED: 147 of 240 matrix points still have relative error > 5 % after the capped extension pass
  (rel_err = max(block SE, series SE)); most are below 0.5 bar where the box holds < 2 molecules on average
  (up to 318 % at IRMOF-1 N2 0.02 bar). An independent check says these error bars are very conservative: the
  GCMC excess at 0.01 bar divided by the Widom Henry coefficient × fugacity is 0.69–1.01 (median 0.97) across all
  24 sets, and the deviation from 1 follows the excess correction (IRMOF-1 N2 0.69 where absolute/excess is
  1.39). The Widom K_H is precise to 0.1–15 % (UiO-66 N2 worst). The simulated side of the low-pressure comparison
  is therefore determined to ~5 %; the uncertainty there is experimental.

### Convergence and system size (cause 4, part 2)
- F5.15 MEASURED (results/phase5/sensitivity.csv; CO2 298 K, 0.1 and 1 bar, all 6 materials): 4x production
  cycles change the loading by a factor 0.992–1.020 (|z| <= 0.21); one extra unit cell per direction changes it by
  0.976–1.011 (|z| <= 0.46). Cause 4: TESTED-REJECTED; no reported gap comes from run length or box size.

### Charges and LJ set (cause 7)
- F5.16 MEASURED: switching framework charges off lowers CO2 loading at 0.1–1 bar to 0.24–0.33x in Mg-MOF-74,
  0.28–0.46x in MFI, 0.71–0.80x in UiO-66, 0.77–0.96x in HKUST-1, 0.81–0.83x in IRMOF-1 and 0.96–0.99x in ZIF-8.
  All-UFF framework LJ (instead of DREIDING H/C/N/O; MOFs only) changes it by 0.90–0.95x (Mg-MOF-74),
  1.04–1.13x (HKUST-1), 1.08–1.11x (IRMOF-1), 1.24–1.34x (UiO-66) and 2.18–2.24x (ZIF-8).
- F5.17 DERIVED (product of the screened mid-P ratio and the variant/main factor; approximate): neither variant
  reconciles a disagreeing set. UiO-66 CO2 (1.58) would become about 1.1–1.3 with no charges and 2.0–2.1 with
  UFF; ZIF-8 CO2 (1.00) would become about 2.2 with UFF; Mg-MOF-74 CO2 (0.54) would become about 0.13–0.18 with no
  charges and about 0.5 with UFF. The electrostatic term carries most of the CO2 binding in Mg-MOF-74 and MFI, so
  the charge set matters there; but removing charges only moves UiO-66 part-way, and the UFF set makes it worse.
  The ZIF-8 result shows the LJ choice for the organic linker can matter by 2x. Cause 7: TESTED; it can shift
  ratios substantially, but does not explain the UiO-66 overprediction with these two variants, and pushes
  Mg-MOF-74 further from experiment.

### Open metal sites, snapshots (cause 6, part 2)
- F5.18 MEASURED (results/phase5/oms_snapshots.csv; CO2 298 K, 0.1 bar, second half of 200 production frames):
  in Mg-MOF-74, 46 % of CO2 molecules have an O within 3.0 Å of Mg (74 % within 3.5 Å; median 3.04 Å). In
  HKUST-1 it is 2 % (7 % within 3.5 Å; median O–Cu 4.88 Å); IRMOF-1 1 %, ZIF-8 and UiO-66 0 %. MFI is not
  analysed (its structure is not in P1 form for the script). So the model already places CO2 at the open Mg
  site; what it lacks there is binding strength, not site geometry (Henry 0.17x, F5.10). In HKUST-1 the model
  CO2 mostly sits away from Cu at 0.1 bar, yet the isotherm agrees with experiment. HYPOTHESIS: the Cu sites
  contribute little to CO2 uptake at 298 K in this pressure range, or a missing Cu–CO2 term is compensated
  elsewhere in the model; these data cannot separate the two.
