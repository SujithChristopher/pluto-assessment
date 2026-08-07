"""Standalone checks for the screening scores on the Done page.

The verdict word (ELIGIBLE / NOT ELIGIBLE) is derived from the per-mechanism
AROM, so the table beside it has to agree with that verdict and has to survive
the cases where a mechanism was never recorded.

Run: uv run python tests/test_done_page_scores.py  ->  prints OK."""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from newgui.sequencer import SCREENING_MECHANISMS
from newgui.shell import DonePage

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _stats(**vals):
    """Build a get_screening_eligibility()-shaped stats dict; a mechanism given
    None was never recorded."""
    _out = {}
    for _m in pfadef.MECHANISMS:
        _v = vals.get(_m)
        _thresh = pfadef.SCREENING_AROM_THRESHOLDS[_m]
        _out[_m] = {
            "value": _v,
            "threshold": _thresh,
            "unit": pfadef.SCREENING_AROM_UNITS[_m],
            "pass": _v is not None and _v >= _thresh,
            "done": _v is not None,
        }
    return _out


def test_every_mechanism_appears_in_screening_order():
    _p = DonePage()
    _p.show_screening_scores(_stats(FPS=40.0, WFE=30.0, WURD=12.0, HOC=5.0),
                             SCREENING_MECHANISMS)
    _html = _p.lblScores.text()
    _pos = [_html.index(pfadef.MECH_LABELS[_m]) for _m in SCREENING_MECHANISMS]
    assert _pos == sorted(_pos), (SCREENING_MECHANISMS, _pos)


def test_values_units_and_thresholds_are_rendered():
    _p = DonePage()
    _p.show_screening_scores(_stats(FPS=40.0, WFE=30.0, WURD=12.0, HOC=5.0),
                             SCREENING_MECHANISMS)
    _html = _p.lblScores.text()
    assert "40.0 deg" in _html, _html
    assert "5.0 cm" in _html, _html          # HOC is an aperture, not an angle
    assert "&ge; 10 deg" in _html, _html
    assert "&ge; 2 cm" in _html, _html


def test_below_threshold_and_missing_mechanisms():
    """A mechanism under its threshold reads as such; one never recorded shows a
    dash rather than a fabricated 0."""
    _p = DonePage()
    _p.show_screening_scores(_stats(FPS=4.0, HOC=None), SCREENING_MECHANISMS)
    _html = _p.lblScores.text()
    assert "4.0 deg" in _html, _html
    assert "below threshold" in _html, _html
    assert "not recorded" in _html, _html
    assert "—" in _html, _html


def test_table_agrees_with_the_verdict():
    """Screening passes if ANY mechanism clears its threshold — the table must
    show at least one pass exactly when the verdict is ELIGIBLE."""
    for _vals, _eligible in (
        ({"HOC": 5.0}, True),               # HOC alone clears 2.0 cm
        ({"FPS": 4.0, "WFE": 2.0}, False),  # everything short
    ):
        _p = DonePage()
        _p.show_screening_scores(_stats(**_vals), SCREENING_MECHANISMS)
        _html = _p.lblScores.text()
        assert (">pass<" in _html) is _eligible, (_vals, _html)


def test_scores_are_cleared_for_an_assessment_session():
    _p = DonePage()
    _p.show_screening_scores(_stats(HOC=5.0), SCREENING_MECHANISMS)
    assert _p.lblScores.text() != ""
    _p.clear_screening_scores()
    assert _p.lblScores.text() == ""


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
