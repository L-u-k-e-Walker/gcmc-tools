# MFI

- Source: raspa3-src v3.0.29 examples/basic/10_mc_adorption_co2_in_mfi (van Koningsveld, van Bekkum, Jansen, Acta Cryst. B 1987, 43, 127)
- Archive: local read-only checkout ~/projects/raspa3-src (tag v3.0.29)
- File in archive: `MFI_SI.cif` (copied unchanged to `original/`)
- License: RASPA3 repository (MIT)
- Charges: Si +2.05, O -1.025 (Bai, Tsapatsis, Siepmann, J. Phys. Chem. C 2013, 117, 24375), taken from the example force_field.json (UseChargesFrom PseudoAtoms); the CIF carries the same values
- Notes: All-silica MFI (Pnma). Method control. Uses the example-10 TraPPE-zeo framework model, not the MOF recipe.

## Checksums
- original `MFI_SI.cif`: sha256 `1be57c99be89150670cde2b33f6e403f325090cb8f2a91aa498380a81c080f4b`
- prepared `MFI.cif`: sha256 `9122f0f6f60626a727b2182c2d0581299127c9ced735af79af3825c0602db80b`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
- none

## Summary
- atoms in CIF: 38; elements: O, Si; net charge: -2.050000 e
- cell: 20.0220, 19.8990, 13.3830, 90.0000, 90.0000, 90.0000
- perpendicular widths (A): 20.022, 19.899, 13.383
- unit cells for 12 A cutoff (minimum image): [2, 2, 2]
