"""RASPA3 3.0.29 input generation and CIF preparation.

Facts this module relies on are documented in docs/RECON.md:
- FugacityCoefficient is read only if it is a JSON float; omitted -> Peng-Robinson.
- HeliumVoidFraction defaults to 1.0 when omitted.
- CIF atoms are typed from _atom_site_label (exact, then digits stripped) but are skipped
  entirely when _atom_site_type_symbol is missing (silent 0-atom framework).
- RASPA3 does not enforce the minimum-image rule; we choose NumberOfUnitCells here.
"""

import json
import math
import re
from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates"
RASPA3_SRC = Path.home() / "projects" / "raspa3-src"


def load_recipe():
    return json.loads((TEMPLATES / "forcefield_recipe.json").read_text())


# ---------------------------------------------------------------- CIF handling

_CELL_KEYS = ["_cell_length_a", "_cell_length_b", "_cell_length_c",
              "_cell_angle_alpha", "_cell_angle_beta", "_cell_angle_gamma"]


def _num(s):
    """CIF number, dropping a trailing standard uncertainty like 26.343(2)."""
    return float(re.sub(r"\(\d+\)$", "", s))


def read_cell(text):
    cell = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in _CELL_KEYS:
            cell[parts[0]] = _num(parts[1])
    missing = [k for k in _CELL_KEYS if k not in cell]
    if missing:
        raise ValueError(f"CIF lacks cell parameters {missing}")
    return [cell[k] for k in _CELL_KEYS]


def cell_volume(cell):
    a, b, c, al, be, ga = cell
    al, be, ga = (math.radians(x) for x in (al, be, ga))
    return a * b * c * math.sqrt(1 - math.cos(al) ** 2 - math.cos(be) ** 2 - math.cos(ga) ** 2
                                 + 2 * math.cos(al) * math.cos(be) * math.cos(ga))


def perpendicular_widths(cell):
    """Distances between opposite cell faces: V / area of each face."""
    a, b, c, al, be, ga = cell
    v = cell_volume(cell)
    return [v / (b * c * math.sin(math.radians(al))),
            v / (a * c * math.sin(math.radians(be))),
            v / (a * b * math.sin(math.radians(ga)))]


def choose_unit_cells(cell, cutoff):
    """Smallest replication with every perpendicular width >= 2 x cutoff (minimum image)."""
    return [max(1, math.ceil(2.0 * cutoff / w - 1e-9)) for w in perpendicular_widths(cell)]


def read_atom_site_loop(text):
    """Return (header_names, rows) of the _atom_site_ loop that holds fractional coordinates."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "loop_":
            j = i + 1
            names = []
            while j < len(lines) and lines[j].strip().startswith("_"):
                names.append(lines[j].strip())
                j += 1
            if "_atom_site_fract_x" in names:
                rows = []
                while j < len(lines):
                    s = lines[j].strip()
                    if not s or s.startswith("_") or s == "loop_" or s.startswith("data_"):
                        break
                    rows.append(s.split())
                    j += 1
                return names, rows
            i = j
        else:
            i += 1
    raise ValueError("no _atom_site loop with fractional coordinates found")


def element_from_label(label):
    m = re.match(r"([A-Z][a-z]?)", label)
    if not m:
        raise ValueError(f"cannot derive element from label {label!r}")
    return m.group(1)


def atom_table(text):
    """List of dicts (label, element, x, y, z, charge or None) from the atom_site loop."""
    names, rows = read_atom_site_loop(text)
    idx = {n: k for k, n in enumerate(names)}
    out = []
    for r in rows:
        if len(r) != len(names):
            raise ValueError(f"atom_site row has {len(r)} fields, header has {len(names)}: {r}")
        label = r[idx["_atom_site_label"]]
        if "_atom_site_type_symbol" in idx:
            element = re.sub(r"[\d+-]+$", "", r[idx["_atom_site_type_symbol"]])
        else:
            element = element_from_label(label)
        charge = _num(r[idx["_atom_site_charge"]]) if "_atom_site_charge" in idx else None
        out.append({"label": label, "element": element,
                    "x": _num(r[idx["_atom_site_fract_x"]]),
                    "y": _num(r[idx["_atom_site_fract_y"]]),
                    "z": _num(r[idx["_atom_site_fract_z"]]),
                    "charge": charge})
    return out


def prepare_cif(src_text):
    """Make a CIF readable by RASPA3 3.0.29 without touching positions or charges.

    Changes (each reported): drop lines before the first `data_` block that are not CIF
    comments (the CoRE 2014-DDEC files start with a Python-dict line), and add an
    `_atom_site_type_symbol` column copied from the element part of the label if missing.
    Returns (new_text, changes, atoms). Raises if the atom table changed.
    """
    changes = []
    lines = src_text.splitlines()
    first_data = next(k for k, l in enumerate(lines) if l.strip().startswith("data_"))
    dropped = [l for l in lines[:first_data] if l.strip() and not l.strip().startswith("#")]
    if dropped:
        changes.append(f"removed {len(dropped)} non-CIF line(s) before data_ block")
        lines = [l for l in lines[:first_data] if l.strip().startswith("#") or not l.strip()] \
            + lines[first_data:]
    text = "\n".join(lines) + "\n"

    names, _ = read_atom_site_loop(text)
    if "_atom_site_type_symbol" not in names:
        out, in_loop, header_done = [], False, False
        for line in text.splitlines():
            s = line.strip()
            if s == "_atom_site_label":
                in_loop = True
                out.append(line)
                out.append(line.replace("_atom_site_label", "_atom_site_type_symbol"))
                continue
            if in_loop and not header_done and not s.startswith("_"):
                header_done = True
            if in_loop and header_done:
                if not s or s == "loop_" or s.startswith("_") or s.startswith("data_"):
                    in_loop = False
                else:
                    parts = s.split()
                    li = names.index("_atom_site_label")
                    parts.insert(li + 1, element_from_label(parts[li]))
                    line = " " + " ".join(parts)
            out.append(line)
        text = "\n".join(out) + "\n"
        changes.append("added _atom_site_type_symbol column (element from label)")

    before, after = atom_table(src_text_without_junk(src_text)), atom_table(text)
    key = lambda a: (a["label"], a["x"], a["y"], a["z"], a["charge"])
    if [key(a) for a in before] != [key(a) for a in after]:
        raise RuntimeError("prepare_cif changed the atom table; refusing")
    if read_cell(src_text) != read_cell(text):
        raise RuntimeError("prepare_cif changed the cell; refusing")
    return text, changes, after


def src_text_without_junk(src_text):
    lines = src_text.splitlines()
    first_data = next(k for k, l in enumerate(lines) if l.strip().startswith("data_"))
    return "\n".join(lines[first_data:]) + "\n"


def is_p1(text):
    m = re.search(r"_symmetry_space_group_name_H-M\s+'([^']+)'", text) or \
        re.search(r"_space_group_name_H-M_alt\s+'([^']+)'", text)
    return bool(m) and m.group(1).replace(" ", "") == "P1"


# ------------------------------------------------------------ force field files

def build_force_field(elements, gases, recipe=None, lj_set="framework_elements"):
    """force_field.json dict for framework `elements` (charges from CIF) and `gases`.

    lj_set: 'framework_elements' (the project recipe) or 'framework_elements_uff' (all-UFF sensitivity set).
    """
    recipe = recipe or load_recipe()
    pseudo, self_int = [], []
    for el in sorted(elements):
        if el not in recipe[lj_set]:
            raise KeyError(f"no LJ parameters for framework element {el}")
        p = recipe[lj_set][el]
        pseudo.append({"name": el, "framework": True, "print_to_output": True, "element": el,
                       "print_as": el, "mass": p["mass"], "charge": 0.0})
        self_int.append({"name": el, "type": "lennard-jones",
                         "parameters": [p["epsilon_K"], p["sigma_A"]], "source": p["source"]})
    needed = {"probe-He"}
    for g in gases:
        mol = json.loads((TEMPLATES / "molecules" / recipe["gases"][g]["molecule_file"]).read_text())
        needed |= {a[0] for a in mol["pseudoAtoms"]}
    for a in recipe["adsorbate_pseudo_atoms"]:
        if a["name"] not in needed:
            continue
        pseudo.append({"name": a["name"], "framework": False,
                       "print_to_output": a.get("print_to_output", True), "element": a["element"],
                       "print_as": a["element"] if a.get("print_to_output", True) else "-",
                       "mass": a["mass"], "charge": a["charge"], "source": a["source"]})
        if a["epsilon_K"] is None:
            self_int.append({"name": a["name"], "type": "none", "parameters": [0.0, 1.0],
                             "source": a["source"]})
        else:
            self_int.append({"name": a["name"], "type": "lennard-jones",
                             "parameters": [a["epsilon_K"], a["sigma_A"]], "source": a["source"]})
    return {"MixingRule": recipe["MixingRule"], "TruncationMethod": recipe["TruncationMethod"],
            "TailCorrections": recipe["TailCorrections"], "CutOffVDW": recipe["CutOffVDW"],
            "PseudoAtoms": pseudo, "SelfInteractions": self_int}


def add_helium_probe(ff):
    """Copy of a force-field dict with the probe-He pseudo-atom (for raspa3-cli void fraction)."""
    ff = json.loads(json.dumps(ff))
    if not any(p["name"] == "probe-He" for p in ff["PseudoAtoms"]):
        he = next(a for a in load_recipe()["adsorbate_pseudo_atoms"] if a["name"] == "probe-He")
        ff["PseudoAtoms"].append({"name": "probe-He", "framework": False, "print_to_output": False,
                                  "element": "He", "print_as": "He", "mass": he["mass"],
                                  "charge": 0.0})
        ff["SelfInteractions"].append({"name": "probe-He", "type": "lennard-jones",
                                       "parameters": [he["epsilon_K"], he["sigma_A"]],
                                       "source": he["source"]})
    return ff


# -------------------------------------------------------------- simulation.json

def component_block(gas, kind, recipe=None, widom_in_gcmc=False, legacy_example11=False):
    recipe = recipe or load_recipe()
    name = recipe["gases"][gas]["component_name"]
    mol = json.loads((TEMPLATES / "molecules" / recipe["gases"][gas]["molecule_file"]).read_text())
    linear_or_more = len(mol["pseudoAtoms"]) > 1
    comp = {"Name": name}
    if kind == "gcmc":
        comp.update({"IdealGasRosenbluthWeight": 1.0, "TranslationProbability": 0.5})
        if linear_or_more:
            comp["RotationProbability"] = 0.5
        comp.update({"ReinsertionProbability": 0.5, "SwapProbability": 1.0})
        if widom_in_gcmc or legacy_example11:
            comp["WidomProbability"] = 1.0
        comp["CreateNumberOfMolecules"] = 0
    elif kind == "widom":
        comp.update({"IdealGasRosenbluthWeight": 1.0, "WidomProbability": 1.0,
                     "CreateNumberOfMolecules": 0})
    elif kind == "nvt1":
        comp.update({"TranslationProbability": 0.5})
        if linear_or_more:
            comp["RotationProbability"] = 0.5
        comp.update({"ReinsertionProbability": 0.5, "CreateNumberOfMolecules": 1})
    else:
        raise ValueError(kind)
    return comp


def simulation_json(*, kind, framework_name, gas, T, P_pa, cycles, init_cycles, unit_cells,
                    void_fraction=None, ideal_gas=False, coulomb_cutoff=12.0,
                    charges_from_cif=True, print_every=None, legacy_example11=False, extra_system=None):
    """Build simulation.json as a dict.

    void_fraction None -> key omitted (RASPA default 1.0, used only for the regression).
    coulomb_cutoff None -> key omitted ('auto' = half the smallest perpendicular width).
    ideal_gas True -> FugacityCoefficient 1.0 (float). False -> key omitted (Peng-Robinson).
    """
    system = {"Type": "Framework", "Name": framework_name,
              "NumberOfUnitCells": [int(n) for n in unit_cells]}
    if void_fraction is not None:
        system["HeliumVoidFraction"] = float(void_fraction)
    if charges_from_cif:
        system["UseChargesFrom"] = "CIF_File"
    if coulomb_cutoff is not None:
        system["CutOffCoulomb"] = float(coulomb_cutoff)
    system.update({"ChargeMethod": "Ewald", "ExternalTemperature": float(T),
                   "ExternalPressure": float(P_pa)})
    system.update(extra_system or {})
    comp = component_block(gas, kind, legacy_example11=legacy_example11)
    if kind == "gcmc" and ideal_gas:
        comp = {"Name": comp["Name"], "FugacityCoefficient": 1.0,
                **{k: v for k, v in comp.items() if k != "Name"}}
    sim = {"SimulationType": "MonteCarlo", "NumberOfCycles": int(cycles),
           "NumberOfInitializationCycles": int(init_cycles),
           "PrintEvery": int(print_every or max(1, cycles // 20)),
           "Systems": [system], "Components": [comp]}
    _assert_float_keys(sim)
    return sim


def _assert_float_keys(sim):
    """Guard against the int-instead-of-float trap (RASPA3 silently ignores ints)."""
    for c in sim["Components"]:
        for k in ("FugacityCoefficient", "IdealGasRosenbluthWeight"):
            if k in c and not isinstance(c[k], float):
                raise TypeError(f"{k} must be a float, got {c[k]!r}")
