"""Standalone logic checks for guided-GUI resume: the (mechanism, task)
extraction that `PlutoGuidedAssessor._completed_pairs` performs on a protocol
CSV, fed into a real `Sequencer.resume_from`.

`_completed_pairs` only reads `self.data.protocol.df` — it never touches
`self.pluto` or any other Qt/hardware state — so it can be called directly as
an unbound method on a minimal duck-typed stub standing in for `self`,
without constructing a real `PlutoGuidedAssessor` (which would need a live
QtPluto/serial connection). This test does exactly that: it calls the real
`newgui.shell.PlutoGuidedAssessor._completed_pairs` against a stub whose
`.data.protocol.df` is a synthetic pandas DataFrame shaped like a protocol
CSV, then feeds the resulting pairs into a real `Sequencer` to confirm the
cursor lands where resume is supposed to leave it. Because the shipped
method is called directly, a future change to its logic (e.g. keying off
`status` instead of `session`) is exercised by this test with no copy to
fall out of sync.

Importing `newgui.shell` pulls in PySide6, qtpluto and qtjedi, but at import
time this only defines classes — `QtPluto`/`JediComm` only open a serial
port inside their own `__init__`, which runs when `PlutoGuidedAssessor.
__init__` constructs one. This test never constructs a `PlutoGuidedAssessor`
(only calls one unbound method on a stub), so no serial port is ever opened.

Run: uv run python tests/test_newgui_resume.py  ->  prints OK."""
import os
import pathlib
import sys
import types

# Make the repo root importable when run as `python tests/test_newgui_resume.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# newgui.shell imports PySide6; running headless avoids needing a display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd

import plutofullassessdef as pfadef
from newgui.sequencer import ASSESSMENT_MECHANISMS, CALIB, Sequencer, Step
from newgui.shell import PlutoGuidedAssessor


def _stub_for(_df):
    """Minimal duck-typed stand-in for self: both extraction methods read only
    self.data.protocol.df, so they can be called unbound without constructing a
    PlutoGuidedAssessor (which would need a live QtPluto/serial connection)."""
    return types.SimpleNamespace(
        data=types.SimpleNamespace(protocol=types.SimpleNamespace(df=_df))
    )


def _completed_pairs_from_df(_df):
    """Calls the real, shipped PlutoGuidedAssessor._completed_pairs against a
    minimal stub for self, so this test exercises the actual implementation
    rather than a hand-copied reimplementation of it."""
    return PlutoGuidedAssessor._completed_pairs(_stub_for(_df))


def _protocol_pairs_from_df(_df):
    """Same, for the real PlutoGuidedAssessor._protocol_pairs."""
    return PlutoGuidedAssessor._protocol_pairs(_stub_for(_df))


def _protocol_df(rows):
    """rows: list of (mechanism, task, session_or_None, status)."""
    return pd.DataFrame(
        {
            "mechanism": [r[0] for r in rows],
            "task": [r[1] for r in rows],
            "session": pd.array([r[2] for r in rows], dtype="string"),
            "status": [r[3] for r in rows],
        }
    )


def test_no_finished_rows_resumes_to_the_very_start():
    _df = _protocol_df(
        [
            ("WURD", "AROM", None, "Incomplete"),
            ("WURD", "PROM", None, "Incomplete"),
            ("WURD", "APROM", None, "Incomplete"),
            ("WURD", "DISC", None, "Incomplete"),
        ]
    )
    _pairs = _completed_pairs_from_df(_df)
    assert _pairs == [], _pairs
    seq = Sequencer("assessment")
    # Nothing to resume: _on_setup_finished only calls resume_from when
    # _completed_pairs() is non-empty, so mirror that guard here too.
    if _pairs:
        seq.resume_from(_pairs)
    assert seq.current() == Step("WURD", CALIB), seq.current()


def test_mixed_statuses_all_count_as_finished():
    """Complete, Skipped and Excluded rows all carry a session value and must
    all be treated as done, landing the cursor on the first row that has no
    session at all."""
    _df = _protocol_df(
        [
            ("WURD", "AROM", "20260101_120000", "Complete"),
            ("WURD", "PROM", "20260101_120000", "Skipped"),
            ("WURD", "APROM", "20260101_120000", "Excluded"),
            ("WURD", "DISC", None, "Incomplete"),
        ]
    )
    _pairs = _completed_pairs_from_df(_df)
    assert set(_pairs) == {
        ("WURD", "AROM"),
        ("WURD", "PROM"),
        ("WURD", "APROM"),
    }, _pairs
    seq = Sequencer("assessment")
    seq.resume_from(_pairs)
    # Calibration is never persisted, so resume parks on WURD calibration first
    # even though only DISC is left in the mechanism.
    assert seq.current() == Step("WURD", CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step("WURD", "DISC"), seq.current()


def test_entirely_finished_protocol_resumes_past_the_end():
    _rows = []
    for _m in pfadef.MECHANISMS:
        for _t in ("AROM", "PROM", "APROM", "DISC"):
            _rows.append((_m, _t, "20260101_120000", "Complete"))
    _df = _protocol_df(_rows)
    _pairs = _completed_pairs_from_df(_df)
    assert len(_pairs) == len(_rows), _pairs
    seq = Sequencer("assessment")
    seq.resume_from(_pairs)
    assert seq.is_done() is True


def test_unaffected_limb_protocol_walks_disc_only():
    """AROM/PROM/APROM are gated out of the protocol when the limb assessed is
    not the affected one, leaving DISC. The flow must walk exactly what the
    protocol contains — stepping into a task with no protocol row raises from
    protocol.set_task."""
    _df = _protocol_df(
        [(_m, "DISC", None, "Incomplete") for _m in pfadef.MECHANISMS]
    )
    seq = Sequencer("assessment")
    seq.restrict_to(_protocol_pairs_from_df(_df))
    # restrict_to filters the step list in place, so the flow keeps the
    # assessment mechanism order regardless of the protocol CSV's row order.
    assert [(_s.mech, _s.task) for _s in seq.steps] == [
        _pair
        for _m in ASSESSMENT_MECHANISMS
        for _pair in ((_m, CALIB), (_m, "DISC"))
    ], seq.steps
    assert seq.current() == Step(ASSESSMENT_MECHANISMS[0], CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step(ASSESSMENT_MECHANISMS[0], "DISC"), seq.current()


def test_restrict_then_resume_lands_on_first_unfinished_task():
    """restrict_to runs before resume_from in _on_setup_finished; the two must
    compose."""
    _df = _protocol_df(
        [
            ("FPS", "DISC", None, "Incomplete"),
            ("WFE", "DISC", None, "Incomplete"),
            ("WURD", "DISC", "20260101_120000", "Complete"),
            ("HOC", "DISC", None, "Incomplete"),
        ]
    )
    seq = Sequencer("assessment")
    seq.restrict_to(_protocol_pairs_from_df(_df))
    seq.resume_from(_completed_pairs_from_df(_df))
    # WURD is first in the assessment order and is done, so the flow resumes on
    # the second mechanism.
    assert seq.current() == Step("WFE", CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step("WFE", "DISC"), seq.current()


def test_restrict_to_a_full_assessment_protocol_changes_nothing():
    _rows = [
        (_m, _t, None, "Incomplete")
        for _m in pfadef.MECHANISMS
        for _t in ("AROM", "PROM", "APROM", "DISC")
    ]
    seq = Sequencer("assessment")
    _before = list(seq.steps)
    seq.restrict_to(_protocol_pairs_from_df(_protocol_df(_rows)))
    assert seq.steps == _before, seq.steps


def test_no_protocol_dataframe_yields_no_pairs():
    """self.data.protocol.df is None before setup builds the protocol CSV;
    _completed_pairs must not blow up and must resume nothing."""
    assert _completed_pairs_from_df(None) == []


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
