"""NIST ISODB access through the official GitHub mirror (NIST-ISODB/isodb-library).

The mirror is identical to the API field for field (docs/RECON.md section 5), and a sparse
checkout avoids thousands of API calls. Workflow:
1. Bibliography (all papers) -> papers whose adsorbents include a case hashkey and whose
   adsorbates include the gas.
2. Sparse-checkout those paper folders; every isotherm file in them whose adsorbent is a case
   hashkey and whose adsorbates include the gas is a candidate.
3. Each candidate is copied unchanged to data/isodb_raw/records/<filename>.json (committed).
The mirror itself (data/isodb_raw/isodb-library/) is gitignored; its commit is recorded.
"""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "isodb_raw"
MIRROR = RAW / "isodb-library"
RECORDS = RAW / "records"
MIRROR_URL = "https://github.com/NIST-ISODB/isodb-library"

GAS_INCHIKEY = {"CO2": "CURLTUGMZLYLDI-UHFFFAOYSA-N",
                "CH4": "VNWKTOKETHGBQD-UHFFFAOYSA-N",
                "N2": "IJGRMHOSHXDMSA-UHFFFAOYSA-N"}


def _git(*args, timeout=600):
    return subprocess.run(["git", "-C", str(MIRROR), *args], check=True, capture_output=True,
                          text=True, timeout=timeout).stdout


def ensure_mirror():
    """Blobless, shallow, sparse clone with the bibliography checked out. Returns the commit."""
    if not (MIRROR / ".git").exists():
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", "--depth", "1",
                        MIRROR_URL, str(MIRROR)], check=True, timeout=600)
        _git("config", "gc.auto", "0")
        _git("sparse-checkout", "set", "--no-cone", "Library/Bibliography/*", "README.md")
        _git("checkout", "-q", "master")
    return _git("rev-parse", "HEAD").strip()


def paper_folder(paper):
    """Mirror folder of a paper = lower-cased bibliography file stem.

    Not derivable from the DOI: e.g. 10.1007/s10450-015-9684-6 lives in 10.1007s1045001596846.
    """
    return paper["_bib_stem"].lower()


def load_bibliography():
    out = []
    for f in sorted((MIRROR / "Library" / "Bibliography").glob("*.json")):
        b = json.loads(f.read_text())
        b["_bib_stem"] = f.stem
        out.append(b)
    return out


def candidate_papers(hashkeys, gas):
    key = GAS_INCHIKEY[gas]
    hk = set(hashkeys)
    papers = []
    for b in load_bibliography():
        if hk & {a["hashkey"] for a in b.get("adsorbents", [])} and \
                key in {a["InChIKey"] for a in b.get("adsorbates", [])}:
            papers.append(b)
    return papers


def checkout_papers(papers):
    """Add paper folders to the sparse checkout (keeps folders already present)."""
    current = set(_git("sparse-checkout", "list").split())
    wanted = current | {f"Library/{paper_folder(p)}/*" for p in papers}
    if wanted != current:
        p = subprocess.run(["git", "-C", str(MIRROR), "sparse-checkout", "set", "--no-cone", "--stdin"],
                           input="\n".join(sorted(wanted)) + "\n", text=True, check=True,
                           capture_output=True, timeout=600)
        del p


def candidate_records(hashkeys, gas, papers):
    """(record dict, mirror path) for isotherms with a case adsorbent and the gas among adsorbates."""
    key = GAS_INCHIKEY[gas]
    hk = set(hashkeys)
    out = []
    for b in papers:
        if not b.get("isotherms"):
            continue                     # paper lists no isotherms; it has no folder in the mirror
        folder = MIRROR / "Library" / paper_folder(b)
        if not folder.exists():
            raise RuntimeError(f"paper folder missing in mirror checkout: {folder.name} ({b['DOI']})")
        for f in sorted(folder.glob("*.json")):
            d = json.loads(f.read_text())
            if d.get("adsorbent", {}).get("hashkey") in hk and \
                    key in [a.get("InChIKey") for a in d.get("adsorbates", [])]:
                out.append((d, f))
    return out


def cache_record(path):
    """Copy a mirror file unchanged into data/isodb_raw/records/. Never overwrites a different file."""
    RECORDS.mkdir(parents=True, exist_ok=True)
    dst = RECORDS / Path(path).name
    if dst.exists():
        if dst.read_bytes() != Path(path).read_bytes():
            raise RuntimeError(f"{dst} differs from mirror copy; raw cache is never modified")
    else:
        shutil.copyfile(path, dst)
    return dst


def registry_matches(aliases, hashkeys):
    """Registry entries (cached materials.json) whose name or a synonym equals an alias, case-insensitive.

    Used to log every name that matched, and to warn if a matching entry is not in cases.yaml.
    """
    reg = json.loads((RAW / "api" / "materials.json").read_text())
    al = {a.strip().lower() for a in aliases}
    rows = []
    for m in reg:
        names = [m["name"]] + list(m.get("synonyms") or [])
        hit = [n for n in names if n.strip().lower() in al]
        if hit:
            rows.append({"hashkey": m["hashkey"], "name": m["name"], "matched": hit,
                         "in_cases_yaml": m["hashkey"] in set(hashkeys)})
    return rows


def fetch(case, gas, hashkeys, log=print):
    """Find, check out and cache all candidate records. Returns (commit, papers, [(record, cached_path)])."""
    commit = ensure_mirror()
    papers = candidate_papers(hashkeys, gas)
    n_empty = sum(1 for p in papers if not p.get("isotherms"))
    log(f"ISODB mirror {commit[:9]}: {len(papers)} candidate papers for {case} + {gas} "
        f"({n_empty} list no isotherms)")
    checkout_papers(papers)
    recs = candidate_records(hashkeys, gas, papers)
    out = [(d, cache_record(f)) for d, f in recs]
    log(f"{len(out)} candidate isotherm records cached in {RECORDS.relative_to(ROOT)}")
    return commit, papers, out
