# ZIF-8

- Source: CoRE MOF 2014-DDEC database (Nazarian, Camp, Sholl, Chem. Mater. 2016, 28, 785)
- Archive: core-mof-1.0-ddec.tar, Zenodo 10.5281/zenodo.3986573, md5 a2e3578003968739640b6faeed361299
- File in archive: `ZIF-8.cif` (copied unchanged to `original/`)
- License: CC-BY-4.0
- Charges: DDEC (DFT: VASP, PBE), as stored in _atom_site_charge
- Notes: Non-CSD entry 'ZIF-8'. Cubic a = 16.991 A, identical to the CSD OFERUN cell (CoRE 2019 OFERUN primitive a = 14.7138 = 16.991*sqrt(3)/2). Chosen over OFERUN04 (a = 17.054 A); see docs/LOG.md.

## Checksums
- original `ZIF-8.cif`: sha256 `df74c0839512586a225668843c9e363bb24ed76eaabd1aa92db616cc63c54f7b`
- prepared `ZIF-8.cif`: sha256 `6608f3746b0e2ca4bba5b6ccd91466e4469d8cd8182bd6609669fc3763c7301e`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
- removed 1 non-CIF line(s) before data_ block
- added _atom_site_type_symbol column (element from label)

## Summary
- atoms in CIF: 276; elements: C, H, N, Zn; net charge: 0.000009 e
- cell: 16.9910, 16.9910, 16.9910, 90.0000, 90.0000, 90.0000
- perpendicular widths (A): 16.991, 16.991, 16.991
- unit cells for 12 A cutoff (minimum image): [2, 2, 2]
