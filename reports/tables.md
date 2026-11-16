# Generated tables (scripts/report_assets.py)

## Simulation vs experiment

Excess simulated uptake vs the per-paper experimental median ('unknown' basis treated as excess).

| Case | Gas | T (K) | exp isotherms (papers) | sim/exp < 0.1 bar | 0.1–1 bar | > 1 bar | inside exp IQR (low/mid/high) | exp IQR ratio (low/mid/high) | without outliers (low/mid/high) | strict filters (low/mid/high) |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| IRMOF-1 | CO2 | 298 | 30 (8) | 0.36 | 0.70 | 1.00 | 0/18/60% | 1.4/1.6/1.1 | 0.36/0.61/1.00 | 0.36/0.61/0.93 |

## Henry coefficients (mmol/g/bar)

| case    | gas   |   T_K |   sim_widom |   sim_widom_err |   exp_median |   exp_n_isotherms |   exp_n_papers |   sim_over_exp |
|:--------|:------|------:|------------:|----------------:|-------------:|------------------:|---------------:|---------------:|
| IRMOF-1 | CO2   |   298 |       0.814 |           0.008 |         0.61 |                 1 |              1 |          1.335 |

## Computed ideal-gas effect

| case    | gas   |   T_K |   P_bar |   phi |   q_real |   q_ideal |   ideal_over_real | note                                        |
|:--------|:------|------:|--------:|------:|---------:|----------:|------------------:|:--------------------------------------------|
| IRMOF-1 | CO2   |   298 |       1 | 0.995 |    0.783 |     0.787 |             1.006 | nan                                         |
| IRMOF-1 | CO2   |   298 |      10 | 0.946 |   11.826 |    12.817 |             1.084 | log-log extrapolation over the last segment |
