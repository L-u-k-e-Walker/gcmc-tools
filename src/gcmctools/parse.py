"""Parse RASPA3 3.0.29 text output (output/output_<T>_<P>.s0.txt).

The JSON output has no loadings, Henry coefficient or enthalpy (docs/RECON.md U1),
so everything comes from the text. Every final quantity takes the LAST match, anchored
on its unit in brackets, because each loading is printed in four units.
"""

import math
import re
from pathlib import Path

_F = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[-+]?inf|-?nan)"


def _last(pattern, text, cast=float):
    m = re.findall(pattern, text)
    if not m:
        return None
    v = m[-1]
    return tuple(cast(x) for x in v) if isinstance(v, tuple) else cast(v)


def _first(pattern, text, cast=float):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else None


def _framework_section(text):
    """Text of the 'Framework 0 [...]' block in 'Component definitions' (up to 'Component 0')."""
    m = re.search(r"\nFramework 0 \[.*?(?=\nComponent 0 \[)", text, re.S)
    return m.group(0) if m else ""


def find_output(run_dir):
    files = sorted(Path(run_dir, "output").glob("output_*.s0.txt"))
    return files[-1] if files else None


def parse_text(text):
    r = {}
    r["temperature_K"] = _last(r"\nTemperature:\s+" + _F + r" \[K\]", text)
    r["pressure_Pa"] = _last(r"\nPressure:\s+" + _F + r" \[Pa\]", text)
    r["helium_void_fraction"] = _last(r"Helium void fraction:\s+" + _F, text)
    r["fugacity_coefficient"] = _last(r"Fugacity coefficient:\s+" + _F + r" \[-\]", text)
    r["compressibility"] = _last(r"Compressibility:\s+" + _F + r" \[-\]", text)
    r["excess_molecules_correction"] = _last(r"Excess molecules:\s+" + _F + r" \[-\]", text)
    fw = _framework_section(text)
    r["framework_atoms"] = _first(r"number Of Atoms:\s+(\d+) \[-\]", fw, int)
    r["framework_net_charge"] = _first(r"net charge:\s+" + _F + r" \[e\]", fw)
    r["framework_mass_amu"] = _first(r"\n    mass:\s+" + _F + r" \[amu\]", fw)
    r["perpendicular_widths"] = _last(r"Perpendicular widths:\s+" + _F + r"\s+" + _F + r"\s+" + _F, text)
    r["coulomb_cutoff_A"] = _last(r"Cutoff Coulomb:\s+" + _F + r" \[", text)

    for basis, tag in (("abs", "Abs."), ("exc", "Excess")):
        v = _last(tag + r" loading average\s+" + _F + r" \+/-\s+" + _F + r" \[mol/kg-framework\]", text)
        r[f"{basis}_mol_kg"], r[f"{basis}_err_mol_kg"] = v if v else (None, None)
        v = _last(tag + r" loading average\s+" + _F + r" \+/-\s+" + _F + r" \[molecules/uc\]", text)
        r[f"{basis}_molec_uc"], r[f"{basis}_err_molec_uc"] = v if v else (None, None)

    v = _last(r"Average Henry coefficient:\s+" + _F + r" \+/-\s+" + _F + r" \[mol/kg/Pa\]", text)
    r["henry_mol_kg_pa"], r["henry_err_mol_kg_pa"] = v if v else (None, None)
    v = _last(r"Enthalpy of adsorption:\s+" + _F + r" \+/-\s+" + _F + r" \[K\]\s*\n\s+" + _F
              + r" \+/-\s+" + _F + r" \[kJ/mol\]", text)
    r["enthalpy_kj_mol"], r["enthalpy_err_kj_mol"] = (v[2], v[3]) if v else (None, None)
    v = _last(r"Measured fugacity:\s+" + _F + r" \+/-\s+" + _F + r" \[Pa\]", text)
    r["measured_fugacity_Pa"], r["measured_fugacity_err_Pa"] = v if v else (None, None)
    v = _last(r"Framework-molecule energy/kʙ 0-0 \[[^\]]+\]:\s*\n\s*-+\n(?:\s*Block\[\s*\d+\][^\n]*\n)+"
              r"\s*-+\n\s*Average\s+" + _F + r" \+/-\s+" + _F + r" \[K\]", text)
    r["framework_molecule_energy_K"], r["framework_molecule_energy_err_K"] = v if v else (None, None)

    r["production_cycles_total"] = _last(r"\nCurrent cycle: \d+ out of (\d+)", text, int)
    r["production_series_exc_mol_kg"] = production_series(text)
    r["finished"] = "Total simulation time:" in text and r.get("production_cycles_total") is not None
    return r


def production_series(text):
    """Instantaneous excess loading (mol/kg) at each production status print."""
    out = []
    for block in re.split(r"\n(?=(?:Initialization: )?Current cycle: )", text):
        if not block.startswith("Current cycle:"):
            continue
        m = re.search(r"excess adsorption:[^\n]*\n[^\n]*molec\./uc[^\n]*\n\s+" + _F + r" mol/kg", block)
        cyc = re.match(r"Current cycle: (\d+)", block)
        if m and cyc:
            out.append((int(cyc.group(1)), float(m.group(1))))
    return out


def parse_run(run_dir):
    f = find_output(run_dir)
    if f is None:
        return None
    r = parse_text(f.read_text(errors="replace"))
    r["output_file"] = str(f)
    return r


def drift_check(series, n_skip=1):
    """Compare first and second half of the production series.

    Returns (difference second-first, combined standard error, flag). Samples are PrintEvery
    cycles apart and treated as independent; flag if |diff| > 2 sigma. The cycle-0 sample is
    skipped (it is the last initialization configuration).
    """
    vals = [v for _, v in series[n_skip:]]
    if len(vals) < 6:
        return None, None, False
    h = len(vals) // 2
    a, b = vals[:h], vals[-h:]

    def m_se(x):
        m = sum(x) / len(x)
        var = sum((y - m) ** 2 for y in x) / (len(x) - 1)
        return m, math.sqrt(var / len(x))

    (ma, sa), (mb, sb) = m_se(a), m_se(b)
    se = math.sqrt(sa ** 2 + sb ** 2)
    diff = mb - ma
    return diff, se, bool(se > 0 and abs(diff) > 2 * se)


def series_stderr(series, n_skip=1):
    """Standard error of the mean from the production status samples, treated as independent.

    An independent cross-check of RASPA3's 5-block error. Samples are PrintEvery cycles apart;
    if they are correlated this underestimates the error, so the larger of the two estimates is used
    for convergence decisions.
    """
    vals = [v for _, v in series[n_skip:]]
    if len(vals) < 4:
        return None
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1) / len(vals))
