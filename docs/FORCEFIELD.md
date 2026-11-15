# Force field

Every value here was read from a file in raspa3-src v3.0.29 (paths relative to
`~/projects/raspa3-src/`) or from a RASPA3 output that echoes what was actually used. Source
citations are the strings stored in those files. I have not checked the papers themselves.

## 1. What example 11 (Cu-BTC + CO2) actually is

Files: `examples/basic/11_mc_adsorption_of_co2_in_cu_btc/{force_field.json, CO2.json, Cu-BTC.cif, simulation.json}`.

| Item | Value | Where |
|---|---|---|
| Framework | rigid; Chui et al. Science 1999 Cu-BTC, Fm-3m, a = 26.343 Å, 624 atoms/cell, mass 9677.95 g/mol | CIF, output |
| Framework LJ | Cu1 UFF ε/k = 2.5161 K, σ = 3.11369 Å; O1 48.1581 K / 3.03315 Å; C1–C3 47.8562 K / 3.47299 Å; H1 7.64893 K / 2.84642 Å (DREIDING, Mayo 1990) | force_field.json `source` strings |
| Framework charges | Cu1 +1.248, O1 −0.624, C1 +0.494, C2 +0.130, C3 −0.156, H1 +0.156 e. The same values are in the CIF and in force_field.json. RASPA3 uses the force-field ones (`UseChargesFrom` default = pseudo-atoms). **No source is given for these charges in any file.** | force_field.json, CIF, input_reader.cpp:798 |
| CO2 | rigid, linear, 3 sites, C–O = 1.149 Å. C: 29.933 K / 2.745 Å, q +0.6512; O: 85.671 K / 3.017 Å, q −0.3256 ("A. Garcia-Sanchez et al., J. Phys. Chem. C 2009, 113, 8814-8820") | CO2.json, force_field.json |
| CO2 critical constants (for Peng–Robinson) | Tc 304.1282 K, Pc 7.3773 MPa, ω 0.22394 | CO2.json |
| Mixing | Lorentz–Berthelot for all unlike pairs (no explicit cross terms) | force_field.json |
| VDW cutoff | 12 Å, cut-and-shift (`"TruncationMethod": "shifted"`); shifts are small, e.g. Cu–Cu −0.003 K, C_co2–O1 −0.050 K | force_field.json, output "shift:" lines |
| Tail corrections | off | force_field.json, output |
| Electrostatics | Ewald, precision 1e-6. For 1×1×1 Cu-BTC: α = 0.2404 Å⁻¹, 7×7×7 k-vectors, real-space cutoff "auto" = half the box width = 13.17 Å | output |
| Polarization | none (all polarizabilities 0) | output |
| Moves | translation, rotation, CBMC reinsertion, CBMC swap, Widom (probabilities 0.5/0.5/0.5/1.0/1.0, normalized to 1/7, 1/7, 1/7, 2/7, 2/7) | simulation.json, output |
| Helium void fraction | not set, so **1.0** (default) | input_reader.cpp:935, output |
| Fugacity | example: `FugacityCoefficient 1.0` (ideal gas); old 298 K runs: key removed, so Peng–Robinson | example simulation.json; cubtc_isotherm/P_*/simulation.json |

## 2. The recipe used for all MOFs in this project

File: `src/gcmctools/templates/forcefield_recipe.json` (applied by `raspa.build_force_field`).

- **Framework LJ per element**, one pseudo-atom per element (CIF labels are matched by their
  element after digits are stripped):
  - DREIDING (Mayo 1990) for H, C, N, O. Values from raspa3-src `forcefield.cpp`
    (`makeMetalOrganicFrameworkForceField`); H, C, O are identical to example 11.
  - UFF (Rappé 1992) for Mg, Cu, Zr, from the same table; Cu is identical to example 11.
  - **Zn is the exception.** The raspa3-src built-in table labels Zn "UFF" but gives 27.677 K /
    4.04 Å. UFF Zn3+2 is D1 = 0.124 kcal/mol, x1 = 2.763 Å (checked in Open Babel `UFF.prm` and
    CP2K `uff_table`, both derived from Rappé 1992). That gives ε/k = 62.3992 K and σ = x1/2^(1/6) =
    2.46155 Å. The all-UFF example `advanced/5_tmmc_methane_in_tobacco_667` uses 62.39 / 2.46. We use
    the UFF value.
- **Framework charges from the CIF** (`"UseChargesFrom": "CIF_File"`):
  - HKUST-1, IRMOF-1, Mg-MOF-74, ZIF-8: DDEC charges from DFT (CoRE MOF 2014-DDEC, Nazarian et al. 2016).
  - UiO-66: DDEC6 charges **predicted by machine learning** (PACMAN, CoRE MOF 2019 v2), because the
    2014-DDEC set has no Zr structures. This is a different charge method. Any UiO-66 result has to say so.
- **Adsorbates** (same for every framework), from `examples/basic/12_*/force_field.json` and its
  molecule files:
  - CO2: as in §1.
  - N2: rigid, N at ±0.55 Å, N 38.298 K / 3.306 Å, q −0.405, plus a massless, LJ-free centre site at
    q +0.810 ("A. Martin-Calvo et al., Phys. Chem. Chem. Phys. 2011, 13, 11165").
  - CH4: united atom, 158.5 K / 3.72 Å ("M. G. Martin et al., J. Chem. Phys. 2001, 114, 7174", TraPPE).
  - All three carry Tc, Pc and ω for Peng–Robinson.
- **Same as example 11:** LB mixing, 12 Å cut-and-shift, no tail corrections, Ewald precision 1e-6.
- **Different from example 11, on purpose, for consistency across structures:** the Ewald real-space
  cutoff is set to **12 Å** (`CutOffCoulomb`) instead of "half the box", which would change with the
  supercell. `NumberOfUnitCells` is chosen so every perpendicular width is ≥ 24 Å.
- **Helium void fraction:** computed per structure with `raspa3-cli --void-fraction --energy`, using
  the same framework LJ and probe-He (10.9 K / 2.64 Å, Hirschfelder), Boltzmann average at 298 K
  (hard-coded in RASPA3).

## 3. MFI (method control)

It uses the framework model of example 10 instead of the MOF recipe:
- O 53.0 K / 3.30 Å, q −1.025; Si 22.0 K / 2.30 Å, q +2.05 ("P. Bai, M. Tsapatsis, J. I. Siepmann,
  J. Phys. Chem. C 2013, 117, 24375-24387").
- Charges come from the force field. The CIF has the same values.
- Same adsorbates, mixing, cutoffs and Ewald settings as §2.

## 4. What this model does not include (relevant to Section 7 of MISSION)
- No polarization and no special treatment of open metal sites (Cu, Mg). A 12-6 LJ term plus fixed
  point charges is all a CO2 molecule sees at a Cu or Mg site.
- Rigid framework, ideal crystal: no defects, no missing linkers (UiO-66), no flexibility or gate
  opening (ZIF-8), no residual solvent.
- Generic framework LJ (UFF/DREIDING) that was not fitted to any of these adsorbates.
