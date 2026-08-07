"""Standalone logic checks for the guided-GUI sequencer.
Run: uv run python tests/test_newgui_sequencer.py  ->  prints OK."""
import pathlib
import sys

# Make the repo root importable when run as `python tests/test_newgui_sequencer.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import plutofullassessdef as pfadef
from newgui.sequencer import (
    ASSESSMENT_MECHANISMS,
    CALIB,
    SCREENING_MECHANISMS,
    Sequencer,
    Step,
    build_steps,
    disc_skip_reason,
    mechanisms_for_mode,
)


def _mech_order(steps):
    seen = []
    for s in steps:
        if s.mech not in seen:
            seen.append(s.mech)
    return seen


def test_assessment_step_list():
    steps = build_steps("assessment")
    # 4 mechanisms x (calib + 4 tasks)
    assert len(steps) == 4 * 5, len(steps)
    assert steps[0] == Step("WURD", CALIB)
    assert [s.task for s in steps[:5]] == [CALIB, "AROM", "PROM", "APROM", "DISC"]
    # Assessment walks the wrist first, the hand last.
    assert _mech_order(steps) == ["WURD", "WFE", "FPS", "HOC"], _mech_order(steps)


def test_screening_step_list():
    steps = build_steps("screening")
    assert len(steps) == 4 * 2, len(steps)
    assert [s.task for s in steps[:2]] == [CALIB, "AROM"]
    assert all(s.task in (CALIB, "AROM") for s in steps)
    # Screening walks the hand first, the wrist last — the reverse of assessment.
    assert _mech_order(steps) == ["HOC", "FPS", "WFE", "WURD"], _mech_order(steps)


def test_both_modes_cover_every_mechanism():
    """Order differs per mode, but neither may drop or invent a mechanism."""
    assert set(SCREENING_MECHANISMS) == set(pfadef.MECHANISMS)
    assert set(ASSESSMENT_MECHANISMS) == set(pfadef.MECHANISMS)
    assert mechanisms_for_mode("screening") == SCREENING_MECHANISMS
    assert mechanisms_for_mode("assessment") == ASSESSMENT_MECHANISMS


def test_advance_and_position():
    seq = Sequencer("assessment")
    assert seq.current() == Step("WURD", CALIB)
    assert seq.position() == (1, 20)
    assert seq.is_done() is False
    seq.advance()
    assert seq.current() == Step("WURD", "AROM")
    assert seq.position() == (2, 20)


def test_advance_to_end():
    seq = Sequencer("screening")
    for _ in range(len(seq.steps)):
        seq.advance()
    assert seq.is_done() is True
    assert seq.current() is None


def test_advance_skips_completed_steps():
    """Auto-skipped DISC (marked completed) is stepped over, landing on the
    next mechanism's calibration."""
    seq = Sequencer("assessment")
    while seq.current() != Step("WURD", "APROM"):
        seq.advance()
    seq.mark_completed(Step("WURD", "DISC"))
    seq.advance()
    assert seq.current() == Step("WFE", CALIB), seq.current()


def test_resume_mid_mechanism_returns_to_that_calibration():
    seq = Sequencer("assessment")
    seq.resume_from([("WURD", "AROM"), ("WURD", "PROM")])
    assert seq.current() == Step("WURD", CALIB), seq.current()
    seq.advance()
    assert seq.current() == Step("WURD", "APROM"), seq.current()


def test_resume_past_a_finished_mechanism():
    seq = Sequencer("assessment")
    seq.resume_from(
        [("WURD", t) for t in ("AROM", "PROM", "APROM", "DISC")]
    )
    assert seq.current() == Step("WFE", CALIB), seq.current()


def test_resume_everything_done():
    seq = Sequencer("screening")
    seq.resume_from([(m, "AROM") for m in pfadef.MECHANISMS])
    assert seq.is_done() is True


def test_disc_skip_reason():
    # No AROM recorded at all.
    assert disc_skip_reason("WFE", None) == "No valid AROM recorded"
    # Joint mechanism below the 10 deg threshold.
    assert disc_skip_reason("WFE", [0.0, 4.0]) == (
        "AROM 4.00deg below 10.0deg threshold"
    )
    # Joint mechanism above threshold -> not skipped.
    assert disc_skip_reason("WFE", [0.0, 40.0]) is None
    # HOC uses cm and a 2.0 threshold.
    assert disc_skip_reason("HOC", [0.0, 1.0]) == (
        "AROM 1.00cm below 2.0cm threshold"
    )
    assert disc_skip_reason("HOC", [0.0, 5.0]) is None


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
