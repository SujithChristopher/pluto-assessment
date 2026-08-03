"""Standalone logic checks for guided-GUI resume: the (mechanism, task)
extraction that `PlutoGuidedAssessor._completed_pairs` performs on a protocol
CSV, fed into a real `Sequencer.resume_from`.

`_completed_pairs` itself lives on `PlutoGuidedAssessor`, which cannot be
constructed without a live QtPluto/serial connection, so this test does not
call it directly. Instead it exercises the exact extraction expression from
its body (`newgui/shell.py`) against a synthetic pandas DataFrame shaped like
a protocol CSV, then feeds the resulting pairs into a real `Sequencer` to
confirm the cursor lands where resume is supposed to leave it. If the
extraction logic were broken (e.g. it included unfinished rows, or dropped
finished ones), the resulting Sequencer cursor position would be wrong and
these assertions would fail.

Run: uv run python tests/test_newgui_resume.py  ->  prints OK."""
import pathlib
import sys

# Make the repo root importable when run as `python tests/test_newgui_resume.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd

from newgui.sequencer import CALIB, Sequencer, Step


def _completed_pairs_from_df(_df):
    """Mirrors newgui/shell.py PlutoGuidedAssessor._completed_pairs body
    verbatim, applied to a plain DataFrame instead of self.data.protocol.df."""
    if _df is None:
        return []
    _done = _df[_df["session"].notna()]
    return list(
        dict.fromkeys(zip(_done["mechanism"].tolist(), _done["task"].tolist()))
    )


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
            ("FPS", "AROM", None, "Incomplete"),
            ("FPS", "PROM", None, "Incomplete"),
            ("FPS", "APROM", None, "Incomplete"),
            ("FPS", "DISC", None, "Incomplete"),
        ]
    )
    _pairs = _completed_pairs_from_df(_df)
    assert _pairs == [], _pairs
    seq = Sequencer("assessment")
    # Nothing to resume: _on_setup_finished only calls resume_from when
    # _completed_pairs() is non-empty, so mirror that guard here too.
    if _pairs:
        seq.resume_from(_pairs)
    assert seq.current() == Step("FPS", CALIB), seq.current()


def test_mixed_statuses_all_count_as_finished():
    """Complete, Skipped and Excluded rows all carry a session value and must
    all be treated as done, landing the cursor on the first row that has no
    session at all."""
    _df = _protocol_df(
        [
            ("FPS", "AROM", "20260101_120000", "Complete"),
            ("FPS", "PROM", "20260101_120000", "Skipped"),
            ("FPS", "APROM", "20260101_120000", "Excluded"),
            ("FPS", "DISC", None, "Incomplete"),
        ]
    )
    _pairs = _completed_pairs_from_df(_df)
    assert set(_pairs) == {
        ("FPS", "AROM"),
        ("FPS", "PROM"),
        ("FPS", "APROM"),
    }, _pairs
    seq = Sequencer("assessment")
    seq.resume_from(_pairs)
    # Calibration is never persisted, so resume parks on FPS calibration first
    # even though only DISC is left in the mechanism.
    assert seq.current() == Step("FPS", CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step("FPS", "DISC"), seq.current()


def test_entirely_finished_protocol_resumes_past_the_end():
    import plutofullassessdef as pfadef

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


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
