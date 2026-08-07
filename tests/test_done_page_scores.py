"""Standalone checks for the end-of-session scores on the Done page.

Screening judges each mechanism's AROM against a threshold and leads with the
eligibility verdict; assessment shows the same numbers with no verdict. Both
have to tell three outcomes apart: recorded, attempted-but-not-finished-in-time
("failed"), and never attempted — collapsing the last two would read as if a
subject who ran out of time had simply not been tested.

Run: uv run python tests/test_done_page_scores.py  ->  prints OK."""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from newgui.sequencer import ASSESSMENT_MECHANISMS, SCREENING_MECHANISMS
from newgui.shell import DonePage

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _summary(**vals):
    """get_arom_summary()-shaped dict. A float is a recorded range, the string
    "failed" is a timed-out attempt, and None is never attempted."""
    _out = {}
    for _m in pfadef.MECHANISMS:
        _v = vals.get(_m)
        _out[_m] = {
            "value": _v if isinstance(_v, float) else None,
            "unit": pfadef.MECH_UNITS[_m],
            "outcome": (
                "complete" if isinstance(_v, float)
                else "failed" if _v == "failed"
                else "not attempted"
            ),
        }
    return _out


def _stats(**vals):
    """The same, with the screening threshold and pass flag added."""
    _out = _summary(**vals)
    for _m, _s in _out.items():
        _s["threshold"] = pfadef.SCREENING_AROM_THRESHOLDS[_m]
        _s["pass"] = (
            _s["outcome"] == "complete" and _s["value"] >= _s["threshold"]
        )
    return _out


#
# Screening
#
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


def test_a_timed_out_mechanism_reads_as_failed_not_as_untested():
    """A subject who could not finish AROM inside the time limit must not be
    reported the same way as a mechanism that was never run."""
    _p = DonePage()
    _p.show_screening_scores(_stats(FPS="failed", HOC=None), SCREENING_MECHANISMS)
    _html = _p.lblScores.text()
    assert "failed" in _html, _html
    assert "not completed in time" in _html, _html
    assert "not attempted" in _html, _html
    assert "—" in _html, _html


def test_below_threshold_is_distinct_from_failed():
    """A measured-but-low AROM is a real number and must still be shown."""
    _p = DonePage()
    _p.show_screening_scores(_stats(FPS=4.0), SCREENING_MECHANISMS)
    _html = _p.lblScores.text()
    assert "4.0 deg" in _html, _html
    assert "below threshold" in _html, _html
    assert "failed" not in _html, _html


def test_table_agrees_with_the_verdict():
    """Screening passes if ANY mechanism clears its threshold — the table must
    show a pass exactly when the verdict is ELIGIBLE."""
    for _vals, _eligible in (
        ({"HOC": 5.0}, True),                     # HOC alone clears 2.0 cm
        ({"FPS": 4.0, "WFE": "failed"}, False),   # one short, one timed out
    ):
        _p = DonePage()
        _p.show_screening_scores(_stats(**_vals), SCREENING_MECHANISMS)
        _html = _p.lblScores.text()
        assert (">pass<" in _html) is _eligible, (_vals, _html)


#
# Assessment
#
def test_assessment_shows_numbers_without_a_verdict():
    _p = DonePage()
    _p.show_assessment_scores(_summary(FPS=38.4, WFE=30.0, WURD=12.0, HOC=5.2),
                              ASSESSMENT_MECHANISMS)
    _html = _p.lblScores.text()
    assert "38.4 deg" in _html, _html
    assert "5.2 cm" in _html, _html
    for _word in ("pass", "below threshold", "Threshold", "&ge;"):
        assert _word not in _html, (_word, _html)


def test_assessment_reads_in_assessment_order():
    _p = DonePage()
    _p.show_assessment_scores(_summary(FPS=38.4, WFE=30.0, WURD=12.0, HOC=5.2),
                              ASSESSMENT_MECHANISMS)
    _html = _p.lblScores.text()
    _pos = [_html.index(pfadef.MECH_LABELS[_m]) for _m in ASSESSMENT_MECHANISMS]
    assert _pos == sorted(_pos), (ASSESSMENT_MECHANISMS, _pos)


def test_assessment_still_distinguishes_failed_from_untested():
    _p = DonePage()
    _p.show_assessment_scores(_summary(WURD="failed", HOC=None),
                              ASSESSMENT_MECHANISMS)
    _html = _p.lblScores.text()
    assert "failed" in _html, _html
    assert "—" in _html, _html


def test_scores_can_be_cleared():
    _p = DonePage()
    _p.show_screening_scores(_stats(HOC=5.0), SCREENING_MECHANISMS)
    assert _p.lblScores.text() != ""
    _p.clear_scores()
    assert _p.lblScores.text() == ""


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
