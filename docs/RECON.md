# Phase 0 recon

Date: 2026-11-15. Everything below was checked against files on disk, the RASPA3 v3.0.29 source
in `~/projects/raspa3-src`, real RASPA3 output in `~/projects/cubtc_isotherm/P_*Pa/output/`,
or live responses from ISODB, GitHub and Zenodo. Hypotheses are labeled as such.

## 1. Resolution of every UNVERIFIED item in MISSION.md

| # | MISSION item | Status | What I found | Evidence |
|---|---|---|---|---|
| U1 | JSON output contains the loadings/Henry | **Resolved: no** | `output_<T>_<P>.s0.json` has only `initialization` (component, force field, units, hardware info) and `output.{MCMoveStatistics, cpuTimings, drift, recomputedEnergies, runningEnergies}`. It has no loadings, Henry coefficient, or enthalpy. The text output must be parsed. The JSON is still useful for energy drift and CPU time. | `cubtc_isotherm/P_100000Pa/output/output_298_1e+05.s0.json` |
| U2 | Heat/enthalpy of adsorption in the output | **Resolved** | Every GCMC run prints `Enthalpy of adsorption: <v> +/- <e> [K]` and the same value in `[kJ/mol]`. It is the fluctuation formula ΔH = (⟨UN⟩−⟨U⟩⟨N⟩)/(⟨N²⟩−⟨N⟩²) − kT, with U = total energy (host–guest + guest–guest). It is loading-dependent and Qst = −ΔH. It always prints "Note: need to subtract the ideal-gas energy" because `idealGasEnergy` is never set from input. For rigid molecules (all three gases here) that intramolecular term is zero, so the printed value is complete. The **zero-loading** ΔH is not printed by Widom. Example 6 gets it from a 1-molecule NVT run (ΔH₀ = ⟨U_hg⟩ − kT for rigid molecules). | `src/raspakit/properties/enthalpy.cpp:16-56`, `enthalpy_of_adsorption_data.ixx:169-197`, `examples/basic/6_*` |
| U3 | Fugacity when `FugacityCoefficient` is omitted | **Resolved: Peng–Robinson** (confirmed) | `System` constructor always builds `EquationOfState(PengRobinson, VanDerWaals mixing)` from Tc, Pc and ω in the molecule JSON. The EOS value is used only when the key is absent. Two traps: (a) the input reader only accepts the key if it is a JSON **float** (`is_number_float()`), so `"FugacityCoefficient": 1` (an int) is **silently ignored** and PR is used; (b) the manual says a value of 0 means "use PR", but the code would store and use 0.0. To get PR, the tool omits the key; to get ideal gas it writes `1.0`. The bulk density and compressibility used for the excess correction **always** come from PR, even when φ is forced to 1.0. | `system.cpp:173-175`, `equation_of_states.cpp:24-130, 228-335`, `input_reader.cpp:547-553`, `docs/manual/commands.md:563-568` |
| U4 | Helium void fraction default and how to compute it | **Resolved** | Default is **1.0** when `HeliumVoidFraction` is absent (`input_reader.cpp:935`). This confirms MISSION §4.4: the old 1 bar run reports `Helium void fraction: 1` and `Excess molecules: 0.44677`, which equals P·V/(Z·kT) for the whole 18 280.8 Å³ cell with PR Z = 0.99451. RASPA3 ships `raspa3-cli --void-fraction --energy -f <ff.json> <cif>`. It averages exp(−βU_He) over random points (He LJ ε/k = 10.9 K, σ = 2.64 Å, Hirschfelder; **T is hard-coded to 298 K**, the usual convention). The probe must be a pseudo-atom named `probe-He` in the force field. **Cu-BTC (example 11 FF): 0.74638 at 10⁶ samples, 0.74623 at 2×10⁶ samples (13 s).** | `structure_properties/energy/void_fraction.cpp`, `cli/commandline.cpp:427-450`, scratch run |
| U5 | ISODB field names, unit strings, categories | **Resolved** (details in §4) | Real schema, unit strings and category labels below. Two important negatives: the per-isotherm `category` is usually **empty**, and `isotherm_type` (excess/absolute) is almost always **empty**. | 5 API records in `data/isodb_raw/api/`; survey of 246 HKUST-1/CO₂ isotherms from the GitHub mirror |
| U6 | Parsing regexes "known to work" | **Confirmed, with care needed** | Each loading line is printed in 4 units (molecules/cell, molecules/uc, mol/kg-framework, mg/g-framework), and Henry in 2 units (mol/kg/Pa, molec./uc/Pa). The parser must anchor on the unit in brackets and take the last block. Periodic status blocks print the running excess loading every `PrintEvery` cycles. That is what the drift check will read. | output text, lines 2061-2088 and 1714-1723 |

## 2. Discrepancies with MISSION.md that need your decision

**Gate 0 decisions (user, 2026-11-15):**
- D1: run the regression at φ = 1.0 and compare against both the MISSION targets and the on-disk PR numbers.
- D2/D3: UiO-66 comes from CoRE MOF 2019/2024 (experimental geometry, ML-predicted PACMAN DDEC6
  charges). This is a different charge method from the other MOFs and must be stated wherever UiO-66
  results appear.
- D4: my call (see LOG.md for the choice and its reasoning).
- D5: `~/projects/CLAUDE.md` is kept updated. It is the only write outside the project (noted in MISSION §2).
- FF recipe approved (§7 "Open choices").
- `kg/mol`: the safe option, i.e. reject as an ambiguous unit string, counted in the ledger.

**D1. The old HKUST-1 runs on disk did not use ideal gas.** `cubtc_isotherm/run_isotherm.py`
*removes* `FugacityCoefficient` (comment: "Real-gas correction … Peng-Robinson"). The run folders
print φ = 0.99945 … 0.842, and README/commit message say so too. The only old setting that matches
MISSION is the void fraction of 1.0.

**D2. The Phase 1 regression targets are not the numbers in `cubtc_isotherm/isotherm.csv`.**

| P (bar) | MISSION target (excess) | isotherm.csv on disk (excess, PR fugacity) | target/disk |
|---:|---:|---:|---:|
| 0.01 | 0.061(3) | 0.0629(37) | 0.970 |
| 0.05 | 0.291(11) | 0.2977(88) | 0.977 |
| 0.1 | 0.540(4) | 0.5438(359) | 0.993 |
| 0.25 | 1.162(85) | 1.1434(573) | 1.016 |
| 0.5 | 2.007(84) | 1.9902(380) | 1.008 |
| 1 | 3.330(77) | 3.3546(1812) | 0.993 |
| 2 | 6.426(158) | 6.2917(1022) | 1.021 |
| 5 | 12.228(95) | 11.9989(378) | 1.019 |

Hypothesis (not verified): the targets come from a different run with φ = 1.0. The +2% at 2 and
5 bar is about what 1/φ predicts (φ = 0.989 and 0.973). The git history of `cubtc_isotherm` has
only the PR version. Either set passes the 3σ-or-10% criterion against the other, so this does
not block Phase 1. It does change what "reproduce with OLD settings" means. **Proposal:** run
the regression with φ = 1.0 (as MISSION states), compare against your targets, and *also* report
the comparison with the on-disk PR numbers.

**D3. The CoRE MOF 2014-DDEC set has no UiO-66 (no Zr structures at all).** By MISSION §6 I
must stop and ask. Options:
- (a) QMOF database (Rosen et al., figshare DOI 10.6084/m9.figshare.13147324, CC-BY-4.0): DFT
  DDEC6 charges, but on **DFT-optimized** geometries, not experimental positions. I have not
  checked whether QMOF contains UiO-66.
- (b) CoRE MOF 2019/2024 (Zenodo 3677685 v2.0.0): experimental geometries, but charges are
  **ML-predicted** DDEC6 (PACMAN), not DFT.
- (c) Drop UiO-66 from the matrix.
- (d) A specific structure you prefer.

**D4. Two Mg-MOF-74 structures in the DDEC set, neither with a CSD refcode:** `Mg-DOBDC.cif`
(V = 1311.6 Å³) and `MgMOF-74.cif` (V = 1368.9 Å³, 4.4% larger). Both are Mg6 H6 C24 O18, P1,
neutral. I cannot tell from the files which is experimental. The archive's header line is the
same boilerplate on all 2,932 files (`'_srcid': 'CAKYAQ_clean'`), so it carries no provenance.
Pick one, or let me look for the Nazarian et al. 2016 SI table that maps these names to sources.

**D5. Writing outside the project.** `~/projects/CLAUDE.md` asks me to keep its project list
updated, but MISSION §2 says "write only inside `~/projects/gcmc-tools`". I have **not** edited
CLAUDE.md. Do you want me to add a `gcmc-tools/` entry there?

## 3. RASPA3 3.0.29 facts that shape Tool 1

### Inputs
- Strict key validation: unknown keys in `simulation.json` are a hard error (`validateInput`).
- Framework charges: system key `UseChargesFrom` defaults to **PseudoAtoms**, meaning charges come
  from `force_field.json`. `"CIF_File"` takes `_atom_site_charge`. The CIF atom → pseudo-atom match uses
  `_atom_site_label`. It tries the exact label first, then the label with digits stripped (`Cu1` → `Cu`).
  The manual's spelling of the default value, `PsuedoAtoms`, is a typo, so the tool never writes that value.
- Cutoffs: `CutOffVDW` (force field) = 12 Å in ex. 11. `CutOffCoulomb` defaults to **half the
  smallest perpendicular width** (13.17 Å for 1×1×1 Cu-BTC). With Ewald precision 10⁻⁶ the total
  electrostatics should not depend on this, but for one consistent recipe the new tool will set
  `CutOffCoulomb: 12.0` explicitly. The regression run keeps "auto" to match the old settings.
- RASPA3 does **not** check the minimum-image rule for simulations. The helper
  `smallestNumberOfUnitCellsForMinimumImagesConvention` exists but only the structure-property
  tools call it. The tool must choose `NumberOfUnitCells` itself (perpendicular width ≥ 2 × 12 Å).
- Swap moves are CBMC swaps by default (`Swap (CBMC)` in the move list).
- The old `run_isotherm.py` copied `restart_data.bin` into each run folder. It is not read without
  an explicit restart key. The new templates will not copy it.

### Silent-failure trap (important)
The DDEC CIFs have no `_atom_site_type_symbol` column. RASPA3 then reads **0 framework atoms**,
exits with status 0, and prints `Average Henry coefficient: inf`. I reproduced this on EDUSIF.
After adding a `_atom_site_type_symbol` column copied from the element label (positions and charges
verified byte-identical), it reads 106 atoms, net charge 0.00000, charges −1.262 … +1.104.
**Tool 1 will (a) write that column during structure preparation and record it in PROVENANCE.md,
and (b) after every run, check that the reported framework atom count and net charge match the CIF.**

### Outputs (3.0.29 text)
- `Abs. loading average <v> +/- <e> [mol/kg-framework]`, `Excess loading average …`: final
  block averages. Default is **5 blocks**, so the error bars are coarse.
- `Average Henry coefficient: <v> +/- <e> [mol/kg/Pa]`: from Widom insertions **in the current
  loaded system**. Only at near-zero loading is it the true Henry coefficient. The tool will get K_H
  from a dedicated Widom-only run (no swap moves, 0 molecules), as in example 12.
- `Enthalpy of adsorption: <v> +/- <e> [kJ/mol]`: see U2.
- Widom also prints `Measured fugacity` vs `Imposed fugacity`, a free consistency check (0.01 bar:
  967 ± 107 Pa measured vs 1000 Pa imposed).
- Old 1 bar run: block 0 = 35.1 molecules/uc vs 31.8–33.5 for blocks 1–4. That is a possible drift
  after only 5,000 initialization cycles. This is why the drift check is needed.

### Void fraction effect, preliminary
For Cu-BTC, φ_He 1.0 → 0.7463 lowers the subtracted bulk term by 25%. At 1 bar that is 0.447 → 0.333
molecules/uc, so excess rises by 0.113 molecules/uc = **0.0117 mmol/g (+0.35%)**. The effect grows
linearly with bulk density. At 10 bar it is about 0.12 mmol/g. This is an estimate from the formula;
Phase 1 will measure it.

### Timing of the old runs (11 concurrent jobs on mixed P/E cores, 25k cycles, Cu-BTC 1×1×1)
126 s (0.01 bar) → 334 s (1 bar) → 1,251 s (5 bar) → 1,670 s (30 bar). Cost scales with loading.

## 4. Structures and force field inventory

### Shipped in raspa3-src (with charges)
| Case | File | Charges | Notes |
|---|---|---|---|
| HKUST-1 | `examples/basic/11_*/Cu-BTC.cif` (Chui 1999, Fm-3m, a = 26.343 Å, 624 atoms) | in CIF **and** in `force_field.json` (Cu 1.248, O −0.624, C1 0.494, C2 0.130, C3 −0.156, H 0.156); source of these charges not stated in the files | regression case |
| IRMOF-1 | `examples/auxiliary/5_make_grids/IRMOF-1.cif` (Eddaoudi 2002, a = 25.832 Å) | in CIF (Zn 1.275, O1 −1.5, O2 −0.6, …); source not stated | the copy in `non_basic/1_*` has all charges 0; the copy in `auxiliary/4_*` has none |
| MFI | `MFI_SI.cif` (van Koningsveld 1987; one identical file in 11 examples) | Si 2.05, O −1.025 (Bai, Tsapatsis, Siepmann 2013 = TraPPE-zeo) | example 10 FF: O 53 K/3.30 Å, Si 22 K/2.30 Å |

### CoRE MOF 2014-DDEC (Nazarian, Camp, Sholl; Zenodo 10.5281/zenodo.3986573, CC-BY-4.0)
Downloaded `core-mof-1.0-ddec.tar` (19,688,960 B, md5 a2e3578003968739640b6faeed361299, matches
Zenodo). 2,932 P1 CIFs with VASP-PBE DDEC charges. Format: line 1 is a Python dict, not CIF; there is
no `_atom_site_type_symbol`; labels are bare elements.

| Case | Candidate | Formula | Cell | Perp. widths (Å) | Cells for 12 Å |
|---|---|---|---|---|---|
| HKUST-1 | FIQCEN_clean | Cu12 H24 C72 O48 | primitive rhombohedral, a = 18.627 Å | 15.21 ×3 | 2×2×2 (1,248 atoms) |
| IRMOF-1 | EDUSIF_clean | Zn8 H24 C48 O26 | primitive | 14.91 ×3 | 2×2×2 (848 atoms) |
| Mg-MOF-74 | Mg-DOBDC / MgMOF-74 (see D4) | Mg6 H6 C24 O18 | P1 | 6.49 / 12.94 / 12.94 | 4×2×2 (864 atoms) |
| ZIF-8 | ZIF-8.cif (a = 16.991) or OFERUN04 (a = 17.054) | Zn12 H120 C96 N48 | cubic | 16.99 | 2×2×2 (2,208 atoms) |
| UiO-66 | **none** (see D3) | | | | |

`OFERUN02_clean_h` (ZIF-8) has only H59 and is rejected as H-deficient. All candidates are
charge-neutral to 10⁻⁴ e.

### Molecules shipped (`data/molecules/example_definitions`, plus copies in the examples)
- CO₂: TraPPE-like 3-site rigid (C–O 1.149 Å); C 29.933 K/2.745 Å q +0.6512; O 85.671 K/3.017 Å q −0.3256 (García-Sánchez 2009).
- N₂: 3-site rigid (N at ±0.55 Å, massless charged COM); N 38.298 K/3.306 Å q −0.405, COM +0.810 (Martin-Calvo 2011).
- CH₄: united atom, 158.5 K/3.72 Å (TraPPE, Martin 2001).
All have Tc, Pc and ω for PR. Example 11 FF: Cu UFF (2.516 K/3.114 Å); O, C, H DREIDING; LB mixing;
cut-and-shift at 12 Å; no tail corrections; Ewald (precision 10⁻⁶).

## 5. ISODB: real schema, unit strings, categories

### Access
- Materials registry: `GET /isodb/api/materials.json` **redirects (302)** to
  `https://adsorption.nist.gov/matdb/api/materials.json`. 9,328 entries `{hashkey, name, synonyms}`.
- Gases: `/isodb/api/gases.json` → `{InChIKey, name, synonyms}`. CO₂ `CURLTUGMZLYLDI-UHFFFAOYSA-N`,
  CH₄ `VNWKTOKETHGBQD-UHFFFAOYSA-N`, N₂ `IJGRMHOSHXDMSA-UHFFFAOYSA-N`.
- Isotherm: `/isodb/api/isotherm/<filename>.json`.
- GitHub mirror `NIST-ISODB/isodb-library` (master @ 9e1ee47): about 54,400 files.
  `Library/<doi-folder>/<filename>.json` plus `Library/Bibliography/<doi>.json` (4,648),
  `Library/Adsorbents/` (9,328) and `Library/Adsorbates/` (455). For 3 sampled records,
  **mirror == API field for field and point for point.**

### Isotherm record schema (identical in API and mirror)
`filename, DOI, articleSource, date, digitizer, adsorbent{hashkey,name}, adsorbates[{InChIKey,name}],
category, temperature (K, usually integer), tabular_data (0/1), isotherm_type, adsorptionUnits,
pressureUnits, compositionType, concentrationUnits, isotherm_data[{pressure, total_adsorption,
species_data[{InChIKey, composition, adsorption}]}]`.
There is **no adsorption/desorption branch field**. Branch has to be inferred, e.g. from
non-monotonic pressure. None of the 246 surveyed records had non-monotonic pressure.

Bibliography record: `DOI, adsorbateGas, adsorbates, adsorbentMaterial, adsorbents[{hashkey,name}],
authors, categories[], isotherms[{filename}], journal, pressures, temperatures, title, year`.

### Survey: all 246 single-component CO₂ isotherms on hashkey `…991daf73…` (CuBTC) in 99 papers
- Per-isotherm `category`: **empty 192**, `exp` 45, `sim` 9. Paper-level `categories` (exp / sim /
  mod / qua, in combinations) is always filled. Empty-category isotherms come from papers labelled
  exp (98), sim (33), qua+sim (18), exp+sim (20), mod+exp (11), and others.
  ⇒ **Rule proposed:** accept as experimental only if the isotherm category is `exp`, OR it is empty
  and the paper's categories contain only exp (or exp+mod). Isotherms from mixed exp+sim papers with
  an empty category are rejected as "ambiguous exp/sim". No guessing.
- `isotherm_type`: empty 240, absolute 4, excess 2 ⇒ basis is mostly `unknown`.
- `pressureUnits`: **all `bar`**. ISODB appears to normalize pressure.
- `adsorptionUnits`: mmol/g 184, molecules/unitcell 24, **kg/mol 15**, cm3(STP)/g 7, mol/mol 3,
  cm3(STP)/cm3 2, wt% 2, mmol/cm3 2, mol/l 2, mol/m3 2, mol/m2 1, cm3/m2 1, mg/g 1.
  `kg/mol` is physically meaningless for an uptake. The values (e.g. 2.9 at 39 bar) look like mol/kg,
  but by the "never guess" rule it gets rejected unless you say otherwise.
- At 298 ± 2 K: 128 isotherms.
- Data defects found: `total_adsorption` is **null** in 5 records while
  `species_data[0].adsorption` holds the value (safe to use for single-component records).
  5 records have a point where adsorption equals pressure exactly, which is a digitizer artifact
  (e.g. `10.1039C0cc02771e.Isotherm1-1`). Exact duplicate data appears in 4 pairs, including the
  same isotherm under a bogus DOI prefix (`10.8888jp206959k` vs `10.1021jp206959k`).
  ⇒ dedupe by data content, flag adsorption==pressure points.
- Material matching: substring matching would be badly wrong (`Au@HKUST-1`, `1Na-HKUST-1`, `CNT@CuBTC`,
  …). Exact alias match on registry name+synonyms gives these hashkeys:

| Case | Hashkey(s) (name) |
|---|---|
| HKUST-1 | 991daf73… (CuBTC; synonyms include Basolite C300, Cu-BTC, Cu3(BTC)2, HKUST-1, MOF-199) |
| IRMOF-1 | 2c9380bd… (IRMOF-1 / MOF-5), e6c566b2… (Zn4O(BDC)3) |
| MFI | b342ae78… (MFI), 5d0728eb… (Silicalite MFI), 62df1ce0… (Silicalite-1), 0d52b431… (ZSM-5: needs per-record Si/Al check, so reject unless the record says all-silica) |
| Mg-MOF-74 | f5e80ffa… (Mg-MOF-74 / CPO-27-Mg …), f4b549a5… (Mg2(dobdc)) |
| UiO-66 | 5ab0dbe0… (UiO-66), 27ce47f7… (UiO-66(Zr)) |
| ZIF-8 | b2dc0287… (ZIF-8 / Basolite Z1200 / MAF-4) |

  Candidate papers (bibliography level): HKUST-1 CO₂ 99, CH₄ 70, N₂ 182; IRMOF-1 81/55/114;
  MFI 10/15/15; Mg-MOF-74 52/20/39; UiO-66 27/13/42; ZIF-8 51/37/81.

## 6. pyGAPS (4.5.0, installed from conda-forge into `ads` along with pytest 9.2.0)
- On Python 3.14 `import pygaps` fails (`importlib.util` used without import). The workaround is
  `import importlib.util` before `import pygaps`. No package patching needed.
- Models: Henry, Langmuir, DSLangmuir, TSLangmuir, BET, GAB, Freundlich, DA, DR, Quadratic,
  TemkinApprox, Virial, Toth, JensenSeaton, FHVST, WVST.
- `IsothermBaseModel.fit` uses unweighted `scipy.optimize.least_squares` and returns **no parameter
  covariance**. ⇒ fit.py will use `scipy.optimize.curve_fit` (weighted by RASPA errors,
  `absolute_sigma=True`) for parameters ± uncertainties, and cross-check against pyGAPS in tests.
- `isotherm_from_isodb` makes a live API call with a 5 s timeout and no cache, so it is not usable for
  the cached, ledgered pipeline. I will write my own parser.
- Unit table: `cm3(STP)` = 4.461×10⁻⁵ mol, i.e. 22.416 cm³/mmol. I will use **22.414 cm³/mmol (STP =
  273.15 K, 101.325 kPa)** as MISSION states, document it, and test it.
- Useful: `pygaps.characterisation.isosteric_enthalpy` (Clausius–Clapeyron from ≥2 temperatures),
  `initial_henry_*`.

## 7. Build plan (Phases 1–2 in detail, later phases as in MISSION)

**Repo setup.** `git init`, branch per phase (`phase0-recon`, `phase1-tool1`, …). `.gitignore`: `runs/`,
the full ISODB mirror clone (`data/isodb_raw/isodb-library/`), `__pycache__`. Committed: the cached
per-isotherm raw JSON actually used, ledger, results CSVs, figures. Package `src/gcmctools` with a
`gcmc` console entry point (installed via `pip install -e .` if pip can be added to `ads`, otherwise
run as `python -m gcmctools.cli`).

**Phase 1: Tool 1.**
1. `data/structures/<id>/`: CIF + PROVENANCE.md (source URL, DOI, license, sha256 of original and of
   prepared file, charge method, every format change made). The prepare step only strips the non-CIF
   header and adds `_atom_site_type_symbol`, with an automated check that positions and charges are
   unchanged.
2. `raspa.py`: write simulation.json, force_field.json and molecule files from templates (FF recipe
   from example 11, extended per element). Options: real gas (default, key omitted) or `--ideal-gas`
   (writes 1.0 float); explicit `HeliumVoidFraction`; `UseChargesFrom: CIF_File`; supercell from
   perpendicular widths; `CutOffCoulomb 12`; `PrintEvery` = cycles/20.
3. `runner.py`: one folder per point under `runs/<case>/<hash>/`, `run.json` manifest with sha256 of
   every input. Job pool ≤ 8 (hard cap 16), long jobs in detached tmux. Resume: a point is complete
   only if the final `LoadingData` block parses AND the framework atom count / net charge check passes;
   otherwise re-run.
4. `parse.py`: final loadings (unit-anchored), Henry, enthalpy, the measured-vs-imposed fugacity, the
   running-average series from status blocks (drift check: production slope or first-half vs
   second-half mean; flag > 2σ or rel. err > 5%), and the atom-count sanity check.
5. Separate runs per isotherm: helium void fraction (`raspa3-cli`), Widom-only K_H, 1-molecule NVT ΔH₀.
6. `fit.py`: Henry (low-P), Langmuir, DSL via curve_fit; pyGAPS cross-check. `units.py`: one tested
   module shared with Tool 2.
7. Regression: HKUST-1 ex. 11 inputs, 1×1×1, φ = 1.0, void fraction 1.0, 20k + 5k cycles, the 8 target
   pressures. Then corrected settings (PR, φ_He = 0.746) and the delta table.
8. `docs/FORCEFIELD.md`. Tests: parse (against the real old outputs), supercell choice, resume logic,
   fits on synthetic data, unit conversions.

**Phase 2: Tool 2 on HKUST-1 CO₂.** Sparse-checkout the mirror for the case's paper folders (no API
crawling). Cache under `data/isodb_raw/`. Clean with the exp/sim rule above, unit allowlist,
±2 K window, dedupe, sample flags from names/titles, ledger with one row per candidate. Consensus on
a log-P grid (median, IQR, n DOIs). Then `gcmc compare`.

**Open choices that the plan assumes unless you say otherwise:**
- One FF recipe for all MOFs: DREIDING (main group) + UFF (metals), LB, 12 Å cut-and-shift, no tail
  corrections, Ewald. **Charges: DDEC from CoRE 2014-DDEC for every MOF, HKUST-1 included** (FIQCEN),
  so charges are consistent across cases. Example 11's own charge set is kept for the regression and
  reused in Phase 5 as the "alternative charges" sensitivity test. MFI keeps its TraPPE-zeo model
  (example 10) as the method control.
- Basis "unknown" is treated as excess only in labeled analyses (per MISSION).
