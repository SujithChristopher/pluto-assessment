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

# Mechanism order differs by mode, by clinical request: screening works from the
# hand outwards (HOC first), assessment works from the wrist inwards (WURD
# first). Both are permutations of pfadef.MECHANISMS — the protocol CSV still
# holds every mechanism, only the order they are walked in changes.
SCREENING_MECHANISMS = ["HOC", "FPS", "WFE", "WURD"]
ASSESSMENT_MECHANISMS = ["WURD", "WFE", "FPS", "HOC"]

assert set(SCREENING_MECHANISMS) == set(pfadef.MECHANISMS), SCREENING_MECHANISMS
assert set(ASSESSMENT_MECHANISMS) == set(pfadef.MECHANISMS), ASSESSMENT_MECHANISMS

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


def mechanisms_for_mode(mode: str) -> list[str]:
    return list(SCREENING_MECHANISMS if mode == "screening" else ASSESSMENT_MECHANISMS)


def build_steps(mode: str) -> list[Step]:
    """Every mechanism, calibration first, then its tasks in protocol order."""
    _steps = []
    for _mech in mechanisms_for_mode(mode):
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

    def restrict_to(self, available: Iterable[tuple[str, str]]) -> None:
        """Keep only the steps the session's protocol actually contains.

        Not every task is in every protocol: tasks whose TASK_DEPENDENCIES entry
        has in_unaffected=False (AROM, PROM, APROM) are gated out when the limb
        being assessed is not the affected one, leaving DISC alone. Walking a
        step that has no protocol row would raise from protocol.set_task, so the
        step list is trimmed to the protocol before the flow starts. A
        mechanism's calibration step survives only if that mechanism kept at
        least one task."""
        _avail = {(_m, _t) for _m, _t in available}
        _steps = []
        _calibrated = set()
        for _step in self.steps:
            if _step.is_calib or (_step.mech, _step.task) not in _avail:
                continue
            if _step.mech not in _calibrated:
                _calibrated.add(_step.mech)
                _steps.append(Step(_step.mech, CALIB))
            _steps.append(_step)
        self.steps = _steps
        self._cursor = 0
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
