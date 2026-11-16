# gcmc-tools

Two tools that work as one pipeline. Tool 1 runs RASPA3 GCMC isotherms. Tool 2 cleans
experimental isotherms from NIST ISODB. Together they are used to study how and why simulated
isotherms of common MOFs and zeolites differ from experiment. `docs/MISSION.md` is the plan.
`docs/RECON.md`, `docs/FORCEFIELD.md`, `docs/LOG.md` and `docs/FINDINGS.md` record what was
checked and found.

Status: Tool 1 (Phase 1) is in progress. Tool 2 is not built yet.

## Requirements
- Conda env `ads` with `raspa3` 3.0.29 (conda-forge), pandas, scipy, matplotlib, pyyaml, pytest, pygaps.
- `~/projects/raspa3-src` checked out at tag `v3.0.29`. Read only; it is used for force-field
  provenance and the example-11 regression inputs.
- tmux, for long runs.

## Tool 1: `gcmc isotherm`

```bash
# A case from cases/cases.yaml (structure, recipe and provenance are in data/structures/<id>/)
bin/gcmc isotherm --case IRMOF-1 --gas CO2 --T 298 --jobs 8

# The same, detached in tmux (log: runs/<case>/<gas>_<T>K/<label>/driver.log)
bin/gcmc isotherm --case IRMOF-1 --gas CO2 --T 298 --detach

# An explicit charged P1 CIF (MOF recipe; charges must be in the CIF)
bin/gcmc isotherm --cif my.cif --gas CH4 --T 298 --pressures 0.1 1 10 --cycles 20000 --init-cycles 5000

# Re-collect results and the plot for a finished run folder
bin/gcmc collect runs/IRMOF-1/CO2_298K/real_vf-auto
```

Defaults:
- Peng–Robinson fugacity (`--ideal-gas` for φ = 1).
- Helium void fraction computed with `raspa3-cli` (`--void-fraction default` omits it, which means
  1.0; or pass a number).
- Unit cells chosen so every perpendicular width is ≥ 2 × 12 Å.
- Ewald real-space cutoff 12 Å.
- Points that end above 5% relative error, or show drift, are re-run once with more cycles
  (`--no-extend` turns this off).
- Each isotherm also gets a Widom-only run (Henry coefficient) and a one-molecule NVT run
  (zero-loading enthalpy).

What it does:
1. Every point is a folder `runs/<case>/<gas>_<T>K/<label>/gcmc/gcmc_<P>Pa_<hash>/` whose name
   carries a hash of all inputs. `run.json` lists the settings and the sha256 of every file.
2. Re-running the same command skips complete points and re-runs crashed or truncated ones. The old
   output is kept as `output.failed-N`. A point is complete only if the output finished, the framework
   atom count matches the CIF and the net charge is zero. This catches RASPA3 silently reading 0
   atoms from a CIF that has no `_atom_site_type_symbol`.
3. It writes `results/<case>/<gas>_<T>K_<label>.csv`, a tidy table with one row per point and basis
   (`material_id, adsorbate, T_K, P_bar, loading_mmol_g, loading_err_mmol_g, basis, source, source_id,
   doi, notes`). Also `..._points.csv` (fugacity coefficient, void fraction, drift, enthalpy, cycles,
   wall time), `....json` (settings, Henry coefficient, ΔH₀, Henry/Langmuir/DSL fits with
   uncertainties) and `....png`.

## Tests
```bash
conda run -n ads python -m pytest -q
```
