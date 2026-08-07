"""Standalone checks for CSV write integrity on the abnormal task paths.

Covers the three things that could silently lose recorded data:
  1. CSVBufferWriter.close() flushing, and tolerating a second call.
  2. A task's writers being closed when the task did NOT run to completion
     (AROM terminated by the trial time limit, or the window dropped mid-task).
  3. PlutoAssessmentProtocolData.update() writing the row it was asked to write
     instead of returning early once every row already has a session, and
     PlutoGuidedAssessor._persist not double-logging an attempt in the details
     JSON when the protocol write fails.

Importing newgui.shell pulls in PySide6/qtpluto but only defines classes; no
serial port is opened because no PlutoGuidedAssessor is ever constructed.

Run: uv run python tests/test_csv_logging_close.py  ->  prints OK."""
import os
import pathlib
import sys
import tempfile
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd

import plutofullassessdef as pfadef
from misc import CSVBufferWriter


def _tmpfile(name):
    return str(pathlib.Path(tempfile.mkdtemp(prefix="plutocsv_")) / name)


def _rows(path):
    """Data rows on disk, header excluded."""
    return pathlib.Path(path).read_text().strip().splitlines()[1:]


def test_close_flushes_the_buffer():
    """Without close(), rows sit in the buffer until the flush interval; the
    task paths that end early rely on close() to get them onto disk."""
    _f = _tmpfile("flush.csv")
    _w = CSVBufferWriter(_f, header=["a", "b"], flush_interval=60.0, max_rows=1000)
    for _i in range(20):
        _w.write_row([_i, _i * 2])
    assert _rows(_f) == [], "rows should still be buffered"
    _w.close()
    assert len(_rows(_f)) == 20, _rows(_f)


def test_close_is_idempotent():
    """closeEvent closes the writers as a backstop after the state machine may
    already have closed them; the second call must not raise."""
    _f = _tmpfile("twice.csv")
    _w = CSVBufferWriter(_f, header=["a"], flush_interval=60.0)
    _w.write_row([1])
    _w.close()
    _w.close()
    assert _rows(_f) == ["1"], _rows(_f)


def _aprom_data(tmpdir, ntrials=3):
    """A real APRomData — it opens both CSV writers in __init__ and needs no
    device."""
    from plutoapromwindow import APRomData

    return APRomData(
        {
            "type": "stroke",
            "limb": "Left",
            "mechanism": "WFE",
            "romtype": pfadef.ROMType.ACTIVE,
            "session": "l_A0_20260101_120000",
            "ntrials": ntrials,
            "rawfile": str(pathlib.Path(tmpdir) / "raw.csv"),
            "summaryfile": str(pathlib.Path(tmpdir) / "summary.csv"),
        }
    )


def test_close_logging_writes_out_an_unfinished_task():
    """The AROM-terminated / window-dropped path: no trial ever completed, so
    terminate_rawlogging() never ran. close_logging() must still land the
    samples on disk."""
    _dir = tempfile.mkdtemp(prefix="plutocsv_")
    _data = _aprom_data(_dir)
    for _i in range(15):
        _data.rawfilewriter.write_row(
            [_i, _i, _i, "", "", "", "Left", "WFE", 1.0, 0.0, 0, 0, "REST"]
        )
    assert _rows(_data.rawfile) == [], "rows should still be buffered"
    _data.close_logging()
    assert len(_rows(_data.rawfile)) == 15, _rows(_data.rawfile)
    # Both writers released, and a second call is harmless.
    assert _data.rawfilewriter is None
    _data.close_logging()


def test_close_logging_after_normal_termination():
    """The normal path already closed both writers; close_logging() on top of it
    must not raise or lose anything."""
    _dir = tempfile.mkdtemp(prefix="plutocsv_")
    _data = _aprom_data(_dir)
    _data.rawfilewriter.write_row(
        [0, 0, 0, "", "", "", "Left", "WFE", 1.0, 0.0, 0, 0, "REST"]
    )
    _data.terminate_rawlogging()
    _data.terminate_summarylogging()
    _data.close_logging()
    assert len(_rows(_data.rawfile)) == 1, _rows(_data.rawfile)


#
# Protocol CSV
#
def _protocol_data(tmpdir, mode="screening"):
    """A real PlutoAssessmentProtocolData against a throwaway data root."""
    import plutofullassesssdata as pfad

    return pfad.PlutoAssessmentProtocolData(
        "T001", mode, "Right", "Left", "Left", "A0", tmpdir, tmpdir
    )


def test_update_still_writes_once_every_row_is_filled():
    """update() used to return early when no row was left without a session,
    so re-running a task after the protocol was full wrote nothing and reported
    no error."""
    _dir = tempfile.mkdtemp(prefix="plutocsv_")
    _p = _protocol_data(_dir)
    for _m in pfadef.MECHANISMS:
        _p.set_mechanism(_m)
        _p.set_task("AROM")
        _p.update(
            session="first", rawfile="r", summaryfile="s", taskcomment="",
            status=pfadef.AssessStatus.COMPLETE.value,
        )
    assert _p.index is None, _p.index
    _p.set_mechanism("HOC")
    _p.set_task("AROM")
    _p.update(
        session="second", rawfile="r2", summaryfile="s2", taskcomment="redone",
        status=pfadef.AssessStatus.COMPLETE.value,
    )
    _df = pd.read_csv(_p.filename, dtype=pfadef.SUMMARY_COLUMN_FORMAT)
    _row = _df[(_df["mechanism"] == "HOC") & (_df["task"] == "AROM")].iloc[0]
    assert _row["session"] == "second", _row.to_dict()
    assert _row["rawfile"] == "r2", _row.to_dict()


def test_update_raises_when_no_row_matches():
    """A write aimed at a row the protocol does not contain must fail loudly
    rather than disappear."""
    _dir = tempfile.mkdtemp(prefix="plutocsv_")
    _p = _protocol_data(_dir)
    _p.set_mechanism("HOC")
    _p._task = "PROM"          # not in the screening protocol
    try:
        _p.update(session="x", rawfile="r", summaryfile="s", taskcomment="",
                  status=pfadef.AssessStatus.COMPLETE.value)
    except ValueError as _exc:
        assert "PROM" in str(_exc), _exc
    else:
        raise AssertionError("update() accepted a task with no protocol row")


#
# _persist ordering
#
class _FailingProtocol:
    mech, task, tasktime = "HOC", "AROM", "20260101_120000"
    rawfilename = summaryfilename = "x.csv"

    def update(self, **_kw):
        raise OSError("protocol CSV is locked")


class _RecordingDetails:
    def __init__(self):
        self.calls = 0

    def update(self, **_kw):
        self.calls += 1


def test_persist_does_not_log_the_attempt_twice_when_the_protocol_write_fails():
    """_persist writes the protocol row (idempotent) before appending to the
    details JSON (not idempotent), so an operator retrying Accept after a failed
    write does not record the same attempt twice."""
    from newgui.shell import PlutoGuidedAssessor

    _details = _RecordingDetails()
    _self = types.SimpleNamespace(
        data=types.SimpleNamespace(
            protocol=_FailingProtocol(), detailedsummary=_details, session="s1"
        )
    )
    for _ in range(3):          # operator presses Accept again and again
        _ok = PlutoGuidedAssessor._persist(
            _self, status=pfadef.AssessStatus.COMPLETE.value,
            payload={"romval": [[0.0, 40.0]]}, write_protocol=True,
        )
        assert _ok is False
    assert _details.calls == 0, _details.calls


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
