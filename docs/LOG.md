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
