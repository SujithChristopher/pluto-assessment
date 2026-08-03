# Guided Single-Window Assessment GUI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new single-window PLUTO assessment GUI in `newgui/` where the hardware button drives a strictly linear protocol (calibration → AROM → PROM → assisted PROM → discrete reaching, over FPS/WFE/WURD/HOC) and the mouse is used only for setup, Accept, and Redo.

**Architecture:** A shell `QMainWindow` holds a `QStackedWidget`. A pure-Python `Sequencer` owns the linear step list and cursor. The existing task windows (`PlutoAPRomAssessWindow`, `PlutoAssistPRomAssessWindow`, `PlutoDiscReachAssessWindow`, `PlutoCalibrationWindow`) are reused unchanged except for a new `embedded=True` keyword that makes them behave as page widgets instead of top-level modals. Persistence goes through the existing `PlutoAssessmentData` so CSV/JSON output is identical to the current app.

**Tech Stack:** Python 3.12+, PySide6, pyqtgraph, pandas, `uv` for all commands.

**Spec:** `docs/superpowers/specs/2026-08-03-guided-gui-design.md`

## Global Constraints

- Package manager is `uv`. Every command is `uv run …`. Never `pip`, never `conda`, never bare `python`.
- Do not modify `plutofullassessment.py`. It must keep running exactly as it does today.
- Changes to root-level task windows are additive only: a new keyword argument defaulting to `False`. No behaviour change when it is absent.
- Data written to disk (protocol CSV, details JSON, raw/summary CSVs, folder layout) must stay identical to the current app.
- Tasks in the new flow: `CALIB`, `AROM`, `PROM`, `APROM`, `DISC`. Never `POSHOLD`, `PROP`, `FCTRLLOW`, `FCTRLMED`, `FCTRLHIGH`.
- Mechanism order comes from `pfadef.MECHANISMS` (`FPS`, `WFE`, `WURD`, `HOC`). Never hardcode a different order.
- Screening runs `CALIB` + `AROM` only. Assessment runs all five.
- No operator-facing skip or back controls anywhere in the new GUI.
- Tests are standalone scripts in `tests/`, run as `uv run python tests/<name>.py`, printing `OK` on success. There is no pytest in this project — follow `tests/test_setup_logic.py`.
- Syntax check after every code change: `uv run python -m py_compile <files>`.

---

### Task 1: Sequencer and auto-skip rules

Pure Python, no Qt, no device. This is the only unit-tested piece.

**Files:**
- Create: `newgui/__init__.py` (empty)
- Create: `newgui/sequencer.py`
- Test: `tests/test_newgui_sequencer.py`

**Interfaces:**
- Consumes: `plutofullassessdef.MECHANISMS` (list of mechanism names).
- Produces:
  - `Step` — frozen dataclass with `.mech: str`, `.task: str`, `.is_calib: bool`
  - `CALIB: str = "CALIB"`, `ASSESSMENT_TASKS: list[str]`, `SCREENING_TASKS: list[str]`
  - `build_steps(mode: str) -> list[Step]`
  - `Sequencer(mode: str)` with `.steps: list[Step]`, `.current() -> Step | None`, `.position() -> tuple[int, int]`, `.is_done() -> bool`, `.mark_completed(step: Step) -> None`, `.advance() -> None`, `.resume_from(completed: Iterable[tuple[str, str]]) -> None`
  - `disc_skip_reason(mech: str, arom: list | None) -> str | None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_newgui_sequencer.py`:

```python
"""Standalone logic checks for the guided-GUI sequencer.
Run: uv run python tests/test_newgui_sequencer.py  ->  prints OK."""
import pathlib
import sys

# Make the repo root importable when run as `python tests/test_newgui_sequencer.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import plutofullassessdef as pfadef
from newgui.sequencer import (
    CALIB,
    Sequencer,
    Step,
    build_steps,
    disc_skip_reason,
)


def test_assessment_step_list():
    steps = build_steps("assessment")
    # 4 mechanisms x (calib + 4 tasks)
    assert len(steps) == 4 * 5, len(steps)
    assert steps[0] == Step("FPS", CALIB)
    assert [s.task for s in steps[:5]] == [CALIB, "AROM", "PROM", "APROM", "DISC"]
    # Mechanism order follows pfadef.MECHANISMS.
    seen = []
    for s in steps:
        if s.mech not in seen:
            seen.append(s.mech)
    assert seen == list(pfadef.MECHANISMS), seen


def test_screening_step_list():
    steps = build_steps("screening")
    assert len(steps) == 4 * 2, len(steps)
    assert [s.task for s in steps[:2]] == [CALIB, "AROM"]
    assert all(s.task in (CALIB, "AROM") for s in steps)


def test_advance_and_position():
    seq = Sequencer("assessment")
    assert seq.current() == Step("FPS", CALIB)
    assert seq.position() == (1, 20)
    assert seq.is_done() is False
    seq.advance()
    assert seq.current() == Step("FPS", "AROM")
    assert seq.position() == (2, 20)


def test_advance_to_end():
    seq = Sequencer("screening")
    for _ in range(len(seq.steps)):
        seq.advance()
    assert seq.is_done() is True
    assert seq.current() is None


def test_advance_skips_completed_steps():
    """Auto-skipped DISC (marked completed) is stepped over, landing on the
    next mechanism's calibration."""
    seq = Sequencer("assessment")
    while seq.current() != Step("FPS", "APROM"):
        seq.advance()
    seq.mark_completed(Step("FPS", "DISC"))
    seq.advance()
    assert seq.current() == Step("WFE", CALIB), seq.current()


def test_resume_mid_mechanism_returns_to_that_calibration():
    seq = Sequencer("assessment")
    seq.resume_from([("FPS", "AROM"), ("FPS", "PROM")])
    assert seq.current() == Step("FPS", CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step("FPS", "APROM"), seq.current()


def test_resume_past_a_finished_mechanism():
    seq = Sequencer("assessment")
    seq.resume_from(
        [("FPS", t) for t in ("AROM", "PROM", "APROM", "DISC")]
    )
    assert seq.current() == Step("WFE", CALIB), seq.current()


def test_resume_everything_done():
    seq = Sequencer("screening")
    seq.resume_from([(m, "AROM") for m in pfadef.MECHANISMS])
    assert seq.is_done() is True


def test_disc_skip_reason():
    # No AROM recorded at all.
    assert disc_skip_reason("WFE", None) == "No valid AROM recorded"
    # Joint mechanism below the 10 deg threshold.
    assert disc_skip_reason("WFE", [0.0, 4.0]) == (
        "AROM 4.00deg below 10.0deg threshold"
    )
    # Joint mechanism above threshold -> not skipped.
    assert disc_skip_reason("WFE", [0.0, 40.0]) is None
    # HOC uses cm and a 2.0 threshold.
    assert disc_skip_reason("HOC", [0.0, 1.0]) == (
        "AROM 1.00cm below 2.0cm threshold"
    )
    assert disc_skip_reason("HOC", [0.0, 5.0]) is None


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run python tests/test_newgui_sequencer.py
```

Expected: `ModuleNotFoundError: No module named 'newgui'`

- [ ] **Step 3: Write the implementation**

Create `newgui/__init__.py` as an empty file, and `newgui/sequencer.py`:

```python
"""Linear step sequencing for the guided assessment GUI.

The guided GUI walks a fixed list of (mechanism, task) steps. This module owns
that list and the cursor into it. It is deliberately free of Qt and of the
device so it can be unit tested.
"""

from dataclasses import dataclass
from typing import Iterable

import plutofullassessdef as pfadef

# Flow-only step: calibration is never a protocol CSV row.
CALIB = "CALIB"

# Task order within a mechanism. Assessment runs the full set; screening is a
# quick AROM-only sweep (matches pfadef.SCREENING_MECH_TASKS).
ASSESSMENT_TASKS = ["AROM", "PROM", "APROM", "DISC"]
SCREENING_TASKS = ["AROM"]

# Minimum AROM range for discrete reaching to be worth running.
DISC_AROM_THRESHOLD = {"HOC": 2.0}      # cm
DISC_AROM_THRESHOLD_DEFAULT = 10.0      # deg
DISC_AROM_UNIT = {"HOC": "cm"}
DISC_AROM_UNIT_DEFAULT = "deg"


@dataclass(frozen=True)
class Step:
    """One stop in the guided flow."""

    mech: str
    task: str

    @property
    def is_calib(self) -> bool:
        return self.task == CALIB


def tasks_for_mode(mode: str) -> list[str]:
    return list(SCREENING_TASKS if mode == "screening" else ASSESSMENT_TASKS)


def build_steps(mode: str) -> list[Step]:
    """Every mechanism, calibration first, then its tasks in protocol order."""
    _steps = []
    for _mech in pfadef.MECHANISMS:
        _steps.append(Step(_mech, CALIB))
        for _task in tasks_for_mode(mode):
            _steps.append(Step(_mech, _task))
    return _steps


def disc_skip_reason(mech: str, arom: list | None) -> str | None:
    """Why discrete reaching should be auto-skipped for this mechanism, or None
    if it should run. Mirrors the rule in plutofullassessment.py."""
    if arom is None:
        return "No valid AROM recorded"
    _thresh = DISC_AROM_THRESHOLD.get(mech, DISC_AROM_THRESHOLD_DEFAULT)
    _unit = DISC_AROM_UNIT.get(mech, DISC_AROM_UNIT_DEFAULT)
    _range = abs(arom[1] - arom[0])
    if _range < _thresh:
        return f"AROM {_range:.2f}{_unit} below {_thresh}{_unit} threshold"
    return None


class Sequencer:
    """Cursor over the step list.

    Completion is tracked as a set of (mechanism, task) pairs for the non-calib
    steps. A calibration step counts as done only when every task of its
    mechanism is done, so resuming mid-mechanism lands on that mechanism's
    calibration and the device is always calibrated before a task runs."""

    def __init__(self, mode: str):
        self.mode = mode
        self.steps: list[Step] = build_steps(mode)
        self._cursor = 0
        self._completed: set[tuple[str, str]] = set()

    def current(self) -> Step | None:
        if self.is_done():
            return None
        return self.steps[self._cursor]

    def position(self) -> tuple[int, int]:
        """1-based (current, total) for the header counter."""
        return min(self._cursor + 1, len(self.steps)), len(self.steps)

    def is_done(self) -> bool:
        return self._cursor >= len(self.steps)

    def mark_completed(self, step: Step) -> None:
        """Record a step as finished. Calibration steps are flow-only and are
        tracked implicitly through their mechanism's tasks."""
        if not step.is_calib:
            self._completed.add((step.mech, step.task))

    def advance(self) -> None:
        self._cursor += 1
        self._skip_completed()

    def resume_from(self, completed: Iterable[tuple[str, str]]) -> None:
        """Rewind to the first step that is not already done."""
        self._completed = {(_m, _t) for _m, _t in completed}
        self._cursor = 0
        self._skip_completed()

    def _skip_completed(self) -> None:
        while self._cursor < len(self.steps):
            _step = self.steps[self._cursor]
            if _step.is_calib:
                if not self._mech_completed(_step.mech):
                    return
            elif (_step.mech, _step.task) not in self._completed:
                return
            self._cursor += 1

    def _mech_completed(self, mech: str) -> bool:
        _tasks = [_s for _s in self.steps if _s.mech == mech and not _s.is_calib]
        return all((_s.mech, _s.task) in self._completed for _s in _tasks)
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
uv run python tests/test_newgui_sequencer.py
```

Expected: each `test_… ok` line, then `OK`.

- [ ] **Step 5: Syntax check**

```bash
uv run python -m py_compile newgui/sequencer.py tests/test_newgui_sequencer.py
```

- [ ] **Step 6: Commit**

```bash
git add newgui/__init__.py newgui/sequencer.py tests/test_newgui_sequencer.py
git commit -m "feat(newgui): linear step sequencer with resume and DISC auto-skip rule"
```

---

### Task 2: `embedded` mode for the reused task windows

The task windows must stop behaving as top-level modals and stop popping the accept/comment dialog, so they can live inside the stack. Additive keyword only; `embedded=False` preserves today's behaviour exactly.

**Files:**
- Modify: `plutocalibwindow.py` (`PlutoCalibrationWindow.__init__`, `closeEvent`)
- Modify: `plutoapromwindow.py` (`PlutoAPRomAssessWindow.__init__`, `closeEvent`)
- Modify: `plutoassistpromwindow.py` (`PlutoAssistPRomAssessWindow.__init__`, `closeEvent`)
- Modify: `plutodiscreachwindow.py` (`PlutoDiscReachAssessWindow.__init__`, `closeEvent`)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: all four classes accept `embedded: bool = False`. When `True`:
  - the constructor does not call `showMaximized()` and ignores `modal`;
  - `closeEvent` delivers its payload with `status=None` and `taskcomment=""` instead of running `CommentDialog`.
  - Payload keys stay as they are today: `PlutoCalibrationWindow` → `{"done": bool}`; `PlutoAPRomAssessWindow` → `{"romval": …, "done": bool, "status": …, "taskcomment": …}`; `PlutoAssistPRomAssessWindow` → same shape as AP-ROM; `PlutoDiscReachAssessWindow` → `{"done": bool, "status": …, "taskcomment": …}` (no `romval`).

- [ ] **Step 1: Add the keyword to `PlutoCalibrationWindow`**

In `plutocalibwindow.py`, extend the signature:

```python
    def __init__(
        self,
        parent=None,
        plutodev: QtPluto = None,
        limb=None,
        mechanism: str = None,
        modal=False,
        dataviewer=False,
        onclosecb=None,
        heartbeat=False,
        embedded=False,
    ):
```

Immediately after `self.ui.setupUi(self)` and the existing size fixes, store the flag and skip modality when embedded:

```python
        # Embedded mode: this window is used as a page inside the guided GUI's
        # stacked widget, so it must not become a top-level modal.
        self._embedded = embedded

        if modal and not embedded:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
```

(Replace the existing `if modal:` block with the version above.)

- [ ] **Step 2: Add the keyword to the three assessment windows**

In each of `plutoapromwindow.py` (`PlutoAPRomAssessWindow`), `plutoassistpromwindow.py` (`PlutoAssistPRomAssessWindow`), `plutodiscreachwindow.py` (`PlutoDiscReachAssessWindow`), extend the signature the same way:

```python
    def __init__(
        self,
        parent=None,
        plutodev: QtPluto = None,
        assessinfo: dict = None,
        modal=False,
        onclosecb=None,
        embedded=False,
    ):
```

and replace the `self.showMaximized()` / `if modal:` pair with:

```python
        # Embedded mode: used as a page inside the guided GUI's stacked widget,
        # so it must not show itself as a maximised top-level modal.
        self._embedded = embedded
        if not embedded:
            self.showMaximized()
            if modal:
                self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
```

- [ ] **Step 3: Bypass `CommentDialog` in `closeEvent` when embedded**

In `plutoapromwindow.py`, inside `closeEvent`, immediately after the existing `self._arom_skipped` early-return block, insert:

```python
        # Embedded: the guided GUI's Accept/Redo footer replaces the comment
        # dialog, so deliver the payload with the status left for the caller.
        if self._embedded:
            data = {
                "romval": self.data.rom,
                "done": self.data.all_trials_done,
                "status": None,
                "taskcomment": "",
            }
            if self.on_close_callback:
                self.on_close_callback(data=data)
            self._detach_pluto_callbacks()
            return super().closeEvent(event)
```

In `plutoassistpromwindow.py`, insert the same block at the top of `closeEvent`, after the existing `self.pluto.set_control_type("NONE")` call:

```python
        if self._embedded:
            data = {
                "romval": self.data.rom,
                "done": self.data.all_trials_done,
                "status": None,
                "taskcomment": "",
            }
            if self.on_close_callback:
                self.on_close_callback(data=data)
            self._detach_pluto_callbacks()
            try:
                self._devdatawnd.close()
            except Exception:
                pass
            return super().closeEvent(event)
```

In `plutodiscreachwindow.py`, insert at the top of `closeEvent` (this window has no `romval`):

```python
        if self._embedded:
            data = {
                "done": self.data.all_trials_done,
                "status": None,
                "taskcomment": "",
            }
            if self.on_close_callback:
                self.on_close_callback(data=data)
            self._detach_pluto_callbacks()
            return super().closeEvent(event)
```

`plutocalibwindow.py` needs no `closeEvent` change — it never shows a comment dialog.

- [ ] **Step 4: Syntax check**

```bash
uv run python -m py_compile plutocalibwindow.py plutoapromwindow.py plutoassistpromwindow.py plutodiscreachwindow.py
```

- [ ] **Step 5: Verify the old GUI is unaffected**

```bash
uv run python plutofullassessment.py
```

Set up a throwaway session and run one AROM task to the end. Expected: window still opens maximised and modal, and the accept/reject comment dialog still appears on completion — i.e. no visible change.

- [ ] **Step 6: Commit**

```bash
git add plutocalibwindow.py plutoapromwindow.py plutoassistpromwindow.py plutodiscreachwindow.py
git commit -m "feat: embedded mode for calibration and assessment task windows"
```

---

### Task 3: Shell window, setup page, ready page

At the end of this task the new GUI launches, runs setup, and parks on the first `ReadyPage` waiting for the PLUTO button. Task pages are not wired yet — pressing the button logs to the status bar and does nothing else.

**Files:**
- Create: `newgui/setup.py`
- Create: `newgui/shell.py`
- Create: `newgui/main.py`

**Interfaces:**
- Consumes: `newgui.sequencer.Sequencer`, `newgui.sequencer.Step`, `newgui.sequencer.CALIB`.
- Produces:
  - `newgui.setup.EmbeddedSetupPage(onstartcb)` — a `QWidget`-usable page wrapping `SessionSetupWindow`; calls `onstartcb(dict)` with the setup dict when Start is pressed.
  - `newgui.shell.PlutoGuidedAssessor(port: str)` — the single `QMainWindow`, with `.pluto`, `.data`, `.seq`, and methods `._show_ready()`, `._start_current_step()` (stub in this task), `._set_footer_hint(text)`, `._set_footer_review()`.
  - `newgui.main.main()` — entry point.

- [ ] **Step 1: Write the embedded setup page**

Create `newgui/setup.py`:

```python
"""Session setup as an embedded page.

Reuses SessionSetupWindow wholesale — mode radios, subject list handling,
timepoint ordering checks — and only strips its window behaviour so it can sit
inside the guided GUI's stacked widget."""

from PySide6 import QtCore, QtWidgets

from sessionsetupwindow import SessionSetupWindow


class EmbeddedSetupPage(SessionSetupWindow):
    """SessionSetupWindow as a page widget. Calls onstartcb(setupdict) when the
    operator presses Start; the dict is the same one the old GUI receives."""

    def __init__(self, onstartcb, parent=None):
        # modal=False and no close callback: the guided shell reacts to Start
        # directly rather than to the window closing.
        super().__init__(parent=parent, modal=False, onclosecb=None)
        self._onstartcb = onstartcb
        # Suppress the one-shot centring in showEvent — meaningless (and
        # disruptive) for a widget inside a layout.
        self._centered = True
        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        # Cancel makes no sense as the first screen of the flow.
        self.pbCancel.setVisible(False)

    def _on_start(self):
        super()._on_start()          # validates, creates the subject record
        if self.result:
            self._onstartcb(dict(self.result))

    def closeEvent(self, event):
        # The base class calls close() at the end of _on_start, which would hide
        # this page. Embedded, the shell owns page switching — swallow it, so
        # the page stays available if setup fails and we come back to it.
        event.ignore()
```

- [ ] **Step 2: Write the shell**

Create `newgui/shell.py`:

```python
"""The single window of the guided PLUTO assessment GUI.

One QMainWindow, one QStackedWidget. The PLUTO hardware button advances the
flow; the mouse is used only for setup, Accept and Redo."""

import pathlib
import time

from PySide6 import QtCore, QtGui, QtWidgets

import plutodefs as pdef
import plutofullassessdef as pfadef
from async_workers import SessionSetupWorker
from plutofullassesssdata import PlutoAssessmentData
from qtpluto import QtPluto
from s3sync import S3SyncWorker, load_s3_config

from newgui.sequencer import CALIB, Sequencer, Step
from newgui.setup import EmbeddedSetupPage

# WURD has no artwork of its own; it reuses the wrist flexion/extension image,
# matching the old GUI.
MECH_IMAGES = {
    "FPS": "fps.png",
    "WFE": "wfe.png",
    "WURD": "wfe.png",
    "HOC": "hoc.png",
}

TASK_INSTRUCTIONS = {
    CALIB: "Fit the {mech} mechanism, then press the PLUTO button to calibrate.",
    "AROM": "Active range of motion. Press the PLUTO button to start.",
    "PROM": "Passive range of motion. Press the PLUTO button to start.",
    "APROM": "Assisted passive range of motion. Press the PLUTO button to start.",
    "DISC": "Discrete reaching. Press the PLUTO button to start.",
}

STEP_LABELS = dict(pfadef.TASK_LABELS)
STEP_LABELS[CALIB] = "Calibration"


class ReadyPage(QtWidgets.QWidget):
    """Between-steps screen: what is coming and how to start it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        _lay = QtWidgets.QVBoxLayout(self)
        _lay.setContentsMargins(40, 30, 40, 30)
        _lay.setSpacing(18)
        _lay.addStretch(1)

        self.lblImage = QtWidgets.QLabel()
        self.lblImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(self.lblImage)

        self.lblWhat = QtWidgets.QLabel()
        self.lblWhat.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblWhat.setStyleSheet("font-size: 22pt; font-weight: 600;")
        _lay.addWidget(self.lblWhat)

        self.lblHow = QtWidgets.QLabel()
        self.lblHow.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblHow.setWordWrap(True)
        self.lblHow.setStyleSheet("font-size: 14pt; color: #2563eb;")
        _lay.addWidget(self.lblHow)
        _lay.addStretch(1)

    def show_step(self, step: Step, resumed: bool = False):
        _label = STEP_LABELS.get(step.task, step.task)
        _mechlabel = pfadef.MECH_LABELS.get(step.mech, step.mech)
        self.lblWhat.setText(
            f"{_mechlabel} — {_label}" + ("  (resumed)" if resumed else "")
        )
        self.lblHow.setText(TASK_INSTRUCTIONS[step.task].format(mech=step.mech))
        _img = pathlib.Path(__file__).resolve().parent.parent / "assets" / MECH_IMAGES[step.mech]
        if step.is_calib and _img.exists():
            _pix = QtGui.QPixmap(_img.as_posix())
            self.lblImage.setPixmap(
                _pix.scaledToHeight(320, QtCore.Qt.TransformationMode.SmoothTransformation)
            )
            self.lblImage.setVisible(True)
        else:
            self.lblImage.setVisible(False)


class DonePage(QtWidgets.QWidget):
    """End of session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        _lay = QtWidgets.QVBoxLayout(self)
        _lay.addStretch(1)
        self.lblTitle = QtWidgets.QLabel("Session complete")
        self.lblTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblTitle.setStyleSheet("font-size: 24pt; font-weight: 600;")
        _lay.addWidget(self.lblTitle)
        self.lblDetail = QtWidgets.QLabel("")
        self.lblDetail.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblDetail.setStyleSheet("font-size: 15pt;")
        _lay.addWidget(self.lblDetail)
        _lay.addStretch(1)


class PlutoGuidedAssessor(QtWidgets.QMainWindow):
    """The single window."""

    def __init__(self, port: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PLUTO Guided Assessment")

        # Device.
        self.pluto = QtPluto(port)
        self.pluto.btnreleased.connect(self._callback_btn_released)
        self.pluto.get_version()
        self.pluto.start_sensorstream()

        # Session data and flow.
        self.data = PlutoAssessmentData()
        self.seq: Sequencer | None = None
        self._setup_worker = None
        self._taskpage = None
        self._resumed = False

        self._build_ui()
        self._init_timers()
        self._init_s3sync()

        self.stack.setCurrentWidget(self.pageSetup)
        self._set_footer_hint("Fill in the session details, then press Start.")
        self.showMaximized()

    #
    # UI construction
    #
    def _build_ui(self):
        _central = QtWidgets.QWidget()
        self.setCentralWidget(_central)
        _outer = QtWidgets.QVBoxLayout(_central)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)

        # Header: where we are.
        _head = QtWidgets.QHBoxLayout()
        _head.setContentsMargins(18, 12, 18, 12)
        self.lblHeader = QtWidgets.QLabel("Session setup")
        self.lblHeader.setStyleSheet("font-size: 16pt; font-weight: 600;")
        self.lblCounter = QtWidgets.QLabel("")
        self.lblCounter.setStyleSheet("font-size: 13pt; color: #6b7280;")
        self.lblS3Sync = QtWidgets.QLabel("")
        _head.addWidget(self.lblHeader)
        _head.addStretch(1)
        _head.addWidget(self.lblCounter)
        _head.addSpacing(20)
        _head.addWidget(self.lblS3Sync)
        _outer.addLayout(_head)

        # Pages.
        self.stack = QtWidgets.QStackedWidget()
        _outer.addWidget(self.stack, 1)

        self.pageSetup = EmbeddedSetupPage(onstartcb=self._on_setup_start)
        self.pageReady = ReadyPage()
        self.pageDone = DonePage()
        for _p in (self.pageSetup, self.pageReady, self.pageDone):
            self.stack.addWidget(_p)

        # Footer: hint line or Accept/Redo.
        _foot = QtWidgets.QHBoxLayout()
        _foot.setContentsMargins(18, 10, 18, 14)
        self.lblHint = QtWidgets.QLabel("")
        self.lblHint.setStyleSheet("font-size: 13pt; color: #6b7280;")
        self.pbAccept = QtWidgets.QPushButton("Accept")
        self.pbAccept.setObjectName("btnPrimary")
        self.pbAccept.setMinimumSize(140, 40)
        self.pbRedo = QtWidgets.QPushButton("Redo")
        self.pbRedo.setMinimumSize(140, 40)
        _foot.addWidget(self.lblHint)
        _foot.addStretch(1)
        _foot.addWidget(self.pbRedo)
        _foot.addWidget(self.pbAccept)
        _outer.addLayout(_foot)
        self._set_footer_hint("")

    def _set_footer_hint(self, text: str):
        self.lblHint.setText(text)
        self.lblHint.setVisible(True)
        self.pbAccept.setVisible(False)
        self.pbRedo.setVisible(False)

    def _set_footer_review(self):
        self.lblHint.setVisible(False)
        self.pbAccept.setVisible(True)
        self.pbRedo.setVisible(True)

    #
    # Timers, status bar, sync
    #
    def _init_timers(self):
        self.apptime = 0
        self.statustimer = QtCore.QTimer()
        self.statustimer.timeout.connect(self._callback_status_timer)
        self.statustimer.start(1000)
        self.heartbeattimer = QtCore.QTimer()
        self.heartbeattimer.timeout.connect(lambda: self.pluto.send_heartbeat())
        self.heartbeattimer.start(250)

    def _callback_status_timer(self):
        self.apptime += 1
        _con = self.pluto.is_connected()
        _step = self.seq.current() if self.seq else None
        self.statusBar().showMessage(
            " | ".join((
                f"{self.apptime:5d}s",
                _con if _con != "" else "Disconnected",
                f"FR: {self.pluto.framerate():4.1f}Hz",
                f"{self.data.subjid}",
                f"{_step.mech}/{_step.task}" if _step else "-",
            ))
        )

    def _init_s3sync(self):
        self._last_sync_kick = 0.0
        self._s3sync = S3SyncWorker(
            root=pfadef.homer_data_root(), config=load_s3_config()
        )
        self._s3sync.status.connect(self._on_s3_status)
        self._s3sync.start()

    def _on_s3_status(self, state, pending, message):
        _map = {
            "disabled": ("⚪ Sync off", "#9aa0a6"),
            "offline": ("⚪ Offline ↻", "#9aa0a6"),
            "syncing": (f"\U0001f535 Syncing… ({pending})", "#2563eb"),
            "synced": ("\U0001f7e2 Synced", "#0a7d00"),
            "error": ("\U0001f534 Sync error", "#c62828"),
        }
        _text, _color = _map.get(state, ("", "#000000"))
        self.lblS3Sync.setText(_text)
        self.lblS3Sync.setStyleSheet(f"color:{_color}; font-weight:600;")
        self.lblS3Sync.setToolTip(message or "")

    def _kick_sync(self):
        _now = time.monotonic()
        if _now - self._last_sync_kick >= 5.0:
            self._last_sync_kick = _now
            self._s3sync.request_sweep()

    #
    # Setup
    #
    def _on_setup_start(self, setup: dict):
        self.data.setup_session(setup)
        self.seq = Sequencer(setup["mode"])
        self.statusBar().showMessage("Creating session folder and protocol...")
        self._set_footer_hint("Creating session folder and protocol...")
        self._setup_worker = SessionSetupWorker(self.data)
        self._setup_worker.finished.connect(self._on_setup_finished)
        self._setup_worker.error.connect(self._on_setup_error)
        self._setup_worker.start()

    def _on_setup_finished(self):
        self._setup_worker = None
        self.pluto.send_heartbeat()
        self.pluto.set_limb(self.data.limb)
        self.setWindowTitle(
            " | ".join((
                "PLUTO Guided Assessment", self.data.subjid, self.data.mode,
                f"Limb: {self.data.limb}",
                "screening" if self.data.is_screening else f"TP: {self.data.timepoint}",
            ))
        )
        self._show_ready()

    def _on_setup_error(self, message: str):
        self._setup_worker = None
        QtWidgets.QMessageBox.critical(
            self, "Error", f"Error during session setup:\n{message}"
        )
        self.stack.setCurrentWidget(self.pageSetup)
        self._set_footer_hint("Fix the session details and press Start again.")

    #
    # Flow
    #
    def _show_ready(self):
        """Park on the ready screen for the current step."""
        _step = self.seq.current()
        if _step is None:
            self._show_done()
            return
        self.pageReady.show_step(_step, resumed=self._resumed)
        self._resumed = False
        self.stack.setCurrentWidget(self.pageReady)
        self._update_header()
        self._set_footer_hint("Press the PLUTO button to continue.")
        self._kick_sync()

    def _show_done(self):
        self.stack.setCurrentWidget(self.pageDone)
        self.lblHeader.setText("Done")
        self.lblCounter.setText("")
        self._set_footer_hint("You can close the window.")
        self._kick_sync()

    def _update_header(self):
        _step = self.seq.current()
        if _step is None:
            return
        _n, _total = self.seq.position()
        self.lblHeader.setText(
            f"{_step.mech} · {STEP_LABELS.get(_step.task, _step.task)}"
        )
        self.lblCounter.setText(f"{_n} / {_total}")

    def _start_current_step(self):
        """Launch the task page for the current step. Wired in Task 4."""
        self.statusBar().showMessage(f"TODO start {self.seq.current()}")

    #
    # Device button
    #
    def _callback_btn_released(self):
        # Navigation only while a task page is not running; task pages attach
        # their own handler and own the button while live.
        if self._taskpage is not None:
            return
        if self.stack.currentWidget() is self.pageReady:
            self._start_current_step()

    def closeEvent(self, event):
        self.statustimer.stop()
        self.heartbeattimer.stop()
        try:
            self._s3sync.stop()
        except Exception:
            pass
        return super().closeEvent(event)
```

- [ ] **Step 3: Write the entry point**

Create `newgui/main.py`:

```python
"""Entry point for the guided PLUTO assessment GUI.

Run: uv run python newgui/main.py"""

import pathlib
import sys

# Make the repository root importable when run as a script from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from plutofullassessment import APP_STYLESHEET
from newgui.shell import PlutoGuidedAssessor


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    window = PlutoGuidedAssessor(port=pfadef.PLUTOCOMM)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Check `S3SyncWorker.stop` exists**

```bash
uv run python -c "import s3sync, inspect; print([m for m in dir(s3sync.S3SyncWorker) if not m.startswith('__')])"
```

If there is no `stop` method, remove the `self._s3sync.stop()` call from `closeEvent` (the `try/except` already tolerates it, but do not leave a call to a method that does not exist).

- [ ] **Step 5: Syntax check**

```bash
uv run python -m py_compile newgui/setup.py newgui/shell.py newgui/main.py
```

- [ ] **Step 6: Run it**

```bash
uv run python newgui/main.py
```

Expected: one maximised window, setup form embedded in it (no separate dialog), header reading "Session setup". Filling in an assessment session and pressing Start swaps to the ready screen showing the FPS image, "Forearm Pronation/Supination — Calibration", counter `1 / 20`, and the hint "Press the PLUTO button to continue." Pressing the device button writes a `TODO start …` message to the status bar.

- [ ] **Step 7: Commit**

```bash
git add newgui/setup.py newgui/shell.py newgui/main.py
git commit -m "feat(newgui): shell window with embedded setup and ready pages"
```

---

### Task 4: Task pages — calibration and assessment steps run

**Files:**
- Create: `newgui/pages.py`
- Modify: `newgui/shell.py` (`_start_current_step`, new `_on_task_closed`, `_on_calib_closed`)

**Interfaces:**
- Consumes: `newgui.sequencer.Step`, `PlutoAssessmentData`, `QtPluto`.
- Produces: `newgui.pages.build_page(step: Step, pluto: QtPluto, data: PlutoAssessmentData, onclosecb) -> QtWidgets.QWidget` — a fresh embedded task widget for the step. The caller must have already called `data.protocol.set_mechanism/set_task` and `data.detailedsummary.set_mechanism/set_task` for non-calibration steps, because the raw/summary filenames derive from them.

- [ ] **Step 1: Write the page factory**

Create `newgui/pages.py`:

```python
"""Builds the embedded task widget for a step.

The assessinfo dicts are copied from plutofullassessment.py so the task windows
receive exactly what they receive in the old GUI."""

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from plutoapromwindow import PlutoAPRomAssessWindow
from plutoassistpromwindow import PlutoAssistPRomAssessWindow
from plutocalibwindow import PlutoCalibrationWindow
from plutodiscreachwindow import PlutoDiscReachAssessWindow
from plutofullassesssdata import PlutoAssessmentData
from qtpluto import QtPluto

from newgui.sequencer import CALIB, Step


def build_page(step: Step, pluto: QtPluto, data: PlutoAssessmentData, onclosecb):
    if step.task == CALIB:
        return _calib_page(step, pluto, data, onclosecb)
    if step.task == "AROM":
        return _rom_page(step, pluto, data, onclosecb, pfadef.ROMType.ACTIVE)
    if step.task == "PROM":
        return _rom_page(step, pluto, data, onclosecb, pfadef.ROMType.PASSIVE)
    if step.task == "APROM":
        return _aprom_page(step, pluto, data, onclosecb)
    if step.task == "DISC":
        return _disc_page(step, pluto, data, onclosecb)
    raise ValueError(f"No page for task [{step.task}]")


def _calib_page(step, pluto, data, onclosecb):
    return PlutoCalibrationWindow(
        plutodev=pluto,
        mechanism=step.mech,
        limb=data.limb,
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _rom_page(step, pluto, data, onclosecb, romtype):
    _protocol = data.protocol
    _info = {
        "type": "stroke",
        "limb": data.limb,
        "mechanism": step.mech,
        "romtype": romtype,
        "session": data.session,
        "ntrials": _protocol.get_no_of_trials(step.mech, step.task),
        "rawfile": _protocol.rawfilename,
        "summaryfile": _protocol.summaryfilename,
    }
    if romtype == pfadef.ROMType.PASSIVE:
        # PROM boundaries come from AROM's best cycle; None when AROM was not
        # completed, which makes the window fall back to a plain display.
        _info["arom"] = data.detailedsummary.get_arom_if_completed()
    return PlutoAPRomAssessWindow(
        plutodev=pluto,
        assessinfo=_info,
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _aprom_page(step, pluto, data, onclosecb):
    _protocol = data.protocol
    return PlutoAssistPRomAssessWindow(
        plutodev=pluto,
        assessinfo={
            "type": "stroke",
            "limb": data.limb,
            "mechanism": step.mech,
            "session": data.session,
            "ntrials": _protocol.get_no_of_trials(step.mech, "APROM"),
            "rawfile": _protocol.rawfilename,
            "summaryfile": _protocol.summaryfilename,
            "arom": data.detailedsummary.get_arom(),
            "duration": pfadef.get_task_constants("APROM").DURATION,
            "apromtype": pfadef.APROM.APROMTYPE,
        },
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _disc_page(step, pluto, data, onclosecb):
    _protocol = data.protocol
    return PlutoDiscReachAssessWindow(
        plutodev=pluto,
        assessinfo={
            "subjid": data.subjid,
            "type": "stroke",
            "limb": data.limb,
            "mechanism": step.mech,
            "session": data.session,
            "ntrials": _protocol.get_no_of_trials(step.mech, "DISC"),
            "rawfile": _protocol.rawfilename,
            "summaryfile": _protocol.summaryfilename,
            "arom": data.detailedsummary.get_arom(),
        },
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )
```

- [ ] **Step 2: Launch pages from the shell**

In `newgui/shell.py`, add the import:

```python
from newgui.pages import build_page
```

Replace the `_start_current_step` stub with:

```python
    def _start_current_step(self):
        """Build and show the task widget for the current step."""
        _step = self.seq.current()
        if _step is None:
            self._show_done()
            return
        # A new mechanism: select it in both data stores before anything else.
        if _step.mech != self.data.protocol.mech:
            self.data.protocol.set_mechanism(_step.mech)
            self.data.detailedsummary.set_mechanism(_step.mech)
        _cb = self._on_calib_closed if _step.is_calib else self._on_task_closed
        if not _step.is_calib:
            # set_task stamps the task time that the raw/summary filenames use,
            # so it must happen before the page is built.
            self.data.protocol.set_task(_step.task)
            self.data.detailedsummary.set_task(_step.task)
        self._taskpage = build_page(_step, self.pluto, self.data, _cb)
        self.stack.addWidget(self._taskpage)
        self.stack.setCurrentWidget(self._taskpage)
        self._update_header()
        self._set_footer_hint("")

    def _discard_taskpage(self):
        """Remove and destroy the current task widget."""
        if self._taskpage is None:
            return
        self.stack.removeWidget(self._taskpage)
        self._taskpage.deleteLater()
        self._taskpage = None

    def _on_calib_closed(self, data=None):
        """Calibration has no review: success advances, failure retries."""
        _done = bool(data and data.get("done"))
        _step = self.seq.current()
        self._discard_taskpage()
        if _done:
            self.data.protocol.set_mechanism_calibrated(_step.mech)
            self.seq.advance()
        self._show_ready()

    def _on_task_closed(self, data=None):
        """A task finished. Review is wired in Task 5; for now just advance."""
        self.statusBar().showMessage(f"task closed: {data}")
        self._discard_taskpage()
        self.seq.advance()
        self._show_ready()
```

- [ ] **Step 3: Syntax check**

```bash
uv run python -m py_compile newgui/pages.py newgui/shell.py
```

- [ ] **Step 4: Run it with the device**

```bash
uv run python newgui/main.py
```

Expected: on the FPS calibration ready screen, pressing the PLUTO button swaps the page to the calibration display inside the same window — no new window appears. Completing calibration returns to a ready screen reading "Forearm Pronation/Supination — Active ROM". Pressing the button again shows the AROM display in the same window; finishing the AROM trial returns to the PROM ready screen.

- [ ] **Step 5: Commit**

```bash
git add newgui/pages.py newgui/shell.py
git commit -m "feat(newgui): run calibration and assessment tasks as embedded pages"
```

---

### Task 5: Review footer — Accept and Redo persist the result

**Files:**
- Modify: `newgui/shell.py` (`_on_task_closed`, new `_on_accept`, `_on_redo`, `_persist`)

**Interfaces:**
- Consumes: `build_page` from Task 4, the payload shape from Task 2.
- Produces: `PlutoGuidedAssessor._persist(status: str, payload: dict, write_protocol: bool)` — writes the details JSON entry and, when `write_protocol` is true, the protocol CSV row.

- [ ] **Step 1: Wire the footer buttons**

In `_build_ui`, after the buttons are created, connect them:

```python
        self.pbAccept.clicked.connect(self._on_accept)
        self.pbRedo.clicked.connect(self._on_redo)
```

- [ ] **Step 2: Replace `_on_task_closed` and add the review handlers**

```python
    def _on_task_closed(self, data=None):
        """A task page finished. Keep its display on screen and swap the footer
        to Accept / Redo. closeEvent() only hides an embedded widget, so it is
        re-shown here to freeze the final display for the operator."""
        self._lastpayload = dict(data or {})
        # The task terminated itself (too many failed AROM trials): no review.
        if self._lastpayload.get("status") == pfadef.AssessStatus.SKIPPED.value:
            self._handle_task_terminated(self._lastpayload)
            return
        if self._taskpage is not None:
            self._taskpage.show()
            self.stack.setCurrentWidget(self._taskpage)
        self._set_footer_review()

    def _on_accept(self):
        _step = self.seq.current()
        self._persist(
            status=pfadef.AssessStatus.COMPLETE.value,
            payload=self._lastpayload,
            write_protocol=True,
        )
        self._discard_taskpage()
        self.seq.mark_completed(_step)
        self._after_accept(_step)

    def _on_redo(self):
        """Log the attempt as rejected (details JSON only, so the protocol row
        stays open) and run the same step again."""
        _step = self.seq.current()
        self._persist(
            status=pfadef.AssessStatus.REJECTED.value,
            payload=self._lastpayload,
            write_protocol=False,
        )
        self._discard_taskpage()
        self._start_current_step()

    def _persist(self, status: str, payload: dict, write_protocol: bool):
        _protocol = self.data.protocol
        self.data.detailedsummary.update(
            romval=payload.get("romval"),
            session=self.data.session,
            tasktime=_protocol.tasktime,
            rawfile=_protocol.rawfilename,
            summaryfile=_protocol.summaryfilename,
            taskcomment="",
            status=status,
        )
        if write_protocol:
            _protocol.update(
                session=self.data.session,
                rawfile=_protocol.rawfilename,
                summaryfile=_protocol.summaryfilename,
                taskcomment="",
                status=status,
            )

    def _after_accept(self, step):
        """Advance past the accepted step. Auto-skip rules land here in Task 6."""
        self.seq.advance()
        self._show_ready()

    def _handle_task_terminated(self, payload):
        """Placeholder until Task 6; treated as an accepted-and-done step."""
        _step = self.seq.current()
        self._discard_taskpage()
        self.seq.mark_completed(_step)
        self.seq.advance()
        self._show_ready()
```

Add `self._lastpayload = {}` next to the other instance attributes in `__init__`.

- [ ] **Step 3: Syntax check**

```bash
uv run python -m py_compile newgui/shell.py
```

- [ ] **Step 4: Run and verify persistence**

```bash
uv run python newgui/main.py
```

Run FPS calibration and FPS AROM. On completion the footer shows Accept / Redo over the finished AROM display.

- Press **Redo**: the AROM display restarts from trial 1, and no protocol row is filled.
- Complete it again and press **Accept**: the flow moves to the PROM ready screen.

Then check the files (adjust the subject id and path):

```bash
uv run python -c "import pandas as pd,sys; print(pd.read_csv(sys.argv[1]))" \
  "$HOME/Documents/HomerPlutoData/fullassessment/<subj>/<limb>/<tp>/<subj>_<limb>_<tp>_protocol.csv"
```

Expected: exactly one filled row for FPS/AROM with `status=Complete` and a session id; the rejected attempt appears only in the `_details.json` file with `status=Rejected`.

- [ ] **Step 5: Commit**

```bash
git add newgui/shell.py
git commit -m "feat(newgui): accept/redo review footer writing protocol and details"
```

---

### Task 6: Auto-skip rules

Two rules carried over from `plutofullassessment.py`: a low or missing AROM auto-skips discrete reaching, and an AROM that terminates on repeated trial time-outs skips AROM (which excludes DISC through the existing task-dependency logic).

**Files:**
- Modify: `newgui/shell.py` (`_after_accept`, `_handle_task_terminated`, new `_skip_step`)

**Interfaces:**
- Consumes: `newgui.sequencer.disc_skip_reason`, `Step`, `PlutoAssessmentProtocolData.skip_task`, `PlutoAssessmentDetailsData.skip_task`.
- Produces: `PlutoGuidedAssessor._skip_step(task: str, reason: str)` — writes the skip to both stores and marks the step completed in the sequencer.

- [ ] **Step 1: Import the rule**

```python
from newgui.sequencer import CALIB, Sequencer, Step, disc_skip_reason
```

- [ ] **Step 2: Implement skipping and the post-AROM rule**

```python
    def _skip_step(self, task: str, reason: str):
        """Record a task as skipped and step the sequencer past it. skip_task
        also marks dependent tasks EXCLUDED (DISC depends on AROM), matching the
        old GUI."""
        _mech = self.data.protocol.mech
        self.data.protocol.skip_task(task, self.data.session, reason)
        self.data.detailedsummary.skip_task(task, self.data.session, reason)
        self.seq.mark_completed(Step(_mech, task))

    def _after_accept(self, step):
        # After AROM, decide whether discrete reaching is worth running.
        if step.task == "AROM" and "DISC" in self.data.protocol.task_not_completed:
            _reason = disc_skip_reason(
                step.mech, self.data.detailedsummary.get_arom_if_completed()
            )
            if _reason is not None:
                self._skip_step("DISC", _reason)
        self.seq.advance()
        self._show_ready()

    def _handle_task_terminated(self, payload):
        """AROM terminated itself after too many timed-out trials. Log the skip
        (which excludes DISC via the task dependencies) and move on."""
        _step = self.seq.current()
        self._discard_taskpage()
        _reason = payload.get("taskcomment") or "Terminated by trial time limit"
        self._skip_step(_step.task, _reason)
        if _step.task == "AROM":
            self.seq.mark_completed(Step(_step.mech, "DISC"))
        self.seq.advance()
        self._show_ready()
```

Note: `_skip_step` must be called while `self.data.protocol.mech` and the detailed summary's mechanism are still the current ones — both are only changed in `_start_current_step`, so this ordering holds.

- [ ] **Step 3: Syntax check**

```bash
uv run python -m py_compile newgui/shell.py
```

- [ ] **Step 4: Verify the low-AROM rule**

```bash
uv run python newgui/main.py
```

Run a session and deliberately produce a tiny AROM range on one mechanism (move only a few degrees through the required cycles), then Accept. Expected: the flow goes straight from AROM to PROM, then APROM, then the *next mechanism's* calibration — DISC is never offered. The protocol CSV shows the DISC row with `status=Skipped` and the threshold reason in `taskcomment`.

- [ ] **Step 5: Verify the AROM-termination rule**

Start an AROM trial and let the 60 s limit expire, then choose "Skip AROM" in the window's own timeout dialog. Expected: no Accept/Redo footer appears; the flow moves to PROM; the protocol CSV shows AROM as `Skipped` and DISC as `Excluded`.

- [ ] **Step 6: Commit**

```bash
git add newgui/shell.py
git commit -m "feat(newgui): auto-skip discrete reaching on low or terminated AROM"
```

---

### Task 7: Resume and the done screen

**Files:**
- Modify: `newgui/shell.py` (`_on_setup_finished`, `_show_done`)

**Interfaces:**
- Consumes: `Sequencer.resume_from`, `PlutoAssessmentProtocolData.df`, `PlutoAssessmentDetailsData.get_screening_eligibility`.
- Produces: `PlutoGuidedAssessor._completed_pairs() -> list[tuple[str, str]]` — the (mechanism, task) pairs already filled in the protocol CSV.

- [ ] **Step 1: Read completed steps out of the protocol CSV**

```python
    def _completed_pairs(self):
        """(mechanism, task) pairs whose protocol row already has a session —
        completed, skipped or excluded, all of them finished as far as the flow
        is concerned."""
        _df = self.data.protocol.df
        if _df is None:
            return []
        _done = _df[_df["session"].notna()]
        return list(
            dict.fromkeys(zip(_done["mechanism"].tolist(), _done["task"].tolist()))
        )
```

- [ ] **Step 2: Resume on setup completion**

In `_on_setup_finished`, replace the final `self._show_ready()` with:

```python
        _completed = self._completed_pairs()
        if _completed:
            self.seq.resume_from(_completed)
            self._resumed = True
        self._show_ready()
```

- [ ] **Step 3: Show the screening verdict on the done screen**

Replace `_show_done` with:

```python
    def _show_done(self):
        self.stack.setCurrentWidget(self.pageDone)
        self.lblHeader.setText("Done")
        self.lblCounter.setText("")
        if self.data.is_screening and self.data.detailedsummary is not None:
            _eligible, _stats = self.data.detailedsummary.get_screening_eligibility()
            self.pageDone.lblDetail.setText(
                "ELIGIBLE" if _eligible else "NOT ELIGIBLE"
            )
            self.pageDone.lblDetail.setStyleSheet(
                "font-size: 20pt; font-weight: 600; color: "
                + ("rgb(0,120,0);" if _eligible else "rgb(170,0,0);")
            )
        else:
            self.pageDone.lblDetail.setText(
                f"{self.data.subjid} · {self.data.limb}"
            )
        self._set_footer_hint("You can close the window.")
        self._kick_sync()
```

- [ ] **Step 4: Syntax check**

```bash
uv run python -m py_compile newgui/shell.py
```

- [ ] **Step 5: Verify resume**

```bash
uv run python newgui/main.py
```

Run FPS calibration, AROM and PROM in an assessment session, accept both, then close the window mid-flow. Relaunch and enter the same subject / limb / time point. Expected: the ready screen reads "Forearm Pronation/Supination — Calibration  (resumed)" — calibration first, because it is not persisted — and pressing through it lands on "Assisted PROM", not on AROM.

- [ ] **Step 6: Verify the screening end screen**

Run a full screening session (4 mechanisms, calibration + AROM each). Expected: after the last accepted AROM the window shows "Session complete" with `ELIGIBLE` or `NOT ELIGIBLE` beneath it.

- [ ] **Step 7: Commit**

```bash
git add newgui/shell.py
git commit -m "feat(newgui): resume an interrupted session and show the end screen"
```

---

## Manual acceptance checklist

Run once at the end, on the device:

- [ ] Assessment session, all four mechanisms: the only mouse actions are setup, Accept and Redo.
- [ ] No second window ever appears (except the task windows' own timeout dialog and error message boxes).
- [ ] The step counter reaches `20 / 20` and the done screen appears.
- [ ] Protocol CSV has exactly one filled row per non-skipped task, statuses `Complete` / `Skipped` / `Excluded` only.
- [ ] `plutofullassessment.py` still runs and behaves as before.
