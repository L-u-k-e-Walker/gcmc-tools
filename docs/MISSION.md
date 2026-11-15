# MISSION: Understand how RASPA3 GCMC isotherms differ from experimental ISODB isotherms, and why

## 0. How to work
- This file is the source of truth. Re-read it at the start of every session.
- Keep `docs/LOG.md` (dated notes: what you did, what you verified, open questions) and
  `docs/FINDINGS.md` (conclusions, each with its evidence). Update both as you go.
- Work in phases (section 8). At every GATE, stop, summarize, and wait for my approval.
- Verify before you assume. Anything marked UNVERIFIED below must be checked against the
  actual files, docs, or API response before you build on it. Record what you found.
- If something blocks you (missing structure, ambiguous data, API down), stop and ask.
  Do not invent a workaround that changes the science.

## 1. Goal
Build two tools that work as one pipeline, then use them to investigate.
- Tool 1 (`gcmc isotherm`): CIF + gas + temperature + pressures -> RASPA3 GCMC isotherm
  with error bars, fits, Henry coefficient, heat of adsorption.
- Tool 2 (`gcmc isodb`, `gcmc compare`): fetch and clean experimental isotherms from NIST
  ISODB, normalize them, and quantify how simulation and experiment differ.
- Investigation: for a fixed set of common MOFs and gases (section 6), determine where
  simulation and experiment disagree, by how much, in which pressure regime, and which
  causes the evidence supports (section 7).
The deliverable is understanding, written up in `reports/REPORT.md`. Agreement between
simulation and experiment is NOT the goal. Never tune anything to make them agree.

## 2. Environment (verified by the user unless marked)
- WSL2 Ubuntu 24.04, user `lukew`, 20 cores (8 fast P-cores + 12 E-cores), 32 GB RAM
  (WSL capped at 26 GB), RTX 5060 Ti (not needed here).
- Conda (Miniforge). Use env `ads`: contains `raspa3` 3.0.29 from conda-forge. Do NOT
  upgrade or reinstall raspa3. You may pip/mamba install Python packages into `ads`
  (pandas, scipy, matplotlib, requests, pyyaml, pytest, pygaps). Export the env to
  `environment.yml` when done.
- `raspalib` (Python bindings) is version-mismatched with the examples. Do not use it.
  Drive RASPA3 through the `raspa3` CLI, which reads `simulation.json` in the cwd.
- RASPA3 source and examples: `~/projects/raspa3-src`, checked out at tag `v3.0.29`
  (must match the binary; newer examples use keywords this binary rejects). READ-ONLY.
- Prior work, READ-ONLY: `~/projects/cubtc_isotherm` (`run_isotherm.py`,
  `collect_isotherm.py`, `isotherm.csv`, `P_*Pa/` run folders). Template inputs came from
  `raspa3-src/examples/basic/11_mc_adsorption_of_co2_in_cu_btc`.
- Each `raspa3` process uses ONE core. Parallelism = many processes. Default max 8
  concurrent; never exceed 16.
- Output parsing that is known to work on 3.0.29 text output (take the LAST match):
  `Abs. loading average <val> +/- <err> [mol/kg-framework]`
  `Excess loading average <val> +/- <err> [mol/kg-framework]`
  `Average Henry coefficient: <val> +/- <err> [mol/kg/Pa]`
  A JSON output file also exists per run (`output/output_<T>_<P>.s0.json`); prefer it if
  it contains the same quantities (UNVERIFIED: inspect its keys).
- Heat/enthalpy of adsorption in the output: UNVERIFIED. Inspect a real output file and
  the RASPA3 docs to find what is printed and under which settings.
- Long runs: start them in a detached tmux session and poll; never block on them.
- Safety: no sudo. Write only inside `~/projects/gcmc-tools`. Never delete outside it.
- Git: this folder is its own repo. Work on feature branches, small commits, clear
  messages. Do not push until I say so. Remote will be
  `git@github.com:L-u-k-e-Walker/gcmc-tools.git` (private).
- Only public structures and public literature data. No proprietary data of any kind.

## 3. Architecture and the shared data contract
```
gcmc-tools/
  src/gcmctools/   raspa.py  runner.py  parse.py  fit.py  units.py
                   isodb.py  clean.py   compare.py  report.py  cli.py
  cases/cases.yaml           # section 6, machine-readable
  data/structures/<id>/      # CIF + PROVENANCE.md (source, DOI, charges, sha256)
  data/isodb_raw/            # cached raw API JSON, never edited
  data/isodb_clean/          # normalized isotherms + accept/reject ledger
  runs/                      # RASPA run folders (gitignored)
  results/                   # tidy CSVs (committed)
  reports/                   # REPORT.md + figures
  tests/   docs/
```
Both tools emit the SAME tidy table (one row per point), so compare never needs to know
where a row came from:
`material_id, adsorbate, T_K, P_bar, loading_mmol_g, loading_err_mmol_g, basis
(excess|absolute|unknown), source (sim|exp), source_id (run hash or ISODB filename),
doi, notes`
Plus one metadata JSON per isotherm (all settings for sim; all original fields and
original units for exp).

## 4. Tool 1: simulation
`gcmc isotherm --case <id>` or explicit `--cif --gas --T --pressures --cycles --init-cycles --jobs`.
Requirements:
1. Reproducible setup: generate each run folder from templates; hash all inputs; write a
   `run.json` manifest. Resumable: skip points whose output is complete; detect and
   re-run crashed or truncated points.
2. Supercell: choose `NumberOfUnitCells` automatically so every perpendicular cell width
   is >= 2 x the cutoff (minimum-image rule). Log the choice.
3. Fugacity: the old runs hard-coded `FugacityCoefficient: 1.0` (ideal gas). Find out
   from the 3.0.29 docs/source how RASPA3 computes fugacity when that key is omitted
   (UNVERIFIED: expected Peng-Robinson from critical constants). Default to the real-gas
   treatment; keep an `--ideal-gas` switch.
4. Excess adsorption and void fraction: in the old 1 bar run, absolute minus excess was
   0.447 molecules per unit cell, which equals P*V/kT for the WHOLE cell. That implies a
   void fraction of about 1.0 was used (probably a default). Confirm how 3.0.29 gets the
   helium void fraction, compute it properly for each structure (helium Widom insertion
   or the documented method), set it explicitly, and report how much excess changes.
5. Convergence: scale cycles with loading; report block-average errors; flag points where
   loading still drifts during production or the relative error exceeds 5%.
6. Outputs per isotherm: tidy CSV (absolute and excess), Henry coefficient, heat of
   adsorption (zero-loading from Widom and loading-dependent if RASPA prints it), fits
   (Henry, Langmuir, dual-site Langmuir; report parameters, uncertainties, residuals;
   prefer pyGAPS models if they fit the need), plot with error bars.
7. Force field: start from exactly what example 11 uses. Read those files and document
   in `docs/FORCEFIELD.md` what the model actually is (LJ source, charges source, CO2
   model, mixing rule, cutoff, tail corrections). Use one consistent recipe for all MOFs.
   For gases other than CO2, use the molecule definitions shipped in raspa3-src.

## 5. Tool 2: experimental data and comparison
ISODB facts: API base `https://adsorption.nist.gov/isodb/api`; one isotherm is at
`/isotherm/<filename>.json`; materials registry at `https://adsorption.nist.gov/matdb`.
NIST also mirrors the whole library on GitHub (`NIST-ISODB/isodb-library`); prefer a
one-time clone over thousands of API calls. `pygaps.parsing.isodb.isotherm_from_isodb`
exists. Field names, unit strings and category labels are UNVERIFIED: fetch a few real
records and inspect before writing the parser.
Requirements:
1. Cache every raw response under `data/isodb_raw/` and never modify it. Be polite to
   the API (cache first, <= 2 requests/s).
2. Material matching by alias table (section 6), preferably via the registry's material
   identifiers. Log every name that matched.
3. Keep only: experimental (not simulated or modeled), single-component, adsorption
   branch, temperature within the window (default +/- 2 K, configurable).
4. Units: strict allowlist with explicit, tested conversions to bar and mmol/g. Document
   each factor (e.g. cm3(STP)/g uses 22.414 cm3/mmol; state the STP convention). wt% is
   ambiguous (per g sorbent vs per g total): convert only if the record or paper states
   which, otherwise reject. Volumetric units that need a density: reject unless the
   density is given. Unknown unit string: reject. NEVER guess.
5. Basis: record excess/absolute if stated; otherwise `unknown` (most volumetric and
   gravimetric measurements are excess; treat unknown as excess only in clearly labeled
   analyses).
6. Ledger: `data/isodb_clean/ledger.csv` with one row per candidate isotherm: accepted or
   rejected, reason, original units, DOI. Nothing is dropped silently.
7. Sample flags from the record text: composite, pellet/shaped, functionalized, doped,
   mixed-metal, defect-engineered, aged or humid. Flagged samples are excluded from the
   "pristine" consensus but kept and plotted separately.
8. Consensus: on a common log-pressure grid, the median and interquartile range across
   accepted pristine isotherms, with the count of independent DOIs at each pressure.
   Outliers are flagged, not deleted.
9. `gcmc compare --case <id>`: overlay sim vs every exp curve and the consensus band;
   compute log10(sim/exp_median) by regime (low < 0.1 bar, mid 0.1 to 1 bar, high > 1
   bar) and whether sim falls inside the experimental IQR; compare Henry coefficients;
   where two exp temperatures exist, compare Clausius-Clapeyron heats.

## 6. Example cases (put in cases/cases.yaml)
Gases: CO2, CH4, N2. Temperature 298 K for all; add 273 K for CO2 (for heats).
Pressures: 10 log-spaced points, 0.01 to 10 bar.
| id | Aliases to match | Why it is in the set |
|---|---|---|
| MFI | silicalite-1, MFI, ZSM-5 (all-silica only) | Rigid, no metals; raspa3-src examples include it. Control for the method. |
| IRMOF-1 | MOF-5, IRMOF-1, Zn4O(BDC)3 | No open metal sites. Sample quality varies widely. |
| HKUST-1 | Cu-BTC, CuBTC, Cu3(BTC)2, MOF-199, Basolite C300 | Open Cu sites. Regression case from prior work. |
| Mg-MOF-74 | CPO-27-Mg, Mg2(dobdc), Mg/DOBDC | Very strong open Mg sites; expect large low-pressure error for CO2. |
| UiO-66 | UiO-66, UiO-66(Zr) (unfunctionalized only) | Missing-linker defects in real samples. |
| ZIF-8 | ZIF-8, MAF-4, Basolite Z1200 | Small cell (needs a supercell), flexible windows. |
Out of scope: water, H2 at 77 K, mixtures, flexible-framework simulation.
Structures: first inventory what raspa3-src ships (CIFs with charges). For the rest, use
a published computation-ready structure that includes atomic charges (e.g. the CoRE MOF
2019 set with DFT-derived charges) and record source, DOI, charge method and sha256 in
PROVENANCE.md. Never edit atomic positions or invent charges. If no defensible charged
structure can be found for a case, stop and ask me.

## 7. Investigation: candidate causes and how to test each
For every case, classify the disagreement, then test causes in this order (cheap,
artifact-type causes first). Mark each cause TESTED-SUPPORTED, TESTED-REJECTED, or
UNTESTED for that case.
1. Data artifacts: units, basis, temperature window, mislabeled or simulated records.
   Test: ledger review; redo the comparison with stricter filters.
2. Excess/absolute and void fraction. Test: compare with both bases; show the effect.
3. Gas non-ideality. Test: ideal vs real-gas fugacity runs.
4. Simulation convergence and size. Test: 4x cycles and a larger supercell on 2 or 3
   points per case.
5. Sample quality (pore volume lost to defects, collapse, residual solvent). Signature:
   exp below sim mostly at HIGH pressure, and exp curves that differ from each other by
   a roughly constant factor. Test: rescale by saturation-capacity ratio or reported
   pore volume / BET area if the record has it; state clearly this is a proxy.
6. Missing physics at open metal sites. Signature: sim below exp at LOW pressure for
   HKUST-1 and Mg-MOF-74 but not for IRMOF-1 or MFI. Test: Henry coefficients and
   low-pressure ratios across cases; snapshot analysis of where molecules sit (distance
   to nearest metal).
7. Charge and force-field sensitivity. Test: charges off; one alternative LJ set if
   available in raspa3-src. This measures sensitivity only. Do not pick the set that
   fits best and call it right.
8. Framework effects the rigid model cannot capture (UiO-66 defects, ZIF-8 flexibility).
   Usually UNTESTED here; say so, and note what experiment or simulation would test it.
Also quantify the experiment-to-experiment spread per case. If labs disagree with each
other by 2x, a 30% sim error is not interpretable; say that explicitly.

## 8. Phases and gates
Phase 0, recon (no code yet): inspect raspa3-src examples, molecule and force-field
  files, a real output file (text and JSON), the docs for fugacity, void fraction and
  enthalpy; fetch 3 to 5 ISODB records and write down the real schema and unit strings;
  check what pyGAPS already covers. Write `docs/RECON.md` and a build plan.
  GATE 0: show me RECON.md, the plan, and every UNVERIFIED item's resolution.
Phase 1, Tool 1 + regression. Reproduce the old HKUST-1 CO2 298 K run with the OLD
  settings (ideal gas, 1x1x1, 20,000 production + 5,000 initialization cycles). Target,
  excess mmol/g: 0.01 bar 0.061(3); 0.05 bar 0.291(11); 0.1 bar 0.540(4); 0.25 bar
  1.162(85); 0.5 bar 2.007(84); 1 bar 3.330(77); 2 bar 6.426(158); 5 bar 12.228(95).
  Pass = each point within 3 combined standard errors or 10%, whichever is larger (GCMC
  is stochastic). Then rerun with corrected fugacity and void fraction and report the
  change. Unit tests for parsing, supercell choice, resume logic, fits.
  GATE 1: regression table, corrected-settings table, test results.
Phase 2, Tool 2 on HKUST-1 CO2 only: fetch, clean, ledger, consensus, comparison plot.
  Unit tests for every unit conversion with hand-computed expected values.
  GATE 2: show the ledger summary (accepted/rejected by reason) and the plot.
Phase 3, pilot + budget: run IRMOF-1 CO2 end to end. Time it. Estimate wall-clock for the
  full matrix (6 materials x 3 gases at 298 K + CO2 at 273 K). Propose cycle counts.
  GATE 3: I approve the budget before the full matrix starts. Target: fits in one
  overnight run (<= 12 h) at 8 concurrent jobs; propose cuts if it does not.
Phase 4, full matrix in tmux, resumable. Then all comparisons.
Phase 5, section 7 tests, prioritized by which cases show the largest unexplained gaps.
  GATE 5: draft FINDINGS.md before writing the final report.
Phase 6, `reports/REPORT.md`: method, data-cleaning statistics, one figure and one
  paragraph per case, a summary table (case x regime: ratio, inside exp IQR or not,
  supported causes), ranked findings with evidence, limitations, next steps. Update the
  README with usage examples for both tools.

## 9. Rules
- No fabricated numbers, DOIs, structures, or citations. If you did not fetch or compute
  it, it does not go in the report.
- Separate what was measured from what is hypothesized, everywhere.
- Report negative and inconclusive results. "Cannot tell from this data" is acceptable.
- Every number in the report must be traceable to a file in `results/` or the ledger.
- Tests must pass before any gate. Do not weaken a test to make it pass.
- Prefer boring, readable code. No speculative features beyond this spec.