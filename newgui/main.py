"""Entry point for the guided PLUTO assessment GUI.

Run: uv run python newgui/main.py"""

import pathlib
import sys

# Make the repository root importable when run as a script from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from plutofullassessment import APP_STYLESHEET
from newgui import errors
from newgui.shell import PlutoGuidedAssessor


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    _logfile = errors.install_error_handling()
    try:
        window = PlutoGuidedAssessor(port=pfadef.PLUTOCOMM)
    except Exception as _exc:
        # Almost always the serial port: PLUTO switched off, a stale Bluetooth
        # pairing, or the wrong port in config.json. Say so rather than dying
        # with a traceback into a terminal nobody is watching.
        errors.log_exception("Could not start the guided GUI", _exc)
        errors.show_error(
            "Cannot connect to PLUTO",
            f"Could not open {pfadef.PLUTOCOMM}.\n\n"
            f"{type(_exc).__name__}: {_exc}\n\n"
            "Check that PLUTO is switched on and connected, and that "
            f"\"com_port\" in\n{pfadef.CONFIG_FILE}\nnames the right port.",
            detail=str(_logfile),
        )
        sys.exit(1)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
