# HKUST-1

- Source: CoRE MOF 2014-DDEC database (Nazarian, Camp, Sholl, Chem. Mater. 2016, 28, 785)
- Archive: core-mof-1.0-ddec.tar, Zenodo 10.5281/zenodo.3986573, md5 a2e3578003968739640b6faeed361299
- File in archive: `FIQCEN_clean.cif` (copied unchanged to `original/`)
- License: CC-BY-4.0
- Charges: DDEC (DFT: VASP, PBE), as stored in _atom_site_charge
- Notes: CSD refcode FIQCEN (Chui et al., Science 1999). Primitive rhombohedral P1 cell.

## Checksums
- original `FIQCEN_clean.cif`: sha256 `00d4fa2d9a36239860aadb91bd1d830eb680cdd1a10be35176815cd4a3c48480`
- prepared `HKUST-1.cif`: sha256 `c30b1311cbbcaaeb4375bcf8b4bacd953adab518703accac8750c8e9b9f6f602`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
- removed 1 non-CIF line(s) before data_ block
- added _atom_site_type_symbol column (element from label)

## Summary
- atoms in CIF: 156; elements: C, Cu, H, O; net charge: -0.000000 e
- cell: 18.6273, 18.6273, 18.6273, 60.0000, 60.0000, 60.0000
- perpendicular widths (A): 15.209, 15.209, 15.209
- unit cells for 12 A cutoff (minimum image): [2, 2, 2]
