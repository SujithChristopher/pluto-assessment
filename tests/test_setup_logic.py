"""Standalone logic checks for the screening/assessment refactor.
Run: uv run python tests/test_setup_logic.py  ->  prints OK."""
import os
import sys
import json
import tempfile
import pathlib

# Make the repo root importable when run as `python tests/test_setup_logic.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Point the data roots at a temp dir BEFORE importing the modules that read them.
_tmp = pathlib.Path(tempfile.mkdtemp())
os.environ["HOME"] = str(_tmp)            # ~/Documents fallback target
os.environ["USERPROFILE"] = str(_tmp)

import plutofullassessdef as pfadef
# Force the module-level paths into the temp dir so nothing touches real data.
pfadef.DATA_DIR = str(_tmp / "fullassessment")
pfadef.SUBJLIST_FILE = str(_tmp / "fullassessment" / "fullassess_subjects.csv")
pfadef.SCREENING_DIR = str(_tmp / "screening")
pfadef.SCREENING_SUBJLIST_FILE = str(_tmp / "screening" / "screening_subjects.csv")

import plutofullassesssdata as pdata
pdata.passdef.DATA_DIR = pfadef.DATA_DIR
pdata.passdef.SCREENING_DIR = pfadef.SCREENING_DIR

# --- is_task_included: no subjtype, affected gate kept ---
assert pfadef.is_task_included("AROM", limb="left", afflimb="left") is True
assert pfadef.is_task_included("AROM", limb="right", afflimb="left") is False
assert pfadef.is_task_included("DISC", limb="right", afflimb="left") is True  # in_unaffected

# --- assessment session: folder + protocol layout, no {type} layer ---
d = pdata.PlutoAssessmentData()
d.setup_session({
    "mode": "assessment", "subjid": "s001", "limb": "left",
    "afflimb": "left", "domlimb": "right", "timepoint": "A0",
})
d.create_session_folder()
assert pathlib.Path(d.basedir) == pathlib.Path(pfadef.DATA_DIR, "s001", "left", "A0"), d.basedir
d.start_protocol()
proto = pathlib.Path(d.protocol.filename)
assert proto.name == "s001_left_A0_protocol.csv", proto.name
assert proto.exists()
import pandas as pd
adf = pd.read_csv(proto)
assert set(adf["task"]) >= {"AROM", "PROM", "APROM"}, set(adf["task"])

# --- screening session: own tree, AROM only, limb == afflimb ---
s = pdata.PlutoAssessmentData()
s.setup_session({"mode": "screening", "subjid": "s002", "afflimb": "right"})
assert s.limb == "right"
s.create_session_folder()
assert pathlib.Path(s.basedir) == pathlib.Path(pfadef.SCREENING_DIR, "s002", "right"), s.basedir
s.start_protocol()
sproto = pathlib.Path(s.protocol.filename)
assert sproto.name == "s002_right_screening_protocol.csv", sproto.name
sdf = pd.read_csv(sproto)
assert set(sdf["task"]) == {"AROM"}, set(sdf["task"])
assert set(sdf["mechanism"]) == set(pfadef.MECHANISMS), set(sdf["mechanism"])
info = json.loads((pathlib.Path(s.basedir) / "subject_info.json").read_text())
assert "domlimb" not in info and info["afflimb"] == "right", info

print("OK")
