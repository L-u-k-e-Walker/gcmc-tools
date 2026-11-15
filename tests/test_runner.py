"""Resume logic: a run folder is complete only if its output parses, finished and is sane."""

import json
import shutil
from pathlib import Path

from gcmctools import runner

DATA = Path(__file__).parent / "data"
SETTINGS = {"kind": "gcmc", "cycles": 20000, "expected_framework_atoms": 624}


def make(tmp_path, settings=SETTINGS, files=None):
    return runner.prepare_run_folder(tmp_path, "gcmc_1e5Pa", files or {"simulation.json": "{}"}, settings)


def put_output(d, src, text=None):
    (d / "output").mkdir()
    dst = d / "output" / "output_298_1e+05.s0.txt"
    if text is None:
        shutil.copyfile(src, dst)
    else:
        dst.write_text(text)


def test_hash_changes_with_any_input(tmp_path):
    a = make(tmp_path)
    b = make(tmp_path, settings={**SETTINGS, "cycles": 40000})
    c = make(tmp_path, files={"simulation.json": "{ }"})
    assert len({a, b, c}) == 3
    assert make(tmp_path) == a                   # same inputs -> same folder (resume)
    m = json.loads((a / "run.json").read_text())
    assert m["files"]["simulation.json"] == runner.sha256_text("{}")


def test_status_complete(tmp_path):
    d = make(tmp_path)
    put_output(d, DATA / "cubtc_298K_1e5Pa.s0.txt")
    assert runner.status(d) == "complete"


def test_status_missing_output(tmp_path):
    assert runner.status(make(tmp_path)) == "incomplete"


def test_status_truncated(tmp_path):
    d = make(tmp_path)
    t = (DATA / "cubtc_298K_1e5Pa.s0.txt").read_text()
    put_output(d, None, t[: len(t) * 2 // 3])
    assert runner.status(d) == "incomplete"


def test_status_wrong_atom_count(tmp_path):
    d = make(tmp_path, settings={**SETTINGS, "expected_framework_atoms": 1248})
    put_output(d, DATA / "cubtc_298K_1e5Pa.s0.txt")
    assert runner.status(d) == "incomplete"


def test_validate_zero_atoms():
    from gcmctools import parse
    r = parse.parse_text((DATA / "zero_atoms.s0.txt").read_text())
    probs = runner.validate(r, {"kind": "widom", "cycles": 10, "expected_framework_atoms": 106})
    assert any("0 atoms" in p for p in probs)
    assert any("henry" in p for p in probs)      # inf Henry coefficient is rejected


def test_cycle_mismatch_is_incomplete(tmp_path):
    d = make(tmp_path, settings={**SETTINGS, "cycles": 40000})
    put_output(d, DATA / "cubtc_298K_1e5Pa.s0.txt")
    assert runner.status(d) == "incomplete"


def test_archive_keeps_failed_output(tmp_path):
    d = make(tmp_path)
    put_output(d, None, "partial")
    runner._archive_old_output(d)
    assert (d / "output.failed-1" / "output_298_1e+05.s0.txt").read_text() == "partial"
    assert not (d / "output").exists()


def test_dead_pid_is_not_running(tmp_path):
    d = make(tmp_path)
    (d / "pid").write_text("999999999")
    assert runner.status(d) == "incomplete"
