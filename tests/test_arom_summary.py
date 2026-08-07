"""Standalone checks for get_arom_summary / get_screening_eligibility.

These read the details JSON that the guided flow actually writes, so the three
outcomes have to be derived from real recorded entries rather than from a hand
-made dict: a completed AROM, one the subject could not finish inside
AROM.TRIAL_TIME_LIMIT (logged Skipped by the terminate path), and one never
reached at all.

Run: uv run python tests/test_arom_summary.py  ->  prints OK."""
import contextlib
import io
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import plutofullassessdef as pfadef
import plutofullassesssdata as pfad

QUIET = contextlib.redirect_stdout(io.StringIO())


def _details(mode="screening"):
    _dir = tempfile.mkdtemp(prefix="aromsum_")
    return pfad.PlutoAssessmentDetailsData(
        "T001", mode, "right", "left", "left", "A0", _dir
    )


def _record(det, mech, rom):
    det.set_mechanism(mech)
    det.set_task("AROM")
    det.update(
        romval=[rom], session="s1", tasktime="20260101_120000",
        rawfile="r.csv", summaryfile="s.csv", taskcomment="",
        status=pfadef.AssessStatus.COMPLETE.value,
    )


def _time_out(det, mech):
    """What _handle_task_terminated does when AROM hits the trial time limit."""
    det.set_mechanism(mech)
    det.set_task("AROM")
    det.skip_task("AROM", "s1", "Terminated by trial time limit")


def test_the_three_outcomes():
    _d = _details()
    with QUIET:
        _record(_d, "HOC", [0.0, 5.4])
        _time_out(_d, "FPS")
        # WFE and WURD are left untouched.
    _sum = _d.get_arom_summary()
    assert _sum["HOC"]["outcome"] == "complete", _sum["HOC"]
    assert abs(_sum["HOC"]["value"] - 5.4) < 1e-9, _sum["HOC"]
    assert _sum["HOC"]["unit"] == "cm", _sum["HOC"]
    assert _sum["FPS"]["outcome"] == "failed", _sum["FPS"]
    assert _sum["FPS"]["value"] is None, _sum["FPS"]
    assert _sum["WFE"]["outcome"] == "not attempted", _sum["WFE"]
    assert _sum["WURD"]["outcome"] == "not attempted", _sum["WURD"]


def test_units_are_per_mechanism():
    _d = _details()
    with QUIET:
        _record(_d, "WFE", [-20.0, 20.0])
    _sum = _d.get_arom_summary()
    assert _sum["WFE"]["unit"] == "deg", _sum["WFE"]
    assert abs(_sum["WFE"]["value"] - 40.0) < 1e-9, _sum["WFE"]


def test_a_failed_mechanism_cannot_pass_screening():
    """The subject never produced a number, so there is nothing to compare with
    the threshold — eligibility must not be inferred from the attempt."""
    _d = _details()
    with QUIET:
        _time_out(_d, "FPS")
    _eligible, _stats = _d.get_screening_eligibility()
    assert _eligible is False, _stats
    assert _stats["FPS"]["pass"] is False, _stats["FPS"]
    assert _stats["FPS"]["outcome"] == "failed", _stats["FPS"]


def test_eligibility_needs_only_one_mechanism():
    _d = _details()
    with QUIET:
        _time_out(_d, "FPS")
        _record(_d, "HOC", [0.0, 5.4])       # clears the 2.0 cm threshold
    _eligible, _stats = _d.get_screening_eligibility()
    assert _eligible is True, _stats
    assert _stats["HOC"]["pass"] is True, _stats["HOC"]
    assert _stats["FPS"]["pass"] is False, _stats["FPS"]


def test_a_measured_but_low_arom_is_not_a_failure():
    _d = _details()
    with QUIET:
        _record(_d, "FPS", [0.0, 4.0])       # under the 10 deg threshold
    _eligible, _stats = _d.get_screening_eligibility()
    assert _eligible is False, _stats
    assert _stats["FPS"]["outcome"] == "complete", _stats["FPS"]
    assert abs(_stats["FPS"]["value"] - 4.0) < 1e-9, _stats["FPS"]


def test_every_mechanism_has_a_threshold_in_screening_stats():
    _d = _details()
    _eligible, _stats = _d.get_screening_eligibility()
    for _m in pfadef.MECHANISMS:
        assert _stats[_m]["threshold"] == pfadef.SCREENING_AROM_THRESHOLDS[_m]
        assert _stats[_m]["unit"] == pfadef.MECH_UNITS[_m]


def test_assessment_summary_carries_no_verdict_fields():
    """get_arom_summary is the assessment readout; it must not leak a pass flag
    that the assessment page would then be tempted to render."""
    _d = _details(mode="assessment")
    with QUIET:
        _record(_d, "WURD", [-15.0, 15.0])
    _sum = _d.get_arom_summary()
    assert set(_sum["WURD"]) == {"value", "unit", "outcome"}, _sum["WURD"]


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
