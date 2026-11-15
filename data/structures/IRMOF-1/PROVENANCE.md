# IRMOF-1

- Source: CoRE MOF 2014-DDEC database (Nazarian, Camp, Sholl, Chem. Mater. 2016, 28, 785)
- Archive: core-mof-1.0-ddec.tar, Zenodo 10.5281/zenodo.3986573, md5 a2e3578003968739640b6faeed361299
- File in archive: `EDUSIF_clean.cif` (copied unchanged to `original/`)
- License: CC-BY-4.0
- Charges: DDEC (DFT: VASP, PBE), as stored in _atom_site_charge
- Notes: CSD refcode EDUSIF. Primitive P1 cell, Zn8 H24 C48 O26.

## Checksums
- original `EDUSIF_clean.cif`: sha256 `390bcb8bec28aa752dfb5765bb34f9003a4d054905cfaf74ddc3c8c60b8e6e7a`
- prepared `IRMOF-1.cif`: sha256 `4348ba6ea4119fa5a53ff76d3420d0c9542d6129965b2981b77d4726ede03575`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
- removed 1 non-CIF line(s) before data_ block
- added _atom_site_type_symbol column (element from label)

## Summary
- atoms in CIF: 106; elements: C, H, O, Zn; net charge: 0.000000 e
- cell: 18.2660, 18.2660, 18.2660, 60.0000, 60.0000, 60.0000
- perpendicular widths (A): 14.914, 14.914, 14.914
- unit cells for 12 A cutoff (minimum image): [2, 2, 2]
