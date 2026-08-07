"""Standalone checks for opening an already-finished session read-only.

Pressing Start on a subject/limb/timepoint that is already complete used to warn
and stop, which told the operator the data existed without letting them look at
it. It now opens the recorded stats instead. The things that must hold: nothing
is written by looking, no session is started, and the check fires for screening
as well as for a timepoint.

Run: uv run python tests/test_view_completed_session.py  ->  prints OK."""
import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_tmp = pathlib.Path(tempfile.mkdtemp(prefix="viewdone_"))

import plutofullassessdef as pfadef
pfadef.DATA_DIR = str(_tmp / "fullassessment")
pfadef.SUBJLIST_FILE = str(_tmp / "fullassessment" / "fullassess_subjects.csv")
pfadef.SCREENING_DIR = str(_tmp / "screening")
pfadef.SCREENING_SUBJLIST_FILE = str(_tmp / "screening" / "screening_subjects.csv")

from PySide6 import QtWidgets

import plutofullassesssdata as pdata
pdata.passdef.DATA_DIR = pfadef.DATA_DIR
pdata.passdef.SCREENING_DIR = pfadef.SCREENING_DIR

from plutofullassesssdata import PlutoAssessmentDetailsData
from newgui.setup import EmbeddedSetupPage
from sessionsetupwindow import SessionSetupWindow

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
QUIET = contextlib.redirect_stdout(io.StringIO())


def _finish(mode, subjid, limb, timepoint=""):
    """Run a whole session to completion so the protocol has no open rows."""
    _d = pdata.PlutoAssessmentData()
    _setup = {"mode": mode, "subjid": subjid, "afflimb": limb, "limb": limb,
              "domlimb": "right", "timepoint": timepoint}
    _d.setup_session(_setup)
    with QUIET:
        _d.create_session_folder()
        _d.start_protocol()
        _p, _s = _d.protocol, _d.detailedsummary
        for _m, _t in dict.fromkeys(zip(_p.df["mechanism"], _p.df["task"])):
            if _m != _p.mech:
                _p.set_mechanism(_m); _s.set_mechanism(_m)
            _p.set_task(_t); _s.set_task(_t)
            _s.update(romval=[[0.0, 40.0]], session=_d.session,
                      tasktime=_p.tasktime, rawfile="r", summaryfile="s",
                      taskcomment="", status=pfadef.AssessStatus.COMPLETE.value)
            _p.update(session=_d.session, rawfile="r", summaryfile="s",
                      taskcomment="", status=pfadef.AssessStatus.COMPLETE.value)
    return _d


_ASSESS = _finish("assessment", "p100", "left", "A0")
_SCREEN = _finish("screening", "s100", "right")


def test_completion_is_detected_in_both_modes():
    assert pfadef.is_session_completed("p100", "left", "assessment", "A0") is True
    assert pfadef.is_session_completed("s100", "right", "screening") is True
    # An untouched subject is not complete in either mode.
    assert pfadef.is_session_completed("nobody", "left", "assessment", "A0") is False
    assert pfadef.is_session_completed("nobody", "left", "screening") is False


def test_a_half_finished_timepoint_is_not_complete():
    """Only a protocol with every row recorded counts; a resumable session must
    still start normally."""
    _d = pdata.PlutoAssessmentData()
    _d.setup_session({"mode": "assessment", "subjid": "p101", "afflimb": "left",
                      "limb": "left", "domlimb": "right", "timepoint": "A0"})
    with QUIET:
        _d.create_session_folder()
        _d.start_protocol()
        _d.protocol.set_mechanism("WURD")
        _d.protocol.set_task("AROM")
        _d.protocol.update(session="s", rawfile="r", summaryfile="s",
                           taskcomment="", status="Complete")
    assert pfadef.is_session_completed("p101", "left", "assessment", "A0") is False


def test_details_path_points_at_the_written_file():
    for _args, _obj in (
        (("p100", "left", "assessment", "A0"), _ASSESS),
        (("s100", "right", "screening"), _SCREEN),
    ):
        _path = pfadef.details_path(*_args)
        assert _path.exists(), _path
        assert _path.as_posix() == _obj.detailedsummary.filename, _path


def test_reading_the_stats_writes_nothing():
    """from_file must not touch the session it is showing."""
    _path = pfadef.details_path("p100", "left", "assessment", "A0")
    _before = (_path.read_bytes(), _path.stat().st_mtime_ns)
    _det = PlutoAssessmentDetailsData.from_file(_path.as_posix())
    _summary = _det.get_arom_summary()
    assert set(_summary) == set(pfadef.MECHANISMS), _summary
    assert all(_s["outcome"] == "complete" for _s in _summary.values()), _summary
    assert (_path.read_bytes(), _path.stat().st_mtime_ns) == _before


def test_a_missing_details_file_is_not_created_by_looking():
    _path = _tmp / "nope" / "missing_details.json"
    try:
        PlutoAssessmentDetailsData.from_file(_path.as_posix())
    except (FileNotFoundError, OSError):
        pass
    else:
        raise AssertionError("from_file invented a details file")
    assert not _path.exists(), _path


def test_screening_stats_load_with_their_verdict():
    _det = PlutoAssessmentDetailsData.from_file(
        pfadef.details_path("s100", "right", "screening").as_posix()
    )
    _eligible, _stats = _det.get_screening_eligibility()
    assert _eligible is True, _stats          # 40 deg / 40 cm clears everything
    assert set(_stats) == set(pfadef.MECHANISMS), _stats


#
# Setup window routing
#
def _fill(win, mode, subjid, limb, timepoint=""):
    win.rbScreening.setChecked(mode == "screening")
    win.rbAssessment.setChecked(mode == "assessment")
    win.txtSubjID.setEditText(subjid)
    win.cbAff.setCurrentText(limb.capitalize())
    if mode == "assessment":
        win.cbDom.setCurrentText("Right")
        win.cbTP.setCurrentText(timepoint)


def test_a_completed_session_does_not_start():
    """The base class still refuses to start it; result stays empty so no
    session folder is ever created."""
    _seen = []
    _w = SessionSetupWindow(modal=False)
    _w._on_already_completed = _seen.append
    _fill(_w, "assessment", "p100", "left", "A0")
    _w._on_start()
    assert _w.result == {}, _w.result
    assert _seen == [{"mode": "assessment", "subjid": "p100", "limb": "left",
                      "timepoint": "A0"}], _seen


def test_a_completed_screening_also_does_not_start():
    _seen = []
    _w = SessionSetupWindow(modal=False)
    _w._on_already_completed = _seen.append
    _fill(_w, "screening", "s100", "right")
    _w._on_start()
    assert _w.result == {}, _w.result
    assert _seen and _seen[0]["mode"] == "screening", _seen


def test_an_unfinished_session_still_starts_normally():
    _seen = []
    _w = SessionSetupWindow(modal=False)
    _w._on_already_completed = _seen.append
    _fill(_w, "assessment", "p101", "left", "A0")
    _w._on_start()
    assert _seen == [], _seen
    assert _w.result["subjid"] == "p101", _w.result


def test_the_guided_page_routes_to_the_viewer_not_the_dialog():
    _started, _viewed = [], []
    _p = EmbeddedSetupPage(onstartcb=_started.append, onviewstatscb=_viewed.append)
    _fill(_p, "assessment", "p100", "left", "A0")
    _p._on_start()
    assert _started == [], _started
    assert _viewed == [{"mode": "assessment", "subjid": "p100", "limb": "left",
                        "timepoint": "A0"}], _viewed


def test_the_guided_page_falls_back_to_the_dialog_without_a_viewer():
    """Wiring the page without a viewer must not swallow the outcome silently."""
    _p = EmbeddedSetupPage(onstartcb=lambda _d: None)
    _called = []
    SessionSetupWindow._on_already_completed = (
        lambda _self, _info: _called.append(_info)
    )
    try:
        _fill(_p, "assessment", "p100", "left", "A0")
        _p._on_start()
    finally:
        del SessionSetupWindow._on_already_completed
    assert len(_called) == 1, _called


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
