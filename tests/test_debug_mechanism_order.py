"""Standalone checks for the DEBUG mechanism-order override.

debugconfig.MECHANISM_ORDER shortens the guided walk so a tester can reach the
mechanism under test without sitting through the other three. It must not change
anything else: the protocol CSV still holds every mechanism, and with DEBUG off
the override is inert no matter what is left in the file.

Run: uv run python tests/test_debug_mechanism_order.py  ->  prints OK."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import debugconfig
import plutofullassessdef as pfadef
from newgui import sequencer as seqmod
from newgui.sequencer import (
    ASSESSMENT_MECHANISMS,
    CALIB,
    SCREENING_MECHANISMS,
    Sequencer,
    Step,
    build_steps,
    debug_mechanism_order,
    mechanisms_for_mode,
)


class _config:
    """Set debugconfig for the duration of a with-block, then put it back."""

    def __init__(self, debug, order):
        self._new = (debug, order)

    def __enter__(self):
        self._old = (debugconfig.DEBUG, debugconfig.MECHANISM_ORDER)
        debugconfig.DEBUG, debugconfig.MECHANISM_ORDER = self._new

    def __exit__(self, *_exc):
        debugconfig.DEBUG, debugconfig.MECHANISM_ORDER = self._old
        return False


def test_shipped_default_is_inert():
    """Whatever DEBUG is set to in the repo, no order override ships enabled."""
    assert debugconfig.MECHANISM_ORDER is None, debugconfig.MECHANISM_ORDER
    assert debug_mechanism_order() is None


def test_no_override_keeps_the_normal_order():
    with _config(True, None):
        assert mechanisms_for_mode("screening") == SCREENING_MECHANISMS
        assert mechanisms_for_mode("assessment") == ASSESSMENT_MECHANISMS


def test_override_applies_to_both_modes():
    with _config(True, ["HOC"]):
        assert mechanisms_for_mode("screening") == ["HOC"]
        assert mechanisms_for_mode("assessment") == ["HOC"]


def test_override_is_ignored_when_debug_is_off():
    """Leaving an order in the file must not affect a production build."""
    with _config(False, ["HOC"]):
        assert debug_mechanism_order() is None
        assert mechanisms_for_mode("assessment") == ASSESSMENT_MECHANISMS


def test_an_empty_order_is_treated_as_no_override():
    for _empty in ([], None):
        with _config(True, _empty):
            assert debug_mechanism_order() is None
            assert mechanisms_for_mode("assessment") == ASSESSMENT_MECHANISMS


def test_a_typo_is_rejected_rather_than_silently_ignored():
    with _config(True, ["HOC", "WFS"]):     # WFS is not a mechanism
        try:
            mechanisms_for_mode("assessment")
        except ValueError as _exc:
            assert "WFS" in str(_exc), _exc
            assert "WURD" in str(_exc), _exc     # the message lists valid names
        else:
            raise AssertionError("an unknown mechanism name was accepted")


def test_a_repeated_mechanism_is_rejected():
    """Two copies of one mechanism would be marked done together the first time
    it completed, silently skipping the second pass."""
    with _config(True, ["HOC", "HOC"]):
        try:
            mechanisms_for_mode("assessment")
        except ValueError as _exc:
            assert "repeats" in str(_exc), _exc
        else:
            raise AssertionError("a repeated mechanism was accepted")


def test_the_walk_covers_only_the_named_mechanisms():
    with _config(True, ["HOC", "FPS"]):
        _steps = build_steps("assessment")
        assert {_s.mech for _s in _steps} == {"HOC", "FPS"}, _steps
        # Calibration first for each, then that mechanism's tasks, in order.
        assert [(_s.mech, _s.task) for _s in _steps[:2]] == [
            ("HOC", CALIB), ("HOC", "AROM")
        ], _steps[:2]
        _seq = Sequencer("assessment")
        assert _seq.current() == Step("HOC", CALIB), _seq.current()
        assert _seq.position() == (1, 2 * 5), _seq.position()


def test_restrict_to_keeps_the_debug_order():
    """The protocol CSV still lists every mechanism; restricting to it must not
    quietly restore the mechanisms the override left out."""
    _protocol = [
        (_m, _t) for _m in pfadef.MECHANISMS
        for _t in ("AROM", "PROM", "APROM", "DISC")
    ]
    with _config(True, ["HOC"]):
        _seq = Sequencer("assessment")
        _seq.restrict_to(_protocol)
        assert {_s.mech for _s in _seq.steps} == {"HOC"}, _seq.steps


def test_the_module_reads_debugconfig_live():
    """The override is read per call, not captured at import, so editing
    debugconfig and relaunching is enough — no stale module-level copy."""
    assert not hasattr(seqmod, "MECHANISM_ORDER"), (
        "sequencer captured the order at import time"
    )


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
