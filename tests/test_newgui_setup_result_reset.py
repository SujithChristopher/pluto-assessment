"""Standalone check that EmbeddedSetupPage resets self.result before every
Start attempt, so a stale dict from a previous (successful) attempt cannot
leak into a later attempt that fails validation.

Regression covered: EmbeddedSetupPage is a long-lived singleton -- after a
failed session-setup worker, PlutoGuidedAssessor._on_setup_error switches
back to the SAME page instance. The base SessionSetupWindow._on_start only
assigns self.result on its success path and returns early (leaving whatever
self.result already held) on a validation failure. Without resetting
self.result at the top of EmbeddedSetupPage._on_start, a later failed
attempt would re-trigger the onstartcb with the previous attempt's dict.

This is exercised at the smallest seam that avoids real Qt dialogs and disk
I/O: the base class's _on_start is monkeypatched to two stand-ins, one that
mimics a validation-failure return (does nothing, exactly like the real
early-return branches) and one that mimics success (sets self.result). Both
stand-ins are faithful to the real method's contract (it either sets
self.result and returns, or returns without touching self.result); only the
disk-backed validation itself is skipped.

Run: uv run python tests/test_newgui_setup_result_reset.py  ->  prints OK."""
import os
import pathlib
import sys
import tempfile

# Make the repo root importable when run as `python tests/test_....py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Headless Qt: no display needed for this widget-construction test.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Point the data roots at a temp dir BEFORE constructing any widget, so
# EmbeddedSetupPage's subject-list loading in __init__ never touches real
# ~/Documents data.
_tmp = pathlib.Path(tempfile.mkdtemp())
os.environ["HOME"] = str(_tmp)
os.environ["USERPROFILE"] = str(_tmp)

import plutofullassessdef as pfadef
pfadef.DATA_DIR = str(_tmp / "fullassessment")
pfadef.SUBJLIST_FILE = str(_tmp / "fullassessment" / "fullassess_subjects.csv")
pfadef.SCREENING_DIR = str(_tmp / "screening")
pfadef.SCREENING_SUBJLIST_FILE = str(_tmp / "screening" / "screening_subjects.csv")

from PySide6 import QtWidgets

import sessionsetupwindow
from newgui.setup import EmbeddedSetupPage

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

_STALE_RESULT = {
    "mode": "assessment", "subjid": "stale_subject", "limb": "left",
    "afflimb": "left", "domlimb": "right", "timepoint": "A0",
}
_FRESH_RESULT = {
    "mode": "assessment", "subjid": "fresh_subject", "limb": "right",
    "afflimb": "right", "domlimb": "left", "timepoint": "A0",
}

# The real base-class method, restored after each test function so the two
# scenarios below don't interfere with each other.
_REAL_ON_START = sessionsetupwindow.SessionSetupWindow._on_start


def _make_page():
    calls = []
    page = EmbeddedSetupPage(onstartcb=lambda d: calls.append(d))
    return page, calls


def test_validation_failure_does_not_leak_stale_result():
    """Mimics a validation-failure return (e.g. timepoint-ordering or
    already-completed check): the base method returns without touching
    self.result -- exactly what SessionSetupWindow._on_start's early-return
    branches do."""
    def _fake_validation_failure(self):
        return  # early return, self.result untouched -- like the real code

    sessionsetupwindow.SessionSetupWindow._on_start = _fake_validation_failure
    try:
        page, calls = _make_page()
        page.result = dict(_STALE_RESULT)  # leftover from a prior successful Start
        page._on_start()
        assert calls == [], f"onstartcb must not fire on validation failure, got {calls}"
        assert page.result == {}, f"result must be reset, not stale: {page.result}"
    finally:
        sessionsetupwindow.SessionSetupWindow._on_start = _REAL_ON_START


def test_success_path_still_delivers_fresh_result():
    """Mimics the success path: the base method sets self.result to the new
    attempt's dict. Confirms the reset does not interfere with a genuine
    success -- the callback must fire with the FRESH dict, never the stale
    one left over from a previous attempt."""
    def _fake_success(self):
        self.result = dict(_FRESH_RESULT)

    sessionsetupwindow.SessionSetupWindow._on_start = _fake_success
    try:
        page, calls = _make_page()
        page.result = dict(_STALE_RESULT)  # leftover from a prior attempt
        page._on_start()
        assert calls == [_FRESH_RESULT], f"expected callback with fresh result, got {calls}"
    finally:
        sessionsetupwindow.SessionSetupWindow._on_start = _REAL_ON_START


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
