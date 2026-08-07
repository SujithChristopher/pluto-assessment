"""Standalone checks for the AROM trial-time-limit prompt.

When the subject cannot finish AROM inside AROM.TRIAL_TIME_LIMIT the assessor is
asked to redo the trial or move on. With MAX_FAILED_TRIALS == 1 there is no next
trial, so moving on ends AROM and disables discrete reaching — the prompt has to
say that is what is being accepted, not offer to "skip" a task.

The prompt is built inline in _handle_trial_timeout, which needs a live device, a
running trial and a modal event loop, so its wording is pinned by reading the
shipped source rather than by driving the dialog. The invariants that outlive
the wording — the constants that make the first timeout terminal, the status
that disables discrete reaching — are asserted directly.

Run: uv run python tests/test_arom_timeout_dialog.py  ->  prints OK."""
import inspect
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import plutofullassessdef as pfadef
from plutoapromwindow import PlutoAPRomAssessWindow

_SRC = inspect.getsource(PlutoAPRomAssessWindow._handle_trial_timeout)
_CLOSE_SRC = inspect.getsource(PlutoAPRomAssessWindow.closeEvent)


def test_one_timed_out_trial_ends_arom():
    """The premise of the new wording: with these constants the very first
    timeout is terminal, so the terminating branch is the one the assessor
    actually sees."""
    assert pfadef.AROM.MAX_FAILED_TRIALS == 1, pfadef.AROM.MAX_FAILED_TRIALS
    assert pfadef.AROM.MAX_FAILED_TRIALS <= pfadef.AROM.NO_OF_TRIALS
    assert pfadef.AROM.TRIAL_TIME_LIMIT == 60.0, pfadef.AROM.TRIAL_TIME_LIMIT


def test_the_prompt_says_arom_is_not_satisfied():
    assert "AROM not satisfied" in _SRC, _SRC
    assert "AROM is not satisfied" in _SRC, _SRC
    assert "discrete reaching will be " in _SRC, _SRC


def test_the_button_accepts_rather_than_skips():
    assert '"Accept" if _terminates else "Next Trial"' in _SRC, _SRC
    assert "Redo Trial" in _SRC, _SRC
    # No skip language survives in anything the assessor reads. The internal
    # _arom_skipped flag keeps its name — it feeds AssessStatus.SKIPPED, which
    # is what the protocol records and what excludes DISC.
    for _gone in ("Skip AROM", "skip AROM", "Skipping"):
        assert _gone not in _SRC, (_gone, _SRC)


def test_the_time_limit_is_read_from_the_constant():
    """Hardcoding "60s" would quietly lie the day the limit changes."""
    assert "int(AROM.TRIAL_TIME_LIMIT)" in _SRC, _SRC
    assert "60" not in _SRC, _SRC


def test_the_logged_reason_matches_what_was_accepted():
    """taskcomment is what lands in the protocol CSV; it should read like the
    dialog the assessor accepted, not like a skip."""
    assert "AROM not satisfied" in _CLOSE_SRC, _CLOSE_SRC
    assert "discrete reaching disabled" in _CLOSE_SRC, _CLOSE_SRC
    assert "unable to perform" not in _CLOSE_SRC, _CLOSE_SRC


def test_the_outcome_is_still_recorded_as_skipped():
    """Only the wording changed. SKIPPED is the status that drives the
    dependent-task exclusion (DISC depends_on AROM), so it must not move."""
    assert "AssessStatus.SKIPPED.value" in _CLOSE_SRC, _CLOSE_SRC
    assert "DISC" in pfadef.TASK_DEPENDENCIES, pfadef.TASK_DEPENDENCIES
    assert "AROM" in pfadef.TASK_DEPENDENCIES["DISC"]["depends_on"]


def test_the_shell_still_disables_discrete_reaching():
    """End to end on the shell side: the terminated payload must skip the task
    and mark DISC done so the flow steps past it."""
    from newgui.shell import PlutoGuidedAssessor

    _src = inspect.getsource(PlutoGuidedAssessor._handle_task_terminated)
    assert "_skip_step" in _src, _src
    assert 'Step(_step.mech, "DISC")' in _src, _src


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
