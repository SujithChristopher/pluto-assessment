"""Standalone check that the guided flow can walk its own mechanism order.

The protocol CSV writes its rows in pfadef.MECHANISMS order (FPS first), while
the guided assessment walks WURD first by clinical request. set_mechanism gates
on the row order for the old GUI's benefit, so with DEBUG off the guided flow's
very first step was rejected:

    ValueError: Mechanism [WURD] does not match the protocol mechanism [FPS]

This walks a real protocol the way newgui.shell._start_current_step does, with
DEBUG pinned off, so the crash cannot come back unnoticed.

Run: uv run python tests/test_guided_walk_order.py  ->  prints OK."""
import contextlib
import io
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import debugconfig
# The bug only exists with the ordering rules switched on, which is how every
# build ships. Pin it so this test never passes for the wrong reason.
debugconfig.DEBUG = False
debugconfig.MECHANISM_ORDER = None

import plutofullassessdef as pfadef
import plutofullassesssdata as pdata
from newgui.sequencer import (
    ASSESSMENT_MECHANISMS,
    CALIB,
    SCREENING_MECHANISMS,
    Sequencer,
)

QUIET = contextlib.redirect_stdout(io.StringIO())


def _protocol(mode):
    _dir = tempfile.mkdtemp(prefix="walkorder_")
    return pdata.PlutoAssessmentProtocolData(
        "T001", mode, "right", "left", "left", "A0", _dir, _dir
    )


def _walk(mode):
    """Drive a protocol exactly as _start_current_step does, in sequencer order,
    and record the mechanisms in the order they were selected."""
    _p = _protocol(mode)
    _seq = Sequencer(mode)
    _seq.restrict_to(list(dict.fromkeys(zip(_p.df["mechanism"], _p.df["task"]))))
    _seen = []
    with QUIET:
        for _step in _seq.steps:
            if _step.task == CALIB:
                continue
            if _step.mech != _p.mech:
                _p.set_mechanism(_step.mech, enforce_order=False)
                _seen.append(_step.mech)
            _p.set_task(_step.task)
            _p.update(session="s1", rawfile=_p.rawfilename,
                      summaryfile=_p.summaryfilename, taskcomment="",
                      status=pfadef.AssessStatus.COMPLETE.value)
    return _p, _seen


def test_the_protocol_rows_really_do_start_with_a_different_mechanism():
    """The premise. If the row order ever matches the walk order, this test
    stops proving anything and should be revisited."""
    _p = _protocol("assessment")
    assert _p.df["mechanism"].iloc[0] == pfadef.MECHANISMS[0], _p.df.head()
    assert _p.df["mechanism"].iloc[0] != ASSESSMENT_MECHANISMS[0], _p.df.head()


def test_the_guided_assessment_walk_completes():
    _p, _seen = _walk("assessment")
    assert _seen == ASSESSMENT_MECHANISMS, _seen
    assert int(_p.df["session"].isna().sum()) == 0, _p.df
    assert _p.index is None, _p.index


def test_the_guided_screening_walk_completes():
    _p, _seen = _walk("screening")
    assert _seen == SCREENING_MECHANISMS, _seen
    assert int(_p.df["session"].isna().sum()) == 0, _p.df


def test_the_row_order_gate_still_guards_the_old_gui():
    """enforce_order defaults to True, and that path must keep rejecting a
    mechanism picked ahead of its turn — that is what stops the old GUI's
    operator jumping the protocol."""
    _p = _protocol("assessment")
    try:
        _p.set_mechanism(ASSESSMENT_MECHANISMS[0])   # WURD, rows start at FPS
    except ValueError as _exc:
        assert "does not match the protocol mechanism" in str(_exc), _exc
    else:
        raise AssertionError("the row-order gate let a mechanism through")


def test_an_absent_mechanism_is_rejected_either_way():
    """Skipping the order gate must not skip the existence check."""
    _p = _protocol("screening")
    for _enforce in (True, False):
        try:
            _p.set_mechanism("NOSUCH", enforce_order=_enforce)
        except ValueError as _exc:
            assert "not in this protocol" in str(_exc), _exc
        else:
            raise AssertionError(f"accepted a bogus mechanism ({_enforce=})")


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
