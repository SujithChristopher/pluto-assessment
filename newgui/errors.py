"""Crash visibility for the guided GUI.

Two jobs:

1. Every run writes a log file, so a crash on the assessment machine can be
   read afterwards instead of being lost with the terminal window.
2. An unhandled exception shows the operator a dialog naming the error and the
   log file, instead of dying silently or printing into a console nobody is
   watching.

The handler deliberately does NOT quit the application. A failure inside one
callback usually leaves the rest of the session usable, and the operator is
better served by being told and deciding than by the window vanishing
mid-assessment."""

import logging
import pathlib
import sys
import traceback
from datetime import datetime as dt

from PySide6 import QtWidgets

import plutofullassessdef as pfadef

_LOGGER_NAME = "newgui"
_logfile: pathlib.Path | None = None
# Guard against an exception raised while reporting an exception, which would
# otherwise recurse until the stack blows.
_reporting = False


def logfile() -> pathlib.Path | None:
    """Path of this run's log file, once install_error_handling has run."""
    return _logfile


def install_error_handling() -> pathlib.Path:
    """Start file logging and route unhandled exceptions to a dialog.

    Returns the log file path. Logs live under the configured data root so they
    sit beside the session data and get picked up by the S3 sync."""
    global _logfile
    _dir = pfadef.homer_data_root() / "logs"
    _dir.mkdir(parents=True, exist_ok=True)
    _logfile = _dir / f"newgui_{dt.now():%Y%m%d_%H%M%S}.log"

    _log = logging.getLogger(_LOGGER_NAME)
    _log.setLevel(logging.INFO)
    _log.handlers.clear()
    _handler = logging.FileHandler(_logfile, encoding="utf-8")
    _handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    )
    _log.addHandler(_handler)
    _log.info("Guided GUI starting (port %s, data root %s)",
              pfadef.PLUTOCOMM, pfadef.homer_data_root())

    sys.excepthook = _excepthook
    return _logfile


def log(message: str, *args) -> None:
    """Record a milestone in this run's log file."""
    logging.getLogger(_LOGGER_NAME).info(message, *args)


def log_exception(context: str, exc: BaseException) -> None:
    """Record an exception that was caught and handled."""
    logging.getLogger(_LOGGER_NAME).error(
        "%s: %s", context, "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    )


def show_error(title: str, text: str, detail: str = "") -> None:
    """Tell the operator something went wrong. No-op without a QApplication
    (unit tests, headless runs) so reporting never becomes its own crash."""
    _app = QtWidgets.QApplication.instance()
    if _app is None:
        return
    _box = QtWidgets.QMessageBox()
    _box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    _box.setWindowTitle(title)
    _box.setText(text)
    if _logfile is not None:
        _box.setInformativeText(f"Written to the log file:\n{_logfile}")
    if detail:
        _box.setDetailedText(detail)
    _box.exec()


def _excepthook(exctype, value, tb) -> None:
    """Log an unhandled exception and show it, then carry on."""
    global _reporting
    _detail = "".join(traceback.format_exception(exctype, value, tb))
    logging.getLogger(_LOGGER_NAME).error("Unhandled exception:\n%s", _detail)
    # Keep the console behaviour too — useful when run from a terminal.
    sys.__excepthook__(exctype, value, tb)
    if _reporting:
        return
    _reporting = True
    try:
        show_error(
            "Something went wrong",
            f"{exctype.__name__}: {value}\n\n"
            "The assessment has not been closed — check the screen before "
            "continuing, and report this with the log file.",
            detail=_detail,
        )
    except Exception:
        pass
    finally:
        _reporting = False
