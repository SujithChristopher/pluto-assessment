"""Standalone checks that the HOC x-axis actually contains what gets drawn on it.

HOC is drawn corner-anchored: _xpos maps the aperture into 0..MAXHOC, pinning
the closed end to the left corner for a right hand and the right corner for a
left one. Every window that draws HOC has to set an x-range that agrees with
that mapping. When it does not, the drawing survives but lands in one half of
the plot — which is exactly what happened to HOC PROM (view spanned the legacy
symmetric [-10, 10]) and to HOC discrete reaching (view spanned the device's
full 9.4 cm aperture while the targets sat inside the subject's smaller AROM).

Both methods under test read only self.data, so they are called unbound against
a duck-typed stub — no QtPluto, no serial port, no pyqtgraph widget.

Run: uv run python tests/test_hoc_display_range.py  ->  prints OK."""
import os
import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import plutofullassessdef as pfadef
from plutoapromwindow import PlutoAPRomAssessWindow
from plutodiscreachwindow import PlutoDiscReachAssessWindow

MAXHOC = pfadef.AROM.MAXHOC


def _rom_stub(romtype, mech="HOC", limb="right"):
    _s = types.SimpleNamespace(
        data=types.SimpleNamespace(mechanism=mech, romtype=romtype, limb=limb),
        _dispsign=1.0,
    )
    # The properties under test read their two siblings; resolve those through
    # the shipped getters so the stub carries the real values, not guesses.
    _s._is_hoc_cycling = PlutoAPRomAssessWindow._is_hoc_cycling.fget(_s)
    _s._is_hoc_prom = PlutoAPRomAssessWindow._is_hoc_prom.fget(_s)
    _s._is_hoc_corner_anchored = (
        PlutoAPRomAssessWindow._is_hoc_corner_anchored.fget(_s)
    )
    return _s


def _disc_stub(arom, limb="right", mech="HOC"):
    _s = types.SimpleNamespace(
        data=types.SimpleNamespace(
            mechanism=mech, limb=limb, arom=list(arom),
        ),
        _dispsign=1.0,
    )
    # _hoc_display_span calls self._xpos; bind the real one to the stub so the
    # span is built from the shipped mapping rather than a copy of it.
    _s._xpos = lambda pos: PlutoDiscReachAssessWindow._xpos(_s, pos)
    return _s


def _xpos(stub, pos):
    return PlutoDiscReachAssessWindow._xpos(stub, pos)


#
# AROM / PROM window
#
def test_hoc_prom_is_corner_anchored_like_arom():
    """The regression: HOC PROM drew its cursor through _xpos but kept the
    symmetric axis, so the whole display sat in one half of the view."""
    for _romtype in (pfadef.ROMType.ACTIVE, pfadef.ROMType.PASSIVE):
        _s = _rom_stub(_romtype)
        assert PlutoAPRomAssessWindow._is_hoc_corner_anchored.fget(_s) is True, _romtype


def test_non_hoc_is_not_corner_anchored():
    _s = _rom_stub(pfadef.ROMType.PASSIVE, mech="WFE")
    assert PlutoAPRomAssessWindow._is_hoc_corner_anchored.fget(_s) is False


def test_hoc_range_contains_the_whole_aperture():
    """A passive hand can be opened anywhere from closed to the device limit, so
    the axis has to hold all of 0..MAXHOC — for either hand, since a left hand
    mirrors through MAXHOC - pos."""
    for _romtype in (pfadef.ROMType.ACTIVE, pfadef.ROMType.PASSIVE):
        for _limb in ("left", "right"):
            _s = _rom_stub(_romtype, limb=_limb)
            _lo, _hi = PlutoAPRomAssessWindow._hoc_x_range(_s)
            for _pos in (0.0, MAXHOC / 2.0, MAXHOC):
                _x = PlutoAPRomAssessWindow._xpos(_s, _pos)
                assert _lo <= _x <= _hi, (_romtype, _limb, _pos, _x, _lo, _hi)


def test_hoc_range_is_not_mostly_empty():
    """The old bug in one number: content spanned 0..9.4 on a 20-wide view."""
    _s = _rom_stub(pfadef.ROMType.PASSIVE)
    _lo, _hi = PlutoAPRomAssessWindow._hoc_x_range(_s)
    assert MAXHOC / (_hi - _lo) > 0.85, (_lo, _hi)


#
# Discrete reaching
#
def test_disc_span_holds_both_targets():
    """Targets sit at 20% and 80% of the recorded AROM; both must be on screen,
    with their half-widths, for either hand."""
    _arom = [0.0, 4.6]
    _range = _arom[1] - _arom[0]
    for _limb in ("left", "right"):
        _s = _disc_stub(_arom, limb=_limb)
        _lo, _hi = PlutoDiscReachAssessWindow._hoc_display_span(_s)
        for _frac in (pfadef.DiscreteReach.TGT1_POSITION,
                      pfadef.DiscreteReach.TGT2_POSITION):
            _tgt = _xpos(_s, _frac * _range + _arom[0])
            _half = 0.5 * pfadef.DiscreteReach.TGT_WIDTH * _range
            assert _lo <= _tgt - _half and _tgt + _half <= _hi, (
                _limb, _frac, _tgt, _lo, _hi
            )


def test_disc_span_tracks_the_subject_not_the_device():
    """A subject who opens to 4.6 cm of a 9.4 cm device used to get half a
    screen; the axis now follows the recorded AROM."""
    _s = _disc_stub([0.0, 4.6])
    _lo, _hi = PlutoDiscReachAssessWindow._hoc_display_span(_s)
    _used = (_xpos(_s, 4.6) - _xpos(_s, 0.0)) / (_hi - _lo)
    assert _used > 0.8, (_used, _lo, _hi)
    assert (_hi - _lo) < MAXHOC, (_lo, _hi)


def test_disc_span_still_anchors_the_closed_end_by_hand():
    """The zoom must not undo the corner anchoring: a right hand opens away from
    the left edge, a left hand away from the right edge."""
    _arom = [0.0, 4.6]
    _r = _disc_stub(_arom, limb="right")
    _rlo, _rhi = PlutoDiscReachAssessWindow._hoc_display_span(_r)
    assert _xpos(_r, 0.0) - _rlo < _rhi - _xpos(_r, 0.0), "closed end not near the left"
    _l = _disc_stub(_arom, limb="left")
    _llo, _lhi = PlutoDiscReachAssessWindow._hoc_display_span(_l)
    assert _lhi - _xpos(_l, 0.0) < _xpos(_l, 0.0) - _llo, "closed end not near the right"


def test_disc_span_survives_a_degenerate_arom():
    """A flat or missing AROM must not collapse the axis to a single point."""
    for _arom in ([3.0, 3.0], [0.0, 0.0]):
        _s = _disc_stub(_arom)
        _lo, _hi = PlutoDiscReachAssessWindow._hoc_display_span(_s)
        assert _hi > _lo, (_arom, _lo, _hi)


def test_disc_span_handles_an_unsorted_arom():
    """get_arom returns whatever was recorded; the low end is not guaranteed
    first."""
    _s = _disc_stub([4.6, 0.0])
    _lo, _hi = PlutoDiscReachAssessWindow._hoc_display_span(_s)
    assert _lo < _hi, (_lo, _hi)
    assert _lo <= _xpos(_s, 0.0) <= _hi
    assert _lo <= _xpos(_s, 4.6) <= _hi


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
