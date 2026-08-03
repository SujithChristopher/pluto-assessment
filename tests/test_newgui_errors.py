"""Standalone checks for the guided GUI's crash reporting.

Verifies that a run writes a log file and that an unhandled exception is
recorded in it — the whole point being that a crash on the assessment machine
leaves evidence behind instead of vanishing with the terminal window.

Run: uv run python tests/test_newgui_errors.py  ->  prints OK."""
import os
import pathlib
import sys
import tempfile

# Make the repo root importable when run as `python tests/test_newgui_errors.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# newgui.errors imports PySide6; running headless avoids needing a display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import plutofullassessdef as pfadef

# Point the data root at a temp dir BEFORE anything writes to it, so the test
# never touches the operator's real HomerPlutoData tree.
_TMP = pathlib.Path(tempfile.mkdtemp())
pfadef.homer_data_root = lambda: _TMP

from newgui import errors


def test_install_creates_a_log_file():
    _path = errors.install_error_handling()
    assert _path.exists(), _path
    assert _path.parent == _TMP / "logs", _path
    assert errors.logfile() == _path
    assert "Guided GUI starting" in _path.read_text(encoding="utf-8")


def test_handled_exception_is_logged_with_its_traceback():
    _path = errors.install_error_handling()
    try:
        raise ValueError("port fell over")
    except ValueError as _exc:
        errors.log_exception("Opening the device", _exc)
    _text = _path.read_text(encoding="utf-8")
    assert "Opening the device" in _text, _text
    assert "ValueError: port fell over" in _text, _text
    # The traceback itself, not just the message — that is what makes a log
    # worth asking the operator for.
    assert "Traceback (most recent call last)" in _text, _text


def test_unhandled_exception_is_logged_and_does_not_raise():
    """sys.excepthook must record the failure and return, so one bad callback
    does not take the assessment window down."""
    _path = errors.install_error_handling()
    _stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        raise RuntimeError("callback exploded")
    except RuntimeError:
        _exctype, _value, _tb = sys.exc_info()
        try:
            sys.excepthook(_exctype, _value, _tb)   # must not raise
        finally:
            sys.stderr.close()
            sys.stderr = _stderr
    _text = _path.read_text(encoding="utf-8")
    assert "Unhandled exception" in _text, _text
    assert "RuntimeError: callback exploded" in _text, _text


def test_show_error_without_a_qapplication_is_a_noop():
    """Reporting must never become its own crash when there is no GUI."""
    errors.install_error_handling()
    errors.show_error("Title", "Body")   # no QApplication instance exists here


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
