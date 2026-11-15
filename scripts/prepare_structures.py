"""Prepare data/structures/<id>/ from the original published files.

Usage (inside `conda run -n ads`):
    python scripts/prepare_structures.py --ddec <dir with CoRE 2014-DDEC re-labeled/> \
        --core2019 <dir with CoreMOF2019_public_v2_20241118/>

For each case: copies the original file unchanged into original/, writes the RASPA-ready
<id>.cif (format-only changes, verified by raspa.prepare_cif), and writes PROVENANCE.md.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gcmctools import raspa, runner  # noqa: E402

DDEC = {"source": "CoRE MOF 2014-DDEC database (Nazarian, Camp, Sholl, Chem. Mater. 2016, 28, 785)",
        "archive": "core-mof-1.0-ddec.tar, Zenodo 10.5281/zenodo.3986573, md5 a2e3578003968739640b6faeed361299",
        "license": "CC-BY-4.0",
        "charges": "DDEC (DFT: VASP, PBE), as stored in _atom_site_charge"}
CORE19 = {"source": "CoRE MOF 2019 dataset v2 (Chung et al.), computation-ready ASR subset",
          "archive": "CoREMOF2019_public_v2_20241119.zip, Zenodo 10.5281/zenodo.14184621, md5 f0af5f8cbeac0f3a622dac42b71f59bd",
          "license": "CC-BY-4.0",
          "charges": "DDEC6 charges PREDICTED BY MACHINE LEARNING (PACMAN v1.1), not DFT"}
R3 = RASPA = raspa.RASPA3_SRC

CASES = {
    "HKUST-1": dict(src="ddec", rel="re-labeled/FIQCEN_clean.cif", meta=DDEC,
                    note="CSD refcode FIQCEN (Chui et al., Science 1999). Primitive rhombohedral P1 cell."),
    "IRMOF-1": dict(src="ddec", rel="re-labeled/EDUSIF_clean.cif", meta=DDEC,
                    note="CSD refcode EDUSIF. Primitive P1 cell, Zn8 H24 C48 O26."),
    "Mg-MOF-74": dict(src="ddec", rel="re-labeled/Mg-DOBDC.cif", meta=DDEC,
                      note="Non-CSD entry 'Mg-DOBDC'. Chosen over 'MgMOF-74.cif' because its cell is "
                           "closest to CSD VOGTIV (CoRE 2019): V 1311.6 vs 1321.6 A^3; see docs/LOG.md."),
    "ZIF-8": dict(src="ddec", rel="re-labeled/ZIF-8.cif", meta=DDEC,
                  note="Non-CSD entry 'ZIF-8'. Cubic a = 16.991 A, identical to the CSD OFERUN cell "
                       "(CoRE 2019 OFERUN primitive a = 14.7138 = 16.991*sqrt(3)/2). Chosen over OFERUN04 "
                       "(a = 17.054 A); see docs/LOG.md."),
    "UiO-66": dict(src="core2019", rel="CoREMOF2019_public_v2_20241118/CR/ASR/RUBTAK01_SL_pacman.cif",
                   meta=CORE19,
                   note="CSD refcode RUBTAK01, manually curated ('SL'). Ideal hydroxylated Zr6O4(OH)4(BDC)6, "
                        "no missing linkers. Charge method differs from the other MOFs (ML, not DFT)."),
}


def write_case(cid, src_path, meta, note, extra=""):
    out = ROOT / "data" / "structures" / cid
    (out / "original").mkdir(parents=True, exist_ok=True)
    orig = out / "original" / src_path.name
    shutil.copyfile(src_path, orig)
    text = src_path.read_text()
    new, changes, atoms = raspa.prepare_cif(text)
    (out / f"{cid}.cif").write_text(new)
    cell = raspa.read_cell(new)
    elements = sorted({a["element"] for a in atoms})
    q = sum(a["charge"] for a in atoms) if atoms[0]["charge"] is not None else None
    info = {"id": cid, "cif": f"{cid}.cif", "p1": raspa.is_p1(new), "natoms_cif_rows": len(atoms),
            "elements": elements, "net_charge": q, "cell": cell,
            "perpendicular_widths": raspa.perpendicular_widths(cell),
            "unit_cells_for_12A": raspa.choose_unit_cells(cell, 12.0),
            "sha256_original": runner.sha256_file(orig), "sha256_prepared": runner.sha256_file(out / f"{cid}.cif"),
            "format_changes": changes}
    (out / "structure.json").write_text(json.dumps(info, indent=2))
    (out / "PROVENANCE.md").write_text(f"""# {cid}

- Source: {meta['source']}
- Archive: {meta['archive']}
- File in archive: `{src_path.name}` (copied unchanged to `original/`)
- License: {meta['license']}
- Charges: {meta['charges']}
- Notes: {note}
{extra}
## Checksums
- original `{orig.name}`: sha256 `{info['sha256_original']}`
- prepared `{cid}.cif`: sha256 `{info['sha256_prepared']}`

## Format changes made for RASPA3 3.0.29 (positions, cell and charges verified unchanged)
{chr(10).join('- ' + c for c in changes) or '- none'}

## Summary
- atoms in CIF: {len(atoms)}; elements: {', '.join(elements)}; net charge: {q if q is None else f'{q:.6f}'} e
- cell: {', '.join(f'{x:.4f}' for x in cell)}
- perpendicular widths (A): {', '.join(f'{w:.3f}' for w in info['perpendicular_widths'])}
- unit cells for 12 A cutoff (minimum image): {info['unit_cells_for_12A']}
""")
    print(cid, len(atoms), elements, f"q={q}", info["unit_cells_for_12A"], changes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ddec", type=Path, required=True)
    ap.add_argument("--core2019", type=Path, required=True)
    a = ap.parse_args()
    roots = {"ddec": a.ddec, "core2019": a.core2019}
    for cid, c in CASES.items():
        write_case(cid, roots[c["src"]] / c["rel"], c["meta"], c["note"])

    # MFI: raspa3-src example 10 (charges in the force field, TraPPE-zeo / Bai et al. 2013)
    write_case("MFI", R3 / "examples/basic/10_mc_adorption_co2_in_mfi/MFI_SI.cif",
               {"source": "raspa3-src v3.0.29 examples/basic/10_mc_adorption_co2_in_mfi (van Koningsveld, "
                          "van Bekkum, Jansen, Acta Cryst. B 1987, 43, 127)",
                "archive": "local read-only checkout ~/projects/raspa3-src (tag v3.0.29)",
                "license": "RASPA3 repository (MIT)",
                "charges": "Si +2.05, O -1.025 (Bai, Tsapatsis, Siepmann, J. Phys. Chem. C 2013, 117, 24375), "
                           "taken from the example force_field.json (UseChargesFrom PseudoAtoms); "
                           "the CIF carries the same values"},
               "All-silica MFI (Pnma). Method control. Uses the example-10 TraPPE-zeo framework model, not the MOF recipe.")
    shutil.copyfile(R3 / "examples/basic/10_mc_adorption_co2_in_mfi/force_field.json",
                    ROOT / "data/structures/MFI/original/example10_force_field.json")

    # HKUST-1 regression model: raspa3-src example 11, unchanged
    ex = ROOT / "data/structures/HKUST-1/example11"
    ex.mkdir(parents=True, exist_ok=True)
    for n in ("Cu-BTC.cif", "force_field.json", "CO2.json"):
        shutil.copyfile(R3 / "examples/basic/11_mc_adsorption_of_co2_in_cu_btc" / n, ex / n)
    (ex / "README.md").write_text(
        "Unchanged copies of raspa3-src v3.0.29 `examples/basic/11_mc_adsorption_of_co2_in_cu_btc`\n"
        "(Cu-BTC.cif from Chui et al. Science 1999, Fm-3m; force_field.json; CO2.json). Used only for the\n"
        "Phase 1 regression and as the alternative-charge sensitivity case. The source of the example's\n"
        "framework charges is not stated in the files.\n\n"
        + "\n".join(f"- `{n}` sha256 `{runner.sha256_file(ex / n)}`" for n in ("Cu-BTC.cif", "force_field.json", "CO2.json")) + "\n")


if __name__ == "__main__":
    main()
