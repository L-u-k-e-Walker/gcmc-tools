# Generated tables (scripts/report_assets.py)

## Simulation vs experiment

Excess simulated uptake / per-paper experimental consensus median, median over grid points in each regime ('unknown' basis treated as excess). (papers) = fewest papers behind any grid point in the regime. Screened = Gate-2 selection minus results/phase5/plausibility_flags.csv.

| Case | Gas | T (K) | exp isotherms: Gate 2 → screened | sim/exp < 0.1 bar (papers) | 0.1–1 bar (papers) | > 1 bar (papers) | exp IQR/median ratio 0.1–1 bar | Gate-2 headline (low/mid/high) | strict (low/mid/high) |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| MFI | CH4 | 298 | 3 → 3 | 0.64 (1) | 0.74 (2) | 0.84 (2) | 1.2 | 0.64/0.74/0.84 | 0.64/0.80/– |
| MFI | CO2 | 273 | 0 | no experimental data | | | | | |
| MFI | CO2 | 298 | 0 | no experimental data | | | | | |
| MFI | N2 | 298 | 0 | no experimental data | | | | | |
| IRMOF-1 | CH4 | 298 | 10 → 10 | 0.08 (1) | 0.48 (1) | 0.85 (6) | 1.5 | 0.08/0.48/0.85 | –/0.60/0.79 |
| IRMOF-1 | CO2 | 273 | 4 → 4 | 0.10 (2) | 0.56 (2) | – | 1.1 | 0.10/0.56/– | 0.13/0.56/– |
| IRMOF-1 | CO2 | 298 | 30 → 30 | 0.35 (1) | 0.70 (3) | 1.00 (3) | 1.6 | 0.35/0.70/1.00 | 0.35/0.61/0.93 |
| IRMOF-1 | N2 | 298 | 3 → 2 | – | 1.33 (1) | 1.02 (1) | 1.0 | 0.00/0.00/1.02 | 0.00/0.00/– |
| HKUST-1 | CH4 | 298 | 23 → 22 | 2.96 (1) | 1.45 (1) | 0.98 (7) | 1.7 | 0.01/1.45/0.98 | 0.01/1.45/0.98 |
| HKUST-1 | CO2 | 273 | 3 → 0 | – | – | – | – | –/10.72/12.05 | –/10.72/12.05 |
| HKUST-1 | CO2 | 298 | 34 → 34 | 0.94 (1) | 0.79 (4) | 0.93 (14) | 1.8 | 0.94/0.79/0.93 | 0.80/0.75/0.89 |
| HKUST-1 | N2 | 298 | 17 → 16 | 0.25 (1) | 0.99 (5) | 1.13 (6) | 1.3 | 0.19/0.99/1.13 | 0.25/1.03/1.14 |
| Mg-MOF-74 | CH4 | 298 | 2 → 2 | – | 0.72 (1) | 0.94 (1) | 1.0 | –/0.72/0.94 | –/0.72/0.94 |
| Mg-MOF-74 | CO2 | 273 | 1 → 0 | – | – | – | – | 0.91/2.17/– | 0.91/2.17/– |
| Mg-MOF-74 | CO2 | 298 | 8 → 8 | 0.09 (2) | 0.54 (2) | 1.20 (1) | 1.2 | 0.09/0.54/1.20 | 0.09/0.56/1.41 |
| Mg-MOF-74 | N2 | 298 | 3 → 3 | 0.35 (1) | 0.30 (3) | – | 1.2 | 0.35/0.30/– | 0.35/0.30/– |
| UiO-66 | CH4 | 298 | 1 → 1 | 1.92 (1) | 1.57 (1) | – | 1.0 | 1.92/1.57/– | 1.92/1.57/– |
| UiO-66 | CO2 | 273 | 5 → 5 | 4.02 (1) | 1.86 (3) | 2.05 (1) | 1.5 | 4.02/1.86/2.05 | 4.02/1.86/1.15 |
| UiO-66 | CO2 | 298 | 4 → 4 | 1.98 (1) | 1.58 (3) | – | 1.1 | 1.98/1.58/– | 1.98/1.58/– |
| UiO-66 | N2 | 298 | 3 → 3 | 1.13 (3) | 1.28 (3) | – | 6.8 | 1.13/1.28/– | 1.13/1.28/– |
| ZIF-8 | CH4 | 298 | 5 → 5 | 1.37 (1) | 1.14 (2) | 0.97 (1) | 1.3 | 1.37/1.14/0.97 | 1.37/1.14/0.74 |
| ZIF-8 | CO2 | 273 | 11 → 11 | 0.61 (1) | 1.00 (4) | 0.93 (1) | 1.8 | 0.61/1.00/0.93 | 0.61/1.00/0.93 |
| ZIF-8 | CO2 | 298 | 12 → 9 | 0.57 (1) | 1.00 (2) | 1.17 (2) | 1.2 | 0.42/1.00/1.17 | 0.42/1.00/1.16 |
| ZIF-8 | N2 | 298 | 6 → 5 | 0.52 (1) | 0.90 (2) | 1.52 (1) | 1.8 | 0.01/0.78/1.52 | 0.52/0.90/1.52 |

## Data cleaning (ISODB candidates per case/gas/T)

A record can be a candidate for several targets (e.g. a 273 K isotherm is a temperature rejection for the 298 K target). Sample-flagged = accepted but with a sample-state flag in the title (shaped, aged/humid); these are shown but excluded from the consensus.

| Case | Gas | T (K) | candidates | temperature | not experimental | ambiguous exp/sim | mixture / other gas | units | duplicate | < 3 points | accepted | sample-flagged | pristine (papers) | removed by screen | used |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MFI | CO2 | 298 | 24 | 11 | 6 | 1 | 6 | 0 | 0 | 0 | 0 | 0 | 0 (0) | 0 | 0 |
| MFI | CO2 | 273 | 24 | 18 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 (0) | 0 | 0 |
| MFI | CH4 | 298 | 42 | 18 | 4 | 0 | 17 | 0 | 0 | 0 | 3 | 0 | 3 (3) | 0 | 3 |
| MFI | N2 | 298 | 28 | 11 | 3 | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 (0) | 0 | 0 |
| IRMOF-1 | CO2 | 298 | 217 | 103 | 54 | 15 | 8 | 5 | 1 | 1 | 30 | 0 | 30 (8) | 0 | 30 |
| IRMOF-1 | CO2 | 273 | 217 | 198 | 1 | 2 | 8 | 4 | 0 | 0 | 4 | 0 | 4 (3) | 0 | 4 |
| IRMOF-1 | CH4 | 298 | 85 | 24 | 34 | 3 | 10 | 3 | 1 | 0 | 10 | 0 | 10 (9) | 0 | 10 |
| IRMOF-1 | N2 | 298 | 151 | 127 | 11 | 1 | 8 | 0 | 1 | 0 | 3 | 0 | 3 (3) | 1 | 2 |
| HKUST-1 | CO2 | 298 | 256 | 118 | 61 | 14 | 10 | 2 | 0 | 0 | 51 | 17 | 34 (18) | 0 | 34 |
| HKUST-1 | CO2 | 273 | 256 | 239 | 0 | 1 | 10 | 3 | 0 | 0 | 3 | 0 | 3 (2) | 3 | 0 |
| HKUST-1 | CH4 | 298 | 178 | 113 | 23 | 4 | 9 | 5 | 0 | 1 | 23 | 0 | 23 (12) | 1 | 22 |
| HKUST-1 | N2 | 298 | 296 | 226 | 40 | 0 | 13 | 0 | 0 | 0 | 17 | 0 | 17 (13) | 1 | 16 |
| Mg-MOF-74 | CO2 | 298 | 138 | 78 | 28 | 14 | 7 | 2 | 0 | 0 | 9 | 1 | 8 (5) | 0 | 8 |
| Mg-MOF-74 | CO2 | 273 | 138 | 130 | 0 | 0 | 7 | 0 | 0 | 0 | 1 | 0 | 1 (1) | 1 | 0 |
| Mg-MOF-74 | CH4 | 298 | 65 | 41 | 13 | 3 | 4 | 2 | 0 | 0 | 2 | 0 | 2 (2) | 0 | 2 |
| Mg-MOF-74 | N2 | 298 | 52 | 43 | 5 | 0 | 1 | 0 | 0 | 0 | 3 | 0 | 3 (3) | 0 | 3 |
| UiO-66 | CO2 | 298 | 75 | 55 | 2 | 8 | 4 | 1 | 0 | 0 | 5 | 1 | 4 (4) | 0 | 4 |
| UiO-66 | CO2 | 273 | 75 | 53 | 0 | 13 | 4 | 0 | 0 | 0 | 5 | 0 | 5 (5) | 0 | 5 |
| UiO-66 | CH4 | 298 | 37 | 28 | 1 | 2 | 4 | 1 | 0 | 0 | 1 | 0 | 1 (1) | 0 | 1 |
| UiO-66 | N2 | 298 | 70 | 64 | 1 | 2 | 0 | 0 | 0 | 0 | 3 | 0 | 3 (3) | 0 | 3 |
| ZIF-8 | CO2 | 298 | 113 | 65 | 9 | 26 | 0 | 1 | 0 | 0 | 12 | 0 | 12 (5) | 3 | 9 |
| ZIF-8 | CO2 | 273 | 113 | 95 | 0 | 6 | 0 | 0 | 1 | 0 | 11 | 0 | 11 (6) | 0 | 11 |
| ZIF-8 | CH4 | 298 | 71 | 44 | 7 | 9 | 2 | 4 | 0 | 0 | 5 | 0 | 5 (4) | 0 | 5 |
| ZIF-8 | N2 | 298 | 124 | 108 | 1 | 7 | 2 | 0 | 0 | 0 | 6 | 0 | 6 (6) | 1 | 5 |
| **all** | | | **2845** | **2010** | **304** | **131** | **154** | **33** | **4** | **2** | **207** | **19** | **188** | **11** | **177** |

## Henry coefficients (mmol/g/bar)

| case      | gas   |   T_K |   sim_widom |   sim_widom_err |   exp_median |   exp_n_isotherms |   exp_n_papers |   sim_over_exp |   scr_exp_median |   scr_exp_n_isotherms |   scr_sim_over_exp |
|:----------|:------|------:|------------:|----------------:|-------------:|------------------:|---------------:|---------------:|-----------------:|----------------------:|-------------------:|
| HKUST-1   | CH4   |   298 |       1.7   |           0.025 |      280.835 |                 1 |              1 |          0.006 |          nan     |                     0 |            nan     |
| HKUST-1   | CO2   |   273 |      16.119 |           0.383 |      nan     |                 0 |              0 |        nan     |          nan     |                   nan |            nan     |
| HKUST-1   | CO2   |   298 |       6.115 |           0.075 |        6.308 |                 1 |              1 |          0.969 |            6.308 |                     1 |              0.969 |
| HKUST-1   | N2    |   298 |       0.379 |           0.005 |        0.761 |                 5 |              4 |          0.499 |            0.539 |                     4 |              0.703 |
| IRMOF-1   | CH4   |   298 |       0.387 |           0.001 |        3.987 |                 1 |              1 |          0.097 |            3.987 |                     1 |              0.097 |
| IRMOF-1   | CO2   |   273 |       1.396 |           0.026 |       52.536 |                 3 |              2 |          0.027 |           52.536 |                     3 |              0.027 |
| IRMOF-1   | CO2   |   298 |       0.81  |           0.01  |        0.61  |                 1 |              1 |          1.329 |            0.61  |                     1 |              1.329 |
| IRMOF-1   | N2    |   298 |       0.197 |           0     |      875.767 |                 1 |              1 |          0     |          nan     |                     0 |            nan     |
| MFI       | CH4   |   298 |       0.645 |           0.004 |        0.976 |                 1 |              1 |          0.661 |            0.976 |                     1 |              0.661 |
| Mg-MOF-74 | CH4   |   298 |       1.013 |           0.001 |      nan     |                 0 |              0 |        nan     |          nan     |                     0 |            nan     |
| Mg-MOF-74 | CO2   |   273 |      26.226 |           1.578 |       23.311 |                 1 |              1 |          1.125 |          nan     |                   nan |            nan     |
| Mg-MOF-74 | CO2   |   298 |       9.53  |           0.129 |       55.638 |                 6 |              3 |          0.171 |           55.638 |                     6 |              0.171 |
| Mg-MOF-74 | N2    |   298 |       0.356 |           0.004 |        0.932 |                 2 |              2 |          0.381 |            0.932 |                     2 |              0.381 |
| UiO-66    | CH4   |   298 |       1.372 |           0.01  |      nan     |                 0 |              0 |        nan     |          nan     |                     0 |            nan     |
| UiO-66    | CO2   |   273 |      13.851 |           0.899 |        6.919 |                 2 |              2 |          2.002 |            6.919 |                     2 |              2.002 |
| UiO-66    | CO2   |   298 |       5.594 |           0.293 |        2.82  |                 1 |              1 |          1.984 |            2.82  |                     1 |              1.984 |
| UiO-66    | N2    |   298 |       0.339 |           0.05  |        0.256 |                 3 |              3 |          1.324 |            0.256 |                     3 |              1.324 |
| ZIF-8     | CH4   |   298 |       0.439 |           0.003 |        0.235 |                 1 |              1 |          1.867 |            0.235 |                     1 |              1.867 |
| ZIF-8     | CO2   |   273 |       1.387 |           0.016 |        3.686 |                 2 |              2 |          0.376 |            3.686 |                     2 |              0.376 |
| ZIF-8     | CO2   |   298 |       0.761 |           0.005 |        2.611 |                 3 |              2 |          0.291 |            0.634 |                     1 |              1.199 |
| ZIF-8     | N2    |   298 |       0.152 |           0.001 |       94.616 |                 2 |              2 |          0.002 |            0.183 |                     1 |              0.831 |

## Computed ideal-gas effect

| case      | gas   |   T_K |   P_bar |   phi |   q_real |   q_ideal |   ideal_over_real | note                                        |
|:----------|:------|------:|--------:|------:|---------:|----------:|------------------:|:--------------------------------------------|
| HKUST-1   | CH4   |   298 |       1 | 0.998 |    0.941 |     0.942 |             1.002 | nan                                         |
| HKUST-1   | CH4   |   298 |      10 | 0.978 |    4.636 |     4.709 |             1.016 | log-log extrapolation over the last segment |
| HKUST-1   | CO2   |   273 |       1 | 0.993 |    4.577 |     4.611 |             1.007 | nan                                         |
| HKUST-1   | CO2   |   273 |      10 | 0.93  |   16.159 |    16.351 |             1.012 | log-log extrapolation over the last segment |
| HKUST-1   | CO2   |   298 |       1 | 0.995 |    2.397 |     2.408 |             1.005 | nan                                         |
| HKUST-1   | CO2   |   298 |      10 | 0.946 |   13.124 |    13.485 |             1.028 | log-log extrapolation over the last segment |
| HKUST-1   | N2    |   298 |       1 | 1     |    0.31  |     0.31  |             1     | nan                                         |
| HKUST-1   | N2    |   298 |      10 | 0.996 |    1.936 |     1.943 |             1.003 | log-log extrapolation over the last segment |
| IRMOF-1   | CH4   |   298 |       1 | 0.998 |    0.333 |     0.334 |             1.002 | nan                                         |
| IRMOF-1   | CH4   |   298 |      10 | 0.978 |    3.161 |     3.23  |             1.022 | log-log extrapolation over the last segment |
| IRMOF-1   | CO2   |   273 |       1 | 0.993 |    1.401 |     1.412 |             1.008 | nan                                         |
| IRMOF-1   | CO2   |   273 |      10 | 0.93  |   24.143 |    26.234 |             1.087 | log-log extrapolation over the last segment |
| IRMOF-1   | CO2   |   298 |       1 | 0.995 |    0.774 |     0.779 |             1.006 | nan                                         |
| IRMOF-1   | CO2   |   298 |      10 | 0.946 |   11.864 |    12.861 |             1.084 | log-log extrapolation over the last segment |
| IRMOF-1   | N2    |   298 |       1 | 1     |    0.141 |     0.141 |             1     | nan                                         |
| IRMOF-1   | N2    |   298 |      10 | 0.996 |    1.267 |     1.272 |             1.004 | log-log extrapolation over the last segment |
| MFI       | CH4   |   298 |       1 | 0.998 |    0.515 |     0.515 |             1.002 | nan                                         |
| MFI       | CH4   |   298 |      10 | 0.978 |    1.842 |     1.856 |             1.008 | log-log extrapolation over the last segment |
| MFI       | CO2   |   273 |       1 | 0.993 |    2.331 |     2.334 |             1.001 | nan                                         |
| MFI       | CO2   |   273 |      10 | 0.93  |    3.024 |     3.038 |             1.005 | log-log extrapolation over the last segment |
| MFI       | CO2   |   298 |       1 | 0.995 |    1.68  |     1.683 |             1.002 | nan                                         |
| MFI       | CO2   |   298 |      10 | 0.946 |    2.716 |     2.734 |             1.007 | log-log extrapolation over the last segment |
| MFI       | N2    |   298 |       1 | 1     |    0.132 |     0.132 |             1     | nan                                         |
| MFI       | N2    |   298 |      10 | 0.996 |    0.84  |     0.843 |             1.003 | log-log extrapolation over the last segment |
| Mg-MOF-74 | CH4   |   298 |       1 | 0.998 |    0.969 |     0.971 |             1.002 | nan                                         |
| Mg-MOF-74 | CH4   |   298 |      10 | 0.978 |    6.31  |     6.4   |             1.014 | log-log extrapolation over the last segment |
| Mg-MOF-74 | CO2   |   273 |       1 | 0.993 |   12.078 |    12.095 |             1.001 | nan                                         |
| Mg-MOF-74 | CO2   |   273 |      10 | 0.93  |   15.893 |    15.967 |             1.005 | log-log extrapolation over the last segment |
| Mg-MOF-74 | CO2   |   298 |       1 | 0.995 |    8.019 |     8.036 |             1.002 | nan                                         |
| Mg-MOF-74 | CO2   |   298 |      10 | 0.946 |   14.227 |    14.326 |             1.007 | log-log extrapolation over the last segment |
| Mg-MOF-74 | N2    |   298 |       1 | 1     |    0.32  |     0.32  |             1     | nan                                         |
| Mg-MOF-74 | N2    |   298 |      10 | 0.996 |    2.492 |     2.501 |             1.004 | log-log extrapolation over the last segment |
| UiO-66    | CH4   |   298 |       1 | 0.998 |    0.849 |     0.851 |             1.001 | nan                                         |
| UiO-66    | CH4   |   298 |      10 | 0.978 |    2.911 |     2.942 |             1.011 | log-log extrapolation over the last segment |
| UiO-66    | CO2   |   273 |       1 | 0.993 |    4.044 |     4.054 |             1.002 | nan                                         |
| UiO-66    | CO2   |   273 |      10 | 0.93  |    7.242 |     7.345 |             1.014 | log-log extrapolation over the last segment |
| UiO-66    | CO2   |   298 |       1 | 0.995 |    2.649 |     2.655 |             1.002 | nan                                         |
| UiO-66    | CO2   |   298 |      10 | 0.946 |    5.847 |     5.933 |             1.015 | log-log extrapolation over the last segment |
| UiO-66    | N2    |   298 |       1 | 1     |    0.27  |     0.27  |             1     | nan                                         |
| UiO-66    | N2    |   298 |      10 | 0.996 |    1.428 |     1.431 |             1.003 | log-log extrapolation over the last segment |
| ZIF-8     | CH4   |   298 |       1 | 0.998 |    0.407 |     0.408 |             1.002 | nan                                         |
| ZIF-8     | CH4   |   298 |      10 | 0.978 |    2.988 |     3.04  |             1.018 | log-log extrapolation over the last segment |
| ZIF-8     | CO2   |   273 |       1 | 0.993 |    1.562 |     1.576 |             1.009 | nan                                         |
| ZIF-8     | CO2   |   273 |      10 | 0.93  |    8.652 |     8.848 |             1.023 | log-log extrapolation over the last segment |
| ZIF-8     | CO2   |   298 |       1 | 0.995 |    0.784 |     0.788 |             1.006 | nan                                         |
| ZIF-8     | CO2   |   298 |      10 | 0.946 |    6.377 |     6.617 |             1.038 | log-log extrapolation over the last segment |
| ZIF-8     | N2    |   298 |       1 | 1     |    0.129 |     0.129 |             1     | nan                                         |
| ZIF-8     | N2    |   298 |      10 | 0.996 |    1.064 |     1.068 |             1.004 | log-log extrapolation over the last segment |

## Records removed by the plausibility screen

| case      | gas   |   T_K | source_id                                | doi                             | reason                                                                      |
|:----------|:------|------:|:-----------------------------------------|:--------------------------------|:----------------------------------------------------------------------------|
| HKUST-1   | CH4   |   298 | 10.1021la800803w.Isotherm28              | 10.1021/la800803w               | R1: apparent q/P 965 mmol/g/bar at P <= 0.1 bar (supercritical gas)         |
| HKUST-1   | CO2   |   273 | 10.1007s10973-013-3497-1.Isotherm2       | 10.1007/s10973-013-3497-1       | R2: below the 298 K experimental consensus at 95% of 21 overlapping points  |
| HKUST-1   | CO2   |   273 | 10.1016j.micromeso.2012.05.021.Isotherm5 | 10.1016/j.micromeso.2012.05.021 | R2: below the 298 K experimental consensus at 86% of 14 overlapping points  |
| HKUST-1   | CO2   |   273 | 10.1016j.micromeso.2012.05.021.Isotherm6 | 10.1016/j.micromeso.2012.05.021 | R2: below the 298 K experimental consensus at 93% of 14 overlapping points  |
| HKUST-1   | N2    |   298 | 10.1021la800803w.Isotherm26              | 10.1021/la800803w               | R1: apparent q/P 394 mmol/g/bar at P <= 0.1 bar (supercritical gas)         |
| IRMOF-1   | N2    |   298 | 10.1016j.micromeso.2008.04.033.isotherm1 | 10.1016/j.micromeso.2008.04.033 | R1: apparent q/P 2162 mmol/g/bar at P <= 0.1 bar (supercritical gas)        |
| Mg-MOF-74 | CO2   |   273 | 10.1016j.poly.2015.01.031.Isotherm5      | 10.1016/j.poly.2015.01.031      | R2: below the 298 K experimental consensus at 100% of 21 overlapping points |
| ZIF-8     | CO2   |   298 | 10.1039C4ee01009d.Isotherm20             | 10.1039/C4ee01009d              | R2: above the 273 K experimental consensus at 100% of 9 overlapping points  |
| ZIF-8     | CO2   |   298 | 10.1039C4ee01009d.Isotherm21             | 10.1039/C4ee01009d              | R2: above the 273 K experimental consensus at 93% of 15 overlapping points  |
| ZIF-8     | CO2   |   298 | 10.1039C4ee01009d.Isotherm22             | 10.1039/C4ee01009d              | R2: above the 273 K experimental consensus at 89% of 19 overlapping points  |
| ZIF-8     | N2    |   298 | 10.1021Am5028346.Isotherm2               | 10.1021/Am5028346               | R1: apparent q/P 1623 mmol/g/bar at P <= 0.1 bar (supercritical gas)        |

## Sensitivity runs (variant / main, z-score)

| case      | variant     |   P_bar |   main |   main_err |   variant_value |   variant_err |   ratio |       z |
|:----------|:------------|--------:|-------:|-----------:|----------------:|--------------:|--------:|--------:|
| HKUST-1   | bigcell     |    0.1  |  0.461 |      0.027 |           0.46  |         0.02  |   1     |  -0.006 |
| HKUST-1   | bigcell     |    1    |  2.397 |      0.056 |           2.421 |         0.04  |   1.01  |   0.342 |
| HKUST-1   | charges_off |    0.01 |  0.06  |      0.015 |           0.062 |         0.013 |   1.04  |   0.118 |
| HKUST-1   | charges_off |    0.1  |  0.461 |      0.027 |           0.444 |         0.027 |   0.964 |  -0.436 |
| HKUST-1   | charges_off |    1    |  2.397 |      0.056 |           1.846 |         0.095 |   0.77  |  -4.994 |
| HKUST-1   | cycles4x    |    0.1  |  0.461 |      0.027 |           0.461 |         0.038 |   1.002 |   0.016 |
| HKUST-1   | cycles4x    |    1    |  2.397 |      0.056 |           2.408 |         0.079 |   1.004 |   0.107 |
| HKUST-1   | uff         |    0.01 |  0.06  |      0.015 |           0.07  |         0.018 |   1.175 |   0.447 |
| HKUST-1   | uff         |    0.1  |  0.461 |      0.027 |           0.522 |         0.031 |   1.134 |   1.492 |
| HKUST-1   | uff         |    1    |  2.397 |      0.056 |           2.483 |         0.087 |   1.036 |   0.831 |
| IRMOF-1   | bigcell     |    0.1  |  0.075 |      0.018 |           0.075 |         0.01  |   0.992 |  -0.029 |
| IRMOF-1   | bigcell     |    1    |  0.774 |      0.074 |           0.756 |         0.035 |   0.976 |  -0.226 |
| IRMOF-1   | charges_off |    0.01 |  0.008 |      0.004 |           0.006 |         0.004 |   0.809 |  -0.238 |
| IRMOF-1   | charges_off |    0.1  |  0.075 |      0.018 |           0.061 |         0.018 |   0.815 |  -0.544 |
| IRMOF-1   | charges_off |    1    |  0.774 |      0.074 |           0.642 |         0.046 |   0.829 |  -1.515 |
| IRMOF-1   | cycles4x    |    0.1  |  0.075 |      0.018 |           0.076 |         0.016 |   1.005 |   0.017 |
| IRMOF-1   | cycles4x    |    1    |  0.774 |      0.074 |           0.781 |         0.047 |   1.009 |   0.076 |
| IRMOF-1   | uff         |    0.01 |  0.008 |      0.004 |           0.009 |         0.004 |   1.14  |   0.175 |
| IRMOF-1   | uff         |    0.1  |  0.075 |      0.018 |           0.083 |         0.017 |   1.105 |   0.317 |
| IRMOF-1   | uff         |    1    |  0.774 |      0.074 |           0.839 |         0.069 |   1.084 |   0.638 |
| MFI       | bigcell     |    0.1  |  0.344 |      0.018 |           0.337 |         0.009 |   0.981 |  -0.323 |
| MFI       | bigcell     |    1    |  1.68  |      0.031 |           1.687 |         0.012 |   1.004 |   0.202 |
| MFI       | charges_off |    0.01 |  0.038 |      0.005 |           0.01  |         0.003 |   0.252 |  -4.798 |
| MFI       | charges_off |    0.1  |  0.344 |      0.018 |           0.096 |         0.012 |   0.279 | -11.533 |
| MFI       | charges_off |    1    |  1.68  |      0.031 |           0.766 |         0.038 |   0.456 | -18.6   |
| MFI       | cycles4x    |    0.1  |  0.344 |      0.018 |           0.344 |         0.022 |   1.002 |   0.021 |
| MFI       | cycles4x    |    1    |  1.68  |      0.031 |           1.681 |         0.034 |   1.001 |   0.033 |
| Mg-MOF-74 | bigcell     |    0.1  |  0.988 |      0.064 |           0.98  |         0.037 |   0.992 |  -0.103 |
| Mg-MOF-74 | bigcell     |    1    |  8.019 |      0.179 |           8.109 |         0.075 |   1.011 |   0.464 |
| Mg-MOF-74 | charges_off |    0.01 |  0.096 |      0.019 |           0.023 |         0.011 |   0.243 |  -3.327 |
| Mg-MOF-74 | charges_off |    0.1  |  0.988 |      0.064 |           0.24  |         0.036 |   0.243 | -10.203 |
| Mg-MOF-74 | charges_off |    1    |  8.019 |      0.179 |           2.642 |         0.122 |   0.329 | -24.854 |
| Mg-MOF-74 | cycles4x    |    0.1  |  0.988 |      0.064 |           1.008 |         0.076 |   1.02  |   0.199 |
| Mg-MOF-74 | cycles4x    |    1    |  8.019 |      0.179 |           8.059 |         0.108 |   1.005 |   0.193 |
| Mg-MOF-74 | uff         |    0.01 |  0.096 |      0.019 |           0.085 |         0.018 |   0.881 |  -0.438 |
| Mg-MOF-74 | uff         |    0.1  |  0.988 |      0.064 |           0.889 |         0.076 |   0.9   |  -0.996 |
| Mg-MOF-74 | uff         |    1    |  8.019 |      0.179 |           7.629 |         0.141 |   0.951 |  -1.71  |
| UiO-66    | bigcell     |    0.1  |  0.51  |      0.054 |           0.502 |         0.022 |   0.984 |  -0.136 |
| UiO-66    | bigcell     |    1    |  2.649 |      0.081 |           2.661 |         0.036 |   1.004 |   0.13  |
| UiO-66    | charges_off |    0.01 |  0.054 |      0.017 |           0.039 |         0.011 |   0.719 |  -0.752 |
| UiO-66    | charges_off |    0.1  |  0.51  |      0.054 |           0.364 |         0.035 |   0.714 |  -2.254 |
| UiO-66    | charges_off |    1    |  2.649 |      0.081 |           2.114 |         0.072 |   0.798 |  -4.946 |
| UiO-66    | cycles4x    |    0.1  |  0.51  |      0.054 |           0.512 |         0.047 |   1.004 |   0.029 |
| UiO-66    | cycles4x    |    1    |  2.649 |      0.081 |           2.628 |         0.063 |   0.992 |  -0.209 |
| UiO-66    | uff         |    0.01 |  0.054 |      0.017 |           0.077 |         0.018 |   1.413 |   0.895 |
| UiO-66    | uff         |    0.1  |  0.51  |      0.054 |           0.682 |         0.047 |   1.337 |   2.399 |
| UiO-66    | uff         |    1    |  2.649 |      0.081 |           3.287 |         0.091 |   1.241 |   5.25  |
| ZIF-8     | bigcell     |    0.1  |  0.075 |      0.011 |           0.076 |         0.009 |   1.011 |   0.061 |
| ZIF-8     | bigcell     |    1    |  0.784 |      0.026 |           0.782 |         0.024 |   0.998 |  -0.052 |
| ZIF-8     | charges_off |    0.01 |  0.007 |      0.006 |           0.007 |         0.005 |   0.973 |  -0.027 |
| ZIF-8     | charges_off |    0.1  |  0.075 |      0.011 |           0.074 |         0.015 |   0.987 |  -0.052 |
| ZIF-8     | charges_off |    1    |  0.784 |      0.026 |           0.755 |         0.04  |   0.963 |  -0.606 |
| ZIF-8     | cycles4x    |    0.1  |  0.075 |      0.011 |           0.075 |         0.016 |   1     |  -0     |
| ZIF-8     | cycles4x    |    1    |  0.784 |      0.026 |           0.78  |         0.064 |   0.996 |  -0.048 |
| ZIF-8     | uff         |    0.01 |  0.007 |      0.006 |           0.016 |         0.006 |   2.197 |   1.088 |
| ZIF-8     | uff         |    0.1  |  0.075 |      0.011 |           0.164 |         0.019 |   2.18  |   3.952 |
| ZIF-8     | uff         |    1    |  0.784 |      0.026 |           1.753 |         0.083 |   2.237 |  11.212 |

## Nearest-metal distances of CO2 at 0.1 bar

| case      | metal   |   n_frames |   n_molecule_samples |   median_d_O_metal_A |   frac_O_metal_lt_3.0A |   frac_O_metal_lt_3.5A |   median_d_C_metal_A |
|:----------|:--------|-----------:|---------------------:|---------------------:|-----------------------:|-----------------------:|---------------------:|
| HKUST-1   | Cu      |        100 |                  945 |                4.883 |                  0.02  |                  0.067 |                5.501 |
| Mg-MOF-74 | Mg      |        100 |                 1201 |                3.042 |                  0.464 |                  0.741 |                3.863 |
| IRMOF-1   | Zn      |        100 |                  108 |                4.497 |                  0.009 |                  0.046 |                4.983 |
| ZIF-8     | Zn      |        100 |                  177 |                5.243 |                  0     |                  0     |                5.622 |
| UiO-66    | Zr      |        100 |                  683 |                5.516 |                  0     |                  0     |                6.042 |
