# Findings

No scientific conclusions yet (Phase 0 is recon only). Method-level facts that affect later
interpretation are in RECON.md. The ones most likely to matter:

- F0.1 Old HKUST-1 runs used helium void fraction 1.0 (default). Evidence: output line
  `Helium void fraction: 1`, `Excess molecules: 0.44677` = PV/(ZkT) for the full cell.
- F0.2 Most ISODB records do not state excess vs absolute (240/246 HKUST-1 CO2 records empty).
  Evidence: survey in RECON.md §5.
- F0.3 Per-isotherm exp/sim labels are mostly missing in ISODB (192/246 empty). Paper-level labels
  must be used, and mixed papers are ambiguous. Evidence: RECON.md §5.
