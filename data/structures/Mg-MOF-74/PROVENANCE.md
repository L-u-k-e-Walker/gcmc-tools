# Mg-MOF-74

- Source: CoRE MOF 2014-DDEC database (Nazarian, Camp, Sholl, Chem. Mater. 2016, 28, 785)
- Archive: core-mof-1.0-ddec.tar, Zenodo 10.5281/zenodo.3986573, md5 a2e3578003968739640b6faeed361299
- File in archive: `Mg-DOBDC.cif` (copied unchanged to `original/`)
- License: CC-BY-4.0
- Charges: DDEC (DFT: VASP, PBE), as stored in _atom_site_charge
- Notes: Non-CSD entry 'Mg-DOBDC'. Chosen over 'MgMOF-74.cif' because its cell is closest to CSD VOGTIV (CoRE 2019): V 1311.6 vs 1321.6 A^3; see docs/LOG.md.

## Checksums
- original `Mg-DOBDC.cif`: sha256 `0c80e2e605b14e0f5a1ab0de7a20cf264ea435a962acc0d96ba4c7b4555a459f`
- prepared `Mg-MOF-74.cif`: sha256 `b846974013d1eb5586abc2e27a9e6049f42273ed17cabe0ca69b8350aa7d06f7`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
- removed 1 non-CIF line(s) before data_ block
- added _atom_site_type_symbol column (element from label)

## Summary
- atoms in CIF: 54; elements: C, H, Mg, O; net charge: 0.000002 e
- cell: 6.7856, 15.1101, 15.1101, 117.8001, 98.6091, 98.6091
- perpendicular widths (A): 6.494, 12.938, 12.938
- unit cells for 12 A cutoff (minimum image): [4, 2, 2]
