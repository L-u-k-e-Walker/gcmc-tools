"""Phase 3 budget for the full matrix, from measured CPU costs (results/budget/calibration.json,
the IRMOF-1 pilot and the HKUST-1 regression).

Cost model (all CPU seconds, independent of other load on the machine):
- per MC step at high loading: c = cpu_per_cycle(10 bar calibration) / max(20, N_box(10 bar));
  a RASPA3 cycle is max(20, N) steps.
- CO2 isotherm = R_CO2 x cost of its 10 bar point. R measured: IRMOF-1 pilot 2.0 (convex isotherm);
  HKUST-1 regression wall times (concave) give about 2.8. We use 2.8.
- CH4/N2: N(P) = N_box(10 bar) * P/10 (linear; low loading), cost_i = c * max(20, N_i) * cycles.
- extension overhead x1.25 (IRMOF-1 pilot: extensions added 985 s to 3859 s).
- Widom + 1-molecule NVT: 368 s per isotherm in the pilot for 848 framework atoms; scaled by atoms.
Wall clock at J jobs: max(total CPU / J, longest single point). Longest-first scheduling assumed.
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R_CO2, EXT, WIDOM_NVT_848 = 2.8, 1.25, 368.0


def estimate(cal, cycles, init, pressures):
    rows = []
    for r in cal:
        n10 = r["molecules_box"]
        c = r["cpu_s_per_cycle"] / max(20.0, n10)
        tot_cycles = cycles + init
        p10 = c * max(20.0, n10) * tot_cycles
        if r["gas"] == "CO2":
            gcmc = R_CO2 * p10
        else:
            gcmc = sum(c * max(20.0, n10 * p / max(pressures)) * tot_cycles for p in pressures)
        extra = WIDOM_NVT_848 * r["framework_atoms_box"] / 848.0 * cycles / 20000
        rows.append({**{k: r[k] for k in ("case", "gas", "T_K")}, "N_box_10bar": n10,
                     "cpu_10bar_point_s": p10, "cpu_isotherm_s": EXT * gcmc + extra,
                     "longest_point_s": p10 * (2 if r["gas"] == "CO2" else 1)})  # a CO2 10-bar point may be extended x2
    return rows


def main(cycles=20000, init=5000):
    cal = json.loads((ROOT / "results/budget/calibration.json").read_text())
    pressures = [0.01, 0.0215443, 0.0464159, 0.1, 0.215443, 0.464159, 1.0, 2.15443, 4.64159, 10.0]
    out = {}
    for label, cyc, ini in (("20k+5k (as Phase 1/pilot)", 20000, 5000), ("10k+5k", 10000, 5000),
                            ("40k+10k", 40000, 10000)):
        rows = estimate(cal, cyc, ini, pressures)
        total = sum(r["cpu_isotherm_s"] for r in rows)
        longest = max(r["longest_point_s"] for r in rows)
        out[label] = {"total_cpu_h": total / 3600, "longest_point_h": longest / 3600,
                      "wall_h_8_jobs": max(total / 8, longest) / 3600,
                      "wall_h_12_jobs": max(total / 12, longest) / 3600, "rows": rows}
        print(f"\n## {label}: total CPU {total / 3600:.1f} h, longest single point {longest / 3600:.2f} h, "
              f"wall at 8 jobs ~ {max(total / 8, longest) / 3600:.1f} h, at 12 jobs ~ {max(total / 12, longest) / 3600:.1f} h")
        if label.startswith("20k"):
            print("| case | gas | T | N in box @10 bar | 10-bar point (CPU h) | isotherm (CPU h) |")
            print("|---|---|---:|---:|---:|---:|")
            for r in sorted(rows, key=lambda r: -r["cpu_isotherm_s"]):
                print(f"| {r['case']} | {r['gas']} | {r['T_K']:g} | {r['N_box_10bar']:.0f} | "
                      f"{r['cpu_10bar_point_s'] / 3600:.2f} | {r['cpu_isotherm_s'] / 3600:.2f} |")
    (ROOT / "results/budget/budget.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    sys.exit(main())
