"""Standalone checks that session setup no longer asks for the limb.

Both modes assess the affected limb, so the setup form has no limb picker and
the dict it hands to the shell must carry limb == afflimb. Everything
downstream (folder names, raw/summary filenames, the affected-limb task gate)
keys off "limb", so its absence or a stale value would silently write a session
into the wrong tree.

Run: uv run python tests/test_setup_window_limb.py  ->  prints OK."""
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_tmp = pathlib.Path(tempfile.mkdtemp(prefix="setupwin_"))

import plutofullassessdef as pfadef
pfadef.DATA_DIR = str(_tmp / "fullassessment")
pfadef.SUBJLIST_FILE = str(_tmp / "fullassessment" / "fullassess_subjects.csv")
pfadef.SCREENING_DIR = str(_tmp / "screening")
pfadef.SCREENING_SUBJLIST_FILE = str(_tmp / "screening" / "screening_subjects.csv")

from PySide6 import QtWidgets

import plutofullassesssdata as pdata
pdata.passdef.DATA_DIR = pfadef.DATA_DIR
pdata.passdef.SCREENING_DIR = pfadef.SCREENING_DIR

from sessionsetupwindow import SessionSetupWindow

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _window():
    return SessionSetupWindow(modal=False)


def test_there_is_no_limb_picker():
    _w = _window()
    assert not hasattr(_w, "cbLimb"), "the limb combo is still being built"
    assert not hasattr(_w, "lblLimb"), "the limb label is still being built"


def test_assessment_start_is_enabled_without_a_limb():
    """Start used to require a limb selection; with the field gone the affected
    side, dominant hand and timepoint are the whole gate."""
    _w = _window()
    _w.rbAssessment.setChecked(True)
    _w.txtSubjID.setEditText("p001")
    _w.cbAff.setCurrentText("Left")
    _w.cbDom.setCurrentText("Right")
    _w.update_ui()
    assert _w.pbStart.isEnabled() is False, "timepoint still missing"
    _w.cbTP.setCurrentText("A0")
    _w.update_ui()
    assert _w.pbStart.isEnabled() is True


def test_assessment_result_uses_the_affected_limb():
    _w = _window()
    _w.rbAssessment.setChecked(True)
    _w.txtSubjID.setEditText("p002")
    _w.cbAff.setCurrentText("Left")
    _w.cbDom.setCurrentText("Right")
    _w.cbTP.setCurrentText("A0")
    _w._on_start()
    assert _w.result["limb"] == "left", _w.result
    assert _w.result["afflimb"] == "left", _w.result
    assert _w.result["domlimb"] == "right", _w.result


def test_screening_result_still_uses_the_affected_limb():
    _w = _window()
    _w.rbScreening.setChecked(True)
    _w.txtSubjID.setEditText("s002")
    _w.cbAff.setCurrentText("Right")
    _w._on_start()
    assert _w.result["limb"] == "right", _w.result
    assert _w.result["timepoint"] == "", _w.result


def test_the_session_lands_under_the_affected_limb():
    """The setup dict is only useful if it puts the session in the right tree."""
    _w = _window()
    _w.rbAssessment.setChecked(True)
    _w.txtSubjID.setEditText("p003")
    _w.cbAff.setCurrentText("Right")
    _w.cbDom.setCurrentText("Right")
    _w.cbTP.setCurrentText("A0")
    _w._on_start()
    _d = pdata.PlutoAssessmentData()
    _d.setup_session(_w.result)
    _d.create_session_folder()
    assert pathlib.Path(_d.basedir) == pathlib.Path(
        pfadef.DATA_DIR, "p003", "right", "A0"
    ), _d.basedir


def test_setup_session_falls_back_to_afflimb():
    """A caller that omits "limb" entirely still gets the affected side."""
    _d = pdata.PlutoAssessmentData()
    _d.setup_session({"mode": "screening", "subjid": "s003", "afflimb": "left"})
    assert _d.limb == "left", _d.limb


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
