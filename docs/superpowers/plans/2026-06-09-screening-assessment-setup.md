# Screening / Assessment Session Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace subject-create + subject-select + limb + time-point selection with one "Session Setup" window offering Screening and Assessment modes, drop the healthy/stroke distinction, and give screening its own AROM-only protocol and directory.

**Architecture:** A new programmatic `SessionSetupWindow` collects everything in one modal and returns a setup dict. `PlutoAssessmentData` gains a `mode` (screening|assessment), loses `type`, and exposes a single `setup_session()`. Folder/file naming and the protocol builder branch on `mode`. The state machine collapses three setup states into one `SETUP_DONE` transition.

**Tech Stack:** Python 3, PySide6 (Qt), pandas. No test framework present — pure-logic tasks are verified with standalone `uv run python` assert scripts under `tests/`; GUI/wiring tasks with `uv run python -m py_compile` plus a manual smoke run.

**Verification conventions (read once):**
- Syntax check any file: `uv run python -m py_compile <file.py>` → Expected: no output, exit 0.
- Logic scripts live in `tests/` and are run directly: `uv run python tests/<name>.py` → Expected: prints `OK` and exits 0; on failure an `AssertionError` traces.
- Tests must write only into a temp dir (use `tempfile.mkdtemp()`); never touch the real Documents data tree.
- Commit after each task. Branch is `hoc-plus` (already not main).

---

## File structure

| File | Responsibility | Action |
|---|---|---|
| `plutofullassessdef.py` | Constants, paths, task-inclusion, screening protocol def, timepoint helpers | Modify |
| `plutofullassesssdata.py` | `PlutoAssessmentData` + protocol/details data classes | Modify |
| `async_workers.py` | Background folder+protocol creation worker | Modify |
| `plutofullassessstatemachine.py` | High-level state machine | Modify |
| `sessionsetupwindow.py` | New combined setup window + `SubjectsListFile` | Create |
| `plutofullassessment.py` | Main window wiring | Modify |
| `subjectselector.py` | Old select window | Delete |
| `subjectcreator.py` | Old create window | Delete |
| `tests/test_setup_logic.py` | Logic checks for defs + data layer | Create |

---

## Task 1: defs — screening constants, task-inclusion, timepoint helpers

**Files:**
- Modify: `plutofullassessdef.py` (paths ~67-68; `TASK_DEPENDENCIES` 129-163; `is_task_included` 634-640)

- [ ] **Step 1: Add screening paths + screening protocol map**

In `plutofullassessdef.py`, right after the existing `SUBJLIST_FILE` line (currently line 68):

```python
DATA_DIR = str(homer_data_root() / "fullassessment")
SUBJLIST_FILE = str(pathlib.Path(DATA_DIR) / "fullassess_subjects.csv")

# Screening: separate tree, single-shot (no timepoint), AROM only.
SCREENING_DIR = str(homer_data_root() / "screening")
SCREENING_SUBJLIST_FILE = str(pathlib.Path(SCREENING_DIR) / "screening_subjects.csv")

# Subjects-list CSV headers per mode.
ASSESS_SUBJECT_HEADER = ["subjid", "domlimb", "afflimb", "createdat"]
SCREENING_SUBJECT_HEADER = ["subjid", "afflimb", "createdat"]
```

Then, immediately after the `MECH_TASKS = { ... }` block (after current line 128), add:

```python
# Screening protocol: AROM only, every mechanism.
SCREENING_MECH_TASKS = {_m: [["AROM"]] for _m in MECHANISMS}
```

- [ ] **Step 2: Remove `in_subjtypes` from `TASK_DEPENDENCIES`**

Replace the whole `TASK_DEPENDENCIES = { ... }` dict (lines 129-163) with the same dict minus every `"in_subjtypes": [...]` entry:

```python
TASK_DEPENDENCIES = {
    "AROM": {"in_unaffected": False, "depends_on": []},
    "PROM": {"in_unaffected": False, "depends_on": []},
    "APROM": {"in_unaffected": False, "depends_on": []},
    "DISC": {"in_unaffected": True, "depends_on": ["AROM"]},
    "POSHOLD": {"in_unaffected": False, "depends_on": ["AROM"]},
    "FCTRLLOW": {"in_unaffected": True, "depends_on": ["AROM"]},
    "FCTRLMED": {"in_unaffected": True, "depends_on": ["AROM"]},
    "FCTRLHIGH": {"in_unaffected": True, "depends_on": ["AROM"]},
    "PROP": {"in_unaffected": True, "depends_on": ["PROM"]},
}
```

- [ ] **Step 3: Drop `subjtype` from `is_task_included` + add timepoint helpers**

Replace `is_task_included` (lines 634-640) with:

```python
def is_task_included(taskname: str, limb: str, afflimb: str) -> bool:
    """Whether the task is included for the given limb and affected limb.
    Subject type is no longer used (all subjects are stroke)."""
    return TASK_DEPENDENCIES[taskname]["in_unaffected"] or limb == afflimb


def assessment_protocol_path(subjid: str, limb: str, timepoint: str) -> pathlib.Path:
    """Path to the assessment protocol CSV for a subject/limb/timepoint."""
    return pathlib.Path(
        DATA_DIR, subjid, limb, timepoint,
        f"{subjid}_{limb}_{timepoint}_protocol.csv",
    )


def is_assessment_timepoint_completed(subjid: str, limb: str, timepoint: str) -> bool:
    """True if the assessment protocol for this timepoint exists and has no
    unfinished (NaN session) rows."""
    _proto = assessment_protocol_path(subjid, limb, timepoint)
    if not _proto.exists():
        return False
    try:
        _df = pd.read_csv(
            _proto.as_posix(), header=0, index_col=None,
            dtype=SUMMARY_COLUMN_FORMAT,
        )
        return not _df["session"].isna().any()
    except Exception:
        return False
```

Confirm `import pandas as pd` and `import pathlib` already exist at the top of the file (they do — `homer_data_root` uses `pathlib`; `SUMMARY_COLUMN_FORMAT` is defined above). If `pandas` is not imported at module top, add `import pandas as pd`.

- [ ] **Step 4: Syntax check**

Run: `uv run python -m py_compile plutofullassessdef.py`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add plutofullassessdef.py
git commit -m "feat(defs): screening constants, drop subjtype from task inclusion, timepoint helpers"
```

---

## Task 2: data layer — `PlutoAssessmentData` mode + `setup_session`

**Files:**
- Modify: `plutofullassesssdata.py` (`PlutoAssessmentData` 51-212)

- [ ] **Step 1: Replace `PlutoAssessmentData` (lines 51-212) with the mode-aware version**

```python
class PlutoAssessmentData(object):
    def __init__(self):
        self.init_values()
        # Ensure both data roots exist.
        pathlib.Path(passdef.DATA_DIR).mkdir(exist_ok=True, parents=True)
        pathlib.Path(passdef.SCREENING_DIR).mkdir(exist_ok=True, parents=True)

    @property
    def mode(self):
        return self._mode

    @property
    def subjid(self):
        return self._subjid

    @property
    def domlimb(self):
        return self._domlimb

    @property
    def afflimb(self):
        return self._afflimb

    @property
    def limb(self):
        return self._limb

    @property
    def timepoint(self):
        return self._timepoint

    @property
    def session(self):
        return self._session

    @property
    def basedir(self):
        return self._basedir

    @property
    def sessdir(self):
        return self._sessdir

    @property
    def protocol(self):
        return self._protocol

    @property
    def detailedsummary(self):
        return self._detailsumry

    @property
    def is_screening(self):
        return self._mode == "screening"

    def init_values(self):
        self._mode = None
        self._subjid = None
        self._domlimb = None
        self._afflimb = None
        self._limb = None
        self._timepoint = None
        self._session = None
        self._basedir = None
        self._sessdir = None
        self._protocol: PlutoAssessmentProtocolData = None
        self._detailsumry: PlutoAssessmentDetailsData = None

    def setup_session(self, setup: dict):
        """Store all setup fields from the Session Setup window in one call.
        Does not perform I/O — the worker calls create_session_folder()."""
        self.init_values()
        self._mode = setup["mode"]
        self._subjid = setup["subjid"]
        self._afflimb = setup["afflimb"]
        # Screening screens the affected limb; limb == afflimb.
        self._limb = setup["afflimb"] if self._mode == "screening" else setup["limb"]
        self._domlimb = setup.get("domlimb", "") or ""
        self._timepoint = setup.get("timepoint", "") or ""

    def create_session_folder(self):
        """Create the session folder tree and write subject_info.json.
        Branches on mode for path layout and session naming."""
        _now = dt.now().strftime("%Y%m%d_%H%M%S")
        if self.is_screening:
            self._session = f"{self.limb[0].lower()}_screen_{_now}"
            self._basedir = pathlib.Path(
                passdef.SCREENING_DIR, self.subjid, self.limb
            )
            _info = {
                "subjid": self.subjid,
                "afflimb": self.afflimb,
                "limb": self.limb,
            }
        else:
            self._session = f"{self.limb[0].lower()}_{self.timepoint}_{_now}"
            self._basedir = pathlib.Path(
                passdef.DATA_DIR, self.subjid, self.limb, self.timepoint
            )
            _info = {
                "subjid": self.subjid,
                "domlimb": self.domlimb,
                "afflimb": self.afflimb,
                "limb": self.limb,
                "timepoint": self.timepoint,
            }
        self._sessdir = pathlib.Path(self.basedir, self.session)
        self.sessdir.mkdir(exist_ok=True, parents=True)
        _fname = pathlib.Path(self._basedir, "subject_info.json").as_posix()
        with open(_fname, "w") as fh:
            json.dump(_info, fh, indent=4)

    def get_session_info(self):
        _str = [
            f"{'' if self.session is None else self.session:<12}",
            f"{'' if self.subjid is None else self.subjid:<8}",
            f"{(self.mode or ''):<10}",
            f"{(self.limb or ''):<6}",
        ]
        return ":".join(_str)

    def start_protocol(self):
        self._protocol = PlutoAssessmentProtocolData(
            self.subjid, self.mode, self.domlimb, self.afflimb,
            self.limb, self.timepoint, self._basedir, self._sessdir,
        )
        self._detailsumry = PlutoAssessmentDetailsData(
            self.subjid, self.mode, self.domlimb, self.afflimb,
            self.limb, self.timepoint, self._basedir,
        )
```

Note: this removes `set_subject`, `set_limb`, `set_timepoint`, `is_timepoint_completed`, and the `type` property. `is_timepoint_completed` callers now use `passdef.is_assessment_timepoint_completed(...)` (the window handles that — Task 5).

- [ ] **Step 2: Syntax check**

Run: `uv run python -m py_compile plutofullassesssdata.py`
Expected: may still pass (later classes reference renamed args only internally). If it errors on undefined names, that is fixed in Task 3. Proceed to Task 3 before re-checking.

- [ ] **Step 3: Commit**

```bash
git add plutofullassesssdata.py
git commit -m "feat(data): mode-aware PlutoAssessmentData with setup_session"
```

---

## Task 3: data layer — protocol & details classes branch on mode

**Files:**
- Modify: `plutofullassesssdata.py` (`PlutoAssessmentProtocolData` 215-660; `PlutoAssessmentDetailsData` 663-911)

- [ ] **Step 1: Update `PlutoAssessmentProtocolData.__init__` signature + stored fields**

Change the constructor (line 218) and the field block (219-226) from `stype` to `mode`:

```python
    def __init__(self, subjid, mode, domlimb, afflimb, slimb, timepoint, basedir, sessdir):
        self._subjid = subjid
        self._mode = mode
        self._domlimb = domlimb
        self._afflimb = afflimb
        self._limb = slimb
        self._timepoint = timepoint
        self._basedir = basedir
        self._sessdir = sessdir
```

- [ ] **Step 2: Update protocol/raw/summary filenames (drop type)**

Replace the `filename` property (278-281):

```python
    @property
    def filename(self):
        if self._mode == "screening":
            _name = f"{self._subjid}_{self._limb}_screening_protocol.csv"
        else:
            _name = f"{self._subjid}_{self._limb}_{self._timepoint}_protocol.csv"
        return pathlib.Path(self._basedir, _name).as_posix()
```

Replace `rawfilename` (377-382):

```python
    @property
    def rawfilename(self):
        return pathlib.Path(
            self._sessdir,
            f"{self._subjid}_{self._limb}_{self._mech}_{self._task}_raw-{self._tasktime}.csv",
        ).as_posix()
```

Replace `summaryfilename` (385-390):

```python
    @property
    def summaryfilename(self):
        return pathlib.Path(
            self._sessdir,
            f"{self._subjid}_{self._limb}_{self._mech}_{self._task}_summary-{self._tasktime}.csv",
        ).as_posix()
```

- [ ] **Step 3: Branch the summary-file builder on mode**

Replace `create_assessment_summary_file` (613-628):

```python
    def create_assessment_summary_file(self):
        if pathlib.Path(self.filename).exists():
            return
        _dframe = pd.DataFrame(columns=pfadef.FA_SUMMARY_HEADER)
        if self._mode == "screening":
            # AROM only, every mechanism, no affected-side gate.
            for _m in pfadef.MECHANISMS:
                _dframe = self._add_rows(_dframe, _m, "AROM", gated=False)
        else:
            for _m in pfadef.MECHANISMS:
                for _t in pfadef.MECH_TASKS[_m][0]:
                    _dframe = self._add_rows(_dframe, _m, _t)
                for _tasks in pfadef.MECH_TASKS[_m][1:]:
                    random.shuffle(_tasks)
                    for _t in _tasks:
                        _dframe = self._add_rows(_dframe, _m, _t)
        _dframe.to_csv(self.filename, sep=",", index=None)
```

- [ ] **Step 4: Update `_add_rows` to drop subjtype and accept a gate flag**

Replace `_add_rows` (630-660):

```python
    def _add_rows(self, dframe, mechname, taskname, gated=True):
        if gated and not pfadef.is_task_included(
            taskname=taskname, limb=self._limb, afflimb=self._afflimb
        ):
            return dframe
        _n = pfadef.get_task_constants(taskname).NO_OF_TRIALS
        return pd.concat(
            [
                dframe,
                pd.DataFrame.from_dict(
                    {
                        "session": pd.Series([pd.NA], dtype="string"),
                        "mechanism": pd.Series([mechname], dtype="string"),
                        "task": pd.Series([taskname], dtype="string"),
                        "ntrial": pd.Series([_n], dtype="Int64"),
                        "rawfile": pd.Series([pd.NA], dtype="string"),
                        "summaryfile": pd.Series([pd.NA], dtype="string"),
                        "mechcomment": pd.Series([pd.NA], dtype="string"),
                        "taskcomment": pd.Series([pd.NA], dtype="string"),
                        "status": pd.Series([pd.NA], dtype="string"),
                    }
                ),
            ],
            ignore_index=True,
        )
```

- [ ] **Step 5: Update `PlutoAssessmentDetailsData` signature, filename, and dict builder**

Change constructor (666) and fields (667-673) `stype` → `mode`:

```python
    def __init__(self, subjid, mode, domlimb, afflimb, slimb, timepoint, basedir):
        self._subjid = subjid
        self._mode = mode
        self._domlimb = domlimb
        self._afflimb = afflimb
        self._limb = slimb
        self._timepoint = timepoint
        self._basedir = basedir
```

Replace `filename` (706-709):

```python
    @property
    def filename(self):
        if self._mode == "screening":
            _name = f"{self._subjid}_{self._limb}_screening_details.json"
        else:
            _name = f"{self._subjid}_{self._limb}_{self._timepoint}_details.json"
        return pathlib.Path(self._basedir, _name).as_posix()
```

Replace `_create_assessment_details_dict` (863-896):

```python
    def _create_assessment_details_dict(self):
        self._val = {
            "subj": self._subjid,
            "mode": self._mode,
            "domlimb": self._domlimb,
            "afflimb": self._afflimb,
            "limb": self._limb,
        }
        if self._mode == "screening":
            for mech in pfadef.MECHANISMS:
                self._val[mech] = {"status": "Incomplete", "tasks": {"AROM": []}}
            return
        for mech in pfadef.MECHANISMS:
            self._val[mech] = {"status": "Incomplete", "tasks": {}}
            for task in pfadef.MECH_TASKS[mech][0]:
                if pfadef.is_task_included(
                    taskname=task, limb=self._limb, afflimb=self._afflimb
                ):
                    self._val[mech]["tasks"][task] = []
            for task_group in pfadef.MECH_TASKS[mech][1:]:
                for task in task_group:
                    if pfadef.is_task_included(
                        taskname=task, limb=self._limb, afflimb=self._afflimb
                    ):
                        self._val[mech]["tasks"][task] = []
```

- [ ] **Step 6: Syntax check**

Run: `uv run python -m py_compile plutofullassesssdata.py`
Expected: no output, exit 0.

- [ ] **Step 7: Write the logic test for the data layer**

Create `tests/test_setup_logic.py`:

```python
"""Standalone logic checks for the screening/assessment refactor.
Run: uv run python tests/test_setup_logic.py  →  prints OK."""
import os
import sys
import json
import tempfile
import pathlib

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
```

- [ ] **Step 8: Run the logic test**

Run: `uv run python tests/test_setup_logic.py`
Expected: prints `OK`, exit 0.

- [ ] **Step 9: Commit**

```bash
git add plutofullassesssdata.py tests/test_setup_logic.py
git commit -m "feat(data): mode-branched protocol/details + screening AROM-only builder + logic test"
```

---

## Task 4: worker — handle both modes

**Files:**
- Modify: `async_workers.py` (whole `LimbSetupWorker`)

- [ ] **Step 1: Generalize the worker**

Replace the `LimbSetupWorker` class body (lines 13-53) so it no longer takes a timepoint and just drives the data object's two I/O steps:

```python
class SessionSetupWorker(QThread):
    """Worker thread for the blocking I/O of session setup:
    folder creation + protocol initialization (both screening and assessment)."""

    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, data_obj, parent=None):
        super().__init__(parent)
        self.data_obj = data_obj

    def run(self):
        try:
            self.started.emit()
            self.progress.emit("Creating session folder...")
            self.data_obj.create_session_folder()
            self.progress.emit("Initializing protocol...")
            self.data_obj.start_protocol()
            self.finished.emit()
        except Exception as e:
            self.error.emit(
                f"Error during session setup: {str(e)}\n{traceback.format_exc()}"
            )


# Backwards-compatible alias (old name still referenced until main window is updated).
LimbSetupWorker = SessionSetupWorker
```

- [ ] **Step 2: Syntax check**

Run: `uv run python -m py_compile async_workers.py`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add async_workers.py
git commit -m "feat(worker): SessionSetupWorker drives folder+protocol for both modes"
```

---

## Task 5: SessionSetupWindow (new combined window)

**Files:**
- Create: `sessionsetupwindow.py`

- [ ] **Step 1: Write the new window + generalized subjects-list file**

Create `sessionsetupwindow.py`:

```python
"""Combined Session Setup window: pick Screening or Assessment, choose/create a
subject, and set limb / affected side / dominant hand / time point in one modal.
Replaces SubjectCreator and SubjectSelector.

Built programmatically (no .ui) so the whole window is self-contained.
"""

import os
import sys
import pandas as pd
from datetime import datetime as dt

from PySide6 import QtCore, QtWidgets

import plutofullassessdef as pfadef


class SubjectsListFile:
    """A subjects-list CSV with a mode-specific header."""

    def __init__(self, filename, header):
        self.filename = filename
        self.header = header
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            self.subjlist = pd.DataFrame(columns=self.header)
            self.subjlist.to_csv(self.filename, index=False)
        else:
            self.subjlist = pd.read_csv(self.filename, dtype=str).fillna("")

    def subject_exists(self, subjid):
        return subjid in self.subjlist["subjid"].values

    def get_subject_info(self, subjid):
        if self.subject_exists(subjid):
            return self.subjlist[self.subjlist["subjid"] == subjid].iloc[0].to_dict()
        return {}

    def add_subject(self, subjinfo: dict):
        if not self.subject_exists(subjinfo["subjid"]):
            self.subjlist = pd.concat(
                [self.subjlist, pd.DataFrame([subjinfo])], ignore_index=True
            )
            self.subjlist.to_csv(self.filename, index=False)


def _list_file(mode):
    if mode == "screening":
        return SubjectsListFile(pfadef.SCREENING_SUBJLIST_FILE,
                                pfadef.SCREENING_SUBJECT_HEADER)
    return SubjectsListFile(pfadef.SUBJLIST_FILE, pfadef.ASSESS_SUBJECT_HEADER)


class SessionSetupWindow(QtWidgets.QMainWindow):
    """One-stop setup. On Start, returns a dict via onclosecb; on Cancel returns {}."""

    SIDES = ["", "Left", "Right"]

    def __init__(self, parent=None, modal=True, onclosecb=None):
        super().__init__(parent)
        self.setWindowTitle("Session Setup")
        self.on_close_callback = onclosecb
        self.result = {}
        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self._build_ui()
        self._wire()
        self._on_mode_changed()
        self.update_ui()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        form = QtWidgets.QFormLayout(central)

        # Mode radios
        self.rbScreening = QtWidgets.QRadioButton("Screening")
        self.rbAssessment = QtWidgets.QRadioButton("Assessment")
        self.rbAssessment.setChecked(True)
        self.modeGroup = QtWidgets.QButtonGroup(self)
        self.modeGroup.addButton(self.rbScreening)
        self.modeGroup.addButton(self.rbAssessment)
        _moderow = QtWidgets.QHBoxLayout()
        _moderow.addWidget(self.rbScreening)
        _moderow.addWidget(self.rbAssessment)
        form.addRow("Mode:", _moderow)

        self.txtSubjID = QtWidgets.QLineEdit()
        form.addRow("Subject ID:", self.txtSubjID)

        self.lblExisting = QtWidgets.QLabel("")
        form.addRow("", self.lblExisting)

        self.cbAff = QtWidgets.QComboBox(); self.cbAff.addItems(self.SIDES)
        self.lblAff = QtWidgets.QLabel("Affected side:")
        form.addRow(self.lblAff, self.cbAff)

        self.cbLimb = QtWidgets.QComboBox(); self.cbLimb.addItems(self.SIDES)
        self.lblLimb = QtWidgets.QLabel("Limb assessed:")
        form.addRow(self.lblLimb, self.cbLimb)

        self.cbDom = QtWidgets.QComboBox(); self.cbDom.addItems(self.SIDES)
        self.lblDom = QtWidgets.QLabel("Dominant hand:")
        form.addRow(self.lblDom, self.cbDom)

        self.cbTP = QtWidgets.QComboBox(); self.cbTP.addItems([""] + list(pfadef.TIMEPOINTS))
        self.lblTP = QtWidgets.QLabel("Time point:")
        form.addRow(self.lblTP, self.cbTP)

        _btnrow = QtWidgets.QHBoxLayout()
        self.pbStart = QtWidgets.QPushButton("Start")
        self.pbCancel = QtWidgets.QPushButton("Cancel")
        _btnrow.addWidget(self.pbStart); _btnrow.addWidget(self.pbCancel)
        form.addRow(_btnrow)

    def _wire(self):
        self.rbScreening.toggled.connect(self._on_mode_changed)
        self.txtSubjID.editingFinished.connect(self._on_subjid_changed)
        for _cb in (self.cbAff, self.cbLimb, self.cbDom, self.cbTP):
            _cb.currentIndexChanged.connect(self.update_ui)
        self.pbStart.clicked.connect(self._on_start)
        self.pbCancel.clicked.connect(self.close)

    @property
    def mode(self):
        return "screening" if self.rbScreening.isChecked() else "assessment"

    def _assessment_fields_visible(self, vis):
        for w in (self.lblLimb, self.cbLimb, self.lblDom, self.cbDom,
                  self.lblTP, self.cbTP):
            w.setVisible(vis)

    def _on_mode_changed(self, *_):
        # Screening: only affected side. Assessment: limb, dominant, timepoint too.
        self._assessment_fields_visible(self.mode == "assessment")
        self._on_subjid_changed()  # re-lookup against the mode's list
        self.update_ui()

    def _on_subjid_changed(self, *_):
        subjid = self.txtSubjID.text().strip().lower()
        listfile = _list_file(self.mode)
        if subjid and listfile.subject_exists(subjid):
            info = listfile.get_subject_info(subjid)
            self.lblExisting.setText("Existing subject — details locked.")
            self.cbAff.setCurrentText((info.get("afflimb", "") or "").capitalize())
            self.cbAff.setEnabled(False)
            if self.mode == "assessment":
                self.cbDom.setCurrentText((info.get("domlimb", "") or "").capitalize())
                self.cbDom.setEnabled(False)
        else:
            self.lblExisting.setText("New subject — will be created on Start." if subjid else "")
            self.cbAff.setEnabled(True)
            self.cbDom.setEnabled(True)
        self.update_ui()

    def update_ui(self):
        ok = self.txtSubjID.text().strip() != "" and self.cbAff.currentText() != ""
        if self.mode == "assessment":
            ok = ok and self.cbLimb.currentText() != "" \
                and self.cbDom.currentText() != "" and self.cbTP.currentText() != ""
        self.pbStart.setEnabled(ok)

    def _on_start(self):
        subjid = self.txtSubjID.text().strip().lower()
        afflimb = self.cbAff.currentText().lower()
        mode = self.mode
        if mode == "assessment":
            limb = self.cbLimb.currentText().lower()
            domlimb = self.cbDom.currentText().lower()
            timepoint = self.cbTP.currentText()
            # Enforce timepoint ordering: previous timepoint must be complete.
            tp_idx = list(pfadef.TIMEPOINTS).index(timepoint)
            if tp_idx > 0:
                prev = pfadef.TIMEPOINTS[tp_idx - 1]
                if not pfadef.is_assessment_timepoint_completed(subjid, limb, prev):
                    QtWidgets.QMessageBox.warning(
                        self, "Timepoint Order Error",
                        f"Cannot select {timepoint}: {prev} is not complete for this limb.",
                    )
                    return
            if pfadef.is_assessment_timepoint_completed(subjid, limb, timepoint):
                QtWidgets.QMessageBox.warning(
                    self, "Already Completed",
                    f"{timepoint} is already complete for {subjid} / {limb}.",
                )
                return
        else:
            limb = afflimb  # screening screens the affected limb
            domlimb = ""
            timepoint = ""

        # Create the subject record if new.
        listfile = _list_file(mode)
        if not listfile.subject_exists(subjid):
            if mode == "screening":
                listfile.add_subject({
                    "subjid": subjid, "afflimb": afflimb,
                    "createdat": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            else:
                listfile.add_subject({
                    "subjid": subjid, "domlimb": domlimb, "afflimb": afflimb,
                    "createdat": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

        self.result = {
            "mode": mode, "subjid": subjid, "limb": limb,
            "afflimb": afflimb, "domlimb": domlimb, "timepoint": timepoint,
        }
        self.close()

    def closeEvent(self, event):
        if self.on_close_callback:
            self.on_close_callback(data=self.result)
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = SessionSetupWindow(onclosecb=lambda data: print(data))
    w.show()
    sys.exit(app.exec())
```

- [ ] **Step 2: Syntax check**

Run: `uv run python -m py_compile sessionsetupwindow.py`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add sessionsetupwindow.py
git commit -m "feat(ui): SessionSetupWindow combining mode/subject/limb/timepoint"
```

---

## Task 6: state machine — collapse setup states

**Files:**
- Modify: `plutofullassessstatemachine.py` (Events 53-56; States 181-200; init dict 214-234; handlers 272-300)

- [ ] **Step 1: Replace the three setup events with one `SETUP_DONE`**

In `class Events` (lines 53-56), replace:

```python
class Events(Enum):
    SUBJECT_SET = 0
    LIMB_SET = auto()
    TIMEPOINT_SET = auto()
```

with:

```python
class Events(Enum):
    SETUP_DONE = 0
```

- [ ] **Step 2: Collapse the setup states**

In `class States` (181-200), replace:

```python
    SUBJ_SELECT = 0
    LIMB_SELECT = auto()
    TIMEPOINT_SELECT = auto()
    MECH_SELECT = auto()
```

with:

```python
    SUBJ_SELECT = 0
    MECH_SELECT = auto()
```

- [ ] **Step 3: Fix the state→action map**

In the `self._stateactions = { ... }` dict (215-234), remove the two lines:

```python
            States.LIMB_SELECT: self._handle_limb_select,
            States.TIMEPOINT_SELECT: self._handle_timepoint_select,
```

- [ ] **Step 4: Replace the three setup handlers with one**

Replace `_handle_subject_select`, `_handle_limb_select`, `_handle_timepoint_select` (272-300) with:

```python
    def _handle_subject_select(self, event, data):
        """The Session Setup window has gathered everything and the worker has
        created the folder + protocol. Move straight to mechanism selection."""
        if event == Events.SETUP_DONE:
            self._state = States.MECH_SELECT
            self._pconsole.append(self._instruction)
            self.log(
                f"Session setup complete: {self._data.subjid} "
                f"[{self._data.mode}] limb={self._data.limb}."
            )
```

(The state machine no longer calls `set_subject`/`set_limb`/`set_timepoint`; the main window's worker has already populated `self._data` via `setup_session` + `create_session_folder` + `start_protocol`.)

- [ ] **Step 5: Syntax check**

Run: `uv run python -m py_compile plutofullassessstatemachine.py`
Expected: no output, exit 0.

- [ ] **Step 6: Commit**

```bash
git add plutofullassessstatemachine.py
git commit -m "feat(sm): collapse subject/limb/timepoint into single SETUP_DONE"
```

---

## Task 7: main window — wire the new flow, remove old controls

**Files:**
- Modify: `plutofullassessment.py` (imports 42-54; DEBUG 182-191; callbacks 215-387; close event 965-989; update_ui 1249-1280; details/session 1331-1337, 1419-1427; layout 1362-1407)

- [ ] **Step 1: Swap imports**

In the import block, replace:

```python
from subjectcreator import SubjectCreator
from subjectselector import SubjectSelector
...
from async_workers import LimbSetupWorker
```

with:

```python
from sessionsetupwindow import SessionSetupWindow
...
from async_workers import SessionSetupWorker
```

(`from async_workers import LimbSetupWorker` is at line 54 — change the imported name. The `SubjectCreator`/`SubjectSelector` imports are lines 44-45.)

- [ ] **Step 2: Replace the DEBUG bootstrap block**

Replace the `if DEBUG:` block (182-191) with a mode-correct bootstrap:

```python
        if DEBUG:
            self.data.setup_session({
                "mode": "assessment", "subjid": "1234", "limb": "left",
                "afflimb": "left", "domlimb": "right", "timepoint": "A0",
            })
            self.data.create_session_folder()
            self.data.start_protocol()
            self.pluto.send_heartbeat()
            self.pluto.set_limb(self.data.limb)
            self._smachine.run_statemachine(Events.SETUP_DONE, {})
```

- [ ] **Step 3: Replace subject/limb/timepoint button wiring**

In `_attach_guicontrol_callbacks` (215-224), replace these lines:

```python
        # Subject
        self.pbCreateSeelectSubject.clicked.connect(self._callback_createselect_subject)
        self.pbSelectSubject.clicked.connect(self._callback_select_subject)
        # Limb
        self.cbLimb.currentIndexChanged.connect(self.update_ui)
        self.pbSetLimb.clicked.connect(self._callback_limb_set)
        # Time point
        self.cbTimePoint.currentIndexChanged.connect(self.update_ui)
        self.pbSetTimePoint.clicked.connect(self._callback_timepoint_set)
```

with:

```python
        # Session setup (combined subject + limb + timepoint)
        self.pbSetupSession.clicked.connect(self._callback_setup_session)
```

- [ ] **Step 4: Replace the old setup callbacks with the new one**

Replace the block of methods `_callback_createselect_subject`, `_callback_select_subject`, `_callback_limb_set`, `_populate_timepoint_combobox`, `_callback_timepoint_set` (258-346) with:

```python
    def _callback_setup_session(self):
        self._maindisable = True
        self._currwndclosed = False
        self._subjwnd = SessionSetupWindow(
            parent=self, modal=True, onclosecb=self._setupwnd_close_event
        )
        self._subjwnd.show()

    def _setupwnd_close_event(self, data):
        if self._currwndclosed is True:
            self._subjwnd = None
            return
        self._currwndclosed = True
        self._maindisable = False
        if data:
            # Store fields, then build folder + protocol off the UI thread.
            self.data.setup_session(data)
            self.statusBar().showMessage("Creating session folder and protocol... Please wait.")
            self._maindisable = True
            self._setup_worker = SessionSetupWorker(self.data)
            self._setup_worker.progress.connect(self._on_setup_worker_progress)
            self._setup_worker.finished.connect(self._on_setup_worker_finished)
            self._setup_worker.error.connect(self._on_setup_worker_error)
            self._setup_worker.start()
        else:
            self._updatetable = True
            self.update_ui()

    def _on_setup_worker_progress(self, message):
        self.statusBar().showMessage(message)

    def _on_setup_worker_finished(self):
        try:
            self._smachine.run_statemachine(Events.SETUP_DONE, {})
            self._subjdetails = self._get_subject_details()
            self._title = " | ".join([
                "Pluto Full Assessment", self.data.subjid, self.data.mode,
                f"Dom: {self.data.domlimb}", f"Aff: {self.data.afflimb}",
                f"Limb: {self.data.limb}",
                f"TP: {self.data.timepoint}" if not self.data.is_screening else "screening",
                f"{self.data.session}",
            ])
            self.setWindowTitle(self._title)
            self.statusBar().showMessage("Session setup completed successfully.")
        except Exception as e:
            self._on_setup_worker_error(f"Error updating UI after setup: {str(e)}")
        finally:
            self._maindisable = False
            self._updatetable = True
            self._setup_worker = None
            self.update_ui()

    def _on_setup_worker_error(self, error_message):
        self._maindisable = False
        self._setup_worker = None
        QMessageBox.critical(self, "Error", f"Error during session setup:\n{error_message}")
        self.statusBar().showMessage("Error during session setup.")
        self.update_ui()
```

Also replace `self._limb_setup_worker = None` (line 180) with `self._setup_worker = None`.

- [ ] **Step 5: Remove dead methods**

Delete the `_subjwnd_close_event` method (965-989) — replaced by `_setupwnd_close_event`. Also delete `_callback_subjtype_select` (773-783): it is unconnected dead code that references the removed `cbSubjectType` and treats `_subjdetails` as a dict (it is now a string).

- [ ] **Step 6: Fix `update_ui` (remove limb/timepoint blocks)**

Replace the subject/limb/timepoint section of `update_ui` (1252-1280) with:

```python
        # Session setup
        self.pbSetupSession.setEnabled(
            self._maindisable is False and self._smachine.state == States.SUBJ_SELECT
        )
        self.lblSubjDetails.setText(self._subjdetails)
```

- [ ] **Step 7: Fix `_get_subject_details` and `_get_session_info`**

Replace `_get_subject_details` (1331-1337):

```python
    def _get_subject_details(self):
        _text = f"{self.data.subjid} | Aff: {self.data.afflimb}"
        if not self.data.is_screening:
            _text += f" | Dom: {self.data.domlimb}"
        return _text
```

Replace the body of `_get_session_info` (1419-1427):

```python
    def _get_session_info(self):
        _str = [
            f"{'' if self.data.session is None else self.data.session:<20}",
            f"{'' if self.data.subjid is None else self.data.subjid:<8}",
            f"{(self.data.mode or ''):<10}",
            f"{(self.data.limb or ''):<8}",
            f"{(self.data.timepoint or ''):<4}",
        ]
        return ":".join(_str)
```

- [ ] **Step 8: Rebuild the "Subject & Session" group with one button**

In `_group_left_column` (1362-1407), replace the Subject & Session population loop (1372-1384) with:

```python
        # Subject & Session: a single Setup Session button + details label.
        self.gbSession = QtWidgets.QGroupBox("Subject && Session")
        sv = QtWidgets.QVBoxLayout(self.gbSession)
        sv.setSpacing(4)
        self.pbSetupSession = QtWidgets.QPushButton("Setup Session")
        sv.addWidget(self.pbSetupSession)
        self._move_into(vl, sv, self.lblSubjDetails)
        # Old per-field controls from the .ui are no longer used — drop them.
        for _old in (
            self.pbCreateSeelectSubject, self.pbSelectSubject,
            self.horizontalLayout_2, self.pbSetLimb,
            self.horizontalLayout_timepoint, self.pbSetTimePoint,
        ):
            if isinstance(_old, QtWidgets.QWidget):
                _old.setParent(None)
            else:
                # nested layout: reparent under a throwaway widget so it is removed
                QtWidgets.QWidget().setLayout(_old)
```

(`pbSetupSession` is created here, so it exists before `_attach_guicontrol_callbacks` runs — confirm `_group_left_column()` is called at line 150, before `_attach_guicontrol_callbacks()` at 194. It is.)

- [ ] **Step 9: Syntax check**

Run: `uv run python -m py_compile plutofullassessment.py`
Expected: no output, exit 0.

- [ ] **Step 10: Grep for stragglers**

Run: `uv run python -c "import re,sys; t=open('plutofullassessment.py').read(); bad=[w for w in ['self.data.type','cbSubjectType','LimbSetupWorker','TYPE_LIMB_SET','LIMB_SELECT','TIMEPOINT_SELECT','_subjwnd_close_event'] if w in t]; print('STRAGGLERS:',bad); sys.exit(1 if bad else 0)"`
Expected: `STRAGGLERS: []`, exit 0. Fix any reported reference.

- [ ] **Step 11: Commit**

```bash
git add plutofullassessment.py
git commit -m "feat(main): single Setup Session flow; drop limb/timepoint controls and type"
```

---

## Task 8: delete dead files, full compile, smoke test

**Files:**
- Delete: `subjectselector.py`, `subjectcreator.py`

- [ ] **Step 1: Confirm nothing else imports the old windows**

Run: `uv run python -c "import subprocess,sys; out=subprocess.run(['git','grep','-n','-E','SubjectCreator|SubjectSelector|from subjectcreator|from subjectselector','--','*.py'],capture_output=True,text=True).stdout; print(out); sys.exit(1 if out.strip() else 0)"`
Expected: empty output, exit 0. (If `verify_mismatch_fix.py` or others reference them, update or leave — they are dev scripts, not the app entry point. Only the app path must be clean.)

- [ ] **Step 2: Delete the old files**

```bash
git rm subjectselector.py subjectcreator.py
```

- [ ] **Step 3: Compile the whole app surface**

Run: `uv run python -m py_compile plutofullassessdef.py plutofullassesssdata.py async_workers.py plutofullassessstatemachine.py sessionsetupwindow.py plutofullassessment.py`
Expected: no output, exit 0.

- [ ] **Step 4: Re-run the logic test**

Run: `uv run python tests/test_setup_logic.py`
Expected: prints `OK`, exit 0.

- [ ] **Step 5: Manual smoke test (requires a display; device optional)**

Run: `uv run python plutofullassessment.py`
Verify by hand:
1. Left column shows a single **Setup Session** button (no separate limb/timepoint rows).
2. Click it → window opens with Mode radios (Assessment default), Subject ID, Affected side, Limb, Dominant, Time point.
3. Select **Screening** → Limb / Dominant / Time point hide; only Affected side remains.
4. Screening: enter a new id, pick Affected = Left, Start → no error; a `screening/<id>/left/<session>/` folder with `<id>_left_screening_protocol.csv` (AROM rows only) appears under `<Documents>/homerpluto/`.
5. Assessment: new id, Limb=Left, Affected=Left, Dominant=Right, TP=A0, Start → `fullassessment/<id>/left/A0/<session>/` with `<id>_left_A0_protocol.csv`.
6. Main window proceeds to mechanism selection after setup.

Note: with `DEBUG = True` (current repo state) the app auto-bootstraps subject `1234`; set `debugconfig.DEBUG = False` to exercise the window manually.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove old subject create/select windows; finalize setup refactor"
```

---

## Self-review notes (already reconciled)

- **Spec coverage:** combined window (T5), modes + visibility (T5), unified id box w/ lookup (T5), screening AROM-only/own dir/single-shot (T1,T3), separate subject lists (T1,T5), affected-side gate kept, subjtype dropped (T1,T3), `{type}` layer + filename type removed (T2,T3), state collapse (T6), main UI rewire + DEBUG/title/session-info (T7), file deletion (T8).
- **Type consistency:** `setup_session(dict)`, `create_session_folder()`, `start_protocol()`, `SessionSetupWorker`, `Events.SETUP_DONE`, `is_task_included(taskname, limb, afflimb)`, `pfadef.is_assessment_timepoint_completed(...)`, `data.mode`/`data.is_screening` — names match across all tasks.
- **Out of scope:** legacy `{type}/` data migration; `plutopropass.py`; task-window internals beyond AROM-only screening.
